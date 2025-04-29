"""API views for netscaler_ext."""

from nautobot.apps.api import NautobotModelViewSet

from netscaler_ext import filters, models
from netscaler_ext.api import serializers


class NetscalerExtExampleModelViewSet(NautobotModelViewSet):  # pylint: disable=too-many-ancestors
    """NetscalerExtExampleModel viewset."""

    queryset = models.NetscalerExtExampleModel.objects.all()
    serializer_class = serializers.NetscalerExtExampleModelSerializer
    filterset_class = filters.NetscalerExtExampleModelFilterSet

    # Option for modifying the default HTTP methods:
    # http_method_names = ["get", "post", "put", "patch", "delete", "head", "options", "trace"]
