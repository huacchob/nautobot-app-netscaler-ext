import json
import unittest
from collections import deque
from typing import Any
from unittest.mock import MagicMock

from netscaler_ext.plugins.tasks.remediation.controller_remediation import (
    DictKey,
    JsonControllerRemediation,
)


def load_fixture(filename: str) -> Any:
    with open(file=filename, mode="r", encoding="utf-8") as f:
        return json.load(fp=f)


class TestJsonControllerRemediation(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base_fixtures_path: str = "netscaler_ext/tests/fixtures/remediation/"
        cls.intended_config = load_fixture(filename=f"{cls.base_fixtures_path}intended_config.json")
        cls.actual_config = load_fixture(filename=f"{cls.base_fixtures_path}actual_config.json")
        cls.config_context = load_fixture(filename=f"{cls.base_fixtures_path}config_context.json")

    def setUp(self):
        rule = MagicMock()
        rule.feature.name = "feature"
        rule.config_type = "json"
        device = MagicMock()
        device.get_config_context.return_value = {"feature_remediation": self.config_context}
        self.compliance_obj = MagicMock()
        self.compliance_obj.rule = rule
        self.compliance_obj.device = device
        self.compliance_obj.intended = self.intended_config
        self.compliance_obj.actual = self.actual_config

    def test_filter_allowed_params(self):
        remediation = JsonControllerRemediation(self.compliance_obj)
        filtered = remediation._filter_allowed_params(
            feature_name="feature",
            config=self.compliance_obj.intended,
            config_context=self.config_context,
        )
        self.assertIn("feature", filtered)
        self.assertSetEqual(set(filtered["feature"].keys()), {"param1", "param2", "param3"})

    def test_process_diff_dictkey(self):
        diff = {}
        path = (DictKey("foo"),)
        value = "bar"
        remediation = JsonControllerRemediation(MagicMock())
        remediation._process_diff(diff, path, value)
        self.assertEqual(diff["foo"], "bar")

    def test_process_diff_str_key(self):
        diff = {}
        path = ("foo",)
        value = "bar"
        remediation = JsonControllerRemediation(MagicMock())
        remediation._process_diff(diff, path, value)
        self.assertEqual(diff["foo"], "bar")

    def test_process_diff_int_key(self):
        diff = []
        path = (0,)
        value = "bar"
        remediation = JsonControllerRemediation(MagicMock())
        remediation._process_diff(diff, path, value)
        self.assertEqual(diff[0], "bar")

    def test_dict_config(self):
        remediation = JsonControllerRemediation(MagicMock())
        intended = {"foo": {"bar": 1}}
        actual = {"foo": {}}
        diff = {}
        stack = deque()
        remediation._dict_config(intended, actual, diff, tuple(), stack)
        self.assertEqual(diff["foo"]["bar"], 1)

    def test_list_config(self):
        remediation = JsonControllerRemediation(MagicMock())
        intended = [{"bar": 1}]
        actual = [{}]
        diff = []
        stack = deque()
        remediation._list_config(intended, actual, diff, tuple(), stack)
        self.assertEqual(diff[0]["bar"], 1)

    def test_str_int_float_config(self):
        remediation = JsonControllerRemediation(MagicMock())
        diff = {}
        remediation._str_int_float_config("foo", "bar", diff, ("baz",))
        self.assertEqual(diff["baz"], "foo")

    def test_inject_required_fields(self):
        remediation = JsonControllerRemediation(MagicMock())
        remediation.required_parameters = ["param1"]
        diff = {"param2": "value2"}
        intended = {"param1": "value1", "param2": "value2"}
        result = remediation._inject_required_fields(diff, intended, ())
        self.assertEqual(result["param1"], "value1")

    def test_clean_diff(self):
        remediation = JsonControllerRemediation(MagicMock())
        diff = {"foo": {}, "bar": {"baz": "qux"}, "empty": []}
        cleaned = remediation._clean_diff(diff)
        self.assertNotIn("foo", cleaned)
        self.assertIn("bar", cleaned)
        self.assertNotIn("empty", cleaned)

    def test_controller_remediation_success(self):
        remediation = JsonControllerRemediation(self.compliance_obj)
        result = remediation.controller_remediation()
        self.assertIsInstance(result, str)
        self.assertIn("param2", result)

    def test_controller_remediation_no_context(self):
        compliance_obj = MagicMock()
        compliance_obj.rule.feature.name = "feature"
        compliance_obj.intended = {"feature": {}}
        compliance_obj.actual = {"feature": {}}
        compliance_obj.device.get_config_context.return_value = {}
        remediation = JsonControllerRemediation(compliance_obj)
        with self.assertRaises(Exception):
            remediation.controller_remediation()

    def test_with_wti_config(self):
        compliance_obj = MagicMock()
        compliance_obj.rule.feature.name = "hostname"
        compliance_obj.intended = load_fixture(filename=f"{self.base_fixtures_path}wti_intended.json")
        compliance_obj.actual = load_fixture(filename=f"{self.base_fixtures_path}wti_backup.json")
        compliance_obj.device.get_config_context.return_value = load_fixture(
            filename=f"{self.base_fixtures_path}wti_remediation_context.json"
        )
        remediation = JsonControllerRemediation(compliance_obj)
        result = remediation.controller_remediation()
        self.assertIsInstance(result, str)
        self.assertIn("hostname", result)


if __name__ == "__main__":
    unittest.main()
