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

    @patch(f"{base_import_path}.cisco_meraki.resolve_controller_url")
    @patch(f"{base_import_path}.cisco_meraki.add_api_path_to_url")
    @patch(f"{base_import_path}.cisco_meraki.DashboardAPI")
    def test_authenticate_resolve_url_error(
        self,
        mock_dashboard_api,
        mock_add_api_path,
        mock_resolve_url,
    ) -> None:
        """Test authentication when resolve_controller_url raises ValueError."""
        mock_resolve_url.side_effect = ValueError("Test Error")
        logger: Logger = getLogger(name="test")
        obj: MagicMock = MagicMock()
        task: MagicMock = MagicMock()
        task.host.password = "mock_api_key"

        with self.assertRaises(ValueError):
            NetmikoCiscoMeraki.authenticate(
                logger=logger,
                obj=obj,
                task=task,
            )
        mock_resolve_url.assert_called_once()
        mock_add_api_path.assert_not_called()
        mock_dashboard_api.assert_not_called()

    @patch(f"{base_import_path}.cisco_meraki.resolve_controller_url")
    @patch(f"{base_import_path}.cisco_meraki.add_api_path_to_url")
    @patch(f"{base_import_path}.cisco_meraki.DashboardAPI")
    def test_authenticate_add_api_path_error(
        self,
        mock_dashboard_api,
        mock_add_api_path,
        mock_resolve_url,
    ) -> None:
        """Test authentication when add_api_path_to_url raises ValueError."""
        mock_resolve_url.return_value = "https://mock-controller-url"
        mock_add_api_path.side_effect = ValueError("Test Error")
        logger: Logger = getLogger(name="test")
        obj: MagicMock = MagicMock()
        task: MagicMock = MagicMock()
        task.host.password = "mock_api_key"

        with self.assertRaises(ValueError):
            NetmikoCiscoMeraki.authenticate(
                logger=logger,
                obj=obj,
                task=task,
            )
        mock_resolve_url.assert_called_once()
        mock_add_api_path.assert_called_once()
        mock_dashboard_api.assert_not_called()

    @patch(f"{base_import_path}.cisco_meraki.resolve_controller_url")
    @patch(f"{base_import_path}.cisco_meraki.add_api_path_to_url")
    @patch(f"{base_import_path}.cisco_meraki.DashboardAPI")
    def test_authenticate_dashboard_api_error(
        self,
        mock_dashboard_api,
        mock_add_api_path,
        mock_resolve_url,
    ) -> None:
        """Test authentication when DashboardAPI returns None."""
        mock_resolve_url.return_value = "https://mock-controller-url"
        mock_add_api_path.return_value = "https://mock-controller-url/api/v1"
        mock_dashboard_api.return_value = None
        logger: Logger = getLogger(name="test")
        obj: MagicMock = MagicMock()
        task: MagicMock = MagicMock()
        task.host.password = "mock_api_key"

        with self.assertRaises(ValueError):
            NetmikoCiscoMeraki.authenticate(
                logger=logger,
                obj=obj,
                task=task,
            )
        mock_resolve_url.assert_called_once()
        mock_add_api_path.assert_called_once()
        mock_dashboard_api.assert_called_once()

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
            authenticated_obj=mock_dashboard_api.return_value,
        )

        # Assertions
        self.assertIsNotNone(obj=setup_dict)
        self.assertIn(member="organizationId", container=setup_dict)

    @patch(f"{base_import_path}.cisco_meraki.DashboardAPI")
    def test_controller_setup_no_org_id(
        self,
        mock_dashboard_api,
    ) -> None:
        """Test controller_setup when organizationId is missing."""
        mock_dashboard_api.return_value = MagicMock()
        logger: Logger = getLogger(name="test")
        device_obj: MagicMock = MagicMock()
        device_obj.get_config_context.return_value = {"some_key": "some_value"}

        with self.assertRaises(ValueError):
            NetmikoCiscoMeraki.controller_setup(
                device_obj=device_obj,
                logger=logger,
                authenticated_obj=mock_dashboard_api.return_value,
            )

    @patch(f"{base_import_path}.cisco_meraki.DashboardAPI")
    def test_controller_setup_no_network_id(
        self,
        mock_dashboard_api,
    ) -> None:
        """Test controller_setup when networkId is missing."""
        mock_dashboard_api.return_value = MagicMock()
        logger: Logger = getLogger(name="test")
        device_obj: MagicMock = MagicMock()
        device_obj.get_config_context.return_value = {"organization_id": "123"}

        setup_dict: dict[str, str] = NetmikoCiscoMeraki.controller_setup(
            device_obj=device_obj,
            logger=logger,
            authenticated_obj=mock_dashboard_api.return_value,
        )

        self.assertIsNotNone(obj=setup_dict)
        self.assertIn(member="organizationId", container=setup_dict)
        self.assertIsNone(setup_dict.get("networkId"))

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
        device_obj: MagicMock = MagicMock()
        responses: dict[str, str] = NetmikoCiscoMeraki.resolve_backup_endpoint(
            authenticated_obj=mock_dashboard_api.return_value,
            device_obj=device_obj,
            logger=logger,
            endpoint_context=config_context.get("ntp_backup"),
            feature_name="ntp_backup",
            **kwargs,
        )

        # Assertions
        self.assertIsNotNone(obj=responses)

    @patch(f"{base_import_path}.cisco_meraki._send_call")
    @patch(f"{base_import_path}.cisco_meraki._resolve_method_callable")
    @patch(f"{base_import_path}.cisco_meraki.DashboardAPI")
    def test_resolve_backup_endpoint_no_method_callable(
        self,
        mock_dashboard_api,
        mock_resolve_method_callable,
        mock_send_call,
    ) -> None:
        """Test resolve_backup_endpoint when _resolve_method_callable returns None."""
        mock_dashboard_api.return_value = MagicMock()
        mock_resolve_method_callable.return_value = None
        logger: Logger = getLogger(name="test")
        config_context: dict[Any, Any] = get_json_fixture(
            folder="config_context",
            file_name="backup_meraki_context.json",
        )

        kwargs: dict[str, Any] = {
            "organizationId": config_context.get("organization_id"),
            "networkId": config_context.get("network_id"),
        }
        device_obj: MagicMock = MagicMock()
        responses: dict[str, str] = NetmikoCiscoMeraki.resolve_backup_endpoint(
            authenticated_obj=mock_dashboard_api.return_value,
            device_obj=device_obj,
            logger=logger,
            endpoint_context=config_context.get("ntp_backup"),
            feature_name="ntp_backup",
            **kwargs,
        )

        self.assertEqual(responses, {})
        mock_resolve_method_callable.assert_called_once()
        mock_send_call.assert_not_called()

    @patch(f"{base_import_path}.cisco_meraki._send_call")
    @patch(f"{base_import_path}.cisco_meraki._resolve_method_callable")
    @patch(f"{base_import_path}.cisco_meraki.DashboardAPI")
    def test_resolve_backup_endpoint_no_send_call_response(
        self,
        mock_dashboard_api,
        mock_resolve_method_callable,
        mock_send_call,
    ) -> None:
        """Test resolve_backup_endpoint when _send_call returns None."""
        mock_dashboard_api.return_value = MagicMock()
        mock_resolve_method_callable.return_value = MagicMock()
        mock_send_call.return_value = None
        logger: Logger = getLogger(name="test")
        config_context: dict[Any, Any] = get_json_fixture(
            folder="config_context",
            file_name="backup_meraki_context.json",
        )

        kwargs: dict[str, Any] = {
            "organizationId": config_context.get("organization_id"),
            "networkId": config_context.get("network_id"),
        }
        device_obj: MagicMock = MagicMock()
        responses: dict[str, str] = NetmikoCiscoMeraki.resolve_backup_endpoint(
            authenticated_obj=mock_dashboard_api.return_value,
            device_obj=device_obj,
            logger=logger,
            endpoint_context=config_context.get("ntp_backup"),
            feature_name="ntp_backup",
            **kwargs,
        )

        self.assertEqual(responses, {})
        mock_resolve_method_callable.assert_called_once()
        mock_send_call.assert_called_once()

    @patch(f"{base_import_path}.cisco_meraki._send_call")
    @patch(f"{base_import_path}.cisco_meraki._resolve_method_callable")
    @patch(f"{base_import_path}.cisco_meraki.DashboardAPI")
    def test_resolve_backup_endpoint_missing_org_id(
        self,
        mock_dashboard_api,
        mock_resolve_method_callable,
        mock_send_call,
    ) -> None:
        """Test resolve_backup_endpoint when organizationId is missing from kwargs."""
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

        kwargs: dict[str, Any] = {
            "networkId": config_context.get("network_id"),
        }
        device_obj: MagicMock = MagicMock()
        with self.assertRaises(ValueError):
            NetmikoCiscoMeraki.resolve_backup_endpoint(
                authenticated_obj=mock_dashboard_api.return_value,
                device_obj=device_obj,
                logger=logger,
                endpoint_context=config_context.get("ntp_backup"),
                feature_name="ntp_backup",
                **kwargs,
            )

    @patch(f"{base_import_path}.cisco_meraki._send_call")
    @patch(f"{base_import_path}.cisco_meraki._resolve_method_callable")
    @patch(f"{base_import_path}.cisco_meraki.DashboardAPI")
    def test_resolve_backup_endpoint_missing_network_id(
        self,
        mock_dashboard_api,
        mock_resolve_method_callable,
        mock_send_call,
    ) -> None:
        """Test resolve_backup_endpoint when networkId is missing from kwargs."""
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

        kwargs: dict[str, Any] = {
            "organizationId": config_context.get("organization_id"),
        }
        device_obj: MagicMock = MagicMock()
        with self.assertRaises(ValueError):
            NetmikoCiscoMeraki.resolve_backup_endpoint(
                authenticated_obj=mock_dashboard_api.return_value,
                device_obj=device_obj,
                logger=logger,
                endpoint_context=config_context.get("ntp_backup"),
                feature_name="ntp_backup",
                **kwargs,
            )

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

        device_obj: MagicMock = MagicMock()
        responses = NetmikoCiscoMeraki.resolve_remediation_endpoint(
            authenticated_obj=mock_dashboard_api.return_value,
            device_obj=device_obj,
            logger=logger,
            endpoint_context=endpoint_context,
            payload=payload,
            organizationId="1278859",
        )

        self.assertIsInstance(responses, list)
        self.assertTrue(any("result" in r for r in responses))

    @patch(f"{base_import_path}.cisco_meraki._resolve_method_callable")
    @patch(f"{base_import_path}.cisco_meraki.DashboardAPI")
    def test_resolve_remediation_endpoint_no_method_callable(
        self,
        mock_dashboard_api,
        mock_resolve_method_callable,
    ) -> None:
        """Test resolve_remediation_endpoint when _resolve_method_callable returns None."""
        mock_dashboard_api.return_value = MagicMock()
        mock_resolve_method_callable.return_value = None
        logger: Logger = getLogger(name="test")

        endpoint_context: dict[Any, Any] = get_json_fixture(
            folder="config_context",
            file_name="remediation_meraki_context.json",
        )["ntp_remediation"]
        payload: dict[Any, Any] = get_json_fixture(
            folder="backup_response",
            file_name="cisco_meraki_backup.json",
        )

        device_obj: MagicMock = MagicMock()
        responses = NetmikoCiscoMeraki.resolve_remediation_endpoint(
            authenticated_obj=mock_dashboard_api.return_value,
            device_obj=device_obj,
            logger=logger,
            endpoint_context=endpoint_context,
            payload=payload,
            organizationId="1278859",
        )

        self.assertEqual(responses, [])
        mock_resolve_method_callable.assert_called_once()

    @patch(f"{base_import_path}.cisco_meraki._send_remediation_call")
    @patch(f"{base_import_path}.cisco_meraki._resolve_method_callable")
    @patch(f"{base_import_path}.cisco_meraki.DashboardAPI")
    def test_resolve_remediation_endpoint_payload_is_dict(
        self,
        mock_dashboard_api,
        mock_resolve_method_callable,
        mock_send_remediation_call,
    ) -> None:
        """Test resolve_remediation_endpoint when payload is a dictionary."""
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

        device_obj: MagicMock = MagicMock()
        NetmikoCiscoMeraki.resolve_remediation_endpoint(
            authenticated_obj=mock_dashboard_api.return_value,
            device_obj=device_obj,
            logger=logger,
            endpoint_context=endpoint_context,
            payload=payload,
            organizationId="1278859",
        )

        mock_send_remediation_call.assert_called_once()
