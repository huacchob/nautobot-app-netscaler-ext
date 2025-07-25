"""Controller remediation."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, OrderedDict

import xmltodict
from django.core.exceptions import ValidationError

if TYPE_CHECKING:
    from nautobot_golden_config.models import ConfigCompliance

# pylint: disable=too-many-arguments, too-many-positional-arguments


@dataclass(frozen=True)
class DictKey:
    """Dict key dataclass.

    Attrs:
        key (Any): The key.
    """

    key: Any


class BaseControllerRemediation(ABC):  # pylint: disable=too-few-public-methods
    """Base remediation class for controllers using JSON config."""

    def __init__(
        self,
        compliance_obj: ConfigCompliance,
    ) -> None:
        """Controller remediation.

        Args:
            compliance_obj (ConfigCompliance): Golden Config Compliance object.
        """
        self.compliance_obj: ConfigCompliance = compliance_obj
        self.feature_name: str = compliance_obj.rule.feature.name.lower()
        self.intended_config: dict[str, Any] = compliance_obj.intended
        self.backup_config: dict[str, Any] = compliance_obj.actual
        self.required_parameters: list[str] = []

    @abstractmethod
    def controller_remediation(self) -> str:
        """Controller remediation.

        Raises:
            ValidationError: Intended or Actual does not have the feature name as the top level key.

        Returns:
            str: Remediation config.
        """
        pass


class JsonControllerRemediation(BaseControllerRemediation):  # pylint: disable=too-few-public-methods
    """Remediation class for controllers."""

    def _filter_allowed_params(
        self,
        feature_name: str,
        config: dict[str, Any],
        config_context: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Filter allowed parameters and remove unwanted parameters.

        Args:
            feature_name (str): Compliance feature name.
            config (dict[str, Any]): Intended or actual config.
            config_context (ConfigContext): Device config context.

        Returns:
            dict[str, Any]: Filtered config.
        """
        if not config_context:
            return {}
        all_optional_arguments: list[str] = []
        for endpoint in config_context:
            if not endpoint.get("parameters", {}).get("optional"):
                return {}
            all_optional_arguments.extend(endpoint["parameters"]["optional"])
            self.required_parameters.extend(endpoint["parameters"]["non_optional"])

        if isinstance(config[feature_name], dict):
            valid_payload_config: dict[str, Any] = {feature_name: {}}
            for key, value in config[feature_name].items():
                if key in all_optional_arguments or key in self.required_parameters:
                    valid_payload_config[feature_name][key] = value
            return valid_payload_config

        if isinstance(config[feature_name], list):
            valid_payload_config: dict[str, Any] = {feature_name: []}
            for item in config[feature_name]:
                params_dict = {}
                for key, value in item.items():
                    if key in all_optional_arguments or key in self.required_parameters:
                        params_dict[key] = value
                if params_dict:
                    valid_payload_config[feature_name].append(params_dict)
            return valid_payload_config
        return {}

    def _process_diff(  # pylint: disable=too-many-branches
        self,
        diff: dict[Any, Any],
        path: tuple[str, ...],
        value: str,
    ) -> None:
        """Process the diff.

        Args:
            diff (dict[Any, Any]): Diff dictionary.
            path (tuple[str, ...]): Path of dictionary keys.
            value (str): The key's value.
        """
        current = diff

        for i, key in enumerate(path):
            is_last = i == len(path) - 1
            next_key = path[i + 1] if not is_last else None

            if isinstance(key, DictKey):
                dict_key: Any = key.key
                if is_last:
                    current[dict_key] = value
                else:
                    if dict_key not in current:
                        current[dict_key] = [] if isinstance(next_key, int) else {}
                    current = current[dict_key]
            elif isinstance(key, (str, float)):
                if is_last:
                    current[key] = value
                else:
                    if key not in current:
                        current[key] = [] if isinstance(next_key, int) else {}
                    current = current[key]

            elif isinstance(key, int):
                # current must be a list
                if not isinstance(current, list):
                    raise TypeError(
                        f"Expected list at index {i}, got {type(current)}",
                    )
                while len(current) <= key:
                    current.append({})
                if is_last:
                    current[key] = value
                else:
                    if not isinstance(current[key], (dict, list)):
                        current[key] = [] if isinstance(next_key, int) else {}
                    current = current[key]

            else:
                raise ValueError(f"Unsupported key type: {key}")

    def _dict_config(
        self,
        intended: dict[Any, Any],
        actual: dict[Any, Any],
        diff: dict[Any, Any],
        path: tuple[Any],
        stack: deque[Tuple[Tuple[str, ...], Any, Any]],
    ) -> None:
        """Dictionary config.

        Args:
            intended (dict[Any, Any]): Intended config.
            actual (dict[Any, Any]): Actual config.
            diff (dict[Any, Any]): Diff dictionary.
            path (tuple[Any]): Path of keys.
            stack (deque[Tuple[Tuple[str, ...], Any, Any]]): Stack of tuples.
        """
        for key, value in intended.items():
            if isinstance(value, dict):
                stack.append(
                    (
                        path + (DictKey(key=key),),
                        actual[key],
                        intended[key],
                    )
                )
                self._dict_config(
                    intended=value,
                    actual=actual[key],
                    diff=diff,
                    path=path + (DictKey(key=key),),
                    stack=stack,
                )
            elif isinstance(value, list):
                stack.append(
                    (
                        path + (DictKey(key=key),),
                        actual[key],
                        intended[key],
                    )
                )
                self._list_config(
                    intended=value,
                    actual=actual[key],
                    diff=diff,
                    path=path + (DictKey(key=key),),
                    stack=stack,
                )
            elif isinstance(value, (str, int, float)):
                if key not in actual:
                    self._process_diff(
                        diff=diff,
                        path=path + (DictKey(key=key),),
                        value=intended[key],
                    )
                else:
                    self._str_int_float_config(
                        intended=intended[key],
                        actual=actual[key],
                        diff=diff,
                        path=path + (DictKey(key=key),),
                    )

    def _list_config(
        self,
        intended: list[Any],
        actual: list[Any],
        diff: dict[Any, Any],
        path: tuple[Any],
        stack: deque[Tuple[Tuple[str, ...], Any, Any]],
    ) -> None:
        """List config.

        Args:
            intended (list[Any]): Intended config.
            actual (list[Any]): Actual config.
            required_params (list[Any]): Required parameters.
            diff (dict[Any, Any]): Diff dictionary.
            path (tuple[Any]): Path of keys.
            stack (deque[Tuple[Tuple[str, ...], Any, Any]]): Stack of tuples.
        """
        for index, intended_item in enumerate(intended):
            if index >= len(actual):
                self._process_diff(
                    diff=diff,
                    path=path + (index,),
                    value=intended_item,
                )
                continue
            actual_item = actual[index]

            if isinstance(intended_item, dict):
                stack.append((path + (index,), actual_item, intended[index]))
                self._dict_config(
                    intended=intended_item,
                    actual=actual_item,
                    diff=diff,
                    path=path + (index,),
                    stack=stack,
                )
            elif isinstance(intended_item, list):
                stack.append((path + (index,), actual_item, intended[index]))
                self._list_config(
                    intended=intended_item,
                    actual=actual_item,
                    diff=diff,
                    path=path + (index,),
                    stack=stack,
                )
            elif isinstance(intended_item, (str, int, float)):
                self._str_int_float_config(
                    intended=intended_item,
                    actual=actual_item,
                    diff=diff,
                    path=path + (index,),
                )
            else:
                self._str_int_float_config(
                    intended=intended_item,
                    actual=actual_item,
                    diff=diff,
                    path=path + (index,),
                )

    def _str_int_float_config(
        self,
        intended: str,
        actual: str,
        diff: dict[Any, Any],
        path: tuple[Any],
    ) -> None:
        """Str config.

        Args:
            intended (str): Intended config.
            actual (str): Actual config.
            diff (dict[Any, Any]): Diff dictionary.
            path (tuple[Any]): Path of keys.
        """
        if actual != intended:
            self._process_diff(diff=diff, path=path, value=intended)

    def _inject_required_fields(
        self,
        diff: dict[Any, Any],
        intended: dict[str, Any],
        path: tuple[Any],
    ) -> dict[Any, Any]:
        """Ensure required parameters are added to modified sections of the diff.

        Args:
            diff (dict[Any, Any]): Diff dictionary.
            intended (dict[str, Any]): Full intended config.
            path (tuple[Any]): Path of keys.
        """
        if isinstance(diff, dict) and isinstance(intended, dict):
            if diff:
                for param in self.required_parameters:
                    if param in intended:
                        diff[param] = intended[param]

            for key in diff:
                if key in intended:
                    self._inject_required_fields(
                        diff=diff[key],
                        intended=intended[key],
                        path=path + (key,),
                    )

        elif isinstance(diff, list) and isinstance(intended, list):
            for idx, (d_item, i_item) in enumerate(zip(diff, intended)):
                self._inject_required_fields(
                    diff=d_item,
                    intended=i_item,
                    path=path + (idx,),
                )

        return diff

    def _clean_diff(self, diff: dict[Any, Any]) -> dict[Any, Any]:
        """Recursively remove empty dicts/lists in diff.

        Args:
            diff (dict[Any, Any]): Diff dictionary.

        Returns:
            dict[Any, Any]: Cleaned diff dictionary.
        """
        if isinstance(diff, dict):
            cleaned = {}
            for k, v in diff.items():
                cleaned_value = self._clean_diff(diff=v)
                if cleaned_value not in ({}, [], None):
                    cleaned[k] = cleaned_value
            return cleaned

        if isinstance(diff, list):
            cleaned = [self._clean_diff(item) for item in diff]
            cleaned = [item for item in cleaned if item not in ({}, [], None)]
            return cleaned if cleaned else []

        return diff

    def controller_remediation(self) -> str:
        """Controller remediation.

        Raises:
            ValidationError: Intended or Actual does not have the feature name as the top level key.

        Returns:
            str: Remediation config.
        """
        intended: dict[str, Any] = self._filter_allowed_params(
            feature_name=self.feature_name,
            config=self.intended_config,
            config_context=self.compliance_obj.device.get_config_context().get(
                f"{self.feature_name}_remediation",
                "",
            ),
        )
        actual: dict[str, Any] = self._filter_allowed_params(
            feature_name=self.feature_name,
            config=self.backup_config,
            config_context=self.compliance_obj.device.get_config_context().get(
                f"{self.feature_name}_remediation",
                "",
            ),
        )
        if not actual or not intended:
            raise ValidationError(
                "There was no config context passed or the config context does not have optional parameters."
            )
        diff: dict[str, Any] = {}
        stack: deque[Tuple[Tuple[str, ...], Any, Any]] = deque()
        stack.append((tuple(), actual, intended))

        while stack:
            path, actual, intended = stack.pop()

            if isinstance(actual, dict) and isinstance(intended, dict):
                self._dict_config(
                    intended=intended,
                    actual=actual,
                    diff=diff,
                    path=path,
                    stack=stack,
                )

            elif isinstance(actual, list) and isinstance(intended, list):
                self._list_config(
                    intended=intended,
                    actual=actual,
                    diff=diff,
                    path=path,
                    stack=stack,
                )
            else:
                self._str_int_float_config(
                    intended=intended,
                    actual=actual,
                    diff=diff,
                    path=path,
                )

        if not diff:
            return ""
        if not diff.get(self.feature_name):
            raise ValidationError(
                f"Feature {self.feature_name} not found in the config.",
            )
        valid_diff: dict[Any, Any] = self._inject_required_fields(
            diff=diff,
            intended=self.intended_config,
            path=(),
        )
        cleaned_diff: dict[Any, Any] = self._clean_diff(diff=valid_diff)
        return json.dumps(cleaned_diff, indent=4)


