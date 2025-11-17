# Golden Config Dispatchers Documentation

## 1. Introduction

Nautobot Golden Config Dispatchers provide a powerful and flexible mechanism to integrate Nautobot Golden Config with various network controller APIs and SDKs. Their primary purpose is to automate the **backup** and **remediation** of device configurations by defining how to interact with external systems. This documentation outlines the core concepts, setup procedures, and platform-specific details for leveraging these dispatchers effectively within your Nautobot environment.

## 2. Core Concepts

### API Endpoint Definitions

The behavior of each dispatcher is driven by YAML-based API endpoint definitions. These files specify how the dispatcher should interact with a particular controller's API or SDK for both backup and remediation tasks.

- **`endpoint`**: The specific API path (e.g., `/api/v1/config/ntpserver`) or the SDK callable (e.g., `endpoint.ntp`) to be invoked.
- **`method`**: The HTTP method to use for API calls (e.g., `GET`, `POST`, `PUT`, `DELETE`).
- **`parameters`**: Defines the arguments required by the API endpoint or SDK callable.
  - `non_optional`: Parameters that are always required and must be provided.
  - `optional`: Parameters that are optional and included only if present in the configuration.
- **`jmespath`**: A JMESPath expression used to extract and transform relevant data from the raw API response. This ensures that only the necessary information is processed and stored in a standardized format.

### Dispatcher Logic

Dispatchers are Python classes that:

1. **Read Endpoint Definitions**: They dynamically load and interpret the YAML endpoint definitions at runtime.
2. **Execute API Calls**: Based on the definitions, they execute the corresponding API calls using either raw HTTP requests (via `requests.Session`) or platform-specific SDKs.
3. **Normalize Responses**: They aggregate and normalize the responses from the external systems into a consistent format (either a merged dictionary or a concatenated list), making them suitable for Nautobot Golden Config's processing.

### Authentication & Session Management

Each dispatcher handles authentication and session management specific to its target platform. This typically involves:

- Establishing a persistent HTTP session.
- Handling authentication mechanisms like API keys, username/password, session cookies, or tokens.
- Persisting authentication details (e.g., cookies, tokens) for subsequent API calls within the session.

### Nautobot Integration

Dispatchers are designed to seamlessly integrate with Nautobot's data model and features:

- **Device Objects**: They leverage information from Nautobot `Device` objects, such as device names, primary IP addresses, and associated `ConfigContext` data.
- **ConfigContext**: `ConfigContext` is used to store platform-specific configuration details, such as controller URLs, organization IDs, network IDs, and endpoint definitions.
- **SecretsGroup**: Credentials for authenticating with external controllers are securely retrieved from Nautobot's `SecretsGroup` objects.

## 3. Nautobot Setup for Golden Config Dispatchers

To effectively utilize Golden Config Dispatchers, certain configurations are required within Nautobot.

### Platform to Framework Mapping

Configure how Nautobot Golden Config maps platforms to the appropriate dispatcher frameworks.

1. Navigate to **Admin** -> **Site administration** -> **Configuration**.
2. Scroll down to the **Golden Configuration** section.
3. You can set a `DEFAULT FRAMEWORK` for all platforms or individually configure `GET CONFIG FRAMEWORK` (for backup) and `MERGE CONFIG FRAMEWORK` (for remediation) for specific platforms. For API dispatchers, you will typically map the platform to the custom dispatcher (e.g., `cisco_meraki` to `cisco_meraki`).

### Secrets Group Creation

Securely store credentials for external controllers using Nautobot's `Secrets Group` feature.

