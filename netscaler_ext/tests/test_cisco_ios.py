import unittest
from unittest.mock import MagicMock, patch

from netscaler_ext.plugins.tasks.dispatcher.cisco_ios import (
    NetmikoCiscoIos,
    snmp_user_command_build,
    snmp_user_template,
)
from netscaler_ext.tests.fixtures import get_cfg_fixture


class TestIosDispatcher(unittest.TestCase):
    """Test the IOS dispatcher."""

    base_import_path: str = "netscaler_ext.plugins.tasks.dispatcher"

    @patch(f"{base_import_path}.cisco_ios.NetmikoCiscoIos._process_config")
    @patch(f"{base_import_path}.cisco_ios.NetmikoCiscoIos.get_command")
    def test_get_config(self, mock_get_command, mock_process_config) -> None:
        """Test the authentication process for the IOS dispatcher."""
        with patch.object(target=NetmikoCiscoIos, attribute="config_commands", new=["show snmp user"]):
            # Setup mocks
            mock_get_command.return_value = MagicMock()
            mock_get_command.return_value.result.return_value = {
                "output": {
                    "show snmp user": get_cfg_fixture(
                        folder="backup_response",
                        file_name="ios_snmp_user.cfg",
                    ),
                }
            }
            snmp_dict = snmp_user_template(
                snmp_user_output=get_cfg_fixture(
                    folder="backup_response",
                    file_name="ios_snmp_user.cfg",
                )
            )
            snmp_config = snmp_user_command_build(parsed_snmp_user=snmp_dict)
            mock_process_config.return_value = snmp_config
            task = MagicMock()
            logger = MagicMock()
            obj = MagicMock()
            backup_file = ""
            remove_lines = []
            substitute_lines = []
            result = NetmikoCiscoIos.get_config(
                task=task,
                logger=logger,
                obj=obj,
                backup_file=backup_file,
                remove_lines=remove_lines,
                substitute_lines=substitute_lines,
            )
            print(result.result)
            self.assertEqual(result.result.get("config"), snmp_config)
