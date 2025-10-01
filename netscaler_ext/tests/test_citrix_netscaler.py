import unittest
from logging import Logger, getLogger
from typing import Any
from unittest.mock import MagicMock, patch

from netscaler_ext.plugins.tasks.dispatcher.citrix_netscaler import NetmikoCitrixNetscaler
from netscaler_ext.tests.fixtures import get_json_fixture


class TestCitrixNetscalerDispatcher(unittest.TestCase):
    """Test the Citrix Netscaler dispatcher."""

    base_import_path: str = "netscaler_ext.plugins.tasks.dispatcher"

    @patch.object(target=NetmikoCitrixNetscaler, attribute="device_url", new="https://netscaler.com")
    @patch.object(target=NetmikoCitrixNetscaler, attribute="session", new_callable=MagicMock)
    @patch.object(target=NetmikoCitrixNetscaler, attribute="configure_session", new=MagicMock())
    @patch.object(target=NetmikoCitrixNetscaler, attribute="return_response_obj")
    def test_resolve_backup_endpoint(self, mock_return_response_obj, mock_session) -> None:
        """Test the authentication process for the Citrix Netscaler dispatcher."""
        # Setup mocks
        mock_return_response_obj.return_value.json.return_value = get_json_fixture(
            folder="api_responses",
            file_name="full_netscaler_response.json",
        )
        mock_session.return_value = MagicMock()
        logger: Logger = getLogger(name="test")
        config_context: dict[Any, Any] = get_json_fixture(
            folder="config_context",
            file_name="backup_netscaler_context.json",
        )

        # Call authenticate
        kwargs: dict[str, Any] = {}
        responses: dict[str, str] = NetmikoCitrixNetscaler.resolve_backup_endpoint(
            controller_obj=None,
            logger=logger,
            endpoint_context=config_context.get("ntp_backup"),
            **kwargs,
        )
        expected_response: dict[str, Any] = get_json_fixture(
            folder="api_responses",
            file_name="netscaler_backup.json",
        )

        # Assertions
        self.assertIsNotNone(obj=responses)
        self.assertEqual(responses, expected_response)
