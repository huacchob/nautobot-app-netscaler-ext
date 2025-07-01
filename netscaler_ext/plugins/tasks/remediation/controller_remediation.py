"""JSON remediation."""

from __future__ import annotations

import json
from collections import deque
from typing import TYPE_CHECKING, Any, Dict, Tuple

from django.core.exceptions import ValidationError

if TYPE_CHECKING:
    from nautobot_golden_config.models import ConfigCompliance


def _feature_name_parser(feature_name: str) -> str:
    """Feature name parser.

    Args:
        feature_name (str): The feature name from config context.

    Returns:
        str: Parsed feature name.
    """
    if "_" in feature_name:
        feat = feature_name.rsplit(sep="_", maxsplit=1)[0]
    elif "-" in feature_name:
        feat = feature_name.rsplit(sep="-", maxsplit=1)[0]
    else:
        feat = feature_name.rsplit(sep=" ", maxsplit=1)[0]
    return feat


def _process_diff(diff: Dict[Any, Any], path: Tuple[str, ...], value: Any) -> None:
    """Process the diff.

    Args:
        diff (Dict[Any, Any]): Diff dictionary.
        path (Tuple[str, ...]): Path of dictionary keys.
        value (Any): The key's value.
    """
    d: Dict[Any, Any] = diff
    for key in path[:-1]:
        d = d.setdefault(key, {})
    d[path[-1]] = value


def controller_remediation(obj: "ConfigCompliance") -> str:
    """Controller remediation.

    Args:
        obj (ConfigCompliance): Compliance object.

    Raises:
        TypeError: Intended or Actual is not a dict.

    Returns:
        str: Remediation json config.
    """
    diff: Dict[str, Any] = {}
    stack: deque[Tuple[Tuple[str, ...], Any, Any]] = deque()
    stack.append((tuple(), obj.actual, obj.intended))

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

    parsed_feature_name: str = _feature_name_parser(feature_name=obj.rule.feature.name)
    if not diff.get(parsed_feature_name.lower()):
        raise ValidationError(f"Feature {parsed_feature_name} not found in diff.")
    return json.dumps(diff[parsed_feature_name.lower()], indent=4)
