"""Menu items."""

from nautobot.apps.ui import NavMenuAddButton, NavMenuGroup, NavMenuItem, NavMenuTab

items = (
    NavMenuItem(
        link="plugins:netscaler_ext:netscalerextexamplemodel_list",
        name="Netscaler Ext",
        permissions=["netscaler_ext.view_netscalerextexamplemodel"],
        buttons=(
            NavMenuAddButton(
                link="plugins:netscaler_ext:netscalerextexamplemodel_add",
                permissions=["netscaler_ext.add_netscalerextexamplemodel"],
            ),
        ),
    ),
)

menu_items = (
    NavMenuTab(
        name="Apps",
        groups=(NavMenuGroup(name="Netscaler Ext", items=tuple(items)),),
    ),
)
