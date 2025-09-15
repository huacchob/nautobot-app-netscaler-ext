"""Netmiko dispatcher for cisco vManage controllers."""

import json
from logging import Logger
from typing import Any

from nautobot.dcim.models import Device
from nornir.core.task import Task
from requests import Response, Session

from netscaler_ext.plugins.tasks.dispatcher.base_controller_driver import BaseControllerDriver
from netscaler_ext.utils.controller import (
    ConnectionMixin,
    format_base_url_with_endpoint,
    resolve_controller_url,
    resolve_jmespath,
    resolve_query,
)


class NetmikoCiscoApic(BaseControllerDriver, ConnectionMixin):
    """APIC Controller Dispatcher class."""

    get_headers: dict[str, str] = {}
    post_headers: dict[str, str] = {}
    controller_url: str = ""
    session: Session
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
        auth_payload = {"aaaUser": {"attributes": {"name": f"{username}", "pwd": f"{password}"}}}
        auth_url: str = format_base_url_with_endpoint(
            base_url=cls.controller_url,
            endpoint="api/aaaLogin.json",
        )
        # TODO: Change verify to true
        cls.session: Session = cls.configure_session()
        auth_resp: Response = cls.return_response_content(
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
        if not auth_resp.get("imdata") or not auth_resp.get("imdata")[0]:
            logger.error(
                "Could not find cookie from APIC controller",
            )
            raise ValueError(
                "Could not find cookie from APIC controller",
            )
        cookie: str = auth_resp.get("imdata")[0].get("aaaLogin", {}).get("attributes", {}).get("token", "")
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
        responses: dict[str, dict[Any, Any]] | list[Any] | None = None
        for endpoint in endpoint_context:
            api_endpoint: str = format_base_url_with_endpoint(
                base_url=cls.controller_url,
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
            if isinstance(jpath_fields, list):
                if responses is None:
                    responses = jpath_fields
                    continue
                if not isinstance(responses, list):
                    raise TypeError(f"All responses should be list but got {type(responses)}")
                responses.extend(jpath_fields)
            else:
                if responses is None:
                    responses = jpath_fields
                if not isinstance(responses, dict):
                    raise TypeError(f"All responses should be dict but got {type(responses)}")
                responses.update(jpath_fields)

        return responses
