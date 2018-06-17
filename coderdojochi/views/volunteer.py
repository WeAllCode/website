from django.db.models import Count
from django.utils import timezone
from django.utils.functional import cached_property
from django.views.generic.base import TemplateView

from coderdojochi.models import Meeting, Mentor


class VolunteerView(TemplateView):
    template_name = 'volunteer.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get active mentors
        context['mentors'] = Mentor.objects.select_related('user').filter(
            is_active=True,
            is_public=True,
            background_check=True,
            avatar_approved=True,
        ).annotate(
            session_count=Count('mentororder')
        ).order_by('-user__role', '-session_count')

        # Get 3 meetings
        context['meetings'] = Meeting.objects.filter(
            is_active=True,
            is_public=True,
            end_date__gte=timezone.now()
        ).order_by('start_date')[:3]

        return context
