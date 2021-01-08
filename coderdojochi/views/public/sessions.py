from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from ...models import Session


class SessionDetailView(DetailView):
    model = Session
    template_name = "public/session-detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context

