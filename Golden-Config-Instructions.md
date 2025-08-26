# Custom Golden Config Dispatchers
## Overview
The custom dispatchers automates backup and remediation of different platform configurations using API calls defined in YAML files.

- <platform_name>.py: Implements dispatcher logic.
- <platform_name>_backup_endpoints.yml: Defines API endpoints for backup operations (get_config).
- <platform_name>_remediation_endpoints.yml: Defines API endpoints for remediation operations (merge_config).
- test_<platform_name>.py: Contains unit tests for dispatcher functionality.

## How It Works
- API Endpoint Definitions

  - Endpoints for backup and remediation are defined in YAML files.
  - Each endpoint specifies the API method, required parameters, and fields to extract from responses.

- Dispatcher Logic

  - The dispatcher reads endpoint definitions and dynamically calls the API/SDK endpoints/callables.
  - For backup, it fetches configuration data.
  - For remediation, it applies changes using defined endpoints.

## Adding API Endpoints
1. Backup Endpoints (<platform_name>_backup_endpoints.yml)
**Purpose**: Define endpoints for retrieving configuration data.

**Structure**:
```
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

**How to Add**:

- Create a new section (e.g., snmp_backup).
- Add endpoint details: endpoint, method, parameters, and jmespath fields to extract.
  - endpoint: Either SDK callable object or API endpoint
  - method: The HTTP method
  - parameters: Any parameters the call must use
    - Just the name is added in the endpoint YAML definition
    - The values must be added to the **controller_setup** method
  - jmespath: jmespath strings used to grab only the important details about the call
- Add the new section name to the **backup_endpoints** list.

2. Remediation Endpoints (<platform_name>_remediation_endpoints.yml)
**Purpose**: Define endpoints for applying configuration changes.

**Structure**:

```
ntp_remediation:
  - endpoint: "endpoint.updateNtp"
    method: "PUT
    parameters:
      non_optional:
        - "required_parameter"
      optional:
        - "name_parameter"
        - "management_parameter"

remediation_endpoints:
  - "ntp_remediation"
```

**How to Add**:

- Create a new section (e.g., snmp_remediation).
- Specify endpoint, method, and parameters (non_optional and optional).
  - endpoint: Either SDK callable object or API endpoint
  - method: The HTTP method
  - parameters: Any parameters the call must use
    - In **non_optional**, just the name is added in the endpoint YAML definition
    - In **optional** the values must come from the remediation config from the config plan
- Add the new section name to the **remediation_endpoints** list.

## Example: Adding a New Backup Endpoint

Suppose you want to back up VLAN settings:

- Add to <platform_name>_backup_endpoints.yml:
```
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
- The dispatcher will now use this endpoint when performing backups.

## Tests
You can find the dispatcher tests in `netscaler_ext/tests/test_<platform_name>.py`

## Additional Information
Platform specific documentation:

- [Cisco Meraki](golden_config_docs/cisco_meraki.md)
