# Cisco APIC Golden Config Dispatcher

## Overview

The **Cisco APIC Golden Config Dispatcher** enables **backup** of ACI fabric data via the APIC REST API.  
It authenticates to APIC, manages a persistent HTTP session with a cookie, and executes the YAML-defined backup endpoints to collect structured data (filtered by JMESPath) for Nautobot Golden Config.

> Note: This dispatcher currently documents the **backup** flow. If you later add a remediation implementation, you can mirror the structure used by other dispatchers.

---

## How It Works

### 1) Authentication & Session

- Resolves the **controller base URL** from the device’s Config Context for controller type `'apic'`.
- Uses the device’s Nornir host credentials (`task.host.username`, `task.host.password`) to authenticate.
- Performs a `POST` to `'api/aaaLogin.json'` with the APIC login payload to obtain a token.
- Stores the token in a **cookie header**: `'Cookie: APIC-cookie=<token>'`.
- Persists a `requests.Session` (via the `ConnectionMixin`) for all subsequent REST calls.

```python
# High-level idea (already implemented in the dispatcher):
auth_url = format_base_url_with_endpoint(base_url=controller_url, endpoint="api/aaaLogin.json")
auth_payload = {"aaaUser": {"attributes": {"name": username, "pwd": password}}}
resp = session.post(auth_url, data=json.dumps(auth_payload), headers={"Content-Type": "text/plain"}, verify=False)
cookie = resp["imdata"][0]["aaaLogin"]["attributes"]["token"]
get_headers = {"Cookie": f"APIC-cookie={cookie}", "Content-Type": "text/plain"}
```

> Security note: TLS verification is currently disabled (`verify=False`) with a TODO to enable it. In production, provide an appropriate CA bundle or set `verify=True`.

### 2) Backup Endpoint Resolution

For each configured endpoint in your `<platform_name>_backup_endpoints.yml`:

1. Build the full API URL by joining the controller base URL with the endpoint path.
2. If a `query` block is provided, append it as URL parameters.
3. Send the request using the shared `Session` and `get_headers`.
4. Extract the required fields with **JMESPath** via `resolve_jmespath`.
5. Aggregate responses across all endpoints, returning a single **dict** or **list** depending on the endpoint outputs.

---

## Required Inputs & Context

- **Device Config Context** must provide the APIC controller URL for controller type `'apic'`.
- **Nornir Host Credentials** must contain:
  - `username` → APIC username
  - `password` → APIC password

---

## Typical Data Flow (Backup)

1. **Authenticate** → Cookie set in `get_headers`.
2. **For each endpoint**:
   - Build API URL with `format_base_url_with_endpoint`.
   - Optionally add `query` parameters with `resolve_query`.
   - Send request via `return_response_content`.
   - Extract fields with `resolve_jmespath`.
   - Aggregate result (list or dict).
3. **Return** aggregated data to the caller (used by Golden Config backup job).

---

## Usage Notes

- You **do not** need to instantiate the dispatcher directly in most cases—your orchestration will call it via the Golden Config job.
- Ensure the device’s Config Context includes the APIC controller URL for controller type `'apic'`.
- Provide valid Nornir credentials for APIC login.
