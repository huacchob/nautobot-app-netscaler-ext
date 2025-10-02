"""Netmiko dispatcher for cisco vManage controllers."""

from logging import Logger
from typing import Any, Optional

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


class NetmikoCiscoVmanage(BaseControllerDriver, ConnectionMixin):
    """Vmanage Controller Dispatcher class."""

    get_headers: dict[str, str] = {}
    post_headers: dict[str, str] = {}
    controller_url: str = ""
    session: Optional[Session] = None
    controller_type: str = "vmanage"

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
        j_security_payload = f"j_username={username}&j_password={password}"
        security_url: str = format_base_url_with_endpoint(
            base_url=cls.controller_url,
            endpoint="j_security_check",
        )
        # TODO: Change verify to true
        cls.session = cls.configure_session()
        security_resp: Response = cls.return_response_obj(
            session=cls.session,
            method="POST",
            url=security_url,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            logger=logger,
            body=j_security_payload,
            verify=False,
        )
        if not security_resp.ok:
            logger.error(
                f"Error in authentication to {security_url}: {security_resp.status_code} - {security_resp.text}"
            )
            raise ValueError(
                f"Error in authentication to {security_url}: {security_resp.status_code} - {security_resp.text}"
            )
        j_session_id: str = security_resp.headers.get("Set-Cookie", "")
        if not j_session_id:
            logger.error(
                "Could not find JSESSIONID from vManage controller",
            )
            raise ValueError(
                "Could not find JSESSIONID from vManage controller",
            )
        token_url: str = format_base_url_with_endpoint(
            base_url=cls.controller_url,
            endpoint="dataservice/client/token",
        )
        token_obj: Response = cls.return_response_obj(
            session=cls.session,
            method="GET",
            url=token_url,
            headers={
                "Cookie": j_session_id,
                "Content-Type": "application/json",
            },
            verify=False,
            logger=logger,
        )
        if not token_obj.ok:
            logger.error(f"Error in retrieving token from {token_url}: {token_obj.status_code} - {token_obj.text}")
            raise ValueError(f"Error in retrieving token from {token_url}: {token_obj.status_code} - {token_obj.text}")
        token_resp = token_obj.json()
        cls.get_headers.update(
            {
                "Cookie": j_session_id,
                "Content-Type": "application/json",
                "X-XSRF-TOKEN": str(token_resp),
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
            response_obj: Response = cls.return_response_obj(
                session=cls.session,
                method=endpoint["method"],
                url=api_endpoint,
                headers=cls.get_headers,
                verify=False,
                logger=logger,
            )
            if not response_obj.ok:
                logger.error(f"Error in API call to {api_endpoint}: {response_obj.status_code} - {response_obj.text}")
                continue
            response: Any = response_obj.json()
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
