"""nornir dispatcher for cisco NXOS."""

from nornir.core.task import Result, Task
from nornir_nautobot.plugins.tasks.dispatcher.default import NetmikoDefault


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
        full_config: str = ""
        for command in cls.config_commands:
            getter_result = cls.get_command(task, logger, obj, command)
            full_config += getter_result.result.get("output").get(command)
        processed_config: str = cls._process_config(logger, full_config, remove_lines, substitute_lines, backup_file)
        return Result(host=task.host, result={"config": processed_config})
