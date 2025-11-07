"""Netmiko dispatcher for cisco vManage controllers."""

from logging import Logger
from typing import Any, Optional

from nautobot.dcim.models import Device
from nornir.core.task import Task
from requests import Session

from netscaler_ext.plugins.tasks.dispatcher.base_controller_driver import (
    BaseControllerDriver,
)
from netscaler_ext.utils.base_connection import ConnectionMixin
from netscaler_ext.utils.helper import (
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
    session: Optional[Session] = None

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
        cls.session: Session = cls.configure_session()
        encoded_creds: str = base_64_encode_credentials(
            username=task.host.username,
            password=task.host.password,
        )
        cls.get_headers.update(
            {
                "Authorization": encoded_creds,
                "Content-Type": "application/json",
            },
        )

    @classmethod
    def resolve_backup_endpoint(
        cls,
        controller_obj: Any,
        logger: Logger,
        endpoint_context: list[dict[Any, Any]],
        feature_name: str,
        **kwargs: Any,
    ) -> dict[str, dict[Any, Any]]:
        """Resolve endpoint with parameters if any.

        Args:
            controller_obj (Any): Controller object or None.
            logger (Logger): Logger object.
            endpoint_context (list[dict[Any, Any]]): controller endpoint context.
            feature_name (str): Feature name being collected.
            kwargs (Any): Keyword arguments.

        Returns:
            Any: Dictionary of responses.
        """
        responses: dict[str, dict[Any, Any]] | list[Any] | None = None
        for endpoint in endpoint_context:
            uri: str = cls._render_uri_template(
                obj=controller_obj,
                logger=logger,
                template=endpoint["endpoint"],
            )
            api_endpoint: str = format_base_url_with_endpoint(
                base_url=cls.device_url,
                endpoint=uri,
            )
            if endpoint.get("query"):
                api_endpoint = resolve_query(
                    api_endpoint=api_endpoint,
                    query=endpoint["query"],
                )
            response: Any = cls.return_response_content(
                session=cls.session,
                method=endpoint["method"],
                url=api_endpoint,
                headers=cls.get_headers,
                verify=False,
                logger=logger,
            )
            if not response:
                logger.error(
                    f"Error in API call to {api_endpoint}: No response",
                )
                continue
            jpath_fields: dict[Any, Any] | list[Any] = resolve_jmespath(
                jmespath_values=endpoint["jmespath"],
                api_response=response,
            )
            if not jpath_fields:
                logger.error(f"jmespath values not found in {response}")
                continue
            if isinstance(jpath_fields, list):
                if responses is None:
                    responses = jpath_fields
                    continue
                if not isinstance(responses, list):
                    raise TypeError(
                        f"All responses should be list but got {type(responses)}",
                    )
                responses.extend(jpath_fields)
            elif isinstance(jpath_fields, dict):
                if responses is None:
                    responses = jpath_fields
                if not isinstance(responses, dict):
                    raise TypeError(
                        f"All responses should be dict but got {type(responses)}",
                    )
                responses.update(jpath_fields)
            else:
                logger.error(
                    f"Unexpected jmespath response type: {type(jpath_fields)}",
                )

        if responses:
            return responses
        logger.error(
            f"No valid responses found for the {feature_name} endpoints",
        )
        return {}

    @classmethod
    def resolve_remediation_endpoint(
        cls,
        controller_obj: Any,
        logger: Logger,
        endpoint_context: list[dict[Any, Any]],
        payload: dict[Any, Any] | list[dict[str, Any]],
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Resolve endpoint with parameters if any.

        Args:
            controller_obj (Any): Controller object, i.e. Meraki Dashboard
                object or None.
            logger (Logger): Logger object.
            endpoint_context (list[dict[Any, Any]]): controller endpoint config context.
            payload (dict[Any, Any] | list[dict[str, Any]]): Payload to pass to the API call.
            kwargs (Any): Keyword arguments.

        Returns:
            list[dict[str, Any]]: List of API responses.
        """
        aggregated_results: list[Any] = []
        for endpoint in endpoint_context:
            uri: str = cls._render_uri_template(
                obj=controller_obj,
                logger=logger,
                template=endpoint["endpoint"],
            )
            api_endpoint: str = format_base_url_with_endpoint(
                base_url=cls.device_url,
                endpoint=uri,
            )
            req_params: list[str] = (
                endpoint["parameters"]["non_optional"]
                if "parameters" in endpoint
                and "non_optional" in endpoint["parameters"]
                else []
            )
            if isinstance(payload, dict):
                payload_copy = payload.copy()
                for param in req_params:
                    if not kwargs.get(param):
                        logger.error(
                            "resolve_endpoint method needs '%s' in kwargs",
                            param,
                        )
                    else:
                        payload_copy.update({param: kwargs[param]})
                response: Any = cls.return_response_content(
                    session=cls.session,
                    method=endpoint["method"],
                    url=api_endpoint,
                    headers=cls.get_headers,
                    verify=False,
                    logger=logger,
                    body=payload_copy,
                )
                if not response:
                    logger.error(
                        "Error in API call to %s: No response",
                        api_endpoint,
                    )
                    continue
                aggregated_results.append(response)
            elif isinstance(payload, list):
                for item in payload:
                    if not isinstance(item, dict):
                        continue
                    item_copy = item.copy()
                    for param in req_params:
                        if not kwargs.get(param):
                            logger.error(
                                "resolve_endpoint method needs '%s' in kwargs",
                                param,
                            )
                        else:
                            item_copy.update({param: kwargs[param]})
                    response: Any = cls.return_response_content(
                        session=cls.session,
                        method=endpoint["method"],
                        url=api_endpoint,
                        headers=cls.get_headers,
                        verify=False,
                        logger=logger,
                        body=item_copy,
                    )
                    if not response:
                        logger.error(
                            "Error in API call to %s: No response",
                            api_endpoint,
                        )
                        continue
                    aggregated_results.append(response)
        return aggregated_results
