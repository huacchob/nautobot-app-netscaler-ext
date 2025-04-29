"""Views for netscaler_ext."""

from nautobot.apps.views import NautobotUIViewSet

from netscaler_ext import filters, forms, models, tables
from netscaler_ext.api import serializers


class NetscalerExtExampleModelUIViewSet(NautobotUIViewSet):
    """ViewSet for NetscalerExtExampleModel views."""

    bulk_update_form_class = forms.NetscalerExtExampleModelBulkEditForm
    filterset_class = filters.NetscalerExtExampleModelFilterSet
    filterset_form_class = forms.NetscalerExtExampleModelFilterForm
    form_class = forms.NetscalerExtExampleModelForm
    lookup_field = "pk"
    queryset = models.NetscalerExtExampleModel.objects.all()
    serializer_class = serializers.NetscalerExtExampleModelSerializer
    table_class = tables.NetscalerExtExampleModelTable
