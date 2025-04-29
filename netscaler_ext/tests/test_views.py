"""Unit tests for views."""

from nautobot.apps.testing import ViewTestCases

from netscaler_ext import models
from netscaler_ext.tests import fixtures


class NetscalerExtExampleModelViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    # pylint: disable=too-many-ancestors
    """Test the NetscalerExtExampleModel views."""

    model = models.NetscalerExtExampleModel
    bulk_edit_data = {"description": "Bulk edit views"}
    form_data = {
        "name": "Test 1",
        "description": "Initial model",
    }

    update_data = {
        "name": "Test 2",
        "description": "Updated model",
    }

    @classmethod
    def setUpTestData(cls):
        fixtures.create_netscalerextexamplemodel()
