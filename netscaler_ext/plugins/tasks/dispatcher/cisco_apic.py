"""Netmiko dispatcher for cisco vManage controllers."""

import json
from logging import Logger
from typing import Any, Optional

from nautobot.dcim.models import Device
from nornir.core.task import Task
from requests import Session

from netscaler_ext.plugins.tasks.dispatcher.base_controller_dispatcher import (
    BaseControllerDispatcher,
)
from netscaler_ext.utils.base_connection import ConnectionMixin
from netscaler_ext.utils.helper import (
    format_base_url_with_endpoint,
    resolve_controller_url,
    resolve_jmespath,
    resolve_query,
)


class NetmikoCiscoApic(BaseControllerDispatcher, ConnectionMixin):
    """APIC Controller Dispatcher class."""

    get_headers: dict[str, str] = {}
    post_headers: dict[str, str] = {}
    controller_url: str = ""
    session: Optional[Session] = None
    controller_type: str = "apic"

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
        cls.controller_url = resolve_controller_url(
            obj=obj,
            controller_type=cls.controller_type,
            logger=logger,
        )
        username, password = task.host.username, task.host.password
        auth_payload = {
            "aaaUser": {
                "attributes": {"name": f"{username}", "pwd": f"{password}"},
            },
        }
        auth_url: str = format_base_url_with_endpoint(
            base_url=cls.controller_url,
            endpoint="api/aaaLogin.json",
        )
        # TODO: Change verify to true
        cls.session: Session = cls.configure_session()
        auth_resp: Any = cls.return_response_content(
            session=cls.session,
            method="POST",
            url=auth_url,
            headers={
                "Content-Type": "text/plain",
            },
            logger=logger,
            body=json.dumps(auth_payload),
            verify=False,
        )
        if not auth_resp:
            logger.error(
                "Could not find cookie from APIC controller",
            )
            raise ValueError(
                "Could not find cookie from APIC controller",
            )
        if not auth_resp.get("imdata") or not auth_resp.get("imdata")[0]:
            logger.error(
                "Could not find cookie from APIC controller",
            )
            raise ValueError(
                "Could not find cookie from APIC controller",
            )
        cookie: str = (
            auth_resp.get("imdata")[0]
            .get("aaaLogin", {})
            .get("attributes", {})
            .get("token", "")
        )
        if not cookie:
            logger.error(
                "Could not find cookie from APIC controller",
            )
            raise ValueError(
                "Could not find cookie from APIC controller",
            )
        cls.get_headers.update(
            {
                "Cookie": f"APIC-cookie={cookie}",
                "Content-Type": "text/plain",
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
                base_url=cls.controller_url,
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
