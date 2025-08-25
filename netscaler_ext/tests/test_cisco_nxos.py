import unittest
from logging import Formatter, Logger, StreamHandler, getLogger
from typing import TextIO
from unittest.mock import patch

from netscaler_ext.tests.fixtures import get_cfg_fixture


class TestWtiDispatcher(unittest.TestCase):
    """Test the WTI dispatcher."""

    base_import_path: str = "netscaler_ext.plugins.tasks.dispatcher"

    @patch(f"{base_import_path}.cisco_nxos.NetmikoCiscoNxos.get_command")
    def test_get_config(self, mock_get_command) -> None:
        """Test the authentication process for the NXOS dispatcher."""
        # Setup mocks
        mock_get_command.return_value = get_cfg_fixture(
            folder="api_responses",
            file_name="nxos_snmp_user.cfg",
        )
        getLogger(name="test")


if __name__ == "__main__":
    unittest.main()
    logger: Logger = getLogger(name="apic_test")
    if not logger.handlers:
        handler: StreamHandler[TextIO] = StreamHandler()
        formatter: Formatter = Formatter(fmt="%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(fmt=formatter)
        logger.addHandler(hdlr=handler)
    logger.setLevel(level="DEBUG")
