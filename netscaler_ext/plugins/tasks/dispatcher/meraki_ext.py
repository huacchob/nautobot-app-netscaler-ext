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


def get_api_key(secrets_group: SecretsGroup) -> str:
    """Get Meraki Dashboard API Key.

    Args:
        secrets_group (SecretsGroup): SecretsGroup object.

    Raises:
        SecretsGroupAssociation.DoesNotExist: SecretsGroupAssociation access
            type TYPE_HTTP or secret type TYPE_TOKEN does not exist.

    Returns:
        str: API key.
    """
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


def open_dashboard_api(dashboard_url: str, dashboard_api_key: str) -> DashboardAPI:
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


def get_org_id(dashboard: DashboardAPI) -> str:
    """Get org ID from dashboard.

    Args:
        dash (DashboardAPI): The DashboardAPI object.

    Returns:
        str: Organization ID.
    """
    orgs = dashboard.organizations.getOrganizations()
    return orgs[0].get("id", "")


def resolve_endpoint(
    dashboard: DashboardAPI,
    endpoint_context: list[dict[Any, Any]],
    organizationId: str,
    networkId: str,
) -> Any:
    """Resolve endpoint with parameters if any.

    Args:
        dashboard (DashboardAPI): _description_
        endpoint_context (list[dict[Any, Any]]): _description_
        organizationId (str): _description_
        networkId (str): _description_

    Returns:
        Any: list of responses.
    """
    responses: list[dict[Any, Any]] = []
    param_mapper: dict[str, str] = {
        "organizationId": organizationId,
        "networkId": networkId,
    }
    for endpoint in endpoint_context:
        meraki_class, meraki_method = endpoint["method"].split(".")
        class_callable = getattr(dashboard, meraki_class)
        method_callable = getattr(class_callable, meraki_method)
        params: dict[str, str] = {}
        if endpoint.get("parameters"):
            for param in endpoint["parameters"]:
                params.update({param: param_mapper[param]})
            responses.append(method_callable(**params))

    return responses


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
        cfg_cntx: OrderedDict[Any, Any] = obj.get_config_context()
        RemotePdb(host="localhost", port=4444).set_trace()
        dash_url: str = cfg_cntx.get("dashboard_url", "")
        if not dash_url:
            logger.error("Could not find the Meraki Dashboard API URL")
            raise ValueError("Could not find the Meraki Dashboard API URL")
        api_key: str = get_api_key(secrets_group=obj.secrets_group)
        logger.info(f"key: {api_key}")
        dashboard: DashboardAPI = open_dashboard_api(
            dashboard_url=dash_url,
            dashboard_api_key=api_key,
        )
        org_id: str = get_org_id(dashboard=dashboard)
        if not org_id:
            logger.error("Could not find the Meraki organization ID")
            raise ValueError("Could not find Meraki organization ID")
        feature_endpoints: str = cfg_cntx.get("endpoints", "")
        if not feature_endpoints:
            logger.error("Could not find the Meraki endpoints")
            raise ValueError("Could not find Meraki endpoints")
        _running_config: list[list[dict[Any, Any]]] = []
        for feature in feature_endpoints:
            endpoints: str = cfg_cntx.get(feature, "")
            _running_config.append(
                resolve_endpoint(
                    dashboard=dashboard,
                    endpoint_context=endpoints,
                    organizationId=org_id,
                    networkId="",
                )
            )
        processed_config: str = cls._process_config(
            logger=logger,
            running_config=str(_running_config),
            remove_lines=remove_lines,
            substitute_lines=substitute_lines,
            backup_file=backup_file,
        )
        return Result(host=task.host, result={"config": processed_config})
