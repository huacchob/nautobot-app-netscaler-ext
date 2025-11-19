"""Netmiko dispatcher for cisco vManage controllers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from logging import Logger

    from nautobot.dcim.models import Device
    from nornir.core.task import Task
    from requests import Session

from netscaler_ext.plugins.tasks.dispatcher.base_api_dispatcher import (
    BaseAPIDispatcher,
)
from netscaler_ext.utils.helper import (
    base_64_encode_credentials,
)


class NetmikoWti(BaseAPIDispatcher):
    """APIC Controller Dispatcher class."""

    @classmethod
    def authenticate(cls, logger: Logger, obj: Device, task: Task) -> Any:
        """Authenticate to controller.

        Args:
            logger (Logger): Logger object.
            obj (Device): Device object.
            task (Task): Nornir Task object.

        Returns:
            Any: Controller object or None.
        """
        cls.url: str = f"https://{obj.primary_ip4.host}"
        cls.session: Session = cls.configure_session()
        encoded_creds: str = base_64_encode_credentials(
            username=task.host.username,
            password=task.host.password,
        )
        cls.get_headers = {
            "Authorization": encoded_creds,
            "Content-Type": "application/json",
        }
