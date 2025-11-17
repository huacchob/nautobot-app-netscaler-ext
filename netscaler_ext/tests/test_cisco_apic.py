import unittest
from logging import Logger, getLogger
from typing import Any
from unittest.mock import MagicMock, patch

from netscaler_ext.plugins.tasks.dispatcher.cisco_apic import NetmikoCiscoApic
from netscaler_ext.tests.fixtures import get_json_fixture


class TestCiscoApicDispatcher(unittest.TestCase):
    """Test the Cisco APIC dispatcher."""

    base_import_path: str = "netscaler_ext.plugins.tasks.dispatcher"

    @patch(f"{base_import_path}.cisco_apic.resolve_controller_url")
    @patch(f"{base_import_path}.cisco_apic.NetmikoCiscoApic.configure_session")
    @patch(f"{base_import_path}.cisco_apic.NetmikoCiscoApic.return_response_content")
    def test_authenticate(
        self,
        mock_return_response_content,
        mock_configure_session,
        mock_resolve_url,
    ) -> None:
        """Test the authentication process for the Cisco APIC dispatcher."""
        # Setup mocks
        mock_resolve_url.return_value = "https://apic.com"
        mock_configure_session.return_value = MagicMock()
        mock_return_response_content.return_value = get_json_fixture(
            folder="api_responses",
            file_name="cisco_apic_auth.json",
        )
        logger: Logger = getLogger(name="test")
        obj: MagicMock = MagicMock()
        task: MagicMock = MagicMock()
        task.host.password = "mock_api_key"
        task.host.username = "mock_api_username"

        # Call authenticate
        NetmikoCiscoApic.authenticate(
            logger=logger,
            obj=obj,
            task=task,
        )

        # Assertions
        mock_resolve_url.assert_called_once()
        mock_configure_session.assert_called_once()

    @patch.object(target=NetmikoCiscoApic, attribute="url", new="https://apic.com")
    @patch.object(target=NetmikoCiscoApic, attribute="session", new_callable=MagicMock)
    @patch.object(target=NetmikoCiscoApic, attribute="configure_session", new=MagicMock())
    @patch.object(target=NetmikoCiscoApic, attribute="return_response_obj")
    def test_resolve_backup_endpoint(self, mock_return_response_obj, mock_session) -> None:
        """Test the authentication process for the Cisco APIC dispatcher."""
        mock_session.return_value = MagicMock()
        mock_return_response_obj.return_value.json.return_value = get_json_fixture(
            folder="api_responses",
            file_name="cisco_apic_backup.json",
        )
        logger: Logger = getLogger(name="test")
        config_context: dict[Any, Any] = get_json_fixture(
            folder="config_context",
            file_name="backup_apic_context.json",
        )

        # Call authenticate
        kwargs: dict[str, Any] = {}
        device_obj: MagicMock = MagicMock()
        responses: dict[str, str] = NetmikoCiscoApic.resolve_backup_endpoint(
            authenticated_obj=None,
            device_obj=device_obj,
            logger=logger,
            endpoint_context=config_context.get("ntp_backup"),
            feature_name="ntp_backup",
            **kwargs,
        )

        # Assertions
        self.assertIsNotNone(obj=responses)
