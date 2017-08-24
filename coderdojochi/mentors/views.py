from django.db.models import Count
from django.utils import timezone
from django.views.generic.base import TemplateView
from django.utils.functional import cached_property


from coderdojochi.models import Meeting

from .models import Mentor


class VolunteerView(TemplateView):
    template_name = 'volunteer.html'

    @cached_property
    def mentors(self):
        return Mentor.objects.select_related('user').filter(
            is_active=True,
            is_public=True,
            background_check=True,
            avatar_approved=True,
        ).annotate(
            session_count=Count('mentororder')
        ).order_by('-user__role', '-session_count')

    @cached_property
    def meetings(self):
        return Meeting.objects.filter(
            is_active=True,
            is_public=True,
            end_date__gte=timezone.now()
        ).order_by('start_date')[:3]
