# Citrix Netscaler Golden Config Dispatcher

## Overview

The **Citrix Netscaler Golden Config Dispatcher** provides **backup** and **remediation** workflows against Citrix Netscaler devices using the device’s HTTPS API. It establishes an authenticated HTTP **session**, executes YAML-defined endpoints, and extracts structured data using **JMESPath** for Nautobot Golden Config.

- **Transport**: HTTPS (using `requests.Session`)
- **Authentication**: `X-NITRO-USER` and `X-NITRO-PASS` headers for credentials
- **Scope**: Backup only

## Authentication Details

Authentication with Citrix Netscaler involves setting specific headers for each API request:

1. **Device URL Construction**: The dispatcher constructs the device's base URL using the Nautobot device's name, typically in the format `https://<device.name>`. A helper function `use_snip_hostname` is used to format the hostname if it follows a specific SNIP convention.
2. **Persistent Session**: A `requests.Session` is created and managed via `ConnectionMixin` for persistent HTTP connections.
3. **Header Configuration**: The `X-NITRO-USER` and `X-NITRO-PASS` headers are populated with the Nautobot device's `username` and `password` respectively. The `Content-Type` header is set to `application/json`.

## Key Features/Differences

- **SNIP Hostname Support**: Includes logic to handle specific SNIP (Subnet IP) hostname formats for Citrix Netscaler devices.
- **Header-based Authentication**: Relies on custom HTTP headers (`X-NITRO-USER`, `X-NITRO-PASS`) for authentication.

## Usage Notes

- **TLS Verification**: For production environments, it is crucial to enable TLS verification (`verify=True`) and provide trusted certificates. The current implementation might use `verify=False` for development convenience.
- **Credentials**: Authentication requires the Nautobot `username` and `password` fields for the device. These are directly used to populate the `X-NITRO-USER` and `X-NITRO-PASS` HTTP headers.
- **ConfigContext Integration**: Backup and remediation endpoints should be defined in YAML under `citrix_netscaler_backup_endpoints.yml` and `citrix_netscaler_remediation_endpoints.yml`.
- **JMESPath**: Ensure your endpoint definitions provide valid `jmespath` queries; otherwise, fields may not be extracted and results could be empty.
- **Error Handling**:
  - If a required `non_optional` parameter is missing during remediation, the dispatcher logs an error.
  - If no valid responses are found for a backup feature, a `ValueError` is raised.
- **Payloads**: Remediation supports both single-dictionary and list-of-dictionaries payloads. `non_optional` parameters are injected into each payload entry as needed.

## File & Class Reference

- **Class**: `NetmikoCitrixNetscaler`
  - Inherits from `BaseAPIDispatcher` and `ConnectionMixin`.
  - `url`: Stores the base device URL (e.g., `https://<device.name>`).
  - `session`: Manages the shared `requests.Session`.
  - `get_headers`: Includes credentials (`X-NITRO-USER`, `X-NITRO-PASS`) and `Content-Type`.
  - Key Methods:
    - `authenticate(logger, obj, task)`: Sets the device URL, initializes the session, and configures authentication headers.
    - `resolve_backup_endpoint(authenticated_obj, device_obj, logger, endpoint_context, feature_name, **kwargs)`: Executes backup endpoints, parses responses with JMESPath, and aggregates results.
    - `resolve_remediation_endpoint(authenticated_obj, device_obj, logger, endpoint_context, payload, **kwargs)`: Executes remediation calls, injecting `non_optional` kwargs into payloads.
- **Helper Function**:
  - `use_snip_hostname(hostname)`: Formats the hostname to a SNIP-compatible format if applicable.
- **YAML Files**:
  - `citrix_netscaler_backup_endpoints.yml`: Defines API endpoints and JMESPath for backup operations.
  - `citrix_netscaler_remediation_endpoints.yml`: Defines API endpoints and parameters for remediation operations.
