"""Base API dispatcher."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

if TYPE_CHECKING:
    from logging import Logger

    from nautobot.dcim.models import Device
    from requests import Session


from netscaler_ext.plugins.tasks.dispatcher.base_dispatcher import (
    BaseDispatcher,
)
from netscaler_ext.utils.base_connection import ConnectionMixin
from netscaler_ext.utils.helper import (
    format_base_url_with_endpoint,
    resolve_jmespath,
    resolve_query,
)


class BaseAPIDispatcher(BaseDispatcher, ConnectionMixin):
    """Base API Dispatcher class."""

    get_headers: dict[str, str] = {}
    post_headers: dict[str, str] = {}
    url: str = ""
    session: Optional[Session] = None
    controller_type: str = ""

    @classmethod
    def resolve_backup_endpoint(
        cls,
        authenticated_obj: Any,
        device_obj: Device,
        logger: Logger,
        endpoint_context: list[dict[Any, Any]],
        feature_name: str,
        **kwargs: Any,
    ) -> Union[list[Any], dict[str, dict[Any, Any]]]:
        """Resolve endpoint with parameters if any.

        Args:
            authenticated_obj (Any): Controller object or None.
            device_obj (Device): Nautobot Device object.
            logger (Logger): Logger object.
            endpoint_context (list[dict[Any, Any]]): controller endpoint context.
            feature_name (str): Feature name being collected.
            kwargs (Any): Keyword arguments.

        Returns:
            Union[list[Any], dict[str, dict[Any, Any]]]: Dictionary of responses.

        Raises:
            TypeError: If the type of responses is inconsistent (list vs dict).
        """
        responses: dict[str, dict[Any, Any]] | list[Any] | None = None
        for endpoint in endpoint_context:
            uri: str = cls._render_uri_template(
                obj=device_obj,
                logger=logger,
                template=endpoint["endpoint"],
            )
            api_endpoint: str = format_base_url_with_endpoint(
                base_url=cls.url,
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
            if response is None:
                logger.error(
                    f"Error in API call to {api_endpoint}: No response",
                )
                continue
            jpath_fields: dict[Any, Any] | list[Any] = resolve_jmespath(
                jmespath_values=endpoint["jmespath"],
                api_response=response,
                logger=logger,
            )
            if not jpath_fields or (isinstance(jpath_fields, dict) and all(v is None for v in jpath_fields.values())):
                logger.error(f"jmespath values not found in {response}")
                continue
            if isinstance(jpath_fields, list):
                if responses is None:
                    responses = jpath_fields
                    continue
                if not isinstance(responses, list):
                    exc_msg: str = f"All responses should be list but got {type(responses)}"
                    raise TypeError(exc_msg)
                responses.extend(jpath_fields)
            elif isinstance(jpath_fields, dict):
                if responses is None:
                    responses = jpath_fields
                if not isinstance(responses, dict):
                    exc_msg: str = f"All responses should be dict but got {type(responses)}"
                    raise TypeError(exc_msg)
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
        authenticated_obj: Any,
        device_obj: Device,
        logger: Logger,
        endpoint_context: list[dict[Any, Any]],
        payload: dict[Any, Any] | list[dict[str, Any]],
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Resolve endpoint with parameters if any.

        Args:
            authenticated_obj (Any): Controller object, i.e. Meraki Dashboard object or None.
            device_obj (Device): Nautobot Device object.
            logger (Logger): Logger object.
            endpoint_context (list[dict[Any, Any]]): controller endpoint config context.
            payload (dict[Any, Any] | list[dict[str, Any]]): Payload to pass to the API call.
            kwargs (Any): Keyword arguments.

        Returns:
            list[dict[str, Any]]: List of API responses.
        """
        aggregated_results: list[Any] = []
        if not cls.session:
            logger.error("No session available for API calls")
            return aggregated_results
        for endpoint in endpoint_context:
            uri: str = cls._render_uri_template(
                obj=device_obj,
                logger=logger,
                template=endpoint["endpoint"],
            )
            api_endpoint: str = format_base_url_with_endpoint(
                base_url=cls.url,
                endpoint=uri,
            )
            req_params: list[str] = (
                endpoint["parameters"]["non_optional"]
                if "parameters" in endpoint and "non_optional" in endpoint["parameters"]
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
