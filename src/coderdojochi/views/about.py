from django.views.generic import TemplateView

from coderdojochi.models import (
    Mentor,
    Order,
)


class AboutView(TemplateView):
    template_name = "about.html"

    def get_context_data(self, **kwargs):
        context = super(AboutView, self).get_context_data(**kwargs)

        # Number of active mentors
        context['mentor_count'] = Mentor.objects.filter(
            is_active=True,
            is_public=True,
        ).count()

        # Number of served students based on checkin counts
        context['students_served_count'] = Order.objects.exclude(
            is_active=False,
            check_in=None
        ).count()

        return context
