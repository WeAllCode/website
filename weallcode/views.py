from coderdojochi.models import Mentor, Session
from django.db.models import Count
from django.utils import timezone
from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = "weallcode/home.html"


class OurStoryView(TemplateView):
    template_name = "weallcode/our_story.html"


class ProgramsView(TemplateView):
    template_name = "weallcode/programs.html"

    def get_context_data(self, **kwargs):
        context = super(ProgramsView, self).get_context_data(**kwargs)

        sessions = Session.objects.filter(
            is_active=True,
            end_date__gte=timezone.now()
        ).order_by('start_date')

        if (
            not self.request.user.is_authenticated or
            not self.request.user.role == 'mentor'
        ):
            sessions = sessions.filter(is_public=True)

        context['sessions'] = sessions

        return context


class TeamView(TemplateView):
    template_name = "weallcode/team.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        all_volunteers = Mentor.objects.select_related('user').filter(
            is_active=True,
            is_public=True,
            background_check=True,
            avatar_approved=True,
        ).annotate(
            session_count=Count('mentororder')
        ).order_by('-user__role', '-session_count')

        mentors = []
        volunteers = []

        for volunteer in all_volunteers:
            if volunteer.session_count >= 10:
                mentors += [volunteer]
            else:
                volunteers += [volunteer]

        context['mentors'] = mentors
        context['top_volunteers'] = volunteers[0:8]
        context['other_volunteers'] = volunteers[8:]


class GetInvolvedView(TemplateView):
    template_name = "weallcode/get_involved.html"


class PrivacyView(TemplateView):
    template_name = "weallcode/privacy.html"


class CreditsView(TemplateView):
    template_name = "weallcode/credits.html"
