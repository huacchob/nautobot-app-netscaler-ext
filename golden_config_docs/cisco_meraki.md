# Cisco Meraki Golden Config Dispatcher

## Overview

The **Cisco Meraki Golden Config Dispatcher** provides **backup** and **remediation** workflows for Cisco Meraki controllers using the official **Meraki Dashboard SDK (`DashboardAPI`)**. This dispatcher dynamically resolves **SDK callables** defined in YAML endpoint files, executes them, and extracts structured data for Nautobot Golden Config.

- **Transport**: HTTPS (via Meraki Dashboard SDK, which uses REST API)
- **Authentication**: API key (from Nautobot device password)
- **Scope**: Backup and Remediation
- **Platform**: `cisco_meraki` (for controller-level interactions)
  - _Note_: For Meraki-managed devices (e.g., APs, switches), refer to the `meraki_managed.py` dispatcher.

## Authentication Details

Authentication with Cisco Meraki is handled by the Meraki Dashboard SDK:

1. **API Key Retrieval**: The API key is securely retrieved from the Nautobot device’s `task.host.password` field.
2. **Controller URL Resolution**: The base controller URL is resolved from the device’s `ConfigContext` for the controller type `'meraki'`, and `api/v1` is appended to form the full API endpoint.
3. **SDK Initialization**: The `DashboardAPI` SDK is initialized with the retrieved API key and the constructed base URL.

## Key Features/Differences

- **SDK-driven Interaction**: Unlike some other dispatchers, this one leverages the official Meraki Dashboard SDK, simplifying API interactions.
- **Controller Setup**: Includes a `controller_setup` method to map essential Meraki-specific parameters (organization ID, network ID, device serial) from Nautobot's `ConfigContext` and `Device` object.
- **Backup and Remediation**: Supports both backup and remediation workflows.

## Usage Notes

- **API Key**: The Nautobot device `password` field is used as the Meraki API key. Ensure this field contains a valid Meraki API key.
- **ConfigContext Requirements**:
  - The device’s `ConfigContext` must define `organization_id` and `network_id` for proper operation.
  - The Nautobot `Device` object's `serial` attribute is also utilized.
- **JMESPath**: Ensure that endpoint YAML definitions provide valid `jmespath` queries to correctly extract required fields from API responses.
- **TLS Verification**: The Meraki SDK handles HTTPS communication. In production, always ensure trusted certificates are used for secure connections.
- **Scope**: This dispatcher is specifically for interacting with the Meraki controller at a high level (e.g., fetching organization-wide settings). For device-specific configurations on Meraki-managed devices, use the `meraki_managed.py` dispatcher.

## File & Class Reference

- **Class**: `NetmikoCiscoMeraki`
  - Inherits from `BaseAPIDispatcher`.
  - `controller_type = "meraki"`
  - `controller_obj`: Stores the initialized Meraki `DashboardAPI` instance.
  - Key Methods:
    - `authenticate(logger, obj, task)`: Establishes the connection to the Meraki Dashboard API and returns the `DashboardAPI` instance.
    - `controller_setup(device_obj, authenticated_obj, logger)`: Retrieves organization ID, network ID, and device serial from `ConfigContext` and the `Device` object.
    - `resolve_backup_endpoint(authenticated_obj, device_obj, logger, endpoint_context, feature_name, **kwargs)`: Executes SDK calls for backup, aggregates results.
    - `resolve_remediation_endpoint(authenticated_obj, device_obj, logger, endpoint_context, payload, **kwargs)`: Executes SDK calls for remediation, handling single dictionary or list of dictionary payloads.
- **YAML Files**:
  - `cisco_meraki_backup_endpoints.yml`: Defines SDK callables and JMESPath for backup operations.
  - `cisco_meraki_remediation_endpoints.yml`: Defines SDK callables and parameters for remediation operations.
