from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from ...models import Guardian, Mentor, MentorOrder, Session


class SessionDetailView(DetailView):
    model = Session
    template_name = "guardian/session_detail.html"

    def get_context_data(self, **kwargs):
        guardian = get_object_or_404(Guardian, user=self.request.user)

        context = super().get_context_data(**kwargs)
        context["students"] = guardian.get_students()
        context["spots_remaining"] = self.object.capacity - self.object.get_active_student_count()
        context["active_mentors"] = Mentor.objects.filter(
            id__in=MentorOrder.objects.filter(session=self.object, is_active=True).values("mentor__id")
        )

        return context

class SessionCancelView(DetailView):
    pass
