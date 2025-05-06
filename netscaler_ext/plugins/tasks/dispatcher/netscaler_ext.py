"""default network_importer API-based driver for Citrix Netscaler."""

from logging import Logger
import pdb

from nautobot.dcim.models import Device
from nornir.core.exceptions import NornirSubTaskError
from nornir.core.task import MultiResult, Result, Task
from nornir_nautobot.exceptions import NornirNautobotException
from nornir_nautobot.plugins.tasks.dispatcher.default import NetmikoDefault
from nornir_netmiko.connections import CONNECTION_NAME
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
        logger.debug(f"Executing get_config for {task.host.name} on {task.host.platform}")
        task.host.platform = NETMIKO_DEVICE_TYPE

        command: str = cls.config_command

        try:
            task.run(task=netmiko_send_command, command_string="nscli", expect_string=r">")
            task.run(
                task=netmiko_send_command,
                command_string="login",
                expect_string=r"Enter userName:",
            )
            task.run(
                task=netmiko_send_command,
                command_string=task.host.username,
                expect_string=r"Enter password",
            )
            task.run(
                task=netmiko_send_command,
                command_string=task.host.password,
                expect_string=r">",  # or whatever prompt appears after successful login
            )
            
        except NornirSubTaskError as exc:
            logger.error(f"Command was not successful: {exc}")

        try:
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
        logger.info("Finished custom dispatcher")
        return Result(host=task.host, result={"config": processed_config})
