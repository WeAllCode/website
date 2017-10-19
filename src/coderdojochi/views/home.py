from django.utils.functional import cached_property
from django.views.generic import TemplateView

from coderdojochi.models import Session


class HomeView(TemplateView):
    template_name = "home.html"

    @cached_property
    def upcoming_classes(self):
        upcoming_classes = Session.objects.filter(
            is_active=True,
            end_date__gte=timezone.now(),
        ).order_by('start_date')

        if (
            not self.request.user.is_authenticated() or
            not self.request.user.role == 'mentor'
        ):
            upcoming_classes = upcoming_classes.filter(is_public=True)

        return upcoming_classes[:3]
