from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView

from coderdojochi.models import Course, Session

from .common import DefaultMetaTags


class ProgramsView(DefaultMetaTags, TemplateView):
    template_name = "weallcode/programs.html"
    url = reverse_lazy("weallcode-programs")

    title = f"Programs | We All Code"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # WEEKEND CLASSES
        weekend_classes = (
            Session.objects.filter(
                is_active=True,
                start_date__gte=timezone.now(),
                course__course_type=Course.WEEKEND,
            )
            .order_by("start_date")
            .prefetch_related("course", "location")
        )

        if not self.request.user.is_authenticated or not self.request.user.role == "mentor":
            weekend_classes = weekend_classes.filter(is_public=True)

        context["weekend_classes"] = weekend_classes

        # SUMMER CAMP CLASSES
        summer_camp_classes = (
            Session.objects.filter(
                is_active=True,
                start_date__gte=timezone.now(),
                course__course_type=Course.CAMP,
            )
            .order_by("start_date")
            .prefetch_related("course", "location")
        )

        if not self.request.user.is_authenticated or not self.request.user.role == "mentor":
            summer_camp_classes = summer_camp_classes.filter(is_public=True)

        context["summer_camp_classes"] = summer_camp_classes

        return context
