# Custom Golden Config Dispatchers

## Overview

The **Custom Golden Config Dispatchers** provide a unified pattern for integrating Nautobot Golden Config with controller APIs and SDKs.  
They define **backup** and **remediation** workflows using YAML-driven endpoint definitions, allowing consistent automation across multiple platforms.

- **Dispatcher File**: `<platform_name>.py` — Implements dispatcher logic.
- **Backup Endpoints**: `<platform_name>_backup_endpoints.yml` — Defines API endpoints for backup (`get_config`).
- **Remediation Endpoints**: `<platform_name>_remediation_endpoints.yml` — Defines API endpoints for remediation (`merge_config`).
- **Tests**: `test_<platform_name>.py` — Unit tests validating dispatcher behavior.

Scope: API-based platforms (e.g., Cisco Meraki, vManage, APIC, Citrix Netscaler, WTI). For CLI-based NXOS see [Cisco NXOS](golden_config_docs/cisco_nxos.md).

---

## Nautobot Setup

Reference this document to setup Nautobot to be compatible with the API dispatchers

[Nautobot Setup](golden_config_docs/nautobot_setup.md)

---

## How It Works

### 1) API Endpoint Definitions

- Endpoints are declared in YAML files.
- Each endpoint specifies:
  - **endpoint**: API path or SDK callable
  - **method**: HTTP method (GET/POST/PUT/DELETE)
  - **parameters**: required (`non_optional`) and optional values
  - **jmespath**: field selectors to extract relevant response data

### 2) Dispatcher Logic

- Reads endpoint definitions at runtime.
- Dynamically executes the target API call (via SDK or raw HTTP).
- Aggregates and normalizes responses:
  - Dict responses → merged into a single dict
  - List responses → concatenated into a single list

---

## Backup Flow

### Processing Steps

1. Resolve endpoint definitions from `<platform_name>_backup_endpoints.yml`.
2. Map required parameters (from ConfigContext or controller_setup).
3. Execute API call with defined method.
4. Extract response fields with **JMESPath**.
5. Aggregate results into a consistent dict or list.

---

## Remediation Flow

### Processing Steps

1. Resolve endpoint definitions from `<platform_name>_remediation_endpoints.yml`.
2. For each endpoint:
   - Resolve SDK callable or API path.
   - Inject **non_optional parameters** into payload from `kwargs`.
   - Send payload (single dict or list of dicts).
3. Collect and return all responses.

---

## Adding API Endpoints

### 1) Backup Endpoints

**Purpose**: Retrieve configuration data from the controller.

**Structure Example**:

```yaml
ntp_backup:
  - endpoint: "endpoint.ntp"
    method: "GET"
    parameters:
      - "required_parameter"
    jmespath:
      name: "name"
      server: "ip"

backup_endpoints:
  - "ntp_backup"
```

**Steps**:

- Create a new section (e.g., `snmp_backup`).
- Define endpoint, method, parameters, and JMESPath fields.
- Add section name to the `backup_endpoints` list.
- Values for parameters must be provided via `controller_setup`.

---

### 2) Remediation Endpoints

**Purpose**: Apply configuration changes.

**Structure Example**:

```yaml
ntp_remediation:
  - endpoint: "endpoint.updateNtp"
    method: "PUT"
    parameters:
      non_optional:
        - "required_parameter"
      optional:
        - "name_parameter"
        - "management_parameter"

remediation_endpoints:
  - "ntp_remediation"
```

**Steps**:

- Create a new section (e.g., `snmp_remediation`).
- Define endpoint, method, and parameters.
- **non_optional**: defined in YAML but values injected from `kwargs`.
- **optional**: pulled from the remediation config plan.
- Add section name to the `remediation_endpoints` list.

**Custom remediation documentation**

- [Custom Remediation](golden_config_docs/custom_remediation.md)

---

## Example: Adding a VLAN Backup Endpoint

```yaml
vlan_backup:
  - endpoint: "endpoint.toVlans"
    method: "GET"
    parameters:
      - "some_parameter"
    jmespath:
      vlanId: "id"
      name: "name"
      subnet: "subnet"

backup_endpoints:
  - "vlan_backup"
```

- Dispatcher will now include VLANs during backup collection.

---

## File & Class Reference

- **Dispatcher File**: `<platform_name>.py`
  - Implements platform-specific logic.
- **YAML Files**:
  - `<platform_name>_backup_endpoints.yml`
  - `<platform_name>_remediation_endpoints.yml`
- **Test File**: `test_<platform_name>.py`

---

## Usage Notes

- **Endpoint Shape**: Ensure JMESPath returns consistent dicts/lists across endpoints.
- **Non-optional Parameters**: Keep minimal; typically tied to device context (e.g., `deviceId`).
- **Bulk Remediation**: Prefer list payloads to send changes per item.
- **Error Handling**:
  - Dispatcher logs errors if parameters are missing or responses invalid.
  - Empty responses may raise exceptions depending on platform.
- **TLS**: Most dispatchers default to `verify=False`. Always enable verification and configure CA bundles in production.
- **Extensibility**: Adding new platforms involves creating a dispatcher file + endpoint YAMLs that follow this pattern.

---

## Additional Information

Platform-specific dispatcher documentation:

- [Cisco NXOS](golden_config_docs/cisco_nxos.md)
- [Cisco Meraki](golden_config_docs/cisco_meraki.md)
- [Cisco vManage](golden_config_docs/cisco_vmanage.md)
- [Cisco APIC](golden_config_docs/cisco_apic.md)
- [Citrix Netscaler](golden_config_docs/citrix_netscaler.md)
- [WTI](golden_config_docs/wti.md)
