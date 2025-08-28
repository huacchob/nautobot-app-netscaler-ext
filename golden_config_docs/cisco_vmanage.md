# Cisco vManage Golden Config Dispatcher

## Overview

The **Cisco vManage Golden Config Dispatcher** integrates with Cisco SD-WAN controllers (vManage) to provide **backup** and **remediation** workflows in Nautobot Golden Config.  
It authenticates against the vManage API using a **two-step session and token exchange**, maintains a persistent HTTPS session, and executes YAML-defined endpoints for collecting and applying configuration data.

- Transport: HTTPS (requests `Session`)
- Auth: Session cookie (`JSESSIONID`) + Anti-CSRF token (`X-XSRF-TOKEN`)
- Scope: Backup + Remediation

---

## How It Works

### 1) Authentication & Session

Authentication in vManage is a two-step process:

1. **Session Login**

   - `POST` to `'j_security_check'` with username/password.
   - Returns a `JSESSIONID` cookie if successful.

2. **Token Retrieval**
   - `GET` to `'dataservice/client/token'`.
   - Returns an **anti-CSRF token**.

Both values are persisted into the dispatcher’s headers for all subsequent requests.

```python
# Conceptual flow
security_url = f"{controller_url}/j_security_check"
session = configure_session()
j_session_id = "JSESSIONID=abc123"
token = "xyz456"

get_headers = {
    "Cookie": j_session_id,
    "Content-Type": "application/json",
    "X-XSRF-TOKEN": token,
}
```

> TLS note: Calls currently use `verify=False`. For production, configure trusted certificates and enable TLS verification.

---

## Backup Flow

### Processing Steps

1. Build the API URL using `format_base_url_with_endpoint(base_url=controller_url, endpoint=...)`.
2. Append any `query` parameters with `resolve_query`.
3. Execute the request with `session` and `get_headers`.
4. Parse and filter the response using `resolve_jmespath`.
5. Aggregate results across endpoints:
   - If results are lists → aggregate as a list.
   - If results are dicts → merge into a single dict.

---

## Remediation Flow

### Processing Steps

Although not implemented in the base dispatcher, remediation follows the same controller pattern:

1. Build the endpoint URL.
2. Inject `non_optional` parameters into the payload (or each payload entry if it’s a list).
3. Execute `POST` or `PUT` with the payload and `get_headers`.
4. Collect and return responses in a list.

### Example (Conceptual)

```python
payload = {"policyId": "123", "state": "deployed"}
responses = dispatcher.resolve_remediation_endpoint(
    controller_obj=None,
    logger=logger,
    endpoint_context=ctx["vmanage_remediation"],
    payload=payload
)
```

---

## File & Class Reference

- **Class**: `'NetmikoCiscoVmanage'`
  - Inherits: `'BaseControllerDriver'`, `'ConnectionMixin'`
  - Attributes:
    - `'controller_type' = "vmanage"`
    - `'controller_url'` – Base controller URL (from config context)
    - `'session'` – persistent HTTPS session
    - `'get_headers'` – includes JSESSIONID + XSRF token
  - Key Methods:
    - `'authenticate(logger, obj, task)'` → performs login + token retrieval
    - `'resolve_backup_endpoint(controller_obj, logger, endpoint_context, **kwargs)'` → executes backup endpoints and aggregates results
    - `'resolve_remediation_endpoint(controller_obj, logger, endpoint_context, payload, **kwargs)'` → remediation (pattern-compatible, extendable)

---

## Usage Notes

- **Authentication**: Requires both a valid JSESSIONID cookie and an XSRF token. Both are injected into request headers.
- **ConfigContext Integration**: Backup and remediation endpoints should be defined in YAML (`cisco_vmanage_backup_endpoints.yml`, `cisco_vmanage_remediation_endpoints.yml`).
- **JMESPath**: Endpoint definitions must provide valid JMESPath queries to correctly extract structured fields.
- **TLS Verification**: The dispatcher currently uses `verify=False`. Always enable verification and provide trusted certificates in production.
- **Remediation**: Not implemented by default but follows the same workflow as backup, using payload-based POST/PUT calls.
- **Scope**: Designed for **Cisco vManage SD-WAN controllers** only.
