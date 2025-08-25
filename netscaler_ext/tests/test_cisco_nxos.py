import unittest
from logging import Formatter, Logger, StreamHandler, getLogger
from typing import Any, TextIO
from unittest.mock import MagicMock, patch

from netscaler_ext.plugins.tasks.dispatcher.cisco_nxos import NetmikoCiscoNxos
from netscaler_ext.tests.fixtures import get_json_fixture


class TestWtiDispatcher(unittest.TestCase):
    """Test the WTI dispatcher."""

    base_import_path: str = "netscaler_ext.plugins.tasks.dispatcher"

    @patch(f"{base_import_path}.wti.NetmikoCiscoNxos.return_response_content")
    def test_resolve_backup_endpoint(self, mock_return_response_content) -> None:
        """Test the authentication process for the WTI dispatcher."""
        # Setup mocks
        NetmikoCiscoNxos.session = MagicMock()
        NetmikoCiscoNxos.device_url = "https://wti.com"
        mock_return_response_content.return_value = get_json_fixture(
            folder="api_responses",
            file_name="wti_backup.json",
        )
        logger: Logger = getLogger(name="test")
        config_context: dict[Any, Any] = get_json_fixture(
            folder="config_context",
            file_name="backup_wti_context.json",
        )

        # Call authenticate
        kwargs: dict[str, Any] = {}
        responses: dict[str, str] = NetmikoCiscoNxos.resolve_backup_endpoint(
            controller_obj=None,
            logger=logger,
            endpoint_context=config_context.get("snmp_backup"),
            **kwargs,
        )

        # Assertions
        self.assertIsNotNone(obj=responses)


if __name__ == "__main__":
    unittest.main()
    logger: Logger = getLogger(name="apic_test")
    if not logger.handlers:
        handler: StreamHandler[TextIO] = StreamHandler()
        formatter: Formatter = Formatter(fmt="%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(fmt=formatter)
        logger.addHandler(hdlr=handler)
    logger.setLevel(level="DEBUG")
