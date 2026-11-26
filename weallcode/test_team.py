from datetime import timedelta

from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from coderdojochi.factories import CDCUserFactory
from coderdojochi.factories import MentorFactory
from coderdojochi.factories import SessionFactory
from coderdojochi.models import MentorOrder


@override_settings(SECURE_SSL_REDIRECT=False)
class TeamPageVolunteersTest(TestCase):
    def mentor(self, first_name):
        return MentorFactory(
            user=CDCUserFactory(first_name=first_name, last_name="Tester"),
            is_public=True,
            background_check=True,
            avatar_approved=True,
        )

    def classes(self, mentor, n, *, days_ago=30, checked_in=True):
        for _ in range(n):
            session = SessionFactory(
                start_date=timezone.now() - timedelta(days=days_ago)
            )
            MentorOrder.objects.create(
                mentor=mentor,
                session=session,
                check_in=timezone.now() if checked_in else None,
            )

    def listed(self):
        ctx = self.client.get(reverse("weallcode-team")).context
        people = ctx["top_mentors"] + ctx["top_volunteers"] + ctx["other_volunteers"]
        return {m.user.first_name: m.session_count for m in people}

    def test_counts_checked_in_classes_only(self):
        # #688: sign-ups without a check-in aren't classes taught.
        ada = self.mentor("Ada")
        self.classes(ada, 3)
        self.classes(ada, 4, checked_in=False)
        assert self.listed() == {"Ada": 3}

    def test_only_recently_active_volunteers(self):
        # #876: 3+ classes taught in the last 2 years.
        recent = self.mentor("Recent")
        self.classes(recent, 3)
        too_few = self.mentor("Few")
        self.classes(too_few, 2)
        lapsed = self.mentor("Lapsed")
        self.classes(lapsed, 12, days_ago=3 * 365)
        self.classes(lapsed, 2)
        assert self.listed() == {"Recent": 3}

    def test_lifetime_count_shown_for_recent_volunteers(self):
        veteran = self.mentor("Veteran")
        self.classes(veteran, 10, days_ago=3 * 365)
        self.classes(veteran, 3)
        assert self.listed() == {"Veteran": 13}

    def test_window_ends_at_last_class_held(self):
        # The 2 years count back from the last class held, not from today.
        quiet = self.mentor("Quiet")
        self.classes(quiet, 3, days_ago=2 * 365 + 200)  # 2.5 years ago
        early = self.mentor("Early")
        self.classes(early, 3, days_ago=5 * 365)  # 5 years ago
        # The last class held: 1 year ago, taught by someone else.
        self.classes(self.mentor("Last"), 1, days_ago=365)
        assert self.listed() == {"Quiet": 3}
