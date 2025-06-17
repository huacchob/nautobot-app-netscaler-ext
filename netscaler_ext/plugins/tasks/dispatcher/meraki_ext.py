"""nornir dispatcher for cisco Meraki."""

from logging import Logger
from typing import Any, OrderedDict

from meraki import DashboardAPI
from nautobot.apps.choices import (
    SecretsGroupAccessTypeChoices,
    SecretsGroupSecretTypeChoices,
)
from nautobot.dcim.models import Device
from nautobot.extras.models import SecretsGroup, SecretsGroupAssociation
from nornir.core.task import Result, Task
from nornir_nautobot.plugins.tasks.dispatcher.default import NetmikoDefault
from remote_pdb import RemotePdb

NETMIKO_DEVICE_TYPE = "cisco_meraki"


def get_api_key(device: Device) -> str:
    """Get Meraki Dashboard API Key.

    Args:
        device (Device): Device object.

    Raises:
        SecretsGroupAssociation.DoesNotExist: SecretsGroupAssociation access
            type TYPE_HTTP or secret type TYPE_TOKEN does not exist.

    Returns:
        str: API key.
    """
    secrets_group: SecretsGroup = device.secrets_group
    RemotePdb(host="localhost", port=4444).set_trace()
    try:
        api_key: str = secrets_group.get_secret_value(
            access_type=SecretsGroupAccessTypeChoices.TYPE_HTTP,
            secret_type=SecretsGroupSecretTypeChoices.TYPE_TOKEN,
        )
    except SecretsGroupAssociation.DoesNotExist as e:
        raise SecretsGroupAssociation.DoesNotExist(
            "SecretsGroupAssociation access_type TYPE_HTTP secret_type TYPE_TOKEN does not exist in the SecretsGroup"
        ) from e
    return api_key


def open_dashboard_api(dash_url: str, dash_api_key: str) -> DashboardAPI:
    """Open Meraki Dashboard API.

    Args:
        dash_url (str): Dashboard URL.
        dash_api_key (str): Dashboard API key.

    Returns:
        DashboardAPI: Dashboard API object.
    """
    return DashboardAPI(
        api_key=dash_api_key,
        base_url=dash_url,
        output_log=False,
        print_console=False,
    )


def get_org_id(dash: DashboardAPI) -> str:
    """Get org ID from dashboard.

    Args:
        dash (DashboardAPI): The DashboardAPI object.

    Returns:
        str: Organization ID.
    """
    orgs = dash.organizations.getOrganizations()
    return orgs[0].get("id", "")


class MerakiDriver(NetmikoDefault):
    """Meraki Dispatcher class."""

    @classmethod
    def get_config(  # pylint: disable=R0913,R0914
        cls,
        task: Task,
        logger: Logger,
        obj: Device,
        backup_file: str,
        remove_lines: list[str],
        substitute_lines: list[str],
    ) -> None | Result:
        task.host.platform = NETMIKO_DEVICE_TYPE
        cfg_cntx: OrderedDict[Any, Any] = obj.get_config_context()
        dash_url: str = cfg_cntx.get("dashboard_url", "")
        if not dash_url:
            logger.error("Could not find the Meraki Dashboard API URL")
            raise ValueError("Could not find the Meraki Dashboard API URL")
        api_key: str = get_api_key(device=obj)
        logger.info(f"key: {api_key}")
        dashboard: DashboardAPI = open_dashboard_api(
            dash_url=dash_url,
            dash_api_key=api_key,
        )
        org_id: str = get_org_id(dash=dashboard)
        if not org_id:
            logger.error("Could not find the Meraki organization ID")
            raise ValueError("Could not find Meraki organization ID")
        _running_config: list[dict[Any, Any]] = dashboard.organizations.getOrganizations()
        processed_config: str = cls._process_config(
            logger=logger,
            running_config=str(_running_config),
            remove_lines=remove_lines,
            substitute_lines=substitute_lines,
            backup_file=backup_file,
        )
        return Result(host=task.host, result={"config": processed_config})
