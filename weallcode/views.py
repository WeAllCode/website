from datetime import datetime
from itertools import chain

from django.conf import settings
from django.contrib import messages, sitemaps
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.http import HttpResponseNotFound
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import FormView, TemplateView

from meta.views import MetadataMixin
from sentry_sdk import capture_message

from coderdojochi.models import Course, Mentor, Session

from .forms import ContactForm
from .models import AssociateBoardMember, BoardMember, StaffMember

User = get_user_model()


def page_not_found_view(*args, **kwargs):
    print('page_not_found_view')
    capture_message("Page not found!", level="error")

    return render(request, "404.html", {
            'sentry_event_id': last_event_id(),
            'SENTRY_DSN': settings.SENTRY_DSN,
        }, status=404)


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


class HomeView(DefaultMetaTags, TemplateView):
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


class OurStoryView(DefaultMetaTags, TemplateView):
    template_name = "weallcode/our_story.html"
    url = reverse_lazy('weallcode-our-story')

    title = f"Our Story | {settings.SITE_NAME}"


class ProgramsView(DefaultMetaTags, TemplateView):
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


class ProgramsSummerCampsView(DefaultMetaTags, TemplateView):
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


class TeamView(DefaultMetaTags, TemplateView):
    template_name = "weallcode/team.html"
    url = reverse_lazy('weallcode-team')

    title = f"Team | {settings.SITE_NAME}"

    # Staff
    def get_staff(self, context):
        context['staff'] = StaffMember.objects.all()

        return context

    # Board Members
    def get_board(self, context):
        board = BoardMember.objects.all()

        board_chair = board.filter(
            role='Chair'
        )

        board_vice_chair = board.filter(
            role='Vice Chair'
        )

        board_treasurer = board.filter(
            role='Treasurer'
        )

        board_secretary = board.filter(
            role='Secretary'
        )

        board_directors = board.filter(
            role='Director'
        ).order_by('name')

        context['board'] = list(chain(
            board_chair,
            board_vice_chair,
            board_treasurer,
            board_secretary,
            board_directors,
        ))

        return context

    # Associate Board Members
    def get_associate_board(self, context):
        associate_board = AssociateBoardMember.objects.all()

        ab_chair = associate_board.filter(
            role='Chair'
        )

        ab_vice_chair = associate_board.filter(
            role='Vice Chair'
        )

        ab_treasurer = associate_board.filter(
            role='Treasurer'
        )

        ab_secretary = associate_board.filter(
            role='Secretary'
        )

        ab_directors = associate_board.filter(
            role='Director'
        ).order_by('name')

        context['associate_board'] = list(chain(
            ab_chair,
            ab_vice_chair,
            ab_treasurer,
            ab_secretary,
            ab_directors,
        ))

        return context

    # Instructors
    def get_instructors(self, context, volunteers):
        context['instructors'] = volunteers.filter(
            user__groups__name__in=['Instructor'],
        ).order_by('user__first_name')

        return context

    # Volunteers
    def get_volunteers(self, context, volunteers):
        all_volunteers = volunteers.annotate(
            session_count=Count('mentororder')
        ).order_by('-user__role', '-session_count')

        mentors = []
        volunteers = []

        for volunteer in all_volunteers:
            if volunteer.session_count >= 10:
                mentors += [volunteer]
            else:
                volunteers += [volunteer]

        context['top_mentors'] = mentors
        # context['other_mentors'] = mentors[8:]
        context['top_volunteers'] = volunteers[0:16]
        context['other_volunteers'] = volunteers[16:]

        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        volunteers = Mentor.objects.select_related('user').filter(
            is_active=True,
            is_public=True,
            background_check=True,
            avatar_approved=True,
        )

        context = self.get_staff(context)
        context = self.get_board(context)
        context = self.get_associate_board(context)
        context = self.get_instructors(context, volunteers)
        context = self.get_volunteers(context, volunteers)

        return context


class JoinUsView(DefaultMetaTags, FormView):
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


class PrivacyView(DefaultMetaTags, TemplateView):
    template_name = "weallcode/privacy.html"
    url = reverse_lazy('weallcode-privacy')

    title = f"Privacy & Terms | {settings.SITE_NAME}"


class CreditsView(DefaultMetaTags, TemplateView):
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
