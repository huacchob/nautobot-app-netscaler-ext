import os
import unittest
from logging import Formatter, Logger, StreamHandler, getLogger
from typing import Any

import django
from nautobot.dcim.models import Device
from nornir import InitNornir
from nornir.core import Nornir
from nornir.core.task import MultiResult, Result, Task

from netscaler_ext.tests import fixtures

fixtures.create_devices_in_orm()

# Set up Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "development.nautobot_config")
django.setup()

# Import the driver
from netscaler_ext.plugins.tasks.dispatcher.netscaler_ext import NetScalerDriver


def setup_logger() -> Logger:
    logger: Logger = getLogger(name="netscaler_test")
    if not logger.handlers:
        handler = StreamHandler()
        formatter = Formatter(fmt="%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(fmt=formatter)
        logger.addHandler(hdlr=handler)
    logger.setLevel(level="DEBUG")
    return logger


def build_nornir() -> Any:
    return InitNornir(config_file="netscaler_ext/tests/fixtures/dispatcher/config.yml")


class TestNetScalerDriver(unittest.TestCase):
    """Test case for NetScalerDispatcher methods."""

    def setUp(self) -> None:
        self.logger: Logger = setup_logger()
        self.device: Device = Device.objects.get(name="netscaler1")
        self.nornir: Nornir = build_nornir()

    def test_get_config_runs_successfully(self) -> None:
        """Ensure NetScalerDriver.get_config() runs and returns expected structure."""

        def runner(task: Task) -> Result | None:
            return NetScalerDriver.get_config(
                task=task,
                logger=self.logger,
                obj=self.device,
                backup_file="netscaler_ext/tests/fixtures/backup_files/netscaler.cfg",
                remove_lines=[],
                substitute_lines=[],
            )

        result: Any = self.nornir.run(task=runner)

        # Validate the structure
        self.assertIn(member="netscaler1", container=result)
        host_result: Any = result["netscaler1"]
        self.assertIsInstance(obj=host_result, cls=MultiResult)
        self.assertIn(member="config", container=host_result.result)
        self.assertIsInstance(obj=host_result[0].result["config"], cls=str)

        # Optionally print for debug
        # print(host_result.result["config"])
        raise ValueError


if __name__ == "__main__":
    unittest.main()
