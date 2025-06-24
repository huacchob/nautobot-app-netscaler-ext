"""Test NetscalerExtExampleModel."""

from nautobot.apps.testing import ModelTestCases

from netscaler_ext import models
from netscaler_ext.tests import fixtures


class TestNetscalerExtExampleModel(ModelTestCases.BaseModelTestCase):
    """Test NetscalerExtExampleModel."""

    model = models.NetscalerExtExampleModel

    @classmethod
    def setUpTestData(cls):
        """Create test data for NetscalerExtExampleModel Model."""
        super().setUpTestData()
        # Create 3 objects for the model test cases.
        fixtures.create_netscalerextexamplemodel()

    def test_create_netscalerextexamplemodel_only_required(self):
        """Create with only required fields, and validate null description and __str__."""
        netscalerextexamplemodel = models.NetscalerExtExampleModel.objects.create(name="Development")
        self.assertEqual(netscalerextexamplemodel.name, "Development")
        self.assertEqual(netscalerextexamplemodel.description, "")
        self.assertEqual(str(netscalerextexamplemodel), "Development")

    def test_create_netscalerextexamplemodel_all_fields_success(self):
        """Create NetscalerExtExampleModel with all fields."""
        netscalerextexamplemodel = models.NetscalerExtExampleModel.objects.create(
            name="Development", description="Development Test"
        )
        self.assertEqual(netscalerextexamplemodel.name, "Development")
        self.assertEqual(netscalerextexamplemodel.description, "Development Test")
