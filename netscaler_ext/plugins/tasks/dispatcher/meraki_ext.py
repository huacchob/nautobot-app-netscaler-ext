"""nornir dispatcher for cisco Meraki."""

from logging import Logger
from typing import Any, Callable, OrderedDict

from meraki import DashboardAPI
from nautobot.apps.choices import (
    SecretsGroupAccessTypeChoices,
    SecretsGroupSecretTypeChoices,
)
from nautobot.dcim.models import Device
from nautobot.extras.models import SecretsGroup, SecretsGroupAssociation
from nornir.core.task import Result, Task
from nornir_nautobot.plugins.tasks.dispatcher.default import NetmikoDefault


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
        dashboard_url (str): Dashboard URL.
        dashboard_api_key (str): Dashboard API key.

    Returns:
        DashboardAPI: Dashboard API object.
    """
    return DashboardAPI(
        api_key=dashboard_api_key,
        base_url=dashboard_url,
        output_log=False,
        print_console=False,
    )


def get_org_id(dashboard: DashboardAPI) -> str:
    """Get org ID from dashboard.

    Args:
        dashboard (DashboardAPI): The DashboardAPI object.

    Returns:
        str: Organization ID.
    """
    return dashboard.organizations.getOrganizations()[0].get("id", "")


def get_case_insensitive_key(
    params_mapper: dict[str, str],
    param: str,
) -> tuple[str, str]:
    """Get case insensitive key from params mapper dict.

    Args:
        params_mapper (dict[str, str]): Params mapper.
        param (str): Param key.

    Returns:
        tuple[str, str]: Param key and value.
    """
    for k, v in params_mapper.items():
        if k.lower() == param.lower():
            return (k, v)
    return ("", "")


def feature_name_parser(feature_name: str) -> str:
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


def resolve_endpoint(
    dashboard: DashboardAPI,
    feature: str,
    endpoint_context: list[dict[Any, Any]],
    organizationId: str,
    networkId: str,
) -> dict[str, dict[Any, Any]]:
    """Resolve endpoint with parameters if any.

    Args:
        dashboard (DashboardAPI): Dashboard API object.
        feature (str): Feature key name.
        endpoint_context (list[dict[Any, Any]]): Meraki endpoint context.
        organizationId (str): Organization ID.
        networkId (str): Network ID.

    Returns:
        Any: Dictionary of responses.
    """
    responses: dict[str, dict[Any, Any]] = {}
    param_mapper: dict[str, str] = {
        "organizationId": organizationId,
        "networkId": networkId,
    }
    feature_name: str = feature_name_parser(feature_name=feature)
    for endpoint in endpoint_context:
        meraki_class, meraki_method = endpoint["method"].split(".")
        method_callable: Callable[[Any], Any] = getattr(
            getattr(dashboard, meraki_class),
            meraki_method,
        )
        params: dict[str, str] = {}
        if endpoint.get("parameters"):
            for param in endpoint["parameters"]:
                if param.lower() not in [p.lower() for p in param_mapper]:
                    continue
                param_key, param_value = get_case_insensitive_key(
                    params_mapper=param_mapper,
                    param=param,
                )
                params.update({param_key: param_value})
        responses.update({feature_name: {endpoint["method"]: method_callable(**params)}})

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
        dash_url: str = cfg_cntx.get("dashboard_url", "")
        if not dash_url:
            logger.error("Could not find the Meraki Dashboard API URL")
            raise ValueError("Could not find the Meraki Dashboard API URL")
        api_key: str = get_api_key(secrets_group=obj.secrets_group)
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
        _running_config: list[dict[str, dict[Any, Any]]] = []
        for feature in feature_endpoints:
            endpoints: list[dict[Any, Any]] = cfg_cntx.get(feature, "")
            _running_config.append(
                resolve_endpoint(
                    dashboard=dashboard,
                    feature=feature,
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
