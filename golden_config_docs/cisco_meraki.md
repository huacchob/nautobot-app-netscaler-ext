# Cisco Meraki Golden Config Dispatcher

## Overview

The **Cisco Meraki Golden Config Dispatcher** provides **backup** and **remediation** workflows for Cisco Meraki controllers using the official **Meraki Dashboard SDK (`DashboardAPI`)**.  
Instead of raw REST calls, this dispatcher dynamically resolves **SDK callables** defined in YAML endpoint files, executes them, and extracts structured data for Nautobot Golden Config.

- Transport: HTTPS (Meraki Dashboard SDK → REST API)
- Auth: API key (from Nautobot device password)
- Scope: Backup + Remediation
- Platform: `cisco_meraki` only
  > For Meraki-managed devices, see the **`meraki_managed.py`** dispatcher.

---

## How It Works

### 1) Authentication & Session

- Uses the **DashboardAPI SDK** for authentication.
- The API key is pulled from the Nautobot device’s `task.host.password`.
- The base controller URL is resolved from the device’s ConfigContext, with `api/v1` appended.

```python
controller_obj = DashboardAPI(
    api_key=task.host.password,
    base_url=controller_url,
    output_log=False,
    print_console=False,
)
```

---

### 2) Controller Setup

- The dispatcher maps required values from the Nautobot `Device` and its `ConfigContext`:
  - **organizationId** – must exist in ConfigContext
  - **networkId** – from ConfigContext
  - **serial** – from the Device model

These values are stored and injected when resolving endpoints.

---

## Backup Flow

### Processing Steps

1. Dynamically resolve the SDK callable using `_resolve_method_callable`.
2. Map required parameters (`organizationId`, `networkId`) with `resolve_params`.
3. Execute the SDK method via `_send_call`.
4. Filter the API response using `resolve_jmespath`.
5. Aggregate results:
   - If responses are lists → aggregate into one list.
   - If responses are dicts → merge into a single dict.

---

## Remediation Flow

### Processing Steps

1. Resolve the SDK callable from the endpoint definition.
2. Prepare payloads, injecting **non-optional parameters** from ConfigContext or kwargs.
3. Execute the method via `_send_remediation_call`.
4. Collect responses into an aggregated list.

Supports:

- **Single dict payloads**
- **List of dict payloads** (each entry handled individually)

### Example (Conceptual)

```python
payload = {"vlanId": "200", "name": "ProdVLAN"}
responses = dispatcher.resolve_remediation_endpoint(
    controller_obj=dashboard,
    logger=logger,
    endpoint_context=ctx["meraki_remediation"],
    payload=payload,
    organizationId="12345",
    networkId="N_67890"
)
```

---

## File & Class Reference

- **Class**: `NetmikoCiscoMeraki`
  - Inherits: `BaseControllerDriver`
  - Attributes:
    - `controller_type = "meraki"`
    - `controller_obj` – Meraki DashboardAPI instance
  - Key Methods:
    - `authenticate(logger, obj, task)` → establishes `DashboardAPI` connection
    - `controller_setup(device_obj, controller_obj, logger)` → retrieves orgId, networkId, serial from ConfigContext
    - `resolve_backup_endpoint(controller_obj, logger, endpoint_context, **kwargs)` → executes SDK calls for backup, aggregates results
    - `resolve_remediation_endpoint(controller_obj, logger, endpoint_context, payload, **kwargs)` → executes SDK calls for remediation

---

## Usage Notes

- **API Key**: The dispatcher uses the Nautobot device `password` field as the Meraki API key.
- **ConfigContext Integration**: Backup and remediation endpoints should be defined in YAML (`cisco_meraki_backup_endpoints.yml`, `cisco_meraki_remediation_endpoints.yml`).
- **ConfigContext Requirements**:
  - Must define `organization_id` and `network_id`.
  - Device `serial` is required.
- **JMESPath**: Ensure endpoint YAMLs define valid `jmespath` queries to extract required fields.
- **TLS**: The Meraki SDK handles HTTPS; always use trusted certificates in production.
- **Scope**:
  - Only for **Meraki controllers** (`cisco_meraki`).
  - For Meraki-managed devices, use **`meraki_managed.py`**.
- **Testing**: Example dispatcher tests are located in `tests/test_cisco_meraki.py`.
