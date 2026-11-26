from datetime import timedelta

from django.db.models import Q
from django.db.models.aggregates import Count
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView

from coderdojochi.models import Mentor
from weallcode.models.associate_board_member import AssociateBoardMember
from weallcode.models.board_member import BoardMember
from weallcode.models.staff import StaffMember

from .common import DefaultMetaTags

# A volunteer is listed once they've taught this many classes in this many years.
RECENT_MIN_CLASSES = 3
RECENT_YEARS = 2


class TeamView(DefaultMetaTags, TemplateView):
    template_name = "weallcode/team.html"
    url = reverse_lazy("weallcode-team")

    title = "Team | We All Code"

    # Instructors
    def get_instructors(self, context, volunteers):
        context["instructors"] = volunteers.filter(
            user__groups__name__in=["Instructor"],
        ).order_by("user__first_name")

        return context

    # Volunteers
    def get_volunteers(self, context, volunteers):
        attended = Q(mentororder__is_active=True, mentororder__check_in__isnull=False)
        recent_since = timezone.now() - timedelta(days=365 * RECENT_YEARS)
        all_volunteers = (
            volunteers.annotate(
                # Classes actually taught (checked in), not sign-ups (#688).
                session_count=Count("mentororder", filter=attended),
                recent_count=Count(
                    "mentororder",
                    filter=attended
                    & Q(mentororder__session__start_date__gte=recent_since),
                ),
            )
            # Only volunteers active lately (#876).
            .filter(recent_count__gte=RECENT_MIN_CLASSES)
            .order_by("-user__role", "-session_count")
        )

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
            is_active=True,
            is_public=True,
            background_check=True,
            avatar_approved=True,
        )

        context["staff"] = StaffMember.objects.get_sorted()
        context["board"] = BoardMember.objects.get_sorted()
        context["associate_board"] = AssociateBoardMember.objects.get_sorted()
        context = self.get_instructors(context, volunteers)
        context = self.get_volunteers(context, volunteers)

        return context
