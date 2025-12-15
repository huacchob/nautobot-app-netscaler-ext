"""App declaration for netscaler_ext."""

# Metadata is inherited from Nautobot. If not including Nautobot in the environment, this should be added
from importlib import metadata

from nautobot.apps import NautobotAppConfig

__version__ = metadata.version(__name__)


class NetscalerExtConfig(NautobotAppConfig):
    """App configuration for the netscaler_ext app."""

    name = "netscaler_ext"
    verbose_name = "Netscaler Ext"
    version = __version__
    author = "Network to Code, LLC"
    description = "Netscaler Ext."
    base_url = "netscaler-ext"
    required_settings = []
    min_version = "3.0.2"
    max_version = "3.9999"
    default_settings = {}
    caching_config = {}
    docs_view_name = "plugins:netscaler_ext:docs"


config = NetscalerExtConfig  # pylint:disable=invalid-name
