"""Base nornir dispatcher for controllers."""

import json
from abc import ABC, abstractmethod
from logging import Logger
from typing import Any, Optional, OrderedDict

from nautobot.dcim.models import Device
from nornir.core.task import Result, Task
from nornir_nautobot.plugins.tasks.dispatcher.default import NetmikoDefault


class BaseControllerDriver(NetmikoDefault, ABC):
    """Base Controller Dispatcher class."""

    @classmethod
    def _feature_name_parser(cls, feature_name: str) -> str:
        """Feature name parser.

        Args:
            feature_name (str): The feature name from config context.

        Returns:
            str: Parsed feature name.
        """
        if "_" in feature_name:
            feat = feature_name.rsplit(sep="_", maxsplit=1)[0]
        elif "-" in feature_name:
            feat = feature_name.rsplit(sep="-", maxsplit=1)[0]
        else:
            feat = feature_name.rsplit(sep=" ", maxsplit=1)[0]
        return feat

    @classmethod
    @abstractmethod
    def authenticate(
        cls,
        config_context: OrderedDict[Any, Any],
        logger: Logger,
        obj: Device,
    ) -> Any:
        """Authenticate to controller.

        Args:
            config_context (OrderedDict[Any, Any]): Config context.
            logger (Logger): Logger object.
            obj (Device): Device object.

        Raises:
            ValueError: Could not find the controller API URL in config context.

        Returns:
            Any: Controller object.
        """
        pass

    @classmethod
    @abstractmethod
    def controller_setup(
        cls,
        controller_obj: Any,
        logger: Logger,
    ) -> dict[str, str]:
        """Setup for controller.

        Args:
            controller_obj (Any): The controller object, i.e DashboardAPI for controller.
            logger (Logger): Logger object.

        Returns:
            dict[str, str]: Map for controller data.
        """
        pass

    @classmethod
    @abstractmethod
    def resolve_endpoint(
        cls,
        controller_obj: Any,
        logger: Logger,
        endpoint_context: list[dict[Any, Any]],
        **kwargs: Any,
    ) -> dict[str, dict[Any, Any]]:
        """Resolve endpoint with parameters if any.

        Args:
            controller_obj (Any): Controller object.
            logger (Logger): Logger object.
            endpoint_context (list[dict[Any, Any]]): controller endpoint context.
            kwargs (Any): Keyword arguments.

        Returns:
            Any: Dictionary of responses.
        """
        pass

    @classmethod
    def get_config(  # pylint: disable=R0913,R0914
        cls,
        task: Task,
        logger: Logger,
        obj: Device,
        backup_file: str,
        remove_lines: list[str],
        substitute_lines: list[str],
    ) -> Optional[Result]:
        """Get the latest configuration from controller.

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
        cfg_cntx: OrderedDict[Any, Any] = obj.get_config_context()
        controller_obj: Any = cls.authenticate(
            config_context=cfg_cntx,
            logger=logger,
            obj=obj,
        )
        controller_dict: dict[str, str] = cls.controller_setup(
            controller_obj=controller_obj,
            logger=logger,
        )
        feature_endpoints: str = cfg_cntx.get("backup_endpoints", "")
        if not feature_endpoints:
            logger.error("Could not find the controller endpoints")
            raise ValueError("Could not find controller endpoints")
        _running_config: dict[str, dict[Any, Any]] = {}
        for feature in feature_endpoints:
            endpoints: list[dict[Any, Any]] = cfg_cntx.get(feature, "")
            feature_name: str = cls._feature_name_parser(feature_name=feature)
            _running_config.update(
                {
                    feature_name: cls.resolve_endpoint(
                        controller_obj=controller_obj,
                        logger=logger,
                        endpoint_context=endpoints,
                        **controller_dict,
                    )
                }
            )
        processed_config: str = cls._process_config(
            logger=logger,
            running_config=json.dumps(obj=_running_config, indent=4),
            remove_lines=remove_lines,
            substitute_lines=substitute_lines,
            backup_file=backup_file,
        )
        return Result(host=task.host, result={"config": processed_config})
