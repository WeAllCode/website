from django.shortcuts import get_object_or_404
from django.utils import timezone
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

        upcoming_prerequisite_sessions = (
            Session.objects.filter(
                is_active=True,
                is_public=True,
                start_date__gte=timezone.now(),
                course__id__in=self.object.course.prerequisite.values_list("id"),
            )
            .distinct("course__code")
            .order_by("course__code", "start_date")
            .values("id", "course__id", "course__code")
        )

        context["upcoming_prerequisite_sessions"] = {p["course__id"]: p for p in list(upcoming_prerequisite_sessions)}

        return context
