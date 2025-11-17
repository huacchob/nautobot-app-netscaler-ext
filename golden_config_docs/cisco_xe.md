# Cisco XE Golden Config Dispatcher

## Overview

The **Cisco XE Golden Config Dispatcher** extends the default Netmiko dispatcher to support XE-specific backup workflows. In addition to collecting the full running configuration, it parses and normalizes **SNMP user configuration** using a **TextFSM template**. This ensures that sensitive SNMP secrets are not exposed in the backup but are still represented consistently for compliance and remediation purposes.

- **Transport**: SSH (Netmiko via Nornir)
- **Authentication**: Standard device credentials (username/password)
- **Scope**: Backup only (with SNMP user normalization)

## Authentication Details

Authentication is handled by Netmiko, leveraging standard SSH username and password credentials configured for the device in Nautobot.

## Key Features/Differences

- **Extended `get_config`**: Overrides the default `get_config()` method to perform multiple CLI commands.
- **SNMP User Normalization**:
  - Executes `show snmp user` to retrieve SNMP user details.
  - Parses the output using a platform-specific TextFSM template (`cisco_xe_show_snmp_user.textfsm`).
  - Rebuilds the SNMP user configuration into normalized CLI commands, replacing sensitive authentication and privacy keys with placeholders (e.g., `<<<SNMP_USER_AUTH_KEY>>>`, `<<<SNMP_USER_PRIV_KEY>>>`).
  - This process protects sensitive data while maintaining a consistent format for configuration diffs.
- **Full Configuration Capture**: Collects the full running configuration using `show running-config`.

## Usage Notes

- **TextFSM Template**: Ensure that the `textfsm_templates/cisco_xe_show_snmp_user.textfsm` file is present and correctly defines how `show snmp user` output should be parsed.
- **Secrets Handling**: The dispatcher intentionally replaces actual SNMP user secrets with placeholders in the backup configuration. During remediation, these placeholders would need to be replaced with actual values if the configuration is to be applied.
- **Compliance**: The normalized SNMP output is crucial for maintaining consistent configuration diffs across backups and preventing the exposure of sensitive data in version control.
- **Scope**: This dispatcher is specifically designed for **Cisco XE platforms** that require special handling for SNMP user configurations. For other platforms, the generic `NetmikoDefault` dispatcher may be more appropriate.

## File & Class Reference

- **Class**: `NetmikoCiscoXe`
  - Inherits from `NetmikoDefault`.
  - `config_commands`: Defines the list of CLI commands to execute for configuration collection (e.g., `["show running-config", "show snmp user"]`).
  - Key Methods:
    - `get_config(task, logger, obj, backup_file, remove_lines, substitute_lines)`: Executes CLI commands, parses SNMP output, rebuilds SNMP configuration, and processes the final output.
- **Helper Functions**:
  - `snmp_user_template(output)`: Parses SNMP output using the TextFSM template.
  - `snmp_user_command_build(parsed)`: Rebuilds SNMP user CLI commands with placeholders.
- **TextFSM Template**:
  - `textfsm_templates/cisco_xe_show_snmp_user.textfsm`: Defines the parsing rules for `show snmp user` output.
