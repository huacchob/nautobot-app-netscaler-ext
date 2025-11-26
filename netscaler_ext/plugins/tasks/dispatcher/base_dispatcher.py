"""Base netmiko dispatcher for controllers."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, OrderedDict

if TYPE_CHECKING:
    from logging import Logger

    from nautobot.dcim.models import Device

from nornir.core.task import Result, Task
from nornir_nautobot.plugins.tasks.dispatcher.default import NetmikoDefault

from netscaler_ext.utils.helper import render_jinja_template


class BaseDispatcher(NetmikoDefault, ABC):
    """Base Dispatcher class."""

    @classmethod
    def _render_uri_template(
        cls,
        obj: Device,
        logger: Logger,
        template: str,
    ) -> str:
        """Render URI template.

        Args:
            obj (Device): The Device object from Nautobot.
            logger (Logger): Logger to log error messages to.
            template (str): A URI template to be rendered.

        Returns:
            str: The ``template`` rendered.
        """
        return render_jinja_template(obj=obj, logger=logger, template=template)

    @classmethod
    def _cc_feature_name_parser(cls, feature_name: str) -> str:
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
        return feat.lower().strip().replace("-", "_").replace(" ", "_")

    @classmethod
    @abstractmethod
    def authenticate(cls, logger: Logger, obj: Device, task: Task) -> Any:
        """Authenticate to controller.

        Args:
            logger (Logger): Logger object.
            obj (Device): Device object.
            task (Task): Nornir Task object.

        Returns:
            Any: Controller object or None.
        """

    @classmethod
    def controller_setup(
        cls,
        device_obj: Device,
        authenticated_obj: Any,
        logger: Logger,
    ) -> dict[str, str]:
        """Setup for controller.

        Args:
            device_obj (Device): Nautobot Device object.
            authenticated_obj (Any): The controller object, i.e DashboardAPI for
                controller or None is not SDK.
            logger (Logger): Logger object.

        Returns:
            dict[str, str]: Map for controller data.
        """
        # Overwrite if needed in child class
        return {}

    @classmethod
    @abstractmethod
    def resolve_backup_endpoint(
        cls,
        authenticated_obj: Any,
        device_obj: Device,
        logger: Logger,
        endpoint_context: list[dict[Any, Any]],
        feature_name: str,
        **kwargs: Any,
    ) -> dict[str, dict[Any, Any]]:
        """Resolve endpoint with parameters if any.

        Args:
            authenticated_obj (Any): Controller object or None.
            device_obj (Device): Nautobot Device object.
            logger (Logger): Logger object.
            endpoint_context (list[dict[Any, Any]]): controller endpoint context.
            feature_name (str): Feature name being collected.
            kwargs (Any): Keyword arguments.

        Returns:
            dict[str, dict[Any, Any]]: Dictionary of responses.
        """

    @classmethod
    def get_config(  # pylint: disable=R0913,R0914
        cls,
        task: Task,
        logger: Logger,
        obj: Device,
        backup_file: str,
        remove_lines: list[str],
        substitute_lines: list[str],
    ) -> Result | None:
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

        Raises:
            ValueError: If controller endpoints cannot be found in the config context.
        """
        cfg_cntx: OrderedDict[Any, Any] = obj.get_config_context()
        authenticated_obj: Any = cls.authenticate(
            logger=logger,
            obj=obj,
            task=task,
        )
        logger.info(
            f"Authenticated to {obj.name} platform: {obj.platform.name}",
        )
        controller_dict: dict[str, str] = cls.controller_setup(
            device_obj=obj,
            authenticated_obj=authenticated_obj,
            logger=logger,
        )
        feature_endpoints: list[str] = cfg_cntx.get("backup_endpoints", "")
        if not feature_endpoints:
            exc_msg: str = "Could not find the controller endpoints"
            logger.error(exc_msg)
            raise ValueError(exc_msg)
        _running_config: dict[str, dict[Any, Any]] = {}
        logger.info(f"Collecting feature endpoint backups for {obj.name}")
        for feature in feature_endpoints:
            endpoints: list[dict[Any, Any]] = cfg_cntx.get(feature, "")
            feature_name: str = cls._cc_feature_name_parser(
                feature_name=feature,
            )
            if not endpoints:
                logger.error(
                    f"Could not find the endpoint context for {feature} in the config context",
                )
                continue
            feature_response: dict[str, dict[Any, Any]] = cls.resolve_backup_endpoint(
                authenticated_obj=authenticated_obj,
                device_obj=obj,
                logger=logger,
                endpoint_context=endpoints,
                feature_name=feature_name,
                **controller_dict,
            )
            if not feature_response:
                logger.error(
                    f"Could not fetch {feature_name} configuration from controller using context {feature} ",
                )
                continue
            _running_config.update({feature_name: feature_response})
        logger.info(
            f"Finished collecting feature endpoint backups for {obj.name}",
        )
        processed_config: str = cls._process_config(
            logger=logger,
            running_config=json.dumps(obj=_running_config, indent=4),
            remove_lines=remove_lines,
            substitute_lines=substitute_lines,
            backup_file=backup_file,
        )
        return Result(host=task.host, result={"config": processed_config})

    @classmethod
    def resolve_remediation_endpoint(
        cls,
        authenticated_obj: Any,
        device_obj: Device,
        logger: Logger,
        endpoint_context: list[dict[Any, Any]],
        payload: dict[Any, Any] | list[dict[str, Any]],
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Resolve endpoint with parameters if any.

        Args:
            authenticated_obj (Any): Controller object, i.e. Meraki Dashboard object or None.
            device_obj (Device): Nautobot Device object.
            logger (Logger): Logger object.
            endpoint_context (list[dict[Any, Any]]): controller endpoint config context.
            payload (dict[Any, Any] | list[dict[str, Any]]): Payload to pass to the API call.
            kwargs (Any): Keyword arguments.

        Returns:
            list[dict[str, Any]]: List of API responses.
        """
        exc_msg: str = "Subclasses must implement this is merge_config is being used."
        raise NotImplementedError(exc_msg)

    @classmethod
    def merge_config(  # pylint: disable=too-many-positional-arguments
        cls,
        task: Task,
        logger,
        obj,
        config: str,
        can_diff: bool = True,
    ) -> Result:
        """Send configuration to merge on the device.

        Args:
            task (Task): Nornir Task.
            logger (logging.Logger): Logger that may be a Nautobot Jobs or Python logger.
            obj (Device): A Nautobot Device Django ORM object instance.
            config (str): The remediation payload.
            can_diff (bool, optional): Can diff the config. Defaults to True.

        Returns:
            Result: Nornir Result object with a dict as a result containing what changed and the result of the push.

        Raises:
            ValueError: If controller endpoints cannot be found in the config context.
        """
        if isinstance(config, str):
            config: dict[Any, Any] = json.loads(config)
        logger.info(
            "Config merge via controller dispatcher starting",
            extra={"object": obj},
        )
        cfg_cntx: OrderedDict[Any, Any] = obj.get_config_context()
        # The above Python code snippet is performing the following actions:
        authenticated_obj: Any = cls.authenticate(
            logger=logger,
            obj=obj,
            task=task,
        )
        controller_dict: dict[str, str] = cls.controller_setup(
            device_obj=obj,
            authenticated_obj=authenticated_obj,
            logger=logger,
        )
        aggregated_results: list[list[dict[str, Any]]] = []
        feature_endpoints: str = cfg_cntx.get("remediation_endpoints", "")
        if not feature_endpoints:
            exc_msg: str = "Could not find the controller endpoints"
            logger.error(exc_msg)
            raise ValueError(exc_msg)
        for remediation_endpoint in config:
            if f"{remediation_endpoint}_remediation" not in feature_endpoints:
                logger.error(
                    f"Could not find the remediation endpoint: {remediation_endpoint}_remediation in {feature_endpoints}",
                    extra={"object": obj},
                )
                continue
            if not cfg_cntx.get(f"{remediation_endpoint}_remediation", ""):
                logger.error(
                    f"Could not find the remediation endpoint: {remediation_endpoint}_remediation in the config context",
                    extra={"object": obj},
                )
                continue
            try:
                aggregated_results.append(
                    cls.resolve_remediation_endpoint(
                        authenticated_obj=authenticated_obj,
                        logger=logger,
                        endpoint_context=cfg_cntx[f"{remediation_endpoint}_remediation"],
                        payload=config[remediation_endpoint],
                        device_obj=obj,
                        **controller_dict,
                    ),
                )
            except NotImplementedError:
                logger.error("resolve_remediation_endpoint was not overriden.")
        if can_diff:
            logger.info(f"result: {aggregated_results}", extra={"object": obj})
            result: dict[str, Any] = {
                "changed": bool(aggregated_results),
                "result": aggregated_results,
                "failed": False,
            }
        else:
            result: dict[str, Any] = {
                "changed": bool(aggregated_results),
                "result": "Hidden to protect sensitive information",
                "failed": False,
            }

        logger.info("Config merge ended", extra={"object": obj})
        final_result: Result = Result(host=task.host, result=result)
        final_result.changed = True
        final_result.failed = False
        return final_result
