from django.urls import reverse_lazy
from django.views.generic import TemplateView

from .common import DefaultMetaTags


class ProgramsSummerCampsView(DefaultMetaTags, TemplateView):
    template_name = "weallcode/programs_summer_camps.html"
    url = reverse_lazy("weallcode-programs-summer-camps")

    title = f"Summer Camps | We All Code"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # SUMMER CAMP CLASSES
        summer_camp_classes = Session.objects.filter(
            is_active=True,
            start_date__gte=timezone.now(),
            course__course_type=Course.CAMP,
        ).order_by("start_date")

        if not self.request.user.is_authenticated or not self.request.user.role == "mentor":
            summer_camp_classes = summer_camp_classes.filter(is_public=True)

        context["summer_camp_classes"] = summer_camp_classes

        return context
