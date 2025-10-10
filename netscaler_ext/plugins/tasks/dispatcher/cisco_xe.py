"""nornir dispatcher for cisco XE."""

from pathlib import Path

import textfsm
from nornir.core.task import Result, Task
from nornir_nautobot.plugins.tasks.dispatcher.default import NetmikoDefault


def snmp_user_template(snmp_user_output: str) -> list[dict[str, str]]:
    """Parse IOS-XE 'show snmp user' using TextFSM template."""
    file_path: Path = Path(__file__).parent
    template_path: Path = file_path.joinpath("textfsm_templates/cisco_xe_show_snmp_user.textfsm")

    with open(template_path, mode="r", encoding="utf-8") as template_file:
        fsm = textfsm.TextFSM(template_file)
        parsed_rows: list[list[str]] = fsm.ParseText(snmp_user_output)

    # Map rows to dicts using the template header
    return [dict(zip(fsm.header, row)) for row in parsed_rows]


def snmp_user_command_build(parsed_snmp_user: list[dict[str, str]]) -> str:
    """Build IOS-XE 'snmp-server user' commands from parsed records."""
    if not parsed_snmp_user:
        return ""

    cmds: list[str] = ["! show snmp user"]
    for u in parsed_snmp_user:
        user = u["USER"]
        group = u.get("GROUP", "")
        auth = (u.get("AUTH") or "").lower()
        priv_proto = (u.get("PRIV_PROTO") or "").lower()
        priv_bits = (u.get("PRIV_BITS") or "").strip()
        access = u.get("ACCESS") or ""

        line = f"snmp-server user {user} {group} v3"

        # auth
        if auth and auth != "none":
            line += f" auth {auth} <<<SNMP_V3_AUTH_PASSWORD>>>"

        # priv
        if priv_proto and priv_proto != "none":
            priv = f"{priv_proto} {priv_bits}".strip()
            line += f" priv {priv} <<<SNMP_V3_PRIV_PASSWORD>>>"

        # access-list (optional on IOS-XE)
        if access:
            line += f" access {access}"

        cmds.append(line)

    return "\n".join(cmds)


class NetmikoCiscoXe(NetmikoDefault):
    """Collection of Netmiko Nornir Tasks specific to Cisco XE devices."""

    config_commands: list[str] = ["show run", "show snmp user"]

    @classmethod
    def get_config(  # pylint: disable=too-many-positional-arguments
        cls,
        task: Task,
        logger,
        obj,
        backup_file: str,
        remove_lines: list,
        substitute_lines: list,
    ) -> Result:
        """Get the latest configuration from XE devices.

        Args:
            task (Task): Nornir Task.
            logger (Logger): Nautobot logger.
            obj (Device): A Nautobot Device Django ORM object instance.
            backup_file (str): Backup file location.
            remove_lines (list[str]): Lines to remove from the configuration.
            substitute_lines (list[str]): Lines to replace in the configuration.

        Returns:
            Result: Nornir Result object with a dict as a result containing the
                running configuration.
        """
        logger.debug(f"Executing get_config for {task.host.name} on {task.host.platform}")
        full_config: str = ""
        for command in cls.config_commands:
            getter_result = cls.get_command(task, logger, obj, command)
            # if "show snmp user" in command:
            #     snmp_user_result: list[dict[str, str]] = snmp_user_template(
            #         snmp_user_output=getter_result.result.get("output").get(
            #             command,
            #         ),
            #     )
            #     full_config += snmp_user_command_build(
            #         parsed_snmp_user=snmp_user_result,
            #     )
            #     continue
            full_config += getter_result.result.get("output").get(command)
        processed_config: str = cls._process_config(logger, full_config, remove_lines, substitute_lines, backup_file)
        return Result(host=task.host, result={"config": processed_config})
