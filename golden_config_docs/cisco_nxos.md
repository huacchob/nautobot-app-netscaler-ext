# Cisco NXOS Golden Config Dispatcher

## Overview

The **Cisco NXOS Golden Config Dispatcher** extends the default **Netmiko dispatcher** to support NXOS-specific backup workflows.  
In addition to collecting the full running configuration, it parses and normalizes **SNMP user configuration** using a **TextFSM template**, ensuring that SNMP secrets are not exposed but are still represented consistently for compliance and remediation.

- Transport: SSH (Netmiko via Nornir)
- Auth: Device credentials (username/password)
- Scope: Backup only (with SNMP user normalization)

---

## How It Works

### 1) Extended `get_config`

- Inherits from `NetmikoDefault`.
- Overrides `get_config()` to:
  1. Run `show run all` (full config).
  2. Run `show snmp user` (SNMP user details).
  3. Parse SNMP output with TextFSM → structured dictionaries.
  4. Rebuild SNMP user config into normalized CLI commands with **placeholders** for secrets.
  5. Combine both configs and pass them through `_process_config()` (line removals, substitutions, file save).

---

## Backup Flow

### Processing Steps

1. Execute command list:
   - `show run all` → append raw running config.
   - `show snmp user` → parse and normalize SNMP users.
2. Parse SNMP output with TextFSM (`cisco_nxos_show_snmp_user.textfsm`).
3. Rebuild structured SNMP config lines:

   ```text
   ! show snmp user
   snmp-server user snmpUser1 network-admin auth sha <<<SNMP_USER_AUTH_KEY>>> priv aes128 <<<SNMP_USER_PRIV_KEY>>> localizedkey
   snmp-server user snmpUser1 use-ipv4 acl ACL1
   ```

4. Merge into a single configuration string.
5. Process final config through `_process_config()`.
6. Return structured configuration for Golden Config backup.

---

## Special Handling: SNMP Users

- **Parsing**:

  - SNMP users parsed into dicts:

    ```python
    {"USERNAME": "snmpUser1", "GROUP": "network-admin", "AUTH": "sha", "PRIV": "aes128", "ACL_FILTER": "ipv4:ACL1"}
    ```

- **Rebuilding**:

  - Converted back to config lines with placeholders for auth/priv keys.
  - Protects secrets while preserving reproducible format for diffs.

- **Template**:
  - Located in `textfsm_templates/cisco_nxos_show_snmp_user.textfsm`.
  - Defines how `show snmp user` output is parsed.

---

## File & Class Reference

- **Class**: `NetmikoCiscoNxos`

  - Inherits: `NetmikoDefault`
  - Attributes:
    - `config_commands = ["show run all", "show snmp user"]`
  - Methods:
    - `get_config(task, logger, obj, backup_file, remove_lines, substitute_lines)`
      - Runs commands, parses SNMP, rebuilds config, processes final output.

- **Helper Functions**:
  - `snmp_user_template(output)` → parses SNMP output with TextFSM.
  - `snmp_user_command_build(parsed)` → rebuilds SNMP user CLI commands with placeholders.

---

## Usage Notes

- **TextFSM Template**: Ensure the template exists at `textfsm_templates/cisco_nxos_show_snmp_user.textfsm`.
- **Secrets**: Placeholders (`<<<SNMP_USER_AUTH_KEY>>>`, `<<<SNMP_USER_PRIV_KEY>>>`) must be replaced with real keys at remediation time.
- **Compliance**: Normalized SNMP output ensures consistent diffs across backups and avoids sensitive data exposure.
- **Scope**: This dispatcher is for **Cisco NXOS platforms** requiring SNMP normalization. Use `NetmikoDefault` for platforms without this requirement.
