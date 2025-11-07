"""Classes and functions for controller dispatcher utils."""

from logging import Logger
from typing import Any, Optional

from requests import Response, Session
from requests.adapters import HTTPAdapter
from requests.exceptions import (
    ConnectionError,
    HTTPError,
    JSONDecodeError,
    Timeout,
)
from urllib3.util import Retry


class ConnectionMixin:
    """Mixin to connect to a service."""

    @classmethod
    def configure_session(cls) -> Session:
        """Configure a requests session.

        Returns:
            Session: Requests session.
        """
        session: Session = Session()
        retries = Retry(
            total=2,
            backoff_factor=0.5,
            backoff_max=5.0,
            status_forcelist=[502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        session.mount(
            prefix="https://",
            adapter=HTTPAdapter(max_retries=retries),
        )
        return session

    @classmethod
    def _return_response(
        cls,
        method: str,
        url: str,
        headers: dict[str, str],
        session: Session,
        logger: Logger,
        body: dict[str, str] | str | None = None,
        verify: bool = True,
    ) -> Optional[Response]:
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
                response: Optional[Response] = ses.request(
                    method=method,
                    url=url,
                    headers=headers,
                    data=body,
                    timeout=(50.0, 100.0),
                    verify=verify,
                )
            except ConnectionError as exc_conn:
                logger.error("Connection error occurred: %s", exc_conn)
                response = None
            except Timeout as exc_timeout:
                logger.error("Request timed out: %s", exc_timeout)
                response = None
            except Exception as exc:
                logger.error("An error occurred: %s", exc)
                response = None
            if not response:
                return response
            if not response.ok:
                logger.error(
                    f"Error in API call to {url}: {response.status_code} - {response.text}",
                )
                return None
        return response

    @classmethod
    def return_response_obj(
        cls,
        method: str,
        url: str,
        headers: dict[str, str],
        session: Session,
        logger: Logger,
        body: dict[str, str] | str | None = None,
        verify: bool = True,
    ) -> Optional[Response]:
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
            Optional[Response]: API Response object or None.
        """
        return cls._return_response(
            method=method,
            url=url,
            headers=headers,
            session=session,
            logger=logger,
            body=body,
            verify=verify,
        )

    @classmethod
    def return_response_content(
        cls,
        method: str,
        url: str,
        headers: dict[str, str],
        session: Session,
        logger: Logger,
        body: dict[str, str] | str | None = None,
        verify: bool = True,
    ) -> Any:
        """Create request and return response payload.

        Args:
            method (str): HTTP Method to use.
            url (str): URL to send request to.
            headers (dict): Headers to use in request.
            session (Session): Session to use.
            logger (Logger): The dispatcher's logger.
            body (dict[str, str] | str | None): Body of request.
            verify (bool): Verify SSL certificate.

        Returns:
            Any: API Response.

        Raises:
            requests.exceptions.HTTPError:
                If the HTTP request returns an unsuccessful status code.
        """
        try:
            response: Optional[Response] = cls._return_response(
                method=method,
                url=url,
                headers=headers,
                session=session,
                logger=logger,
                body=body,
                verify=verify,
            )
            if not response:
                return response
            json_response: dict[str, Any] = response.json()
            return json_response
        except JSONDecodeError:
            text_response: str = response.text
            return text_response
        except HTTPError as http_err:
            logger.error(http_err)
            return None
