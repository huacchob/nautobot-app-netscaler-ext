"""JSON remediation."""

from __future__ import annotations

import json
from collections import deque
from typing import TYPE_CHECKING, Any, Dict, Tuple

from django.core.exceptions import ValidationError

if TYPE_CHECKING:
    from nautobot_golden_config.models import ConfigCompliance


def _filter_allowed_params(
    feature_name: str,
    config_context: list[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Filter allowed parameters and remove unwanted parameters.

    Args:
        feature_name (str): Compliance feature name.
        config_context (ConfigContext): Device config context.
        config (dict[str, Any]): Intended or actual config.

    Returns:
        dict[str, Any]: Filtered config.
    """
    valid_payload_config: dict[str, Any] = {feature_name: {}}
    all_optional_arguments: list[str] = []
    for endpoint in config_context:
        all_optional_arguments.extend(endpoint["parameters"]["optional"])

    for key, value in config[feature_name].items():
        if key in all_optional_arguments:
            valid_payload_config[feature_name][key] = value
    return valid_payload_config


def _process_diff(diff: Dict[Any, Any], path: Tuple[str, ...], value: Any) -> None:
    """Process the diff.

    Args:
        diff (Dict[Any, Any]): Diff dictionary.
        path (Tuple[str, ...]): Path of dictionary keys.
        value (Any): The key's value.
    """
    for key in path[:-1]:
        diff = diff.setdefault(key, {})
    diff[path[-1]] = value


def controller_remediation(obj: "ConfigCompliance") -> str:
    """Controller remediation.

    Args:
        obj (ConfigCompliance): Compliance object.

    Raises:
        ValidationError: Intended or Actual does not have the feature name as the top level key.

    Returns:
        str: Remediation json config.
    """
    feature_name: str = obj.rule.feature.name.lower()
    intended: dict[str, Any] = _filter_allowed_params(
        feature_name=feature_name,
        config_context=obj.device.get_config_context().get(f"{feature_name}_remediation", ""),
        config=obj.intended,
    )
    actual: dict[str, Any] = _filter_allowed_params(
        feature_name=feature_name,
        config_context=obj.device.get_config_context().get(f"{feature_name}_remediation", ""),
        config=obj.actual,
    )
    diff: Dict[str, Any] = {}
    stack: deque[Tuple[Tuple[str, ...], Any, Any]] = deque()
    stack.append((tuple(), actual, intended))

    while stack:
        path, actual, intended = stack.pop()

        if isinstance(actual, dict) and isinstance(intended, dict):
            for i_key in intended:
                if i_key not in actual:
                    _process_diff(
                        diff=diff,
                        path=path + (i_key,),
                        value=intended[i_key],
                    )
                else:
                    stack.append((path + (i_key,), actual[i_key], intended[i_key]))

        else:
            if actual != intended:
                _process_diff(diff=diff, path=path, value=intended)

    if not diff.get(feature_name):
        raise ValidationError(f"Feature {feature_name} not found in the config.")
    return json.dumps(diff, indent=4)
