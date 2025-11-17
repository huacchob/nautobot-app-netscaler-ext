# WTI Golden Config Dispatcher

## Overview

The **WTI Golden Config Dispatcher** provides **backup** and **remediation** workflows for WTI devices using their HTTPS API. It establishes an authenticated HTTP **session**, executes YAML-defined endpoints, and extracts structured data using **JMESPath** for Nautobot Golden Config.

- **Transport**: HTTPS (using `requests.Session`)
- **Authentication**: Basic (Base64-encoded `username:password` in `Authorization` header)
- **Scope**: Backup and Remediation

## Authentication Details

Authentication with WTI devices uses Basic Authentication over HTTPS:

1. **Device URL Construction**: The dispatcher constructs the device's base URL using the Nautobot device’s primary IPv4 address, in the format `https://<device.primary_ip4.host>`.
2. **Persistent Session**: A `requests.Session` is created and managed via `ConnectionMixin` for persistent HTTP connections.
3. **Credential Encoding**: The Nautobot device's `username` and `password` are Base64-encoded into a single string.
4. **Header Configuration**: The Base64-encoded credentials are then included in the `Authorization` header (e.g., `Authorization: Basic <encoded_credentials>`). The `Content-Type` header is set to `application/json`.

## Key Features/Differences

- **Basic Authentication**: Utilizes standard HTTP Basic Authentication for secure access.

## Usage Notes

- **TLS Verification**: For production environments, it is crucial to enable TLS verification (`verify=True`) and provide trusted certificates. The current implementation might use `verify=False` for development convenience.
- **Credentials**: Authentication requires the Nautobot `username` and `password` fields for the device. These are Base64-encoded and sent in the `Authorization` header.
- **ConfigContext Integration**: Backup and remediation endpoints should be defined in YAML under `wti_backup_endpoints.yml` and `wti_remediation_endpoints.yml`.
- **JMESPath**: Ensure your endpoint definitions provide valid `jmespath` queries; otherwise, fields may not be extracted and results could be empty.
- **Error Handling**:
  - If a required `non_optional` parameter is missing during remediation, the dispatcher logs an error.
  - If no valid responses are found for a backup feature, a `ValueError` is raised.
- **Payloads**: Remediation supports both single-dictionary and list-of-dictionaries payloads. `non_optional` parameters are injected into each payload entry as needed.

## File & Class Reference

- **Class**: `NetmikoWti`
  - Inherits from `BaseAPIDispatcher` and `ConnectionMixin`.
  - `url`: Stores the base device URL (e.g., `https://<primary_ip4>`).
  - `session`: Manages the shared `requests.Session`.
  - `get_headers`, `post_headers`: Include the Base64 `Authorization` header.
  - Key Methods:
    - `authenticate(logger, obj, task)`: Sets the device URL, initializes the session, and configures authentication headers.
    - `resolve_backup_endpoint(authenticated_obj, device_obj, logger, endpoint_context, feature_name, **kwargs)`: Executes backup endpoints, parses responses with JMESPath, and aggregates results.
    - `resolve_remediation_endpoint(authenticated_obj, device_obj, logger, endpoint_context, payload, **kwargs)`: Executes remediation calls, injecting `non_optional` kwargs into payloads.
- **Helper Function**:
  - `base_64_encode_credentials(username, password)`: Encodes username and password into a Base64 string for Basic Authentication.
- **YAML Files**:
  - `wti_backup_endpoints.yml`: Defines API endpoints and JMESPath for backup operations.
  - `wti_remediation_endpoints.yml`: Defines API endpoints and parameters for remediation operations.
