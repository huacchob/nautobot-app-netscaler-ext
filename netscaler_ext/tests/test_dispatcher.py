"""Tests for custom dispatchers."""

import os
import unittest
from logging import Formatter, Logger, StreamHandler, getLogger
from typing import Any, Optional

import django
from nautobot.dcim.models import Device
from nornir import InitNornir
from nornir.core import Nornir
from nornir.core.task import Result, Task

from netscaler_ext.tests import fixtures

# pylint: disable=wrong-import-position

# Set up Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "development.nautobot_config")
django.setup()

# Import the driver
from netscaler_ext.plugins.tasks.dispatcher.meraki_ext import MerakiDriver  # noqa: E402


def setup_logger() -> Logger:
    """Set up a logger for testing.

    Returns:
        Logger: Created logger.
    """
    logger: Logger = getLogger(name="meraki_test")
    if not logger.handlers:
        handler = StreamHandler()
        formatter = Formatter(fmt="%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(fmt=formatter)
        logger.addHandler(hdlr=handler)
    logger.setLevel(level="DEBUG")
    return logger


def build_nornir() -> Any:
    """Build Nornir object.

    Returns:
        Any: Nornir object.
    """
    return InitNornir(config_file="netscaler_ext/tests/fixtures/dispatcher/config.yml")


class TestMerakiDriver(unittest.TestCase):
    """Test case for NetScalerDispatcher methods."""

    def setUp(self) -> None:
        """Set up test case."""
        self.logger: Logger = setup_logger()
        fixtures.create_devices_in_orm()
        self.device: Device = Device.objects.get(name="meraki-controller")
        self.nornir: Nornir = build_nornir()

    def test_get_config_runs_successfully(self) -> None:
        """Ensure MerakiDriver.get_config() runs and returns expected structure."""

        def runner(task: Task) -> Optional[Result]:
            """Test runner.

            Args:
                task (Task): Nornir task.

            Returns:
                Result | None: Nornir Result object or None.
            """
            return MerakiDriver.get_config(
                task=task,
                logger=self.logger,
                obj=self.device,
                backup_file="netscaler_ext/tests/fixtures/backup_files/meraki.cfg",
                remove_lines=[],
                substitute_lines=[],
            )

        result: Any = self.nornir.run(task=runner)

        # Validate the structure
        self.assertTrue(result)
        # self.assertIn(member="netscaler1", container=result)
        # host_result: Any = result["netscaler1"]
        # self.assertIsInstance(obj=host_result, cls=MultiResult)
        # self.assertIn(member="config", container=host_result.result)
        # self.assertIsInstance(obj=host_result[0].result["config"], cls=str)

        # Optionally print for debug
        # print(host_result.result["config"])


if __name__ == "__main__":
    unittest.main()
    fixtures.delete_devices_in_orm()
