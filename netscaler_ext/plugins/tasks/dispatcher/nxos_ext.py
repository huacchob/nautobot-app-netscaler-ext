"""nornir dispatcher for cisco NXOS."""

from pathlib import Path

import textfsm
from nornir.core.task import Result, Task
from nornir_nautobot.plugins.tasks.dispatcher.default import NetmikoDefault


def snmp_user_template(snmp_user_output: str) -> list[dict[str, str]]:
    """SNMP user textfsm template.

    Args:
        snmp_user_output (str): SNMP user command output.

    Returns:
        list[dict[str, str]]: List of parsed SNMP users.
    """
    file_path: Path = Path(__file__).parent

    template_path: Path = file_path.joinpath(
        "textfsm_templates/cisco_nxos_show_snmp_user.textfsm",
    )
    with open(file=template_path, mode="r", encoding="utf-8") as template_file:
        fsm = textfsm.TextFSM(template=template_file)
        parsed_results: list[str] = fsm.ParseText(text=snmp_user_output)

    parsed_users: list[dict[str, str]] = []
    for row in parsed_results:
        parsed_users.append(dict(zip(fsm.header, row)))
    return parsed_users


def snmp_user_command_build(parsed_snmp_user: list[dict[str, str]]) -> str:
    """Builds a list of SNMP user commands.

    Args:
        parsed_snmp_user (list[dict[str, str]]): List of parsed SNMP users.

    Returns:
        str: SNMP user commands.
    """
    snmp_user_commands: list[str] = []
    if not parsed_snmp_user:
        return ""
    snmp_user_commands.append("! show snmp user")
    for snmp_user in parsed_snmp_user:
        single_user: str = ""
        single_user += f"snmp-server user {snmp_user['USERNAME']} {snmp_user['GROUP']}"
        if snmp_user["AUTH"] and snmp_user["AUTH"] != "no":
            if "(no)" in snmp_user["AUTH"]:
                auth = snmp_user["AUTH"].replace("(no)", "")
            else:
                auth: str = snmp_user["AUTH"]
            single_user += f" auth {auth} <<<SNMP_USER_AUTH_KEY>>>"
        if snmp_user["PRIV"] and snmp_user["PRIV"] != "no":
            if "(no)" in snmp_user["PRIV"]:
                priv = snmp_user["PRIV"].replace("(no)", "")
            else:
                priv: str = snmp_user["PRIV"]
            single_user += f" priv {priv} <<<SNMP_USER_PRIV_KEY>>>"
        single_user += " localizedkey"
        snmp_user_commands.append(single_user)
        if snmp_user["ACL_FILTER"]:
            acl: str = snmp_user["ACL_FILTER"].replace("ipv4:", "")
            snmp_user_commands.append(
                f"snmp-server user {snmp_user['USERNAME']} use-ipv4 acl {acl}",
            )

    return "\n".join(snmp_user_commands)


class NetmikoCiscoNxos(NetmikoDefault):
    """Collection of Netmiko Nornir Tasks specific to Cisco NXOS devices."""

    config_commands: list[str] = ["show run all", "show snmp user"]

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
        """Get the latest configuration from the device using Netmiko.

        Args:
            task (Task): Nornir Task.
            logger (logging.Logger): Logger that may be a Nautobot Jobs or Python logger.
            obj (Device): A Nautobot Device Django ORM object instance.
            remove_lines (list): A list of regex lines to remove configurations.
            substitute_lines (list): A list of dictionaries with to remove and replace lines.

        Returns:
            Result: Nornir Result object with a dict as a result containing the running configuration
                { "config: <running configuration> }
        """
        logger.debug(f"Executing get_config for {task.host.name} on {task.host.platform}")
        logger.info(obj.get_config_context())
        full_config: str = ""
        for command in cls.config_commands:
            getter_result = cls.get_command(task, logger, obj, command)
            if "show snmp user" in command:
                snmp_user_result: list[dict[str, str]] = snmp_user_template(
                    snmp_user_output=getter_result.result.get("output").get(
                        command,
                    ),
                )
                full_config += snmp_user_command_build(
                    parsed_snmp_user=snmp_user_result,
                )
                continue
            full_config += getter_result.result.get("output").get(command)
        processed_config: str = cls._process_config(logger, full_config, remove_lines, substitute_lines, backup_file)
        return Result(host=task.host, result={"config": processed_config})
