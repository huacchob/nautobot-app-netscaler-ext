import unittest
from logging import Logger, getLogger
from typing import Any
from unittest.mock import MagicMock, patch

from netscaler_ext.plugins.tasks.dispatcher.wti import NetmikoWti
from netscaler_ext.tests.fixtures import get_json_fixture


class TestWtiDispatcher(unittest.TestCase):
    """Test the WTI dispatcher."""

    base_import_path: str = "netscaler_ext.plugins.tasks.dispatcher"

    @patch.object(target=NetmikoWti, attribute="device_url", new="https://wti.com")
    @patch.object(target=NetmikoWti, attribute="session", new_callable=MagicMock)
    @patch.object(target=NetmikoWti, attribute="configure_session", new=MagicMock())
    @patch.object(target=NetmikoWti, attribute="return_response_obj")
    def test_resolve_backup_endpoint(self, mock_return_response_obj, mock_session) -> None:
        """Test the authentication process for the WTI dispatcher."""
        # Setup mocks
        mock_return_response_obj.return_value.json.return_value = get_json_fixture(
            folder="api_responses",
            file_name="wti_backup.json",
        )
        mock_session.return_value = MagicMock()
        logger: Logger = getLogger(name="test")
        config_context: dict[Any, Any] = get_json_fixture(
            folder="config_context",
            file_name="backup_wti_context.json",
        )

        # Call authenticate
        kwargs: dict[str, Any] = {}
        responses: dict[str, str] = NetmikoWti.resolve_backup_endpoint(
            controller_obj=None,
            logger=logger,
            endpoint_context=config_context.get("snmp_backup"),
            **kwargs,
        )

        # Assertions
        self.assertIsNotNone(obj=responses)
