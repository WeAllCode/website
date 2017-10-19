from django.views.generic.base import TemplateView


class PrivacyView(TemplateView):
    template_name = "privacy.html"
