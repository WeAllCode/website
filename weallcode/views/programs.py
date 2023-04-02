from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView
from django.conf import settings

from coderdojochi.models import Course, Session

from .common import DefaultMetaTags
import arrow


class ProgramsView(DefaultMetaTags, TemplateView):
    template_name = "weallcode/programs.html"
    url = reverse_lazy("weallcode-programs")

    title = f"Programs | We All Code"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        IS_PARENT = True if user.is_authenticated and user.role == "guardian" else False
        IS_MENTOR = True if user.is_authenticated and user.role == "mentor" else False
        NOW = arrow.now()

        # region WEEKEND CLASSES
        weekend_classes = (
            Session.objects.filter(
                is_active=True,
                start_date__gte=timezone.now(),
                course__course_type=Course.WEEKEND,
            )
            .order_by(
                "start_date",
            )
            .prefetch_related(
                "course",
                "location",
            )
        )

        if not user.is_authenticated or not user.role == "mentor":
            weekend_classes = weekend_classes.filter(is_public=True)

        weekend_classes = list(weekend_classes)

        for session in weekend_classes:
            if IS_MENTOR:
                session.start_time = session.mentor_start_date
                session.end_time = session.mentor_end_date

                if (
                    session.mentor_capacity
                    and len(session.get_mentor_orders()) >= session.mentor_capacity
                ):
                    session.class_status = "Class Full"
                else:
                    session.class_status = "Volunteer"

            else:
                session.start_time = arrow.get(session.start_date).to(
                    settings.TIME_ZONE
                )
                session.end_time = session.end_date

                # MAX_DAYS_FOR_PARENTS (30) days before the class start time
                open_signup_time = session.start_time.shift(
                    days=-settings.MAX_DAYS_FOR_PARENTS
                )

                if IS_PARENT and NOW < open_signup_time:
                    session.class_status = (
                        f"Sign up available {open_signup_time.humanize(NOW)}"
                    )
                elif session.get_active_student_count() >= session.capacity:
                    session.class_status = "Class Full"
                else:
                    session.class_status = "Sign up"

        context["weekend_classes"] = weekend_classes

        # endregion

        # region SUMMER CAMP CLASSES
        summer_camp_classes = (
            Session.objects.filter(
                is_active=True,
                start_date__gte=timezone.now(),
                course__course_type=Course.CAMP,
            )
            .order_by(
                "start_date",
            )
            .prefetch_related(
                "course",
                "location",
            )
        )

        if not user.is_authenticated or not user.role == "mentor":
            summer_camp_classes = summer_camp_classes.filter(is_public=True)

        context["summer_camp_classes"] = summer_camp_classes
        # endregion

        return context
