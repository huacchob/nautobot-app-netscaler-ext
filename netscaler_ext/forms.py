"""Forms for netscaler_ext."""

from django import forms
from nautobot.apps.forms import NautobotBulkEditForm, NautobotFilterForm, NautobotModelForm, TagsBulkEditFormMixin

from netscaler_ext import models


class NetscalerExtExampleModelForm(NautobotModelForm):  # pylint: disable=too-many-ancestors
    """NetscalerExtExampleModel creation/edit form."""

    class Meta:
        """Meta attributes."""

        model = models.NetscalerExtExampleModel
        fields = "__all__"


class NetscalerExtExampleModelBulkEditForm(TagsBulkEditFormMixin, NautobotBulkEditForm):  # pylint: disable=too-many-ancestors
    """NetscalerExtExampleModel bulk edit form."""

    pk = forms.ModelMultipleChoiceField(
        queryset=models.NetscalerExtExampleModel.objects.all(), widget=forms.MultipleHiddenInput
    )
    description = forms.CharField(required=False)

    class Meta:
        """Meta attributes."""

        nullable_fields = [
            "description",
        ]


class NetscalerExtExampleModelFilterForm(NautobotFilterForm):
    """Filter form to filter searches."""

    model = models.NetscalerExtExampleModel
    field_order = ["q", "name"]

    q = forms.CharField(
        required=False,
        label="Search",
        help_text="Search within Name.",
    )
    name = forms.CharField(required=False, label="Name")
