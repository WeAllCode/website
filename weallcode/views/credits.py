from django.views.generic import TemplateView

from .common import DefaultMetaTags


class CreditsView(DefaultMetaTags, TemplateView):
    template_name = "weallcode/credits.html"
    # url = reverse_lazy("weallcode-credits")

    title = "Credits & Attributions | We All Code"
