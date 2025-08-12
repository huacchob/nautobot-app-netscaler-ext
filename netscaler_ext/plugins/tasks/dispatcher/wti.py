"""Netmiko dispatcher for cisco vManage controllers."""

from logging import Logger
from typing import Any

from nautobot.dcim.models import Device
from nornir.core.task import Task
from requests import Session

from netscaler_ext.plugins.tasks.dispatcher.base_controller_driver import BaseControllerDriver
from netscaler_ext.utils.controller import (
    ConnectionMixin,
    base_64_encode_credentials,
    format_base_url_with_endpoint,
    resolve_jmespath,
    resolve_query,
)


class NetmikoWti(BaseControllerDriver, ConnectionMixin):
    """APIC Controller Dispatcher class."""

    get_headers: dict[str, str] = {}
    post_headers: dict[str, str] = {}
    device_url: str = ""
    session: Session

    @classmethod
    def authenticate(cls, logger: Logger, obj: Device, task: Task) -> Any:
        """Authenticate to controller.

        Args:
            logger (Logger): Logger object.
            obj (Device): Device object.
            task (Task): Nornir Task object.

        Raises:
            ValueError: Could not find the controller API URL in config context.

        Returns:
            Any: Controller object or None.
        """
        cls.device_url: str = f"https://{obj.primary_ip4.host}"
        encoded_creds: str = base_64_encode_credentials(
            username=task.host.username,
            password=task.host.password,
        )
        cls.get_headers.update(
            {
                "Authorization": encoded_creds,
                "Content-Type": "application/json",
            }
        )

    @classmethod
    def resolve_backup_endpoint(
        cls,
        controller_obj: Any,
        logger: Logger,
        endpoint_context: list[dict[Any, Any]],
        **kwargs: Any,
    ) -> dict[str, dict[Any, Any]]:
        """Resolve endpoint with parameters if any.

        Args:
            controller_obj (Any): Controller object or None.
            logger (Logger): Logger object.
            endpoint_context (list[dict[Any, Any]]): controller endpoint context.
            kwargs (Any): Keyword arguments.

        Returns:
            Any: Dictionary of responses.
        """
        responses: dict[str, dict[Any, Any]] = {}
        for endpoint in endpoint_context:
            api_endpoint: str = format_base_url_with_endpoint(
                base_url=cls.device_url,
                endpoint=endpoint["endpoint"],
            )
            if endpoint.get("query"):
                api_endpoint = resolve_query(
                    api_endpoint=api_endpoint,
                    query=endpoint["query"],
                )
            response = cls.return_response_content(
                session=cls.session,
                method=endpoint["method"],
                url=api_endpoint,
                headers=cls.get_headers,
                verify=False,
                logger=logger,
            )
            jpath_fields: dict[str, Any] = resolve_jmespath(
                jmespath_values=endpoint["jmespath"],
                api_response=response,
            )
            if not jpath_fields:
                logger.error(f"jmespath values not found in {response}")
                continue
            responses.update(jpath_fields)

        return responses

    # @classmethod
    # def resolve_remediation_endpoint(
    #     cls,
    #     controller_obj: Any,
    #     logger: Logger,
    #     endpoint_context: list[dict[Any, Any]],
    #     payload: dict[Any, Any] | list[dict[str, Any]],
    #     **kwargs: Any,
    # ) -> list[dict[str, Any]]:
    #     """Resolve endpoint with parameters if any.

    #     Args:
    #         controller_obj (Any): Controller object, i.e. Meraki Dashboard
    #             object or None.
    #         logger (Logger): Logger object.
    #         endpoint_context (list[dict[Any, Any]]): controller endpoint config context.
    #         payload (dict[Any, Any] | list[dict[str, Any]]): Payload to pass to the API call.
    #         kwargs (Any): Keyword arguments.

    #     Returns:
    #         list[dict[str, Any]]: List of API responses.
    #     """
    #     aggregated_results: list[Any] = []
    #     for method_context in endpoint_context:
    #         method_callable: Optional[Callable[[Any], Any]] = _resolve_method_callable(
    #             controller_obj=controller_obj,
    #             method=method_context["endpoint"],
    #             logger=logger,
    #         )
    #         if not method_callable:
    #             logger.error(
    #                 f"The method {method_context['endpoint']} does not exist in the controller object",
    #             )
    #             continue
    #         if isinstance(payload, dict):
    #             for param in method_context["parameters"]["non_optional"]:
    #                 if not kwargs.get(param):
    #                     logger.error(
    #                         f"resolve_endpoint method needs '{param}' in kwargs",
    #                     )
    #                 payload.update({param: kwargs[param]})
    #             try:
    #                 response: Any = method_callable(**payload)
    #             except TypeError:
    #                 logger.error(
    #                     f"The params {payload} are not valid/sufficient for the {method_callable} method",
    #                 )
    #                 continue
    #             except Exception as e:
    #                 logger.warning(
    #                     e,
    #                 )
    #                 continue
    #             aggregated_results.append(response)
    #         if isinstance(payload, list):
    #             for item in payload:
    #                 for param in method_context["parameters"]["non_optional"]:
    #                     if not kwargs.get(param):
    #                         logger.error(
    #                             f"resolve_endpoint method needs '{param}' in kwargs",
    #                         )
    #                     item.update({param: kwargs[param]})
    #                 try:
    #                     response: Any = method_callable(**item)
    #                 except TypeError:
    #                     logger.error(
    #                         f"The params {item} are not valid/sufficient for the {method_callable} method",
    #                     )
    #                     continue
    #                 except Exception as e:
    #                     logger.warning(
    #                         e,
    #                     )
    #                     continue
    #                 aggregated_results.append(response)
    #     return aggregated_results
