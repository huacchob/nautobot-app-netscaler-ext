"""Create fixtures for tests."""

from netscaler_ext.models import NetscalerExtExampleModel


def create_netscalerextexamplemodel():
    """Fixture to create necessary number of NetscalerExtExampleModel for tests."""
    NetscalerExtExampleModel.objects.create(name="Test One")
    NetscalerExtExampleModel.objects.create(name="Test Two")
    NetscalerExtExampleModel.objects.create(name="Test Three")
