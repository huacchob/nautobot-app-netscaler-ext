import unittest
from logging import Logger, getLogger
from typing import Any
from unittest.mock import MagicMock, patch

from netscaler_ext.plugins.tasks.dispatcher.citrix_netscaler import NetmikoCitrixNetscaler
from netscaler_ext.tests.fixtures import get_json_fixture


class TestCitrixNetscalerDispatcher(unittest.TestCase):
    """Test the Citrix Netscaler dispatcher."""

    base_import_path: str = "netscaler_ext.plugins.tasks.dispatcher"

    @patch(f"{base_import_path}.citrix_netscaler.use_snip_hostname")
    @patch.object(target=NetmikoCitrixNetscaler, attribute="configure_session")
    def test_authenticate(
        self,
        mock_configure_session,
        mock_use_snip_hostname,
    ) -> None:
        """Test the authentication process for the Citrix Netscaler dispatcher."""
        NetmikoCitrixNetscaler.get_headers = {}
        mock_use_snip_hostname.return_value = "https://netscaler.com"
        mock_configure_session.return_value = MagicMock()
        logger: Logger = getLogger(name="test")
        obj: MagicMock = MagicMock()
        task: MagicMock = MagicMock()
        task.host.password = "mock_api_key"
        task.host.username = "mock_api_username"

        NetmikoCitrixNetscaler.authenticate(
            logger=logger,
            obj=obj,
            task=task,
        )

        mock_use_snip_hostname.assert_called_once()
        mock_configure_session.assert_called_once()
        self.assertIn("X-NITRO-USER", NetmikoCitrixNetscaler.get_headers)
        self.assertIn("X-NITRO-PASS", NetmikoCitrixNetscaler.get_headers)

    @patch(f"{base_import_path}.citrix_netscaler.use_snip_hostname")
    @patch.object(target=NetmikoCitrixNetscaler, attribute="configure_session")
    def test_authenticate_no_snip_hostname(
        self,
        mock_configure_session,
        mock_use_snip_hostname,
    ) -> None:
        """Test authentication when use_snip_hostname returns an empty string."""
        NetmikoCitrixNetscaler.get_headers = {}
        mock_use_snip_hostname.return_value = ""
        logger: Logger = getLogger(name="test")
        obj: MagicMock = MagicMock()
        task: MagicMock = MagicMock()
        task.host.password = "mock_api_key"
        task.host.username = "mock_api_username"

        NetmikoCitrixNetscaler.authenticate(
            logger=logger,
            obj=obj,
            task=task,
        )

        mock_use_snip_hostname.assert_called_once()
        mock_configure_session.assert_called_once()
        self.assertIn("X-NITRO-USER", NetmikoCitrixNetscaler.get_headers)
        self.assertEqual(NetmikoCitrixNetscaler.get_headers["X-NITRO-USER"], "mock_api_username")

    @patch(f"{base_import_path}.citrix_netscaler.use_snip_hostname")
    @patch.object(target=NetmikoCitrixNetscaler, attribute="configure_session")
    def test_authenticate_no_username(
        self,
        mock_configure_session,
        mock_use_snip_hostname,
    ) -> None:
        """Test authentication when username is missing."""
        NetmikoCitrixNetscaler.get_headers = {}
        mock_use_snip_hostname.return_value = "https://netscaler.com"
        logger: Logger = getLogger(name="test")
        obj: MagicMock = MagicMock()
        task: MagicMock = MagicMock()
        task.host.password = "mock_api_key"
        task.host.username = ""

        NetmikoCitrixNetscaler.authenticate(
            logger=logger,
            obj=obj,
            task=task,
        )

        mock_use_snip_hostname.assert_called_once()
        mock_configure_session.assert_called_once()
        self.assertIn("X-NITRO-USER", NetmikoCitrixNetscaler.get_headers)
        self.assertEqual(NetmikoCitrixNetscaler.get_headers["X-NITRO-USER"], "")

    @patch(f"{base_import_path}.citrix_netscaler.use_snip_hostname")
    @patch.object(target=NetmikoCitrixNetscaler, attribute="configure_session")
    def test_authenticate_no_password(
        self,
        mock_configure_session,
        mock_use_snip_hostname,
    ) -> None:
        """Test authentication when password is missing."""
        NetmikoCitrixNetscaler.get_headers = {}
        mock_use_snip_hostname.return_value = "https://netscaler.com"
        logger: Logger = getLogger(name="test")
        obj: MagicMock = MagicMock()
        task: MagicMock = MagicMock()
        task.host.password = ""
        task.host.username = "mock_api_username"

        NetmikoCitrixNetscaler.authenticate(
            logger=logger,
            obj=obj,
            task=task,
        )

        mock_use_snip_hostname.assert_called_once()
        mock_configure_session.assert_called_once()
        self.assertIn("X-NITRO-PASS", NetmikoCitrixNetscaler.get_headers)
        self.assertEqual(NetmikoCitrixNetscaler.get_headers["X-NITRO-PASS"], "")

    @patch.object(target=NetmikoCitrixNetscaler, attribute="url", new="https://netscaler.com")
    @patch.object(target=NetmikoCitrixNetscaler, attribute="session", new_callable=MagicMock)
    @patch.object(target=NetmikoCitrixNetscaler, attribute="configure_session", new=MagicMock())
    @patch.object(target=NetmikoCitrixNetscaler, attribute="return_response_content")
    def test_resolve_backup_endpoint(self, mock_return_response_content, mock_session) -> None:
        """Test the authentication process for the Citrix Netscaler dispatcher."""
        # Setup mocks
        mock_session.return_value = MagicMock()
        mock_return_response_content.return_value = get_json_fixture(
            folder="api_responses",
            file_name="full_netscaler_response.json",
        )
        logger: Logger = getLogger(name="test")
        config_context: dict[Any, Any] = get_json_fixture(
            folder="config_context",
            file_name="backup_netscaler_context.json",
        )

        # Call authenticate
        kwargs: dict[str, Any] = {}
        device_obj: MagicMock = MagicMock()
        responses: dict[str, str] = NetmikoCitrixNetscaler.resolve_backup_endpoint(
            authenticated_obj=None,
            device_obj=device_obj,
            logger=logger,
            endpoint_context=config_context.get("ntp_backup"),
            feature_name="ntp_backup",
            **kwargs,
        )
        expected_response: dict[str, Any] = get_json_fixture(
            folder="api_responses",
            file_name="netscaler_backup.json",
        )

        # Assertions
        self.assertIsNotNone(obj=responses)
        self.assertEqual(responses, expected_response)

    @patch.object(target=NetmikoCitrixNetscaler, attribute="url", new="https://netscaler.com")
    @patch.object(target=NetmikoCitrixNetscaler, attribute="session", new_callable=MagicMock)
    @patch.object(target=NetmikoCitrixNetscaler, attribute="configure_session", new=MagicMock())
    @patch.object(target=NetmikoCitrixNetscaler, attribute="return_response_content")
    def test_resolve_backup_endpoint_no_response(self, mock_return_response_content, mock_session) -> None:
        """Test resolve_backup_endpoint when no response is returned."""
        mock_session.return_value = MagicMock()
        mock_return_response_content.return_value = None
        logger: Logger = getLogger(name="test")
        config_context: dict[Any, Any] = get_json_fixture(
            folder="config_context",
            file_name="backup_netscaler_context.json",
        )

        kwargs: dict[str, Any] = {}
        device_obj: MagicMock = MagicMock()
        responses: dict[str, str] = NetmikoCitrixNetscaler.resolve_backup_endpoint(
            authenticated_obj=None,
            device_obj=device_obj,
            logger=logger,
            endpoint_context=config_context.get("ntp_backup"),
            feature_name="ntp_backup",
            **kwargs,
        )

        self.assertEqual(responses, {})

    @patch.object(target=NetmikoCitrixNetscaler, attribute="url", new="https://netscaler.com")
    @patch.object(target=NetmikoCitrixNetscaler, attribute="session", new_callable=MagicMock)
    @patch.object(target=NetmikoCitrixNetscaler, attribute="configure_session", new=MagicMock())
    @patch.object(target=NetmikoCitrixNetscaler, attribute="return_response_content")
    def test_resolve_backup_endpoint_jmespath_not_found(self, mock_return_response_content, mock_session) -> None:
        """Test resolve_backup_endpoint when jmespath values are not found."""
        mock_session.return_value = MagicMock()
        mock_return_response_content.return_value = {"some_key": "some_value"}
        logger: Logger = getLogger(name="test")
        config_context: dict[Any, Any] = get_json_fixture(
            folder="config_context",
            file_name="backup_netscaler_context.json",
        )

        kwargs: dict[str, Any] = {}
        device_obj: MagicMock = MagicMock()
        responses: dict[str, str] = NetmikoCitrixNetscaler.resolve_backup_endpoint(
            authenticated_obj=None,
            device_obj=device_obj,
            logger=logger,
            endpoint_context=config_context.get("ntp_backup"),
            feature_name="ntp_backup",
            **kwargs,
        )

        self.assertEqual(responses, {})
