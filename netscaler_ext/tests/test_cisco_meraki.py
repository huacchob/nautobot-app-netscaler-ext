import unittest
from logging import Logger, getLogger
from typing import Any
from unittest.mock import MagicMock, patch

from meraki import DashboardAPI

from netscaler_ext.plugins.tasks.dispatcher.cisco_meraki import NetmikoCiscoMeraki
from netscaler_ext.tests.fixtures import get_json_fixture


class TestCiscoMerakiDispatcher(unittest.TestCase):
    """Test the Cisco Meraki dispatcher."""

    base_import_path: str = "netscaler_ext.plugins.tasks.dispatcher"

    @patch(f"{base_import_path}.cisco_meraki.resolve_controller_url")
    @patch(f"{base_import_path}.cisco_meraki.add_api_path_to_url")
    @patch(f"{base_import_path}.cisco_meraki.DashboardAPI")
    def test_authenticate(
        self,
        mock_dashboard_api,
        mock_add_api_path,
        mock_resolve_url,
    ) -> None:
        """Test the authentication process for the Cisco Meraki dispatcher."""
        # Setup mocks
        mock_resolve_url.return_value = "https://mock-controller-url"
        mock_add_api_path.return_value = "https://mock-controller-url/api/v1"
        mock_dashboard_api.return_value = MagicMock()
        logger: Logger = getLogger(name="test")
        obj: MagicMock = MagicMock()
        task: MagicMock = MagicMock()
        task.host.password = "mock_api_key"

        # Call authenticate
        controller: DashboardAPI = NetmikoCiscoMeraki.authenticate(
            logger=logger,
            obj=obj,
            task=task,
        )

        # Assertions
        mock_resolve_url.assert_called_once()
        mock_add_api_path.assert_called_once_with(
            api_path="api/v1",
            base_url="https://mock-controller-url",
        )
        mock_dashboard_api.assert_called_once_with(
            api_key="mock_api_key",
            base_url="https://mock-controller-url/api/v1",
            output_log=False,
            print_console=False,
        )
        self.assertIsNotNone(obj=controller)

    @patch(f"{base_import_path}.cisco_meraki.DashboardAPI")
    def test_controller_setup(
        self,
        mock_dashboard_api,
    ) -> None:
        """Test the authentication process for the Cisco Meraki dispatcher."""
        # Setup mocks
        mock_dashboard_api.return_value = MagicMock()
        logger: Logger = getLogger(name="test")
        device_obj: MagicMock = MagicMock()
        device_obj.get_config_context.return_value = get_json_fixture(
            folder="config_context",
            file_name="backup_meraki_context.json",
        )

        # Call authenticate
        setup_dict: dict[str, str] = NetmikoCiscoMeraki.controller_setup(
            device_obj=device_obj,
            logger=logger,
            controller_obj=mock_dashboard_api.return_value,
        )

        # Assertions
        self.assertIsNotNone(obj=setup_dict)
        self.assertIn(member="organizationId", container=setup_dict)

    @patch(f"{base_import_path}.cisco_meraki._send_call")
    @patch(f"{base_import_path}.cisco_meraki._resolve_method_callable")
    @patch(f"{base_import_path}.cisco_meraki.DashboardAPI")
    def test_resolve_backup_endpoint(
        self,
        mock_dashboard_api,
        mock_resolve_method_callable,
        mock_send_call,
    ) -> None:
        """Test the authentication process for the Cisco Meraki dispatcher."""
        # Setup mocks
        mock_dashboard_api.return_value = MagicMock()
        mock_resolve_method_callable.return_value = MagicMock()
        mock_send_call.return_value = get_json_fixture(
            folder="api_responses",
            file_name="cisco_meraki_backup.json",
        )
        logger: Logger = getLogger(name="test")
        config_context: dict[Any, Any] = get_json_fixture(
            folder="config_context",
            file_name="backup_meraki_context.json",
        )

        # Call authenticate
        kwargs: dict[str, Any] = {
            "organizationId": config_context.get("organization_id"),
            "networkId": config_context.get("network_id"),
        }
        responses: dict[str, str] = NetmikoCiscoMeraki.resolve_backup_endpoint(
            controller_obj=mock_dashboard_api.return_value,
            logger=logger,
            endpoint_context=config_context.get("ntp_backup"),
            **kwargs,
        )

        # Assertions
        self.assertIsNotNone(obj=responses)

    @patch(f"{base_import_path}.cisco_meraki._resolve_method_callable")
    @patch(f"{base_import_path}.cisco_meraki.DashboardAPI")
    def test_resolve_remediation_endpoint(
        self,
        mock_dashboard_api,
        mock_resolve_method_callable,
    ) -> None:
        """Test the remediation endpoint resolution for Cisco Meraki dispatcher."""
        # Setup mocks
        mock_dashboard_api.return_value = MagicMock()
        mock_method = MagicMock(return_value={"result": "success"})
        mock_resolve_method_callable.return_value = mock_method
        logger: Logger = getLogger(name="test")

        endpoint_context: dict[Any, Any] = get_json_fixture(
            folder="config_context",
            file_name="remediation_meraki_context.json",
        )["ntp_remediation"]
        payload: dict[Any, Any] = get_json_fixture(
            folder="backup_response",
            file_name="cisco_meraki_backup.json",
        )

        responses = NetmikoCiscoMeraki.resolve_remediation_endpoint(
            controller_obj=mock_dashboard_api.return_value,
            logger=logger,
            endpoint_context=endpoint_context,
            payload=payload,
            organizationId="1278859",
        )

        self.assertIsInstance(responses, list)
        self.assertTrue(any("result" in r for r in responses))
