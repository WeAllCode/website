from collections import defaultdict
from datetime import datetime
from itertools import chain

from django.conf import settings
from django.contrib import messages, sitemaps
from django.contrib.auth import get_user_model
from django.db.models import Count
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
    print("page_not_found_view")
    capture_message("Page not found!", level="error")

    return render(
        request,
        "404.html",
        {"sentry_event_id": last_event_id(), "SENTRY_DSN": settings.SENTRY_DSN,},
        status=404,
    )


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
    url = reverse_lazy("weallcode-home")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        sessions = Session.objects.filter(
            is_active=True, start_date__gte=timezone.now()
        ).order_by("start_date")

        if (
            not self.request.user.is_authenticated
            or not self.request.user.role == "mentor"
        ):
            sessions = sessions.filter(is_public=True)

        if len(sessions) > 0:
            context["next_session"] = sessions[0]

        return context


class OurStoryView(DefaultMetaTags, TemplateView):
    template_name = "weallcode/our_story.html"
    url = reverse_lazy("weallcode-our-story")

    title = f"Our Story | We All Code"


class ProgramsView(DefaultMetaTags, TemplateView):
    template_name = "weallcode/programs.html"
    url = reverse_lazy("weallcode-programs")

    title = f"Programs | We All Code"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # WEEKEND CLASSES
        weekend_classes = Session.objects.filter(
            is_active=True,
            start_date__gte=timezone.now(),
            course__course_type=Course.WEEKEND,
        ).order_by("start_date")

        if (
            not self.request.user.is_authenticated
            or not self.request.user.role == "mentor"
        ):
            weekend_classes = weekend_classes.filter(is_public=True)

        context["weekend_classes"] = weekend_classes

        # SUMMER CAMP CLASSES
        summer_camp_classes = Session.objects.filter(
            is_active=True,
            start_date__gte=timezone.now(),
            course__course_type=Course.CAMP,
        ).order_by("start_date")

        if (
            not self.request.user.is_authenticated
            or not self.request.user.role == "mentor"
        ):
            summer_camp_classes = summer_camp_classes.filter(is_public=True)

        context["summer_camp_classes"] = summer_camp_classes

        return context


class ProgramsSummerCampsView(DefaultMetaTags, TemplateView):
    template_name = "weallcode/programs-summer-camps.html"
    url = reverse_lazy("weallcode-programs-summer-camps")

    title = f"Summer Camps | We All Code"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # SUMMER CAMP CLASSES
        summer_camp_classes = Session.objects.filter(
            is_active=True,
            start_date__gte=timezone.now(),
            course__course_type=Course.CAMP,
        ).order_by("start_date")

        if (
            not self.request.user.is_authenticated
            or not self.request.user.role == "mentor"
        ):
            summer_camp_classes = summer_camp_classes.filter(is_public=True)

        context["summer_camp_classes"] = summer_camp_classes

        return context


class TeamView(DefaultMetaTags, TemplateView):
    template_name = "weallcode/team.html"
    url = reverse_lazy("weallcode-team")

    title = f"Team | We All Code"

    # Staff
    def get_staff(self, context):
        context["staff"] = StaffMember.objects.filter(is_active=True,)

        return context

    # Board Members
    def get_board(self, context):
        board = BoardMember.objects.filter(is_active=True,)

        # NOTE: We're splitting and reordering them manually since the website requires a specific order.
        roles = defaultdict(list)

        for person in board:
            roles[person.role].append(person)

        # The correct order
        context["board"] = list(
            chain(
                roles["Chair"],
                roles["Vice Chair"],
                roles["Treasurer"],
                roles["Secretary"],
                roles["Director"],
            )
        )

        return context

    # Associate Board Members
    def get_associate_board(self, context):
        associate_board = AssociateBoardMember.objects.filter(is_active=True,).order_by(
            "name"
        )

        # NOTE: We're splitting and reordering them manually since the website requires a specific order.
        roles = defaultdict(list)

        for person in associate_board:
            roles[person.role].append(person)

        # The correct order
        context["associate_board"] = list(
            chain(
                roles["Chair"],
                roles["Vice Chair"],
                roles["Treasurer"],
                roles["Secretary"],
                roles["Director"],
            )
        )

        return context

    # Instructors
    def get_instructors(self, context, volunteers):
        context["instructors"] = volunteers.filter(
            user__groups__name__in=["Instructor"],
        ).order_by("user__first_name")

        return context

    # Volunteers
    def get_volunteers(self, context, volunteers):
        all_volunteers = volunteers.annotate(
            session_count=Count("mentororder")
        ).order_by("-user__role", "-session_count")

        mentors = []
        volunteers = []

        for volunteer in all_volunteers:
            if volunteer.session_count >= 10:
                mentors += [volunteer]
            else:
                volunteers += [volunteer]

        context["top_mentors"] = mentors
        # context['other_mentors'] = mentors[8:]
        context["top_volunteers"] = volunteers[0:16]
        context["other_volunteers"] = volunteers[16:]

        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        volunteers = Mentor.objects.select_related("user").filter(
            is_active=True, is_public=True, background_check=True, avatar_approved=True,
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
    url = reverse_lazy("weallcode-join-us")
    success_url = reverse_lazy("weallcode-join-us")

    title = f"Join Us | We All Code"

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        form.send_email()
        messages.success(
            self.request,
            "Thank you for contacting us! We will respond as soon as possible.",
        )

        return super().form_valid(form)


class AssociateBoardView(DefaultMetaTags, TemplateView):
    template_name = "weallcode/associate_board.html"
    url = reverse_lazy("weallcode-associate-board")

    title = f"Join our Associate Board | We All Code"


class PrivacyView(DefaultMetaTags, TemplateView):
    template_name = "weallcode/privacy.html"
    url = reverse_lazy("weallcode-privacy")

    title = f"Privacy & Terms | We All Code"


class CreditsView(DefaultMetaTags, TemplateView):
    template_name = "weallcode/credits.html"
    url = reverse_lazy("weallcode-credits")

    title = f"Credits & Attributions | We All Code"


class StaticSitemapView(sitemaps.Sitemap):
    priority = 0.5
    changefreq = "daily"

    def items(self):
        return [
            "weallcode-home",
            "weallcode-our-story",
            "weallcode-programs",
            "weallcode-programs-summer-camps",
            "weallcode-team",
            "weallcode-join-us",
            "weallcode-privacy",
            "weallcode-credits",
        ]

    def location(self, item):
        return reverse(item)

    def lastmod(self, item):
        return datetime.now()
