from django.urls import reverse_lazy
from django.views.generic import TemplateView

from .common import DefaultMetaTags


class OurStoryView(DefaultMetaTags, TemplateView):
    template_name = "weallcode/our_story.html"
    url = reverse_lazy("weallcode-our-story")

    title = f"Our Story | We All Code"
