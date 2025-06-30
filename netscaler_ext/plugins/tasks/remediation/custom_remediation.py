"""Custom remediation."""

from __future__ import annotations

import json
from collections import deque
from typing import TYPE_CHECKING, Any, Dict, Tuple

from django.core.exceptions import ValidationError
from hier_config import Host

if TYPE_CHECKING:
    from nautobot_golden_config.models import ConfigCompliance


def regular_remediation(
    obj: "ConfigCompliance",
) -> str:
    """Returns the remediating config.

    Args:
        obj (ConfigCompliance): Compliance object.

    Returns:
        str: Remediation config.
    """
    from nautobot_golden_config.models import RemediationSetting

    hierconfig_os = obj.device.platform.network_driver_mappings["hier_config"]
    if not hierconfig_os:
        raise ValidationError(f"platform {obj.device.platform.network_driver} is not supported by hierconfig.")

    try:
        remediation_setting_obj = RemediationSetting.objects.get(platform=obj.rule.platform)
    except Exception as err:  # pylint: disable=broad-except:
        raise ValidationError(f"Platform {obj.network_driver} has no Remediation Settings defined.") from err

    remediation_options = remediation_setting_obj.remediation_options

    try:
        hc_kwargs = {"hostname": obj.device.name, "os": hierconfig_os}
        if remediation_options:
            hc_kwargs.update(hconfig_options=remediation_options)
        host = Host(**hc_kwargs)

    except Exception as err:  # pylint: disable=broad-except:
        raise Exception(  # pylint: disable=broad-exception-raised
            f"Cannot instantiate HierConfig on {obj.device.name}, check Device, Platform and Hier Options."
        ) from err

    host.load_generated_config(config_text=obj.intended)
    host.load_running_config(config_text=obj.actual)
    host.remediation_config()
    remediation_config = host.remediation_config_filtered_text(include_tags={}, exclude_tags={})

    return remediation_config


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


def remediation_func(
    obj: "ConfigCompliance",
) -> str:
    """Routes to the remediation function.

    Args:
        obj (ConfigCompliance): Compliance object.

    Returns:
        str: Remediation config.
    """
    if obj.device.platform.name in ["meraki_managed"]:
        return controller_remediation(obj=obj)
    else:
        return regular_remediation(obj=obj)
