from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView

from coderdojochi.models import Session

from .common import DefaultMetaTags


class HomeView(DefaultMetaTags, TemplateView):
    template_name = "weallcode/home.html"
    url = reverse_lazy("weallcode-home")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        sessions = Session.objects.filter(
            is_active=True,
            start_date__gte=timezone.now(),
        ).order_by("start_date")

        if (
            not self.request.user.is_authenticated
            or not self.request.user.role == "mentor"
        ):
            sessions = sessions.filter(is_public=True)

        if len(sessions) > 0:
            context["next_session"] = sessions[0]

        return context
