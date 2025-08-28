# WTI Golden Config Dispatcher

## Overview

The **WTI Golden Config Dispatcher** provides **backup** and **remediation** workflows against WTI devices using the device’s HTTPS API.  
It establishes an authenticated HTTP **session**, executes YAML-defined endpoints, and extracts structured data using **JMESPath** for Nautobot Golden Config.

- Transport: HTTPS (requests `Session`)
- Auth: Basic (Base64-encoded `username:password` in `Authorization` header)
- Scope: Backup + Remediation

---

## How It Works

### 1) Authentication & Session

- Builds the device base URL from the Nautobot device’s primary IPv4 address: `https://<device.primary_ip4.host>`.
- Creates a persistent `requests.Session` via `ConnectionMixin`.
- Encodes credentials to Base64 and sets headers:
  - `'Authorization': <base64-of-username:password>`
  - `'Content-Type': 'application/json'`

```python
# Conceptual flow (already implemented in the dispatcher)
device_url = f"https://{device.primary_ip4.host}"
session = configure_session()
auth_header = base_64_encode_credentials(username, password)
get_headers = {"Authorization": auth_header, "Content-Type": "application/json"}
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

### Examples (Remediation)

**Runtime call (conceptual)**

```python
payload = {"id": 3, "state": "off"}
responses = dispatcher.resolve_remediation_endpoint(
    controller_obj=None,
    logger=logger,
    endpoint_context=ctx["wti_remediation"],
    payload=payload,
    deviceId="ABC-123"   # injected into payload
)
```

---

## File & Class Reference

- Class: `'NetmikoWti'`
  - Inherits: `'BaseControllerDriver'`, `'ConnectionMixin'`
  - Attributes:
    - `'device_url'` – base device URL, `https://<primary_ip4>`
    - `'session'` – shared `requests.Session`
    - `'get_headers'`, `'post_headers'` – include Base64 `Authorization`
  - Key methods:
    - `'authenticate(logger, obj, task)'` – sets device URL, session, and headers
    - `'resolve_backup_endpoint(controller_obj, logger, endpoint_context, **kwargs)'` – executes backup endpoints and aggregates results
    - `'resolve_remediation_endpoint(controller_obj, logger, endpoint_context, payload, **kwargs)'` – executes remediation calls (single dict or list of dicts), injecting `non_optional` kwargs into payloads

---

## Usage Notes

- **TLS Verification**: The dispatcher currently uses `verify=False`. For production, always configure trusted certificates and enable verification.
- **Credentials**: Authentication requires the Nautobot `username` and `password` fields for the device. These are Base64-encoded into the `Authorization` header.
- **ConfigContext Integration**: Backup and remediation endpoints should be defined in YAML under `wti_backup_endpoints.yml` and `wti_remediation_endpoints.yml`.
- **JMESPath**: Ensure your endpoint definitions provide valid `jmespath` queries; otherwise, fields may not be extracted and results could be empty.
- **Error Handling**:
  - If a required `non_optional` parameter is missing, the dispatcher logs an error.
  - If no valid responses are found, a `ValueError` is raised.
- **Payloads**: Remediation supports both single-dict and list-of-dicts payloads. Non-optional parameters are injected into each payload entry.
- **Scope**: This dispatcher is designed only for **WTI devices** exposing an HTTPS API. Do not reuse for other platforms.
