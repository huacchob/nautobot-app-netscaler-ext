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

    @patch.object(target=NetmikoCiscoVmanage, attribute="controller_url", new="https://vmanage.com")
    @patch.object(target=NetmikoCiscoVmanage, attribute="session", new_callable=MagicMock)
    @patch.object(target=NetmikoCiscoVmanage, attribute="configure_session", new=MagicMock())
    @patch.object(target=NetmikoCiscoVmanage, attribute="return_response_obj")
    def test_resolve_backup_endpoint(self, mock_return_response_obj, mock_session) -> None:
        """Test the get_config process for the Cisco vManage dispatcher."""
        # Setup mocks
        mock_session.return_value = MagicMock()
        mock_return_response_obj.return_value.json.return_value = get_json_fixture(
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
        responses: dict[str, str] = NetmikoCiscoVmanage.resolve_backup_endpoint(
            controller_obj=None,
            logger=logger,
            endpoint_context=config_context.get("ntp_backup"),
            **kwargs,
        )

        # Assertions
        self.assertIsNotNone(obj=responses)
        self.assertIn(member="templateName", container=responses)
        self.assertIn(member="templateId", container=responses)
