"""Netmiko dispatcher for cisco vManage controllers."""

import json
from logging import Logger
from typing import Any

from nautobot.dcim.models import Device
from nornir.core.task import Task
from requests import Session

from netscaler_ext.plugins.tasks.dispatcher.base_api_dispatcher import (
    BaseAPIDispatcher,
)
from netscaler_ext.utils.helper import (
    format_base_url_with_endpoint,
    resolve_controller_url,
)


class NetmikoCiscoApic(BaseAPIDispatcher):
    """APIC Controller Dispatcher class."""

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
        cls.url = resolve_controller_url(
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
            base_url=cls.url,
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
