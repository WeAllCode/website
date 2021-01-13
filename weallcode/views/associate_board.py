from django.urls import reverse_lazy
from django.views.generic import TemplateView

from .common import DefaultMetaTags


class AssociateBoardView(DefaultMetaTags, TemplateView):
    template_name = "weallcode/associate_board.html"
    url = reverse_lazy("weallcode-associate-board")

    title = f"Join our Associate Board | We All Code"
