"""Hierconfig remediation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from hier_config import Host

if TYPE_CHECKING:
    from nautobot_golden_config.models import ConfigCompliance


def hierconfig_remediation(
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
