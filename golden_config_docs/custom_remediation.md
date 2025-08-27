# Custom Remediation for Nautobot Golden Config

## Introduction

The **Custom Remediation** module extends Nautobot Golden Config by providing a way to automatically generate **remediation payloads** when a device’s configuration does not match its intended state.

This module works by comparing:

- The **intended configuration**
- The **actual configuration**

It then produces a **JSON payload** that can be sent to the device through a controller API or SDK to remediate the differences.

---

## How It Works

The remediation process follows these steps:

1. **Filter Parameters**  
   The module first checks the device’s **ConfigContext** for valid parameters.

   - **Non-optional parameters** are always required.
   - **Optional parameters** are included only if present in the config.
   - Any other keys are removed from the comparison.

2. **Build the Diff**  
   The module walks through the intended and actual configurations:

   - If a value is missing in the actual config, it is added to the diff.
   - If a value is different, it is updated in the diff.
   - Nested dictionaries and lists are handled recursively.

3. **Ensure Required Fields**  
   Any **non-optional parameters** defined in the ConfigContext are added back into the diff, even if they were unchanged, to make sure remediation requests contain all required values.

4. **Clean the Diff**  
   Empty structures (empty lists, dicts, or null values) are removed to keep the payload minimal and valid.

5. **Output Remediation JSON**  
   Finally, the cleaned diff is returned as a **pretty-printed JSON string**, ready to be used in API remediation calls.

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

This payload can then be sent to the controller API to fix the device’s configuration.

---

## Usage

You typically won’t instantiate remediation classes directly. Instead, call the provided helper function:

```python
from nautobot_golden_config.models import ConfigCompliance
from custom_remediation import controller_remediation

# Retrieve an existing compliance object
compliance_obj = ConfigCompliance.objects.get(id="1234-abcd")

# Generate the remediation payload
remediation_payload = controller_remediation(compliance_obj)

print(remediation_payload)
```

The function automatically selects the correct remediation class based on the compliance object’s configuration type.  
Currently, only **JSON** remediation is supported.

---

## Requirements

- The 'ConfigCompliance' object must contain both **intended** and **actual** configurations.
- A valid **ConfigContext** must exist for the device, containing:
  - '<feature_name>\_remediation' with parameter definitions
  - Keys split into 'non_optional' and 'optional'

If these conditions are not met, a 'ValidationError' is raised.

---

## Error Handling

The remediation process will raise errors in the following cases:

- **Missing ConfigContext** or no valid parameters defined.
- **Feature not found** in the intended or actual configuration.
- **Unsupported config type** (anything other than JSON).

---

## Extending the Module

If you need to support another config format (e.g., XML or YAML), you can extend the base class:

1. Subclass 'BaseControllerRemediation'.
2. Implement your own 'controller_remediation()' method.
3. Update the factory function ('controller_remediation()') to handle the new type.

Example:

```python
if config_type == "json":
    remediation = JsonControllerRemediation(obj)
else:
    raise ValidationError("Unsupported config type")
```

---

## Summary

- The 'custom_remediation' module generates JSON payloads to bring devices back into compliance.
- It uses the **ConfigContext** to validate parameters and ensures all required values are included.
- Output is always a clean, ready-to-use remediation payload.
- Errors are raised if input data is incomplete or unsupported.
