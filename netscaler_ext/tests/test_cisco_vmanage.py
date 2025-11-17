"""Unit tests for the Cisco vManage dispatcher."""

import unittest
from logging import Logger, getLogger
from typing import Any
from unittest.mock import MagicMock, patch

from netscaler_ext.plugins.tasks.dispatcher.cisco_vmanage import NetmikoCiscoVmanage
from netscaler_ext.tests.fixtures import get_json_fixture


class TestCiscoVmanageDispatcher(unittest.TestCase):
    """Test the Cisco vManage dispatcher."""

    base_import_path: str = "netscaler_ext.plugins.tasks.dispatcher"

    @patch(f"{base_import_path}.cisco_vmanage.resolve_controller_url")
    @patch(f"{base_import_path}.cisco_vmanage.NetmikoCiscoVmanage.configure_session")
    @patch(f"{base_import_path}.cisco_vmanage.NetmikoCiscoVmanage.return_response_obj")
    def test_authenticate(
        self,
        mock_return_response_obj,
        mock_configure_session,
        mock_resolve_url,
    ) -> None:
        """Test the authentication process for the Cisco vManage dispatcher."""
        # Setup mocks
        mock_resolve_url.return_value = "https://vmanage.com"
        mock_configure_session.return_value = MagicMock()
        mock_return_response_obj.return_value = MagicMock()
        mock_return_response_obj.return_value.headers = {
            "Set-Cookie": "JSESSIONID=mock_session_id",
        }
        logger: Logger = getLogger(name="test")
        obj: MagicMock = MagicMock()
        task: MagicMock = MagicMock()
        task.host.password = "mock_api_key"
        task.host.username = "mock_api_username"

        # Call authenticate
        NetmikoCiscoVmanage.authenticate(
            logger=logger,
            obj=obj,
            task=task,
        )

        # Assertions
        mock_resolve_url.assert_called_once()
        mock_configure_session.assert_called_once()

    @patch(f"{base_import_path}.cisco_vmanage.resolve_controller_url")
    @patch(f"{base_import_path}.cisco_vmanage.NetmikoCiscoVmanage.configure_session")
    @patch(f"{base_import_path}.cisco_vmanage.NetmikoCiscoVmanage.return_response_obj")
    def test_authenticate_resolve_url_error(
        self,
        mock_return_response_obj,
        mock_configure_session,
        mock_resolve_url,
    ) -> None:
        """Test authentication when resolve_controller_url raises ValueError."""
        mock_resolve_url.side_effect = ValueError("Test Error")
        logger: Logger = getLogger(name="test")
        obj: MagicMock = MagicMock()
        task: MagicMock = MagicMock()
        task.host.password = "mock_api_key"
        task.host.username = "mock_api_username"

        with self.assertRaises(ValueError):
            NetmikoCiscoVmanage.authenticate(
                logger=logger,
                obj=obj,
                task=task,
            )
        mock_resolve_url.assert_called_once()
        mock_configure_session.assert_not_called()
        mock_return_response_obj.assert_not_called()

    @patch(f"{base_import_path}.cisco_vmanage.resolve_controller_url")
    @patch(f"{base_import_path}.cisco_vmanage.NetmikoCiscoVmanage.configure_session")
    @patch(f"{base_import_path}.cisco_vmanage.NetmikoCiscoVmanage.return_response_obj")
    def test_authenticate_no_security_resp(
        self,
        mock_return_response_obj,
        mock_configure_session,
        mock_resolve_url,
    ) -> None:
        """Test authentication when security response is None."""
        mock_resolve_url.return_value = "https://vmanage.com"
        mock_configure_session.return_value = MagicMock()
        mock_return_response_obj.return_value = None
        logger: Logger = getLogger(name="test")
        obj: MagicMock = MagicMock()
        task: MagicMock = MagicMock()
        task.host.password = "mock_api_key"
        task.host.username = "mock_api_username"

        with self.assertRaises(ValueError):
            NetmikoCiscoVmanage.authenticate(
                logger=logger,
                obj=obj,
                task=task,
            )
        mock_resolve_url.assert_called_once()
        mock_configure_session.assert_called_once()
        mock_return_response_obj.assert_called_once()

    @patch(f"{base_import_path}.cisco_vmanage.resolve_controller_url")
    @patch(f"{base_import_path}.cisco_vmanage.NetmikoCiscoVmanage.configure_session")
    @patch(f"{base_import_path}.cisco_vmanage.NetmikoCiscoVmanage.return_response_obj")
    def test_authenticate_no_set_cookie(
        self,
        mock_return_response_obj,
        mock_configure_session,
        mock_resolve_url,
    ) -> None:
        """Test authentication when security response has no Set-Cookie header."""
        mock_resolve_url.return_value = "https://vmanage.com"
        mock_configure_session.return_value = MagicMock()
        mock_return_response_obj.return_value = MagicMock()
        mock_return_response_obj.return_value.headers = {}
        logger: Logger = getLogger(name="test")
        obj: MagicMock = MagicMock()
        task: MagicMock = MagicMock()
        task.host.password = "mock_api_key"
        task.host.username = "mock_api_username"

        with self.assertRaises(ValueError):
            NetmikoCiscoVmanage.authenticate(
                logger=logger,
                obj=obj,
                task=task,
            )
        mock_resolve_url.assert_called_once()
        mock_configure_session.assert_called_once()
        mock_return_response_obj.assert_called_once()

    @patch(f"{base_import_path}.cisco_vmanage.resolve_controller_url")
    @patch(f"{base_import_path}.cisco_vmanage.NetmikoCiscoVmanage.configure_session")
    @patch(f"{base_import_path}.cisco_vmanage.NetmikoCiscoVmanage.return_response_obj")
    @patch(f"{base_import_path}.cisco_vmanage.NetmikoCiscoVmanage.return_response_content")
    def test_authenticate_no_token_resp(
        self,
        mock_return_response_content,
        mock_return_response_obj,
        mock_configure_session,
        mock_resolve_url,
    ) -> None:
        """Test authentication when token response is None."""
        mock_resolve_url.return_value = "https://vmanage.com"
        mock_configure_session.return_value = MagicMock()
        mock_return_response_obj.return_value = MagicMock()
        mock_return_response_obj.return_value.headers = {
            "Set-Cookie": "JSESSIONID=mock_session_id",
        }
        mock_return_response_content.return_value = None
        logger: Logger = getLogger(name="test")
        obj: MagicMock = MagicMock()
        task: MagicMock = MagicMock()
        task.host.password = "mock_api_key"
        task.host.username = "mock_api_username"

        with self.assertRaises(ValueError):
            NetmikoCiscoVmanage.authenticate(
                logger=logger,
                obj=obj,
                task=task,
            )
        mock_resolve_url.assert_called_once()
        mock_configure_session.assert_called_once()
        mock_return_response_obj.assert_called_once()
        mock_return_response_content.assert_called_once()

    @patch.object(target=NetmikoCiscoVmanage, attribute="url", new="https://vmanage.com")
    @patch.object(target=NetmikoCiscoVmanage, attribute="session", new_callable=MagicMock)
    @patch.object(target=NetmikoCiscoVmanage, attribute="configure_session", new=MagicMock())
    @patch.object(target=NetmikoCiscoVmanage, attribute="return_response_content")
    def test_resolve_backup_endpoint(self, mock_return_response_content, mock_session) -> None:
        """Test the get_config process for the Cisco vManage dispatcher."""
        # Setup mocks
        mock_session.return_value = MagicMock()
        mock_return_response_content.return_value = get_json_fixture(
            folder="api_responses",
            file_name="cisco_vmanage_backup.json",
        )
        logger: Logger = getLogger(name="test")
        config_context: dict[Any, Any] = get_json_fixture(
            folder="config_context",
            file_name="backup_vmanage_context.json",
        )

        # Call authenticate
        kwargs: dict[str, Any] = {}
        device_obj: MagicMock = MagicMock()
        responses: dict[str, str] = NetmikoCiscoVmanage.resolve_backup_endpoint(
            authenticated_obj=None,
            device_obj=device_obj,
            logger=logger,
            endpoint_context=config_context.get("ntp_backup"),
            feature_name="ntp_backup",
            **kwargs,
        )

        # Assertions
        self.assertIsNotNone(obj=responses)
        self.assertIn(member="templateName", container=responses)
        self.assertIn(member="templateId", container=responses)

    @patch.object(target=NetmikoCiscoVmanage, attribute="url", new="https://vmanage.com")
    @patch.object(target=NetmikoCiscoVmanage, attribute="session", new_callable=MagicMock)
    @patch.object(target=NetmikoCiscoVmanage, attribute="configure_session", new=MagicMock())
    @patch.object(target=NetmikoCiscoVmanage, attribute="return_response_content")
    def test_resolve_backup_endpoint_no_response(self, mock_return_response_content, mock_session) -> None:
        """Test resolve_backup_endpoint when no response is returned."""
        mock_session.return_value = MagicMock()
        mock_return_response_content.return_value = None
        logger: Logger = getLogger(name="test")
        config_context: dict[Any, Any] = get_json_fixture(
            folder="config_context",
            file_name="backup_vmanage_context.json",
        )

        kwargs: dict[str, Any] = {}
        device_obj: MagicMock = MagicMock()
        responses: dict[str, str] = NetmikoCiscoVmanage.resolve_backup_endpoint(
            authenticated_obj=None,
            device_obj=device_obj,
            logger=logger,
            endpoint_context=config_context.get("ntp_backup"),
            feature_name="ntp_backup",
            **kwargs,
        )

        self.assertEqual(responses, {})

    @patch.object(target=NetmikoCiscoVmanage, attribute="url", new="https://vmanage.com")
    @patch.object(target=NetmikoCiscoVmanage, attribute="session", new_callable=MagicMock)
    @patch.object(target=NetmikoCiscoVmanage, attribute="configure_session", new=MagicMock())
    @patch.object(target=NetmikoCiscoVmanage, attribute="return_response_content")
    def test_resolve_backup_endpoint_jmespath_not_found(self, mock_return_response_content, mock_session) -> None:
        """Test resolve_backup_endpoint when jmespath values are not found."""
        mock_session.return_value = MagicMock()
        mock_return_response_content.return_value = {"some_key": "some_value"}
        logger: Logger = getLogger(name="test")
        config_context: dict[Any, Any] = get_json_fixture(
            folder="config_context",
            file_name="backup_vmanage_context.json",
        )

        kwargs: dict[str, Any] = {}
        device_obj: MagicMock = MagicMock()
        responses: dict[str, str] = NetmikoCiscoVmanage.resolve_backup_endpoint(
            authenticated_obj=None,
            device_obj=device_obj,
            logger=logger,
            endpoint_context=config_context.get("ntp_backup"),
            feature_name="ntp_backup",
            **kwargs,
        )

        self.assertEqual(responses, {})
