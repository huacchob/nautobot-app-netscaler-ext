"""Filtering for netscaler_ext."""

from nautobot.apps.filters import NameSearchFilterSet, NautobotFilterSet

from netscaler_ext import models


class NetscalerExtExampleModelFilterSet(NameSearchFilterSet, NautobotFilterSet):  # pylint: disable=too-many-ancestors
    """Filter for NetscalerExtExampleModel."""

    class Meta:
        """Meta attributes for filter."""

        model = models.NetscalerExtExampleModel

        # add any fields from the model that you would like to filter your searches by using those
        fields = "__all__"
