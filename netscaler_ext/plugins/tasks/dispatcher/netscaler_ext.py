"""default network_importer API-based driver for Citrix Netscaler."""

from logging import Logger

from nautobot.dcim.models import Device
from nornir.core.exceptions import NornirSubTaskError
from nornir.core.task import MultiResult, Result, Task
from nornir_nautobot.exceptions import NornirNautobotException
from nornir_nautobot.plugins.tasks.dispatcher.default import NetmikoDefault
from nornir_netmiko.tasks import netmiko_send_command

NETMIKO_DEVICE_TYPE = "netscaler"


class NetScalerDriver(NetmikoDefault):
    """Simply override the config_command class attribute in the subclass."""

    config_command: str = "show runningConfig"
    tcp_port: int = 22

    @classmethod
    def get_config(  # pylint: disable=R0913,R0914
        cls,
        task: Task,
        logger: Logger,
        obj: Device,
        backup_file: str,
        remove_lines: list[str],
        substitute_lines: list[str],
    ) -> None | Result:
        """Get the latest configuration from Netscaler devices.

        Args:
            task (Task): Nornir Task.
            logger (Logger): Nautobot logger.
            obj (Device): Device object.
            backup_file (str): Backup file location.
            remove_lines (list[str]): Lines to remove from the configuration.
            substitute_lines (list[str]): Lines to replace in the configuration.

        Returns:
            None | Result: Nornir Result object with a dict as a result
                containing the running configuration or None.
        """
        logger.debug(f"Executing get_config for {task.host.name} on {task.host.platform}")
        task.host.platform = NETMIKO_DEVICE_TYPE

        command: str = cls.config_command
        try:
            task.run(
                task=netmiko_send_command,
                use_timing=True,
                command_string="nscli",
            )
            task.run(
                task=netmiko_send_command,
                use_timing=True,
                command_string="login",
            )
            task.run(
                task=netmiko_send_command,
                use_timing=True,
                command_string=task.host.username,
            )
            task.run(
                task=netmiko_send_command,
                use_timing=True,
                command_string=task.host.password,
            )
            result: MultiResult = task.run(
                task=netmiko_send_command,
                use_timing=True,
                command_string=command,
            )
        except NornirSubTaskError as exc:
            exc_result: Result = exc.result
            error_msg: str = f"Failed with an unknown issue. `{exc_result.exception}`"
            logger.error(msg=error_msg, extra={"object": obj})
            raise NornirNautobotException(error_msg)

        if result[0].failed:
            return result[0]

        _running_config: str = result[0].result
        processed_config: str = cls._process_config(
            logger=logger,
            running_config=_running_config,
            remove_lines=remove_lines,
            substitute_lines=substitute_lines,
            backup_file=backup_file,
        )
        return Result(host=task.host, result={"config": processed_config})
