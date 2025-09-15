"""nornir dispatcher for Cisco WLC (AireOS)."""

from nornir_nautobot.plugins.tasks.dispatcher.default import NetmikoDefault


class NetmikoCiscoWlc(NetmikoDefault):
    """Collection of Netmiko Nornir Tasks specific to Cisco WLC devices."""

    config_command = "show run-config commands"
