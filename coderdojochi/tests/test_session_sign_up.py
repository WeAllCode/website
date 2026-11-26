from datetime import date
from datetime import timedelta

from django.contrib.messages import get_messages
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from coderdojochi.factories import CDCUserFactory
from coderdojochi.factories import MentorFactory
from coderdojochi.factories import SessionFactory
from coderdojochi.forms import StudentForm
from coderdojochi.models import Guardian
from coderdojochi.models import MentorOrder
from coderdojochi.models import Order
from coderdojochi.models import Student


@override_settings(SECURE_SSL_REDIRECT=False)
class MentorCancelCutoffTest(TestCase):
    # #843: mentors can't cancel within 24 hours of their arrival time.
    def setUp(self):
        self.mentor = MentorFactory(
            user=CDCUserFactory(role="mentor"),
            background_check=True,
        )

    def signed_up(self, hours_from_now, user=None):
        # mentor_start_date is an hour before start_date.
        start = timezone.now() + timedelta(hours=hours_from_now + 1)
        session = SessionFactory(start_date=start)
        order = MentorOrder.objects.create(mentor=self.mentor, session=session)
        self.client.force_login(user or self.mentor.user)
        return session, order

    def cancel(self, session):
        return self.client.post(reverse("session-sign-up", args=[session.pk]))

    def test_can_cancel_more_than_a_day_ahead(self):
        session, order = self.signed_up(hours_from_now=48)
        self.cancel(session)
        order.refresh_from_db()
        assert order.is_active is False

    def test_cannot_cancel_within_a_day(self):
        session, order = self.signed_up(hours_from_now=10)
        response = self.cancel(session)
        order.refresh_from_db()
        assert order.is_active is True
        assert any("24 hours" in str(m) for m in get_messages(response.wsgi_request))

    def test_cancel_page_hides_the_form_within_a_day(self):
        session, _ = self.signed_up(hours_from_now=10)
        response = self.client.get(reverse("session-sign-up", args=[session.pk]))
        assert response.context["too_late_to_cancel"] is True
        assert b"Yes, cancel" not in response.content

    def test_staff_can_cancel_within_a_day(self):
        self.mentor.user.is_staff = True
        self.mentor.user.save()
        session, order = self.signed_up(hours_from_now=10)
        self.cancel(session)
        order.refresh_from_db()
        assert order.is_active is False


@override_settings(SECURE_SSL_REDIRECT=False)
class GuardianCancelReasonTest(TestCase):
    # #930: record why a student cancelled.
    def setUp(self):
        user = CDCUserFactory(role="guardian")
        self.guardian = Guardian.objects.create(user=user)
        self.student = Student.objects.create(
            guardian=self.guardian,
            first_name="Kid",
            last_name="Tester",
            birthday=date(2015, 1, 1),
            gender="girl",
        )
        self.session = SessionFactory(start_date=timezone.now() + timedelta(days=7))
        self.order = Order.objects.create(
            guardian=self.guardian,
            session=self.session,
            student=self.student,
        )
        self.client.force_login(user)
        self.url = reverse(
            "session-sign-up",
            args=[self.session.pk, self.student.pk],
        )

    def test_reason_saved_on_cancel(self):
        self.client.post(self.url, {"cancel_reason": "  Sick this week  "})
        self.order.refresh_from_db()
        assert self.order.is_active is False
        assert self.order.cancel_reason == "Sick this week"

    def test_reason_optional(self):
        self.client.post(self.url)
        self.order.refresh_from_db()
        assert self.order.is_active is False
        assert self.order.cancel_reason == ""

    def test_cancel_page_has_reason_field(self):
        response = self.client.get(self.url)
        assert b'name="cancel_reason"' in response.content


class StudentPreferredNameTest(TestCase):
    # #1549: what the student likes to be called.
    def test_display_first_name(self):
        student = Student(first_name="Alexandra", preferred_name="Alex")
        assert student.display_first_name == "Alex"
        assert Student(first_name="Sam").display_first_name == "Sam"

    def test_form_field_is_optional(self):
        form = StudentForm()
        assert "preferred_name" in form.fields
        assert form.fields["preferred_name"].required is False
        names = list(form.fields)
        assert names.index("preferred_name") == names.index("last_name") + 1
