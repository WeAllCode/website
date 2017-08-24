from django.views.generic.base import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from coderdojochi.models import Mentor, Meeting
from django.utils import timezone
from django.db.models import Count


class VolunteerView(TemplateView):
    template_name = 'volunteer.html'

    def get_context_data(self, **kwargs):
        context = super(VolunteerView, self).get_context_data(**kwargs)
        context['mentors'] = Mentor.objects.select_related('user').filter(
            is_active=True,
            is_public=True,
            background_check=True,
            avatar_approved=True,
        ).annotate(
            session_count=Count('mentororder')
        ).order_by('-user__role', '-session_count')

        context['upcoming_meetings'] = Meeting.objects.filter(
            is_active=True,
            is_public=True,
            end_date__gte=timezone.now()
        ).order_by('start_date')[:3]

        return context
