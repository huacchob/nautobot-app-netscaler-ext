# Cisco Meraki Golden Config Dispatcher

## Overview

The **Cisco Meraki Golden Config Dispatcher** enables **backup** and **remediation** of configurations on Cisco Meraki controllers.  
Unlike other platforms that may use raw API requests, this dispatcher leverages the **Meraki Dashboard SDK ('DashboardAPI')** to interact with the controller.

The dispatcher is specific to the **'cisco_meraki' platform** and is designed to work seamlessly with Nautobot Golden Config.  
For Meraki-managed devices, see the separate dispatcher: **'meraki_managed.py'**.

---

## How It Works

### 1. Authentication

- The dispatcher authenticates to the Meraki controller using the **DashboardAPI** SDK.
- The API key is retrieved from the device’s **Nornir host password**.
- The base controller URL is resolved from the device’s **ConfigContext** and updated to include the API path ('api/v1').

```python
controller_obj = DashboardAPI(
    api_key=task.host.password,
    base_url=controller_url,
    output_log=False,
    print_console=False,
)
```

### 2. Controller Setup

- Reads configuration context from the device.
- Requires:
  - **organizationId** → must exist in ConfigContext.
  - **networkId** → provided by ConfigContext.
  - **serial** → from the Nautobot 'Device' model.

These values are mapped for use in endpoint resolution.

---

## Backup Flow

### Process

1. The dispatcher dynamically resolves the SDK callable using '\_resolve_method_callable'.
2. Parameters are mapped ('organizationId', 'networkId') via 'resolve_params'.
3. The method is executed with '\_send_call'.
4. The API response is filtered with 'resolve_jmespath'.
5. All results are aggregated (as dicts or lists) and returned.

---

## Remediation Flow

### Process

1. Dispatcher resolves the SDK callable.
2. Payloads are prepared and enriched with **non-optional parameters** from ConfigContext.
3. '\_send_remediation_call' is executed.
4. All responses are collected into a result list.

Supports:

- **Single dict payloads**.
- **List of dict payloads** (each item sent separately).

---

## Additional Information

- This dispatcher is only for **Cisco Meraki controllers** ('cisco_meraki').
- For **Meraki-managed devices**, use the 'meraki_managed.py' dispatcher.
- Example tests can be found in 'tests/test_cisco_meraki.py'.
