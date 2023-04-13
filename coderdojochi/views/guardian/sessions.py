from django.conf import settings
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

import arrow

from ...models import (
    Guardian,
    Mentor,
    MentorOrder,
    Order,
    Session,
)


class SessionDetailView(DetailView):
    model = Session
    template_name = "guardian/session_detail.html"

    def get_context_data(self, **kwargs):
        guardian = get_object_or_404(Guardian, user=self.request.user)

        context = super().get_context_data(**kwargs)
        context["students"] = guardian.get_students()
        context["spots_remaining"] = (
            self.object.capacity - self.object.get_active_student_count()
        ) > 0
        context["active_mentors"] = Mentor.objects.filter(
            id__in=MentorOrder.objects.filter(
                session=self.object, is_active=True
            ).values("mentor__id")
        )

        context["has_students_enrolled"] = Order.objects.filter(
            student__in=context["students"],
            session=self.object,
            is_active=True,
        ).count()

        NOW = arrow.now()

        session_start_time = arrow.get(self.object.start_date).to(
            settings.TIME_ZONE
        )

        # MAX_DAYS_FOR_PARENTS (30) days before the class start time
        open_signup_time = session_start_time.shift(
            days=-settings.MAX_DAYS_FOR_PARENTS
        )

        if NOW < open_signup_time:
            context["class_not_open_for_signups"] = True
            context["class_time_until_open"] = open_signup_time.humanize(NOW)

        elif self.object.get_active_student_count() >= self.object.capacity:
            context["class_full"] = True

        return context
