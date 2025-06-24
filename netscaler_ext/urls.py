"""Django urlpatterns declaration for netscaler_ext app."""

from django.templatetags.static import static
from django.urls import path
from django.views.generic import RedirectView
from nautobot.apps.urls import NautobotUIViewSetRouter

from netscaler_ext import views

app_name = "netscaler_ext"
router = NautobotUIViewSetRouter()

# The standard is for the route to be the hyphenated version of the model class name plural.
# for example, ExampleModel would be example-models.
router.register("netscaler-ext-example-models", views.NetscalerExtExampleModelUIViewSet)


urlpatterns = [
    path("docs/", RedirectView.as_view(url=static("netscaler_ext/docs/index.html")), name="docs"),
]

urlpatterns += router.urls
