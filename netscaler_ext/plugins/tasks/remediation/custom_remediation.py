"""Custom remediation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from netscaler_ext.plugins.tasks.remediation.controller_remediation import controller_remediation
from netscaler_ext.plugins.tasks.remediation.hierconfig_remediation import hierconfig_remediation

if TYPE_CHECKING:
    from nautobot_golden_config.models import ConfigCompliance


def remediation_func(
    obj: "ConfigCompliance",
) -> str:
    """Routes to the remediation function.

    Args:
        obj (ConfigCompliance): Compliance object.

    Returns:
        str: Remediation config.
    """
    if obj.device.get_config_context().get("remediation_endpoints"):
        return controller_remediation(obj=obj)
    return hierconfig_remediation(obj=obj)
