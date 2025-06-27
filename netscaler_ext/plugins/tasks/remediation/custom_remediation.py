"""Custom remediation."""

# from django.core.exceptions import ValidationError
# from hier_config import Host as HierConfigHost
from nautobot_golden_config.models import (
    ConfigCompliance,
    _get_hierconfig_remediation,
)

# from nautobot_golden_config.models import (
#     ConfigCompliance,
#     RemediationSetting,
#     _get_hierconfig_remediation,
# )


def remediation_func(obj: ConfigCompliance) -> str:
    """Returns the remediating config.

    Args:
        obj (ConfigCompliance): Compliance object.

    Returns:
        str: Remediation config.
    """
    if obj.device.platform.name == "cisco_nxos":
        return _get_hierconfig_remediation(obj=obj)
    # hierconfig_os = obj.device.platform.network_driver_mappings["hier_config"]

    # try:
    #     remediation_setting_obj = RemediationSetting.objects.get(platform=obj.rule.platform)
    # except Exception as err:  # pylint: disable=broad-except:
    #     raise ValidationError(f"Platform {obj.network_driver} has no Remediation Settings defined.") from err

    # remediation_options = remediation_setting_obj.remediation_options

    # try:
    #     hc_kwargs = {"hostname": obj.device.name, "os": hierconfig_os}
    #     if remediation_options:
    #         hc_kwargs.update(hconfig_options=remediation_options)
    #     host = HierConfigHost(**hc_kwargs)

    # except Exception as err:  # pylint: disable=broad-except:
    #     raise Exception(  # pylint: disable=broad-exception-raised
    #         f"Cannot instantiate HierConfig on {obj.device.name}, check Device, Platform and Hier Options."
    #     ) from err

    # host.load_generated_config(obj.intended)
    # host.load_running_config(obj.actual)
    # host.remediation_config()
    # remediation_config = host.remediation_config_filtered_text(include_tags={}, exclude_tags={})

    # return remediation_config
