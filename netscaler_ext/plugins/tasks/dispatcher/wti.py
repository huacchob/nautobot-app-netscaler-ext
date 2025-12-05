"""Netmiko dispatcher for cisco vManage controllers."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Optional, Union

import requests
from requests import exceptions as req_exceptions

if TYPE_CHECKING:
    from logging import Logger

    from nautobot.dcim.models import Device
    from nornir.core.task import Task
    from requests import Session

from netscaler_ext.plugins.tasks.dispatcher.api_base_dispatcher import (
    ApiBaseDispatcher,
)
from netscaler_ext.utils.helper import (
    base_64_encode_credentials,
)


class NetmikoWti(ApiBaseDispatcher):
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

    @classmethod
    def _return_response(
        cls,
        method: str,
        url: str,
        headers: dict[str, str],
        session: requests.Session,
        logger: Logger,
        body: Optional[Union[dict[str, str], str]] = None,
        verify: bool = True,
    ) -> Optional[requests.Response]:
        """Create request for authentication and return response object.

        Args:
            method (str): HTTP Method to use.
            url (str): URL to send request to.
            headers (dict): Headers to use in request.
            session (Session): Session to use.
            logger (Logger): The dispatcher's logger.
            body (dict[str, str] | str | None): Body of request.
            verify (bool): Verify SSL certificate.

        Returns:
            Optional[Response]: API Response object.
        """
        with session as ses:
            try:
                response: Optional[requests.Response] = ses.request(
                    method=method,
                    url=url,
                    headers=headers,
                    data=json.dumps(body),
                    timeout=(50.0, 100.0),
                    verify=verify,
                )
            except req_exceptions.SSLError as exc_ssl:
                exc_msg: str = f"SSL error occurred: {exc_ssl}"
                logger.error(exc_msg)
                response = None
            except req_exceptions.Timeout as exc_timeout:
                exc_msg: str = f"Request timed out: {exc_timeout}"
                logger.error(exc_msg)
                response = None
            except req_exceptions.ConnectionError as exc_conn:
                exc_msg: str = f"Connection error occurred: {exc_conn}"
                logger.error(exc_msg)
                response = None
            except req_exceptions.RequestException as exc_req:
                exc_msg: str = f"Request exception occurred: {exc_req}"
                logger.error(exc_msg)
                response = None
            except Exception as exc:
                exc_msg: str = f"An error occurred: {exc}"
                logger.error(exc_msg)
                response = None
        if response is None:
            return response
        if not response.ok:
            logger.error(
                f"Endpoint {url} returned {response.status_code}: {response.text}",
            )
            return None
        return response
