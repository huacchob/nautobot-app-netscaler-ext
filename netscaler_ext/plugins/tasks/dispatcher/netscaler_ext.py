"""default network_importer API-based driver for Citrix Netscaler."""

from logging import Logger

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
        """
        Retrieve and process the configuration from a network device via CLI.

        This method performs the following:
          - Sets up the task's device platform for CLI backup.
          - Executes a CLI command using Netmiko (with timing enabled) to
            obtain the device's running configuration.
          - Processes the CLI backup by removing and substituting specified
            lines and saves the result to a backup file.
          - Validates and utilizes the RouterOS API to retrieve configuration
            data if the dependency is available.
          - Processes the API configuration similarly to the CLI configuration.
          - Returns a Result object containing the processed API configuration.

        Args:
          cls:
              The context being passed in.
          task (Task):
              The task instance representing the network device operation.
          logger:
              The logger object used for recording debug and error messages.
          obj:
              (Device): A Nautobot Device Django ORM object instance.
          backup_file (str):
              The file path where the backup configuration will be stored.
          remove_lines (list[str]):
              A list of string patterns or specific lines to remove from the
                configuration output.
          substitute_lines (list[str]):
              A list of string patterns or mappings to substitute within the
                configuration output.

        Returns:
          Result:
              A result object containing the processed API configuration. The
                object includes the host details
              and a dictionary with the key "config" mapping to the processed
                configuration string.

        Raises:
          NornirNautobotException:
              If the CLI command execution fails, if the RouterOS API
                dependency is unavailable,
              or if any error occurs during API configuration retrieval or
                processing.

        Notes:
          - The function assumes that `cls.config_command` is defined.
          - The CLI configuration is handled with a delay factor to ensure
            complete retrieval.
          - The SSL context is created and configured to support plaintext
            login using specific cipher settings.
          - The method processes the configuration data by invoking
          `cls._process_config`, applying removals and subs as specified.
        """
        logger.debug(f"Executing get_config for {task.host.name} on {task.host.platform}")
        task.host.platform = NETMIKO_DEVICE_TYPE
        task.host.open_connection(
            connection=CONNECTION_NAME,
            configuration=task.nornir.config,
            extras={"banner_timeout": 30},
        )

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
        except Exception:
            print("Falied")

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

    # @staticmethod
    # def merge_config(
    #     task: Task,
    #     logger: Logger,
    #     obj: Device,
    #     config: str,
    # ) -> Result:
    #     """Send configuration to merge on the device.

    #     Args:
    #         task (Task): Nornir Task.
    #         logger (NornirLogger): Custom NornirLogger object to reflect job_results (via Nautobot Jobs) and Python logger.
    #         obj (Device): A Nautobot Device Django ORM object instance.
    #         config (str): The config set.

    #     Raises:
    #         NornirNautobotException: Authentication error.
    #         NornirNautobotException: Timeout error.
    #         NornirNautobotException: Other exception.

    #     Returns:
    #         Result: Nornir Result object with a dict as a result containing what changed and the result of the push.
    #     """
    #     # Adjust platform type to switch to CLI config push
    #     NETMIKO_FAIL_MSG: list[str] = ["bad", "failed", "failure"]  # pylint: disable=C0103
    #     task.host.platform = NETMIKO_DEVICE_TYPE
    #     logger.info(msg="Config merge starting", extra={"object": obj})

    #     try:
    #         # Push API configuration
    #         config_list: list[str] = config.splitlines()
    #         push_result_api: MultiResult = task.run(
    #             task=netmiko_send_config,
    #             config_commands=config_list,
    #         )

    #         # Check if there's any CLI configuration to push
    #         cli_configuration: str = obj.cf.get("cli_configuration", "")
    #         if cli_configuration:
    #             cli_config_list: list[str] = cli_configuration.splitlines()

    #             # Send command
    #             push_result_cli: MultiResult = task.run(
    #                 task=netmiko_send_config,
    #                 config_commands=cli_config_list,
    #             )
    #             push_results: list[Result] = [push_result_api[0], push_result_cli[0]]
    #         else:
    #             push_results: list[Result] = [push_result_api[0]]

    #     except NornirSubTaskError as exc:
    #         exc_result: Result = exc.result
    #         logger.error(
    #             msg=f"Failed with error: `{exc_result.exception}`",
    #             extra={"object": obj},
    #         )
    #         raise NornirNautobotException()

    #     failed: bool = any(any(msg in result.result.lower() for msg in NETMIKO_FAIL_MSG) for result in push_results)
    #     if failed:
    #         logger.warning(
    #             msg="Config merged with errors, please check full info log below.",
    #             extra={"object": obj},
    #         )
    #         for result in push_results:
    #             logger.error(
    #                 msg=f"result: {result.result}",
    #                 extra={"object": obj},
    #             )
    #             result.failed = True
    #     else:
    #         logger.info(
    #             msg="Config merged successfully.",
    #             extra={"object": obj},
    #         )
    #         for result in push_results:
    #             logger.info(
    #                 msg=f"result: {result.result}",
    #                 extra={"object": obj},
    #             )
    #             result.failed = False

    #     changed: bool = any(result.changed for result in push_results)

    #     return Result(
    #         host=task.host,
    #         result={
    #             "changed": changed,
    #             "result": "\n".join(result.result for result in push_results),
    #             "failed": failed,
    #         },
    #     )
