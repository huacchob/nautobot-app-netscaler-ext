"""Django API urlpatterns declaration for netscaler_ext app."""

from nautobot.apps.api import OrderedDefaultRouter

from netscaler_ext.api import views

router = OrderedDefaultRouter()
# add the name of your api endpoint, usually hyphenated model name in plural, e.g. "my-model-classes"
router.register("netscaler-ext-example-models", views.NetscalerExtExampleModelViewSet)

app_name = "netscaler_ext-api"
urlpatterns = router.urls
