"""API serializers for netscaler_ext."""

from nautobot.apps.api import NautobotModelSerializer, TaggedModelSerializerMixin

from netscaler_ext import models


class NetscalerExtExampleModelSerializer(NautobotModelSerializer, TaggedModelSerializerMixin):  # pylint: disable=too-many-ancestors
    """NetscalerExtExampleModel Serializer."""

    class Meta:
        """Meta attributes."""

        model = models.NetscalerExtExampleModel
        fields = "__all__"

        # Option for disabling write for certain fields:
        # read_only_fields = []
