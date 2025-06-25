"""Test NetscalerExtExampleModel Filter."""

from nautobot.apps.testing import FilterTestCases

from netscaler_ext import filters, models
from netscaler_ext.tests import fixtures


class NetscalerExtExampleModelFilterTestCase(FilterTestCases.FilterTestCase):  # pylint: disable=too-many-ancestors
    """NetscalerExtExampleModel Filter Test Case."""

    queryset = models.NetscalerExtExampleModel.objects.all()
    filterset = filters.NetscalerExtExampleModelFilterSet
    generic_filter_tests = (
        ("id",),
        ("created",),
        ("last_updated",),
        ("name",),
    )

    @classmethod
    def setUpTestData(cls):
        """Setup test data for NetscalerExtExampleModel Model."""
        fixtures.create_netscalerextexamplemodel()

    def test_q_search_name(self):
        """Test using Q search with name of NetscalerExtExampleModel."""
        params = {"q": "Test One"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_q_invalid(self):
        """Test using invalid Q search for NetscalerExtExampleModel."""
        params = {"q": "test-five"}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)
