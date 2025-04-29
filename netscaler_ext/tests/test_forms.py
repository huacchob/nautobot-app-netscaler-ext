"""Test netscalerextexamplemodel forms."""

from django.test import TestCase

from netscaler_ext import forms


class NetscalerExtExampleModelTest(TestCase):
    """Test NetscalerExtExampleModel forms."""

    def test_specifying_all_fields_success(self):
        form = forms.NetscalerExtExampleModelForm(
            data={
                "name": "Development",
                "description": "Development Testing",
            }
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_specifying_only_required_success(self):
        form = forms.NetscalerExtExampleModelForm(
            data={
                "name": "Development",
            }
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_validate_name_netscalerextexamplemodel_is_required(self):
        form = forms.NetscalerExtExampleModelForm(data={"description": "Development Testing"})
        self.assertFalse(form.is_valid())
        self.assertIn("This field is required.", form.errors["name"])
