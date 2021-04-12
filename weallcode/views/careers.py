from django.urls import reverse_lazy
from django.views.generic import TemplateView

from .common import DefaultMetaTags


class CareersView(DefaultMetaTags, TemplateView):
    template_name = "weallcode/careers/careers.html"
    url = reverse_lazy("weallcode-careers")

    title = f"Careers | We All Code"


class CareersOperationsView(DefaultMetaTags, TemplateView):
    template_name = "weallcode/careers/operations.html"
    url = reverse_lazy("weallcode-careers-operations")

    title = f"Operations | Careers | We All Code"


class CareersEducatorView(DefaultMetaTags, TemplateView):
    template_name = "weallcode/careers/educator.html"
    url = reverse_lazy("weallcode-careers-educator")

    title = f"STEM Educator | Careers | We All Code"
