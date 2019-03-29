from django.views.generic import TemplateView
from coderdojochi.models import Session
from django.utils import timezone


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


class GetInvolvedView(TemplateView):
    template_name = "weallcode/get_involved.html"


class PrivacyView(TemplateView):
    template_name = "weallcode/privacy.html"


class CreditsView(TemplateView):
    template_name = "weallcode/credits.html"
