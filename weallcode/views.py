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


class HomeView(MetadataMixin, TemplateView):
    template_name = "weallcode/home.html"
    title = "We All Code"
    description = (
        "We All Code is volunteer run nonprofit organization that teaches web, game, and app development to "
        "youth ages 7 to 17 free of charge."
    )
    image = "weallcode/images/photos/real-coding-skills.jpg"
    twitter_card = "summary_large_image"
    twitter_site = "@weallcode"
    twitter_creator = "@weallcode"
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

        context['show_intro'] = self.request.COOKIES.get('has_seen_intro', 'false') == 'false'

        return context


class OurStoryView(MetadataMixin, TemplateView):
    template_name = "weallcode/our_story.html"
    title = f"Our Story | {settings.SITE_NAME}"
    description = (
        "We All Code is volunteer run nonprofit organization that teaches web, game, and app development to "
        "youth ages 7 to 17 free of charge."
    )
    image = "weallcode/images/photos/real-coding-skills.jpg"
    twitter_card = "summary_large_image"
    twitter_site = "@weallcode"
    twitter_creator = "@weallcode"
    url = reverse_lazy('weallcode-our-story')


class ProgramsView(MetadataMixin, TemplateView):
    template_name = "weallcode/programs.html"
    title = f"Programs | {settings.SITE_NAME}"
    description = (
        "We All Code is volunteer run nonprofit organization that teaches web, game, and app development to "
        "youth ages 7 to 17 free of charge."
    )
    image = "weallcode/images/photos/real-coding-skills.jpg"
    twitter_card = "summary_large_image"
    twitter_site = "@weallcode"
    twitter_creator = "@weallcode"
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


class ProgramsSummerCampsView(MetadataMixin, TemplateView):
    template_name = "weallcode/programs-summer-camps.html"
    title = f"Summer Camps | {settings.SITE_NAME}"
    description = (
        "We All Code is volunteer run nonprofit organization that teaches web, game, and app development to "
        "youth ages 7 to 17 free of charge."
    )
    image = "weallcode/images/photos/real-coding-skills.jpg"
    twitter_card = "summary_large_image"
    twitter_site = "@weallcode"
    twitter_creator = "@weallcode"
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


class TeamView(MetadataMixin, TemplateView):
    template_name = "weallcode/team.html"
    title = f"Team | {settings.SITE_NAME}"
    description = (
        "We All Code is volunteer run nonprofit organization that teaches web, game, and app development to "
        "youth ages 7 to 17 free of charge."
    )
    image = "weallcode/images/photos/real-coding-skills.jpg"
    twitter_card = "summary_large_image"
    twitter_site = "@weallcode"
    twitter_creator = "@weallcode"
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

        context['mentors'] = mentors
        context['top_volunteers'] = volunteers[0:8]
        context['other_volunteers'] = volunteers[8:]
        return context


class GetInvolvedView(MetadataMixin, FormView):
    template_name = "weallcode/get_involved.html"
    form_class = ContactForm
    title = f"Get Involved | {settings.SITE_NAME}"
    description = (
        "We All Code is volunteer run nonprofit organization that teaches web, game, and app development to "
        "youth ages 7 to 17 free of charge."
    )
    image = "weallcode/images/photos/real-coding-skills.jpg"
    twitter_card = "summary_large_image"
    twitter_site = "@weallcode"
    twitter_creator = "@weallcode"
    url = reverse_lazy('weallcode-get-involved')
    success_url = reverse_lazy('weallcode-get-involved')

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        form.send_email()
        messages.success(
            self.request,
            "Thank you for contacting us! We will respond as soon as possible."
        )

        return super().form_valid(form)


class PrivacyView(MetadataMixin, TemplateView):
    template_name = "weallcode/privacy.html"
    title = f"Privacy & Terms | {settings.SITE_NAME}"
    description = (
        "We All Code is volunteer run nonprofit organization that teaches web, game, and app development to "
        "youth ages 7 to 17 free of charge."
    )
    image = "weallcode/images/photos/real-coding-skills.jpg"
    twitter_card = "summary_large_image"
    twitter_site = "@weallcode"
    twitter_creator = "@weallcode"
    url = reverse_lazy('weallcode-privacy')


class CreditsView(MetadataMixin, TemplateView):
    template_name = "weallcode/credits.html"
    title = f"Credits & Attributions | {settings.SITE_NAME}"
    description = (
        "We All Code is volunteer run nonprofit organization that teaches web, game, and app development to "
        "youth ages 7 to 17 free of charge."
    )
    image = "weallcode/images/photos/real-coding-skills.jpg"
    twitter_card = "summary_large_image"
    twitter_site = "@weallcode"
    twitter_creator = "@weallcode"
    url = reverse_lazy('weallcode-credits')


class StaticSitemapView(sitemaps.Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return ['weallcode-home', 'weallcode-our-story', 'weallcode-programs', 'weallcode-programs-summer-camps',
                'weallcode-team', 'weallcode-get-involved', 'weallcode-privacy', 'weallcode-credits']

    def location(self, item):
        return reverse(item)

    def lastmod(self, item):
        return datetime.now()
