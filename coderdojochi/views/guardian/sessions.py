from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from ...models import Guardian, Session


class SessionDetailView(DetailView):
    model = Session
    template_name = "guardian/session-detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # print(kwargs["object"])

        guardian = get_object_or_404(Guardian, user=self.request.user)

        context["students"] = guardian.get_students()
        # context["spots_remaining"] = object.capacity - object.get_active_student_count()

        return context
