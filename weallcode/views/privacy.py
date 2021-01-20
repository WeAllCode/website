from django.urls import reverse_lazy
from django.views.generic import TemplateView

from .common import DefaultMetaTags


class PrivacyView(DefaultMetaTags, TemplateView):
    template_name = "weallcode/privacy.html"
    url = reverse_lazy("weallcode-privacy")

    title = f"Privacy & Terms | We All Code"
