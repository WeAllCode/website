from coderdojochi.models import Mentor, Session
from coderdojochi.util import email
from django.conf import settings
from django.contrib import messages
from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone
from django.views.generic import TemplateView
from weallcode.forms import ContactForm


class HomeView(TemplateView):
    template_name = "weallcode/home.html"

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)

        sessions = Session.objects.filter(
            is_active=True,
            end_date__gte=timezone.now()
        ).order_by('start_date')

        if (
            not self.request.user.is_authenticated or
            not self.request.user.role == 'mentor'
        ):
            sessions = sessions.filter(is_public=True)

        if len(sessions) > 0:
            context['next_session'] = sessions[0]

        context['show_intro'] = self.request.COOKIES.get('has_seen_intro', 'false') == 'false'

        return context


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
        return context


class ContactView(TemplateView):
    template_name = "weallcode/contact.html"

    def get_context_data(self):
        return { "form": ContactForm() }

    def post(self, request, **kwargs):
        if request.POST['human']:
            return messages.error(request, "Bad robot.")

        form = ContactForm(request.POST)

        if form.is_valid():
            email(
                subject=f"{request.POST['name']} | We All Code Contact Form",
                recipients=[settings.CONTACT_EMAIL],
                reply_to=[f"{request.POST['name']}<{request.POST['email']}>"],
                template_name='contact-email',
                merge_global_data={
                    'interest': request.POST['interest'],
                    'message': request.POST['message']
                },
            )

            messages.success(
                request,
                "Thank you for contacting us! We will respond as soon as possible."
            )

            form = ContactForm()
        else:
            messages.error(request, "There was an error. Please try again.")

        context = self.get_context_data(**kwargs)
        context['form'] = form

        return render(request, self.template_name, context)


class GetInvolvedView(ContactView):
    template_name = "weallcode/get_involved.html"


class PrivacyView(TemplateView):
    template_name = "weallcode/privacy.html"


class CreditsView(TemplateView):
    template_name = "weallcode/credits.html"
