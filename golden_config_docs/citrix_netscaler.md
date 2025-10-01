# Citrix Netscaler Golden Config Dispatcher

## Overview

The **Citrix Netscaler Golden Config Dispatcher** provides **backup** and **remediation** workflows against Citrix Netscaler devices using the device’s HTTPS API.  
It establishes an authenticated HTTP **session**, executes YAML-defined endpoints, and extracts structured data using **JMESPath** for Nautobot Golden Config.

- Transport: HTTPS (requests `Session`)
- Auth: `X-NITRO-USER` and `X-NITRO-PASS` for credentials
- Scope: Backup

---

## How It Works

### 1) Authentication & Session

- Builds the device base URL from the Nautobot device’s primary IPv4 address: `https://<device.name>`.
- Creates a persistent `requests.Session` via `ConnectionMixin`.
- Creates headers:
  - `X-NITRO-USER: <task.host.username>`
  - `X-NITRO-PASS: <task.host.password>`
  - `Content-Type: application/json`

```python
# Conceptual flow (already implemented in the dispatcher)
device_url = f"https://{device.name}"
session = configure_session()
get_headers = {'X-NITRO-USER': 'username', 'X-NITRO-PASS': 'password', "Content-Type": "application/json"}
```

> TLS note: Calls are currently made with `verify=False`. For production, supply a trusted CA bundle and enable verification.

---

## Backup Flow

### Processing Steps

1. Build the full URL with `format_base_url_with_endpoint(base_url=device_url, endpoint=...)`.
2. Optionally append `query` parameters via `resolve_query`.
3. Send the HTTP request using the shared `session` and `get_headers`.
4. Extract fields using `resolve_jmespath`.
5. Aggregate across endpoints:
   - If endpoints return lists → aggregate as a list
   - If endpoints return dicts → merge into a single dict

---

## Remediation Flow

### Processing Steps

1. Build the endpoint URL per entry.
2. If `non_optional` parameters are defined, inject them from provided `kwargs` into the payload (or into each item in a payload list).
3. Send the HTTP request with JSON body using the shared `session` and `get_headers`.
4. Append each HTTP response to an aggregate result list.

## File & Class Reference

- Class: `'NetmikoCitrixNetscaler'`
  - Inherits: `'BaseControllerDriver'`, `'ConnectionMixin'`
  - Attributes:
    - `'device_url'` – base device URL, `https://<device.name>`
    - `'session'` – shared `requests.Session`
    - `'get_headers'` – include credentials `X-NITRO-USER` and `X-NITRO-PASS`
  - Key methods:
    - `'authenticate(logger, obj, task)'` – sets device URL, session, and headers
    - `'resolve_backup_endpoint(controller_obj, logger, endpoint_context, **kwargs)'` – executes backup endpoints and aggregates results

---

## Usage Notes

- **TLS Verification**: The dispatcher currently uses `verify=False`. For production, always configure trusted certificates and enable verification.
- **Credentials**: Authentication requires the Nautobot `username` and `password` fields for the device. These are Added to the `X-NITRO-USER` and `X-NITRO-PASS` header parameters.
- **ConfigContext Integration**: Backup and remediation endpoints should be defined in YAML under `citrix_netscaler_backup_endpoints.yml` and `citrix_netscaler_remediation_endpoints.yml`.
- **JMESPath**: Ensure your endpoint definitions provide valid `jmespath` queries; otherwise, fields may not be extracted and results could be empty.
- **Error Handling**:
  - If a required `non_optional` parameter is missing, the dispatcher logs an error.
  - If no valid responses are found, a `ValueError` is raised.
- **Payloads**: Remediation supports both single-dict and list-of-dicts payloads. Non-optional parameters are injected into each payload entry.
- **Scope**: This dispatcher is designed only for **Citrix Netscaler devices** exposing an HTTPS API. Do not reuse for other platforms.