- A `Secrets Group` must contain at least two `Secrets` with `Access Type: Generic` and `Secret Type: Password` and `Username`. An optional third `Secret` with `Secret Type: Secret` can also be added.
- Refer to the [Nautobot Secrets Documentation](https://docs.nautobot.com/projects/core/en/stable/user-guide/platform-functionality/secret/) for detailed instructions.

### Controller Platforms Specific Setup

For dispatchers interacting with controller platforms (e.g., Meraki, vManage, APIC), additional setup is required.

#### Location Type for Controllers

Ensure that the `Location Type` used to store your controllers accepts `Controller` objects.

1. Navigate to **ORGANIZATION** -> **LOCATIONS** -> **Location Types**.
2. Edit the relevant `Location Type` and add `dcim | controller` to the `Content types` field.

#### Controller Device Placeholder

It is recommended to create a dedicated "controller device placeholder" in Nautobot for system-level API calls to the controller, distinct from devices managed by the controller. This allows for collecting controller-wide information without associating it with a specific managed device.

- For example, a Meraki controller placeholder might use the `cisco_meraki` platform, while individual Meraki APs use `meraki_managed`.
- Refer to the [Nautobot Device Creation Documentation](https://docs.nautobot.com/projects/core/en/stable/user-guide/feature-guides/getting-started/creating-devices/) for creating devices.

#### External Integration

Configure `External Integrations` to define connectivity details (remote URL, secrets group) for your controllers.

1. Navigate to **EXTENSIBILITY** -> **AUTOMATION** -> **External Integrations**.
2. Create an `External Integration` linking your controller to its remote URL and the appropriate `Secrets Group`.
3. Refer to the [Nautobot External Integrations Documentation](https://docs.nautobot.com/projects/core/en/stable/user-guide/platform-functionality/externalintegration/) for more details.

#### Controller Creation

Create `Controller` objects in Nautobot, associating them with their respective `External Integrations`, platforms, and controller device placeholders.

1. Navigate to **DEVICES** -> **CONTROLLERS** -> **Controllers**.
2. When creating a controller, ensure it has the correct `External Integration`, `Platform`, and is linked to its `Controller Device Placeholder`.
3. Refer to the [Nautobot Controller Documentation](https://docs.nautobot.com/projects/core/en/stable/user-guide/feature-guides/wireless-networks-and-controllers/#controllers) for detailed instructions.

#### Updating Golden Config Settings to Disable Ping Tests

For controller placeholder devices that may not have a pingable IP address (e.g., cloud-managed controllers), it's crucial to disable Golden Config's default ping test.

1. Navigate to **GOLDEN CONFIG** -> **SETUP** -> **Golden Config Settings**.
2. Create a new `Golden Config Settings` object specifically for your controller platforms.
3. Use a `Dynamic Group` to limit these settings to only the relevant controller devices.
4. Adjust the `weight` of this setting to ensure it takes precedence for controller devices.
5. **Uncheck** the `Backup Test` box to disable the ping test for devices covered by these settings.

## 4. Backup Workflow

The backup workflow is designed to retrieve the current configuration or state from a network device or controller.

### Backup Workflow Purpose

To collect configuration data from the target system and store it within Nautobot for compliance, diffing, and historical tracking.

### Processing Steps

1. **Resolve Endpoint Definitions**: The dispatcher loads the relevant backup endpoint definitions from the `<platform_name>_backup_endpoints.yml` file.
2. **Map Parameters**: Required parameters for the API call are mapped from the Nautobot `Device`'s `ConfigContext` or other relevant attributes.
3. **Execute API Call**: The dispatcher executes the API call (HTTP request or SDK callable) as defined in the endpoint.
4. **Extract Data with JMESPath**: The raw API response is processed using the specified JMESPath expression to extract and filter only the necessary configuration data.
5. **Aggregate Results**: If multiple endpoints are defined for a feature, their results are aggregated. Dictionary responses are merged, and list responses are concatenated.
6. **Return Structured Data**: The aggregated and normalized data is returned to the Golden Config job.

### Example Backup Endpoint Definition

```yaml
# <platform_name>_backup_endpoints.yml
ntp_backup:
  - endpoint: "/api/v1/config/ntpserver"
    method: "GET"
    parameters: [] # No specific parameters for this endpoint
    jmespath: "ntpserver[*].{ntp_server: servername, preferred: preferredntpserver}"

backup_endpoints:
  - "ntp_backup"
```

## 5. Remediation Workflow

The remediation workflow is designed to apply configuration changes to a network device or controller to bring its state into compliance with the intended configuration.

### Remediation Workflow Purpose

To automatically generate and apply configuration payloads to rectify deviations between the actual and intended device configurations.

### Processing Steps

1. **Resolve Endpoint Definitions**: The dispatcher loads the relevant remediation endpoint definitions from the `<platform_name>_remediation_endpoints.yml` file.
2. **Prepare Payloads**: For each endpoint, a payload is constructed based on the desired configuration changes. `non_optional` parameters defined in the YAML are injected into this payload from the `kwargs` provided to the dispatcher.
3. **Execute API Call**: The dispatcher executes the API call (HTTP request or SDK callable) with the prepared payload.
4. **Collect Responses**: The responses from each remediation API call are collected into an aggregated list.

### Example Remediation Endpoint Definition

```yaml
# <platform_name>_remediation_endpoints.yml
ntp_remediation:
  - endpoint: "/api/v1/config/ntpserver"
    method: "PUT"
    parameters:
      non_optional:
        - "ntp_server_id" # Example: a required ID for the NTP server object
      optional:
        - "preferred"
        - "servername"
    # JMESPath is typically not used for remediation endpoints as we are sending data

remediation_endpoints:
  - "ntp_remediation"
```

### Custom Remediation

The custom remediation module (`custom_remediation.py`) plays a crucial role in generating the necessary payloads for the remediation workflow. It compares the intended configuration (from Golden Config) with the actual configuration (obtained via the backup workflow) and produces a JSON payload representing the differences. This payload is then passed to the dispatcher's `resolve_remediation_endpoint` method.

## 6. Platform-Specific Dispatchers

This section provides details on each supported platform dispatcher.

### Cisco APIC

- **Overview**: Provides backup workflows for Cisco ACI fabrics via the APIC REST API. Authenticates using username/password to obtain a cookie-based token.
- **Authentication Details**: Uses `POST` to `api/aaaLogin.json` to get an `APIC-cookie` token, which is then used in subsequent request headers.
- **Key Features/Differences**: Backup only.
- **Usage Notes**: Requires APIC controller URL in Nautobot `ConfigContext` for controller type `'apic'`. Device `username` and `password` must be valid APIC credentials.
- **File & Class Reference**:
  - Class: `NetmikoCiscoApic` (inherits `BaseAPIDispatcher`)
  - Files: `cisco_apic.py`, `cisco_apic_backup_endpoints.yml`

### Cisco Meraki

- **Overview**: Provides backup and remediation workflows for Cisco Meraki controllers using the official Meraki Dashboard SDK.
- **Authentication Details**: Uses the Meraki Dashboard SDK (`DashboardAPI`) for authentication. The API key is derived from the Nautobot device's `password` field.
- **Key Features/Differences**: Leverages an SDK instead of raw HTTP requests. Requires `organizationId` and `networkId` from `ConfigContext`.
- **Usage Notes**: The Nautobot device `password` field is used as the Meraki API key.
- **File & Class Reference**:
  - Class: `NetmikoCiscoMeraki` (inherits `BaseAPIDispatcher`)
  - Files: `cisco_meraki.py`, `cisco_meraki_backup_endpoints.yml`, `cisco_meraki_remediation_endpoints.yml`

### Cisco NXOS

- **Overview**: Extends the default Netmiko dispatcher for NXOS-specific backup workflows. It collects the full running configuration and normalizes SNMP user configuration using TextFSM templates.
- **Authentication Details**: Standard Netmiko authentication via SSH (username/password).
- **Key Features/Differences**: Special handling for SNMP users, parsing them with TextFSM and rebuilding them with placeholders for secrets to ensure consistent diffs.
- **Usage Notes**: Requires `cisco_nxos_show_snmp_user.textfsm` template.
- **File & Class Reference**:
  - Class: `NetmikoCiscoNxos` (inherits `NetmikoDefault`)
  - Files: `cisco_nxos.py`, `textfsm_templates/cisco_nxos_show_snmp_user.textfsm`

### Cisco IOS

- **Overview**: Extends the default Netmiko dispatcher to support IOS-specific backup workflows. It collects the full running configuration and normalizes SNMP user configuration using TextFSM templates.
- **Authentication Details**: Standard Netmiko authentication via SSH (username/password).
- **Key Features/Differences**: Special handling for SNMP users, parsing them with TextFSM and rebuilding them with placeholders for secrets to ensure consistent diffs.
- **Usage Notes**: Requires `cisco_ios_show_snmp_user.textfsm` template.
- **File & Class Reference**:
  - Class: `NetmikoCiscoIos` (inherits `NetmikoDefault`)
  - Files: `cisco_ios.py`, `textfsm_templates/cisco_ios_show_snmp_user.textfsm`

### Cisco XE

- **Overview**: Extends the default Netmiko dispatcher to support XE-specific backup workflows. It collects the full running configuration and normalizes SNMP user configuration using TextFSM templates.
- **Authentication Details**: Standard Netmiko authentication via SSH (username/password).
- **Key Features/Differences**: Special handling for SNMP users, parsing them with TextFSM and rebuilding them with placeholders for secrets to ensure consistent diffs.
- **Usage Notes**: Requires `cisco_xe_show_snmp_user.textfsm` template.
- **File & Class Reference**:
  - Class: `NetmikoCiscoXe` (inherits `NetmikoDefault`)
  - Files: `cisco_xe.py`, `textfsm_templates/cisco_xe_show_snmp_user.textfsm`

### Cisco vManage

- **Overview**: Integrates with Cisco SD-WAN controllers (vManage) for backup and remediation. Authenticates via a two-step session and token exchange.
- **Authentication Details**: Two-step process: 1) `POST` to `j_security_check` for `JSESSIONID` cookie, 2) `GET` to `dataservice/client/token` for `X-XSRF-TOKEN`. Both are used in subsequent requests.
- **Key Features/Differences**: Complex authentication mechanism involving both a session cookie and an anti-CSRF token.
- **Usage Notes**: Requires vManage controller URL in Nautobot `ConfigContext` for controller type `'vmanage'`.
- **File & Class Reference**:
  - Class: `NetmikoCiscoVmanage` (inherits `BaseAPIDispatcher`)
  - Files: `cisco_vmanage.py`, `cisco_vmanage_backup_endpoints.yml`, `cisco_vmanage_remediation_endpoints.yml`

### Citrix Netscaler

- **Overview**: Provides backup and remediation workflows for Citrix Netscaler devices using their HTTPS API.
- **Authentication Details**: Uses `X-NITRO-USER` and `X-NITRO-PASS` headers for credentials.
- **Key Features/Differences**: Uses a specific SNIP hostname format for URL construction.
- **Usage Notes**: Authentication requires Nautobot `username` and `password` fields for the device.
- **File & Class Reference**:
  - Class: `NetmikoCitrixNetscaler` (inherits `BaseAPIDispatcher`)
  - Files: `citrix_netscaler.py`, `citrix_netscaler_backup_endpoints.yml`, `citrix_netscaler_remediation_endpoints.yml`

### WTI

- **Overview**: Provides backup and remediation workflows for WTI devices using their HTTPS API.
- **Authentication Details**: Uses Basic Authentication (Base64-encoded `username:password`) in the `Authorization` header.
- **Key Features/Differences**: Basic authentication.
- **Usage Notes**: Authentication requires Nautobot `username` and `password` fields for the device.
- **File & Class Reference**:
  - Class: `NetmikoWti` (inherits `BaseAPIDispatcher`)
  - Files: `wti.py`, `wti_backup_endpoints.yml`, `wti_remediation_endpoints.yml`

## 7. General Usage Notes

- **Endpoint Shape**: Ensure that JMESPath expressions consistently return either dictionaries or lists across all endpoints for a given feature to avoid `TypeError` during aggregation.
- **Non-optional Parameters**: Keep the number of `non_optional` parameters in your YAML endpoint definitions minimal. These are typically tied to device-specific context (e.g., `deviceId`, `organizationId`).
- **Bulk Remediation**: For remediation tasks involving multiple items (e.g., updating several VLANs), prefer using list payloads where each entry in the list represents a single item to be remediated.
- **Error Handling**: Dispatchers log errors if required parameters are missing, API calls fail, or JMESPath expressions do not yield valid results. Monitor Nautobot job logs for these messages.
- **TLS Verification**: For production environments, always enable TLS verification (`verify=True`) and configure trusted CA bundles to ensure secure communication with external controllers. The current examples might use `verify=False` for development convenience.
- **Extensibility**: Adding support for new platforms involves creating a new dispatcher Python file and corresponding YAML endpoint definition files that adhere to the patterns outlined in this documentation.

---
