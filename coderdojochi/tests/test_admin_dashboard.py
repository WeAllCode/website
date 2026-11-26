from datetime import date

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from coderdojochi.factories import MentorFactory
from coderdojochi.factories import SessionFactory
from coderdojochi.models import Guardian
from coderdojochi.models import MentorOrder
from coderdojochi.models import Order
from coderdojochi.models import Student


@override_settings(SECURE_SSL_REDIRECT=False)
class AdminDashboardTest(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_user(
            username="staff",
            email="staff@example.com",
            is_staff=True,
        )
        self.guardian = Guardian.objects.create(
            user=get_user_model().objects.create_user(username="guardian"),
        )
        self.n = 0

    def add_session(self, *, students=(), mentors_checked_in=0, mentors_not=0):
        session = SessionFactory()
        for birthday, gender, checked_in in students:
            self.n += 1
            student = Student.objects.create(
                guardian=self.guardian,
                first_name=f"Kid{self.n}",
                last_name="Tester",
                birthday=birthday,
                gender=gender,
            )
            Order.objects.create(
                guardian=self.guardian,
                session=session,
                student=student,
                check_in=timezone.now() if checked_in else None,
            )
        for checked_in in [True] * mentors_checked_in + [False] * mentors_not:
            MentorOrder.objects.create(
                mentor=MentorFactory(),
                session=session,
                check_in=timezone.now() if checked_in else None,
            )
        return session

    def get(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("cdc-admin"))
        assert response.status_code == 200
        return response

    def test_no_checked_in_orders(self):
        # Sentry PRODUCTION-43J: ZeroDivisionError averaging an empty age list.
        response = self.get()
        assert response.context["average_age"] == 0

    def test_stats_and_mentor_counts(self):
        start = SessionFactory.build().start_date
        age_10 = date(start.year - 10, 1, 1)
        age_12 = date(start.year - 12, 1, 1)
        session = self.add_session(
            students=[
                (age_10, "Boy", True),
                (age_10, "F", True),
                (age_12, "girl", True),
                (age_12, "nonbinary", False),
            ],
            mentors_checked_in=2,
            mentors_not=1,
        )
        response = self.get()
        ctx = response.context
        assert ctx["total_past_orders_count"] == 4
        assert ctx["total_checked_in_orders_count"] == 3
        assert sorted(ctx["gender_count"]) == [("female", 2), ("male", 1)]
        assert ctx["age_count"] == [(10, 2), (12, 1)]
        assert ctx["average_age"] == 11
        row = next(s for s in ctx["sessions"] if s.pk == session.pk)
        assert (row.num_orders, row.num_attended) == (4, 3)
        assert (row.num_mentor_orders, row.num_mentor_attended) == (3, 2)

    def test_query_count_does_not_grow_with_sessions(self):
        kid = [(date(2015, 1, 1), "girl", True)]
        self.add_session(students=kid, mentors_checked_in=1, mentors_not=1)
        self.get()  # warm-up: the first request after login updates last_login
        with CaptureQueriesContext(connection) as one:
            self.get()
        for _ in range(4):
            self.add_session(students=kid, mentors_checked_in=1, mentors_not=1)
        with CaptureQueriesContext(connection) as five:
            self.get()
        assert len(five) == len(one), (len(one), len(five))
