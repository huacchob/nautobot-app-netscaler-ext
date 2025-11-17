import unittest
from logging import Logger, getLogger
from typing import Any
from unittest.mock import MagicMock, patch

from netscaler_ext.plugins.tasks.dispatcher.wti import NetmikoWti
from netscaler_ext.tests.fixtures import get_json_fixture


class TestWtiDispatcher(unittest.TestCase):
    """Test the WTI dispatcher."""

    base_import_path: str = "netscaler_ext.plugins.tasks.dispatcher"

    @patch(f"{base_import_path}.wti.base_64_encode_credentials")
    @patch.object(target=NetmikoWti, attribute="configure_session")
    def test_authenticate(
        self,
        mock_configure_session,
        mock_base_64_encode_credentials,
    ) -> None:
        """Test the authentication process for the WTI dispatcher."""
        NetmikoWti.get_headers = {}
        mock_base_64_encode_credentials.return_value = "mock_encoded_creds"
        mock_configure_session.return_value = MagicMock()
        logger: Logger = getLogger(name="test")
        obj: MagicMock = MagicMock()
        obj.primary_ip4.host = "1.1.1.1"
        task: MagicMock = MagicMock()
        task.host.password = "mock_api_key"
        task.host.username = "mock_api_username"

        NetmikoWti.authenticate(
            logger=logger,
            obj=obj,
            task=task,
        )

        mock_base_64_encode_credentials.assert_called_once()
        mock_configure_session.assert_called_once()
        self.assertIn("Authorization", NetmikoWti.get_headers)

    @patch(f"{base_import_path}.wti.base_64_encode_credentials")
    @patch.object(target=NetmikoWti, attribute="configure_session")
    def test_authenticate_no_username(
        self,
        mock_configure_session,
        mock_base_64_encode_credentials,
    ) -> None:
        """Test authentication when username is missing."""
        NetmikoWti.get_headers = {}
        mock_base_64_encode_credentials.return_value = "mock_encoded_creds"
        mock_configure_session.return_value = MagicMock()
        logger: Logger = getLogger(name="test")
        obj: MagicMock = MagicMock()
        obj.primary_ip4.host = "1.1.1.1"
        task: MagicMock = MagicMock()
        task.host.password = "mock_api_key"
        task.host.username = ""

        NetmikoWti.authenticate(
            logger=logger,
            obj=obj,
            task=task,
        )

        mock_base_64_encode_credentials.assert_called_once()
        mock_configure_session.assert_called_once()
        self.assertIn("Authorization", NetmikoWti.get_headers)

    @patch(f"{base_import_path}.wti.base_64_encode_credentials")
    @patch.object(target=NetmikoWti, attribute="configure_session")
    def test_authenticate_no_password(
        self,
        mock_configure_session,
        mock_base_64_encode_credentials,
    ) -> None:
        """Test authentication when password is missing."""
        NetmikoWti.get_headers = {}
        mock_base_64_encode_credentials.return_value = "mock_encoded_creds"
        mock_configure_session.return_value = MagicMock()
        logger: Logger = getLogger(name="test")
        obj: MagicMock = MagicMock()
        obj.primary_ip4.host = "1.1.1.1"
        task: MagicMock = MagicMock()
        task.host.password = ""
        task.host.username = "mock_api_username"

        NetmikoWti.authenticate(
            logger=logger,
            obj=obj,
            task=task,
        )

        mock_base_64_encode_credentials.assert_called_once()
        mock_configure_session.assert_called_once()
        self.assertIn("Authorization", NetmikoWti.get_headers)

    @patch(f"{base_import_path}.wti.base_64_encode_credentials")
    @patch.object(target=NetmikoWti, attribute="configure_session")
    def test_authenticate_base64_encode_error(
        self,
        mock_configure_session,
        mock_base_64_encode_credentials,
    ) -> None:
        """Test authentication when base_64_encode_credentials raises ValueError."""
        NetmikoWti.get_headers = {}
        mock_base_64_encode_credentials.side_effect = ValueError("Test Error")
        logger: Logger = getLogger(name="test")
        obj: MagicMock = MagicMock()
        obj.primary_ip4.host = "1.1.1.1"
        task: MagicMock = MagicMock()
        task.host.password = "mock_api_key"
        task.host.username = "mock_api_username"

        with self.assertRaises(ValueError):
            NetmikoWti.authenticate(
                logger=logger,
                obj=obj,
                task=task,
            )

        mock_base_64_encode_credentials.assert_called_once()
        mock_configure_session.assert_called_once()
        self.assertNotIn("Authorization", NetmikoWti.get_headers)

    @patch.object(target=NetmikoWti, attribute="return_response_content")
    def test_resolve_backup_endpoint(self, mock_return_response_content) -> None:
        """Test the authentication process for the WTI dispatcher."""
        # Setup mocks
        mock_return_response_content.return_value = get_json_fixture(
            folder="api_responses",
            file_name="wti_backup.json",
        )
        NetmikoWti.session = MagicMock()
        logger: Logger = getLogger(name="test")
        config_context: dict[Any, Any] = get_json_fixture(
            folder="config_context",
            file_name="backup_wti_context.json",
        )

        # Call authenticate
        kwargs: dict[str, Any] = {}
        device_obj: MagicMock = MagicMock()
        responses: dict[str, str] = NetmikoWti.resolve_backup_endpoint(
            authenticated_obj=None,
            device_obj=device_obj,
            logger=logger,
            endpoint_context=config_context.get("snmp_backup"),
            feature_name="snmp_backup",
            **kwargs,
        )

        # Assertions
        self.assertIsNotNone(obj=responses)

    @patch.object(target=NetmikoWti, attribute="url", new="https://wti.com")
    @patch.object(target=NetmikoWti, attribute="configure_session", new=MagicMock())
    @patch.object(target=NetmikoWti, attribute="return_response_content")
    def test_resolve_backup_endpoint_no_response(self, mock_return_response_content) -> None:
        """Test resolve_backup_endpoint when no response is returned."""
        mock_return_response_content.return_value = None
        NetmikoWti.session = MagicMock()
        logger: Logger = getLogger(name="test")
        config_context: dict[Any, Any] = get_json_fixture(
            folder="config_context",
            file_name="backup_wti_context.json",
        )

        kwargs: dict[str, Any] = {}
        device_obj: MagicMock = MagicMock()
        responses: dict[str, str] = NetmikoWti.resolve_backup_endpoint(
            authenticated_obj=None,
            device_obj=device_obj,
            logger=logger,
            endpoint_context=config_context.get("snmp_backup"),
            feature_name="snmp_backup",
            **kwargs,
        )

        self.assertEqual(responses, {})

    @patch.object(target=NetmikoWti, attribute="url", new="https://wti.com")
    @patch.object(target=NetmikoWti, attribute="configure_session", new=MagicMock())
    @patch.object(target=NetmikoWti, attribute="return_response_content")
    def test_resolve_backup_endpoint_jmespath_not_found(self, mock_return_response_content) -> None:
        """Test resolve_backup_endpoint when jmespath values are not found."""
        mock_return_response_content.return_value = {"some_key": "some_value"}
        NetmikoWti.session = MagicMock()
        logger: Logger = getLogger(name="test")
        config_context: dict[Any, Any] = get_json_fixture(
            folder="config_context",
            file_name="backup_wti_context.json",
        )

        kwargs: dict[str, Any] = {}
        device_obj: MagicMock = MagicMock()
        responses: dict[str, str] = NetmikoWti.resolve_backup_endpoint(
            authenticated_obj=None,
            device_obj=device_obj,
            logger=logger,
            endpoint_context=config_context.get("snmp_backup"),
            feature_name="snmp_backup",
            **kwargs,
        )

        self.assertEqual(responses, {})
