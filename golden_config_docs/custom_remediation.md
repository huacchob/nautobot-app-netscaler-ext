# Custom Remediation for Nautobot Golden Config

## Overview

The **Custom Remediation** module is a critical component of Nautobot Golden Config, designed to automatically generate **remediation payloads** when a device’s configuration deviates from its intended state. It achieves this by comparing the **intended configuration** (the desired state) with the **actual configuration** (the current state of the device) and producing a structured **JSON payload** that can be sent to a controller API or SDK to remediate the identified differences.

- **Input**: Intended configuration (from Golden Config) vs. Actual configuration (from backup workflow).
- **Output**: JSON remediation payload.
- **Scope**: Remediation only (this module does not perform backup operations directly).

## How It Works

The custom remediation process involves several key steps to accurately identify and format configuration differences for remediation:

1. **Parameter Filtering**:
   - The module reads remediation parameters from the device’s **ConfigContext**.
   - **Non-optional parameters** are always included in the generated diff.
   - **Optional parameters** are included only if they are present in the configuration differences.
   - Any other keys not explicitly defined as parameters are filtered out.
2. **Diff Building**:
   - A recursive comparison is performed between the intended and actual configurations.
   - If a configuration element is missing in the actual config but present in the intended, it's added to the diff.
   - If an element differs between the intended and actual configs, it's updated in the diff.
   - This process supports comparing dictionaries, lists, and primitive data types.
3. **Required Field Injection**:
   - After the initial diff is built, all `non_optional` parameters specified in the `ConfigContext` are re-injected into the diff. This ensures that the remediation payload always contains all values required by the target API, even if those values haven't changed.
4. **Diff Cleanup**:
   - The generated diff is cleaned to remove any empty lists, dictionaries, or null values. This ensures that the final JSON payload is minimal, valid, and focused only on the necessary changes.
5. **Payload Output**:
   - The final, cleaned diff is returned as a **pretty-printed JSON string**, which is then ready to be sent to the appropriate controller API or SDK for applying the remediation.

## Usage Notes

- **Invocation**: The custom remediation logic is typically invoked through the `controller_remediation()` helper function, rather than directly instantiating the underlying classes.

  ```python
  from nautobot_golden_config.models import ConfigCompliance
  from netscaler_ext.plugins.tasks.remediation.controller_remediation import controller_remediation

  # Assuming compliance_obj is an instance of ConfigCompliance
  compliance_obj = ConfigCompliance.objects.get(id="<some-compliance-id>")
  payload = controller_remediation(compliance_obj)
  print(payload)
  ```

- **Supported Formats**: Currently, this module primarily supports **JSON** for generating remediation payloads.
- **ConfigContext Requirements**:
  - The device’s `ConfigContext` must contain a section named `<feature_name>_remediation` (e.g., `ntp_remediation`).
  - Within this section, parameters should be explicitly split into `non_optional` and `optional` lists.
- **Error Handling**:
  - The module raises a `ValidationError` if the `ConfigContext` is missing, the specified feature is not present, or an unsupported configuration type is provided.
- **Extensibility**: The module is designed to be extensible. New remediation formats (e.g., XML, YAML) can be added by subclassing `BaseControllerRemediation` and updating the factory method within the module.

## File & Class Reference

- **Helper Function**:
  - `controller_remediation(compliance_obj)`: Orchestrates the entire remediation process, including parameter filtering, diff building, required field injection, and diff cleanup, returning the final JSON payload.
- **Classes**:
  - `BaseControllerRemediation`: An abstract base class defining the interface for remediation logic.
  - `JsonControllerRemediation`: The concrete implementation for generating JSON remediation payloads.
- **Example ConfigContext**:
  - `remediation_meraki_context.json`: An example of a `ConfigContext` structure used for Meraki remediation.
