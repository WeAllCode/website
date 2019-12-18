from datetime import datetime

from coderdojochi.models import Course, Mentor, Session
from django.conf import settings
from django.contrib import messages, sitemaps
from django.db.models import Count
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import FormView
from meta.views import MetadataMixin

from .forms import ContactForm


class WeAllCodeView(MetadataMixin, FormView):
    description = (
        "We All Code is volunteer run nonprofit organization that teaches web, game, and app development to "
        "youth ages 7 to 17 free of charge."
    )
    image = "weallcode/images/photos/real-coding-skills.jpg"
    twitter_card = "summary_large_image"
    twitter_creator = "@weallcode"
    twitter_site = "@weallcode"

    def get_context_data(self, **kwargs):
        return {
            "donate_url": "https://paypal.com/us/fundraiser/charity/193426",
            "paypal_donate_url": "https://paypal.com/us/fundraiser/charity/193426",
            "patreon_donate_url": "https://www.patreon.com/weallcode",
        }


class HomeView(WeAllCodeView):
    template_name = "weallcode/home.html"
    title = "We All Code"
    url = reverse_lazy('weallcode-home')

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

        return context


class OurStoryView(WeAllCodeView):
    template_name = "weallcode/our_story.html"
    title = f"Our Story | {settings.SITE_NAME}"
    url = reverse_lazy('weallcode-our-story')


class ProgramsView(WeAllCodeView):
    template_name = "weallcode/programs.html"
    title = f"Programs | {settings.SITE_NAME}"
    url = reverse_lazy('weallcode-programs')

    def get_context_data(self, **kwargs):
        context = super(ProgramsView, self).get_context_data(**kwargs)

        # WEEKEND CLASSES
        weekend_classes = Session.objects.filter(
            is_active=True,
            end_date__gte=timezone.now(),
            course__course_type=Course.WEEKEND,
        ).order_by('start_date')

        if (
            not self.request.user.is_authenticated or
            not self.request.user.role == 'mentor'
        ):
            weekend_classes = weekend_classes.filter(is_public=True)

        context['weekend_classes'] = weekend_classes

        # SUMMER CAMP CLASSES
        summer_camp_classes = Session.objects.filter(
            is_active=True,
            end_date__gte=timezone.now(),
            course__course_type=Course.CAMP,
        ).order_by('start_date')

        if (
            not self.request.user.is_authenticated or
            not self.request.user.role == 'mentor'
        ):
            summer_camp_classes = summer_camp_classes.filter(is_public=True)

        context['summer_camp_classes'] = summer_camp_classes

        return context


class ProgramsSummerCampsView(WeAllCodeView):
    template_name = "weallcode/programs-summer-camps.html"
    title = f"Summer Camps | {settings.SITE_NAME}"
    url = reverse_lazy('weallcode-programs-summer-camps')

    def get_context_data(self, **kwargs):
        context = super(ProgramsSummerCampsView, self).get_context_data(**kwargs)

        # SUMMER CAMP CLASSES
        summer_camp_classes = Session.objects.filter(
            is_active=True,
            end_date__gte=timezone.now(),
            course__course_type=Course.CAMP,
        ).order_by('start_date')

        if (
            not self.request.user.is_authenticated or
            not self.request.user.role == 'mentor'
        ):
            summer_camp_classes = summer_camp_classes.filter(is_public=True)

        context['summer_camp_classes'] = summer_camp_classes

        return context


class TeamView(WeAllCodeView):
    template_name = "weallcode/team.html"
    title = f"Team | {settings.SITE_NAME}"
    url = reverse_lazy('weallcode-team')

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

        context['top_mentors'] = mentors[0:8]
        context['other_mentors'] = mentors[8:]
        context['top_volunteers'] = volunteers[0:8]
        context['other_volunteers'] = volunteers[8:]
        return context


class JoinUsView(WeAllCodeView):
    template_name = "weallcode/join_us.html"
    form_class = ContactForm
    title = f"Join Us | {settings.SITE_NAME}"
    url = reverse_lazy('weallcode-join-us')
    success_url = reverse_lazy('weallcode-join-us')

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        form.send_email()
        messages.success(
            self.request,
            "Thank you for contacting us! We will respond as soon as possible."
        )

        return super().form_valid(form)


class PrivacyView(WeAllCodeView):
    template_name = "weallcode/privacy.html"
    title = f"Privacy & Terms | {settings.SITE_NAME}"
    url = reverse_lazy('weallcode-privacy')


class CreditsView(WeAllCodeView):
    template_name = "weallcode/credits.html"
    title = f"Credits & Attributions | {settings.SITE_NAME}"
    url = reverse_lazy('weallcode-credits')


class StaticSitemapView(sitemaps.Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return ['weallcode-home', 'weallcode-our-story', 'weallcode-programs', 'weallcode-programs-summer-camps',
                'weallcode-team', 'weallcode-join-us', 'weallcode-privacy', 'weallcode-credits']

    def location(self, item):
        return reverse(item)

    def lastmod(self, item):
        return datetime.now()
