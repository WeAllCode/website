from datetime import datetime

from django.conf import settings
from django.contrib import messages, sitemaps
from django.db.models import Count
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import FormView, TemplateView

from meta.views import MetadataMixin

from coderdojochi.models import Course, Mentor, Session

from .forms import ContactForm


class DefaultMetaTags(MetadataMixin):
    title = None
    description = (
        "We All Code is volunteer run nonprofit organization that teaches web, game, and app development to "
        "youth ages 7 to 17 free of charge."
    )
    image = "weallcode/images/photos/real-coding-skills.jpg"
    twitter_card = "summary_large_image"
    twitter_creator = "@weallcode"
    twitter_site = "@weallcode"


class DefaultContext():
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        paypal_url = "https://paypal.com/us/fundraiser/charity/193426"

        context["donate_url"] = paypal_url
        context["paypal_donate_url"] = paypal_url
        context["patreon_donate_url"] = "https://www.patreon.com/weallcode"

        return context


class HomeView(DefaultMetaTags, DefaultContext, TemplateView):
    template_name = "weallcode/home.html"
    url = reverse_lazy('weallcode-home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        sessions = Session.objects.filter(
            is_active=True,
            start_date__gte=timezone.now()
        ).order_by('start_date')

        if (
            not self.request.user.is_authenticated or
            not self.request.user.role == 'mentor'
        ):
            sessions = sessions.filter(is_public=True)

        if len(sessions) > 0:
            context['next_session'] = sessions[0]

        return context


class OurStoryView(DefaultMetaTags, DefaultContext, TemplateView):
    template_name = "weallcode/our_story.html"
    url = reverse_lazy('weallcode-our-story')

    title = f"Our Story | {settings.SITE_NAME}"


class ProgramsView(DefaultMetaTags, DefaultContext, TemplateView):
    template_name = "weallcode/programs.html"
    url = reverse_lazy('weallcode-programs')

    title = f"Programs | {settings.SITE_NAME}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # WEEKEND CLASSES
        weekend_classes = Session.objects.filter(
            is_active=True,
            start_date__gte=timezone.now(),
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
            start_date__gte=timezone.now(),
            course__course_type=Course.CAMP,
        ).order_by('start_date')

        if (
            not self.request.user.is_authenticated or
            not self.request.user.role == 'mentor'
        ):
            summer_camp_classes = summer_camp_classes.filter(is_public=True)

        context['summer_camp_classes'] = summer_camp_classes

        return context


class ProgramsSummerCampsView(DefaultMetaTags, DefaultContext, TemplateView):
    template_name = "weallcode/programs-summer-camps.html"
    url = reverse_lazy('weallcode-programs-summer-camps')

    title = f"Summer Camps | {settings.SITE_NAME}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # SUMMER CAMP CLASSES
        summer_camp_classes = Session.objects.filter(
            is_active=True,
            start_date__gte=timezone.now(),
            course__course_type=Course.CAMP,
        ).order_by('start_date')

        if (
            not self.request.user.is_authenticated or
            not self.request.user.role == 'mentor'
        ):
            summer_camp_classes = summer_camp_classes.filter(is_public=True)

        context['summer_camp_classes'] = summer_camp_classes

        return context


class TeamView(DefaultMetaTags, DefaultContext, TemplateView):
    template_name = "weallcode/team.html"
    url = reverse_lazy('weallcode-team')

    title = f"Team | {settings.SITE_NAME}"

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


class JoinUsView(DefaultMetaTags, DefaultContext, FormView):
    template_name = "weallcode/join_us.html"
    form_class = ContactForm
    url = reverse_lazy('weallcode-join-us')
    success_url = reverse_lazy('weallcode-join-us')

    title = f"Join Us | {settings.SITE_NAME}"

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        form.send_email()
        messages.success(
            self.request,
            "Thank you for contacting us! We will respond as soon as possible."
        )

        return super().form_valid(form)


class PrivacyView(DefaultMetaTags, DefaultContext, TemplateView):
    template_name = "weallcode/privacy.html"
    url = reverse_lazy('weallcode-privacy')

    title = f"Privacy & Terms | {settings.SITE_NAME}"


class CreditsView(DefaultMetaTags, DefaultContext, TemplateView):
    template_name = "weallcode/credits.html"
    url = reverse_lazy('weallcode-credits')

    title = f"Credits & Attributions | {settings.SITE_NAME}"


class StaticSitemapView(sitemaps.Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return [
            'weallcode-home',
            'weallcode-our-story',
            'weallcode-programs',
            'weallcode-programs-summer-camps',
            'weallcode-team',
            'weallcode-join-us',
            'weallcode-privacy',
            'weallcode-credits',
        ]

    def location(self, item):
        return reverse(item)

    def lastmod(self, item):
        return datetime.now()
