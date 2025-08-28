# Custom Remediation for Nautobot Golden Config

## Overview

The **Custom Remediation** module extends Nautobot Golden Config by automatically generating **remediation payloads** when a device’s configuration deviates from its intended state.  
It compares the **intended configuration** with the **actual configuration** and produces a **JSON payload** that can be sent to a controller API or SDK to remediate differences.

- Input: Intended vs. Actual configurations
- Output: JSON remediation payload
- Scope: Remediation only (no backup)

---

## How It Works

### 1) Parameter Filtering

- Reads the device’s **ConfigContext** for remediation parameters.
- **Non-optional parameters** → always included.
- **Optional parameters** → included only if present in the config.
- Other keys → filtered out.

### 2) Diff Building

- Recursively compares intended vs. actual config:
  - If missing → add to diff.
  - If different → update in diff.
  - Supports dicts, lists, and primitives.

### 3) Required Field Injection

- Ensures all **non-optional parameters** from ConfigContext are re-added to the diff, even if unchanged.
- Guarantees remediation payloads contain required values.

### 4) Diff Cleanup

- Removes empty lists, dicts, or null values.
- Produces a minimal, valid JSON payload.

### 5) Payload Output

- Returns the final diff as a **pretty-printed JSON string**, ready for remediation.

---

## Example

Suppose the intended configuration specifies an NTP server, but the actual device config is missing it.

**Intended:**

```json
{
  "ntp": {
    "server": "192.0.2.1",
    "name": "ntp-server"
  }
}
```

**Actual:**

```json
{
  "ntp": {}
}
```

**Generated Remediation Payload:**

```json
{
  "ntp": {
    "server": "192.0.2.1",
    "name": "ntp-server"
  }
}
```

This payload can then be sent to the controller API for remediation.

---

## File & Class Reference

- **Helper Function**:

  - `controller_remediation(compliance_obj)`
    - Orchestrates remediation process:
      - Filters params
      - Builds diff
      - Injects required fields
      - Cleans diff
      - Returns JSON string

- **Classes**:
  - `BaseControllerRemediation` → abstract base class
  - `JsonControllerRemediation` → JSON implementation (default)

---

## Usage Notes

- **Invocation**: Typically called through `controller_remediation()` rather than instantiating classes directly.

```python
from nautobot_golden_config.models import ConfigCompliance
from custom_remediation import controller_remediation

compliance_obj = ConfigCompliance.objects.get(id="1234-abcd")
payload = controller_remediation(compliance_obj)
print(payload)
```

- **Supported Formats**: Currently only **JSON** remediation is supported.
- **ConfigContext Requirements**:
  - Must contain `<feature_name>_remediation` section.
  - Keys must be split into `non_optional` and `optional`.
- **Error Handling**:
  - Raises `ValidationError` if ConfigContext is missing, feature is not present, or unsupported config type is provided.
- **Extensibility**:
  - Add new remediation formats by subclassing `BaseControllerRemediation` and updating the factory method.

---

## Summary

- Compares **intended vs. actual config** and outputs JSON remediation payloads.
- Validates parameters using **ConfigContext**.
- Guarantees required values are included.
- Cleans output for compliance-friendly payloads.
- Extensible for future config formats (e.g., XML, YAML).
