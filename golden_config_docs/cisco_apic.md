# Cisco APIC Golden Config Dispatcher

## Overview

The **Cisco APIC Golden Config Dispatcher** provides **backup** workflows for Cisco ACI fabrics via the **APIC REST API**.  
It authenticates with the APIC controller, maintains a persistent HTTP session using a cookie-based token, and executes YAML-defined endpoints to retrieve structured data filtered through **JMESPath** for Nautobot Golden Config.

- Transport: HTTPS (requests `Session`)
- Auth: Username + Password → APIC login token (`APIC-cookie`)
- Scope: Backup only

---

## How It Works

### 1) Authentication & Session

- Resolves the APIC controller base URL from the Nautobot **ConfigContext** for controller type `'apic'`.
- Uses the device’s Nornir host credentials (`username`, `password`) to authenticate.
- Issues a `POST` to `api/aaaLogin.json` with APIC login payload.
- Extracts the **login token** from the response and sets it in request headers:

```python
auth_url = format_base_url_with_endpoint(base_url=controller_url, endpoint="api/aaaLogin.json")
auth_payload = {"aaaUser": {"attributes": {"name": username, "pwd": password}}}
resp = session.post(auth_url, data=json.dumps(auth_payload), headers={"Content-Type": "text/plain"}, verify=False)
cookie = resp["imdata"][0]["aaaLogin"]["attributes"]["token"]
get_headers = {"Cookie": f"APIC-cookie={cookie}", "Content-Type": "text/plain"}
```

- A persistent `requests.Session` (via `ConnectionMixin`) is reused for all further API calls.

> **TLS Note**: Calls are currently made with `verify=False`. For production, provide trusted CA bundles and enable verification.

---

### 2) Backup Flow

#### Processing Steps

1. For each configured endpoint in `<platform_name>_backup_endpoints.yml`:
   - Build full API URL with `format_base_url_with_endpoint`.
   - If `query` params exist, append them with `resolve_query`.
   - Send the request using the shared `session` and `get_headers`.
2. Parse the API response with **resolve_jmespath** to extract only required fields.
3. Aggregate results:
   - If endpoints return lists → extend into one list.
   - If endpoints return dicts → merge into a single dict.
4. Return aggregated structured data to the Golden Config job.

---

## File & Class Reference

- **Class**: `NetmikoCiscoApic`
  - Inherits: `BaseControllerDriver`, `ConnectionMixin`
  - Attributes:
    - `controller_type = "apic"`
    - `controller_url` – base APIC controller URL (from ConfigContext)
    - `session` – shared `requests.Session`
    - `get_headers` – includes APIC-cookie for authenticated calls
  - Key Methods:
    - `authenticate(logger, obj, task)` → logs into APIC and stores session cookie
    - `resolve_backup_endpoint(controller_obj, logger, endpoint_context, **kwargs)` → executes backup endpoints, parses JMESPath, and aggregates results

---

## Usage Notes

- **Device ConfigContext**: Must define the APIC controller URL for controller type `'apic'`.
- **ConfigContext Integration**: Backup and remediation endpoints should be defined in YAML (`cisco_apic_backup_endpoints.yml`, `cisco_apic_remediation_endpoints.yml`).
- **Credentials**: The Nautobot device’s `username` and `password` must match valid APIC login credentials.
- **TLS**: Update the dispatcher to use `verify=True` and trusted certificates in production.
- **Error Handling**:
  - If no cookie is returned from APIC, a `ValueError` is raised.
  - If `jmespath` filters do not match the API response, the dispatcher logs an error and continues.
- **Scope**: Backup endpoints only. Remediation is not implemented for APIC in this dispatcher.
