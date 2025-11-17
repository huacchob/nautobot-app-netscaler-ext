# Cisco vManage Golden Config Dispatcher

## Overview

The **Cisco vManage Golden Config Dispatcher** integrates with Cisco SD-WAN controllers (vManage) to provide **backup** and **remediation** workflows within Nautobot Golden Config. It authenticates against the vManage API using a **two-step session and token exchange**, maintains a persistent HTTPS session, and executes YAML-defined endpoints for collecting and applying configuration data.

- **Transport**: HTTPS (using `requests.Session`)
- **Authentication**: Session cookie (`JSESSIONID`) + Anti-CSRF token (`X-XSRF-TOKEN`)
- **Scope**: Backup only

## Authentication Details

Authentication with Cisco vManage is a two-step process to establish a secure and authorized session:

1. **Session Login (`j_security_check`)**:
   - A `POST` request is sent to the `j_security_check` endpoint with the user's `username` and `password`.
   - If successful, the response includes a `JSESSIONID` cookie, which is essential for maintaining the session.
2. **Anti-CSRF Token Retrieval**:
   - A `GET` request is made to the `dataservice/client/token` endpoint.
   - This request retrieves an **anti-CSRF token** (`X-XSRF-TOKEN`), which is required for subsequent API calls to prevent Cross-Site Request Forgery attacks.

Both the `JSESSIONID` cookie and the `X-XSRF-TOKEN` are then persisted in the dispatcher’s headers for all subsequent API requests, ensuring proper authorization and session management.

## Key Features/Differences

- **Two-Step Authentication**: Handles vManage's specific authentication flow involving both a session cookie and an anti-CSRF token.
- **Persistent Session**: Utilizes `requests.Session` to maintain an authenticated session across multiple API calls.

## Usage Notes

- **Controller URL**: The vManage controller URL must be defined in the Nautobot `ConfigContext` for the controller type `'vmanage'`.
- **Credentials**: The Nautobot device’s `username` and `password` fields must contain valid vManage login credentials.
- **TLS Verification**: For production environments, it is crucial to enable TLS verification (`verify=True`) and provide trusted certificates. The current implementation might use `verify=False` for development convenience.
- **JMESPath**: Endpoint definitions must provide valid JMESPath queries to correctly extract structured fields from API responses.

## File & Class Reference

- **Class**: `NetmikoCiscoVmanage`
  - Inherits from `BaseAPIDispatcher` and `ConnectionMixin`.
  - `controller_type = "vmanage"`
  - `url`: Stores the base vManage controller URL (resolved from `ConfigContext`).
  - `session`: Manages the persistent `requests.Session`.
  - `get_headers`: Includes the `JSESSIONID` cookie and `X-XSRF-TOKEN` for authenticated calls.
  - Key Methods:
    - `authenticate(logger, obj, task)`: Performs the two-step login and token retrieval process.
    - `resolve_backup_endpoint(authenticated_obj, device_obj, logger, endpoint_context, feature_name, **kwargs)`: Executes backup endpoints and aggregates results.
    - `resolve_remediation_endpoint(authenticated_obj, device_obj, logger, endpoint_context, payload, **kwargs)`: Handles remediation by building endpoint URLs, injecting parameters into payloads, and executing API calls.
- **YAML Files**:
  - `cisco_vmanage_backup_endpoints.yml`: Defines API endpoints and JMESPath for backup operations.
  - `cisco_vmanage_remediation_endpoints.yml`: Defines API endpoints and parameters for remediation operations.
