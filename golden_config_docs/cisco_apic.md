# Cisco APIC Golden Config Dispatcher

## Overview

The **Cisco APIC Golden Config Dispatcher** provides **backup** workflows for Cisco ACI fabrics via the **APIC REST API**. It authenticates with the APIC controller, maintains a persistent HTTP session using a cookie-based token, and executes YAML-defined endpoints to retrieve structured data filtered through **JMESPath** for Nautobot Golden Config.

- **Transport**: HTTPS (using `requests.Session`)
- **Authentication**: Username + Password -> APIC login token (`APIC-cookie`)
- **Scope**: Backup only

## Authentication Details

Authentication with Cisco APIC involves a multi-step process to establish a secure session:

1. **Controller URL Resolution**: The dispatcher first resolves the APIC controller's base URL from the Nautobot `ConfigContext` for the controller type `'apic'`.
2. **Credential Usage**: It uses the device’s Nornir host credentials (`username`, `password`) to authenticate.
3. **Login Request**: A `POST` request is sent to the `api/aaaLogin.json` endpoint with the APIC login payload.
4. **Token Extraction**: The login token (cookie) is extracted from the response and stored in the `get_headers` for all subsequent API calls.
5. **Persistent Session**: A `requests.Session` (managed by `ConnectionMixin`) is reused for all further API interactions, ensuring session persistence.

## Key Features/Differences

- **Cookie-based Authentication**: Utilizes APIC's cookie-based authentication mechanism for session management.
- **Backup Only**: This dispatcher is currently designed for backup operations only; remediation is not implemented.

## Usage Notes

- **Device ConfigContext**: The Nautobot `Device` associated with the APIC controller must have a `ConfigContext` defined that specifies the APIC controller URL for controller type `'apic'`.
- **Credentials**: The Nautobot device’s `username` and `password` fields must contain valid APIC login credentials.
- **TLS Verification**: For production environments, it is crucial to update the dispatcher to use `verify=True` and provide trusted CA bundles for TLS verification. The current implementation might use `verify=False` for development convenience.
- **Error Handling**:
  - A `ValueError` is raised if no cookie is returned from the APIC authentication process.
  - If `jmespath` filters do not match the API response, the dispatcher logs an error and continues processing other endpoints.

## File & Class Reference

- **Class**: `NetmikoCiscoApic`
  - Inherits from `BaseAPIDispatcher` and `ConnectionMixin`.
  - `controller_type = "apic"`
  - `url`: Stores the base APIC controller URL (resolved from `ConfigContext`).
  - `session`: Manages the persistent `requests.Session`.
  - `get_headers`: Contains the `APIC-cookie` for authenticated calls.
  - Key Methods:
    - `authenticate(logger, obj, task)`: Handles login to APIC and stores the session cookie.
    - `resolve_backup_endpoint(authenticated_obj, device_obj, logger, endpoint_context, feature_name, **kwargs)`: Executes backup endpoints, parses responses with JMESPath, and aggregates results.
- **YAML Files**:
  - `cisco_apic_backup_endpoints.yml`: Defines the API endpoints for backup operations.