class XMLControllerRemediation(JsonControllerRemediation):  # pylint: disable=too-few-public-methods
    """Remediation class for controllers using XML config."""

    def __init__(
        self,
        compliance_obj: ConfigCompliance,
    ) -> None:
        """Controller remediation.

        Args:
            compliance_obj (ConfigCompliance): Golden Config Compliance object.
        """
        self.compliance_obj: ConfigCompliance = compliance_obj
        self.feature_name: str = compliance_obj.rule.feature.name.lower()
        self.intended_config: OrderedDict[str, Any] = xmltodict.parse(
            xml_input=compliance_obj.intended,
        )
        self.backup_config: OrderedDict[str, Any] = xmltodict.parse(
            xml_input=compliance_obj.actual,
        )
        self.required_parameters: list[str]


def controller_remediation(obj: "ConfigCompliance") -> str:
    """Controller remediation.

    Args:
        obj (ConfigCompliance): Compliance object.

    Returns:
        str: Remediation json config.
    """
    remediation: BaseControllerRemediation
    config_type = obj.rule.config_type.lower().strip()
    if config_type == "json":
        remediation = JsonControllerRemediation(
            compliance_obj=obj,
        )
    elif config_type == "xml":
        remediation = XMLControllerRemediation(
            compliance_obj=obj,
        )
    else:
        raise ValidationError(
            f"Config type {obj.rule.config_type} is not supported.",
        )
    return remediation.controller_remediation()
