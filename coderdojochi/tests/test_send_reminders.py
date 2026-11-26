from datetime import date
from datetime import timedelta
from io import StringIO
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.test import override_settings
from django.utils import timezone

from coderdojochi import util
from coderdojochi.management.commands.send_reminders import birthdays_due
from coderdojochi.models import Course
from coderdojochi.models import EmailSuppression
from coderdojochi.models import Guardian
from coderdojochi.models import Location
from coderdojochi.models import Mentor
from coderdojochi.models import MentorOrder
from coderdojochi.models import Order
from coderdojochi.models import Session
from coderdojochi.models import Student

GUARDIAN_WEEK = "Upcoming class reminder"
GUARDIAN_DAY = "Your class is coming up!"
MENTOR_WEEK = "Your We All Code class is in less than a week!"
MENTOR_DAY = "Your We All Code class is tomorrow!"
FIRST_CLASS = "Thanks for coming to your first class!"
BIRTHDAY = "Happy birthday from We All Code!"


def run(*args):
    out = StringIO()
    call_command("send_reminders", *args, stdout=out)
    return out.getvalue()


def sent():
    """(recipient, subject) for every message in the outbox, sorted."""
    return sorted((m.to[0], m.subject) for m in mail.outbox)


@override_settings(EMAIL_DAILY_LIMIT=90)
class SendRemindersTest(TestCase):
    def setUp(self):
        self.enterContext(mock.patch("coderdojochi.util.time.sleep"))
        self.users = get_user_model().objects
        self.course = Course.objects.create(
            code="PY",
            title="Intro to Python",
            slug="intro-to-python",
            duration=timedelta(hours=3),
        )
        self.location = Location.objects.create(
            name="HQ",
            address="1 Main",
            city="Chicago",
            state="IL",
            zip="60601",
        )
        self.instructor = self.mentor("instructor")

    def user(self, name):
        return self.users.create_user(
            username=name,
            email=f"{name}@example.com",
            first_name=name.title(),
            last_name="Tester",
        )

    def mentor(self, name):
        return Mentor.objects.create(user=self.user(name))

    def session(self, starts_in, *, is_active=True):
        return Session.objects.create(
            course=self.course,
            location=self.location,
            instructor=self.instructor,
            start_date=timezone.now() + starts_in,
            is_active=is_active,
        )

    def enroll(self, session, guardian_name, student_name="Kid", **kwargs):
        guardian = Guardian.objects.filter(user__username=guardian_name).first()
        if guardian is None:
            guardian = Guardian.objects.create(user=self.user(guardian_name))
        student = Student.objects.create(
            guardian=guardian,
            first_name=student_name,
            last_name="Tester",
            birthday=date(2015, 1, 1),
            gender="other",
        )
        return Order.objects.create(
            guardian=guardian,
            session=session,
            student=student,
            **kwargs,
        )

    def sign_up(self, session, mentor, **kwargs):
        return MentorOrder.objects.create(mentor=mentor, session=session, **kwargs)

    def test_tests_cannot_send_real_email(self):
        # Django's test runner swaps in the in-memory backend; nothing leaves the box.
        assert settings.EMAIL_BACKEND == "django.core.mail.backends.locmem.EmailBackend"
        assert not settings.ANYMAIL.get("RESEND_API_KEY")

    def test_week_and_day_reminders_go_to_the_right_people(self):
        week = self.session(timedelta(days=5))
        day = self.session(timedelta(hours=20))
        self.enroll(week, "wendy")
        self.enroll(day, "dana")
        self.sign_up(week, self.mentor("mwen"))
        self.sign_up(day, self.mentor("mday"))

        run()

        assert sent() == [
            ("dana@example.com", GUARDIAN_DAY),
            ("mday@example.com", MENTOR_DAY),
            ("mwen@example.com", MENTOR_WEEK),
            ("wendy@example.com", GUARDIAN_WEEK),
        ]

    def test_running_twice_sends_once(self):
        session = self.session(timedelta(days=5))
        order = self.enroll(session, "wendy")
        mentor_order = self.sign_up(session, self.mentor("mwen"))

        run()
        run()

        assert sent() == [
            ("mwen@example.com", MENTOR_WEEK),
            ("wendy@example.com", GUARDIAN_WEEK),
        ]
        order.refresh_from_db()
        mentor_order.refresh_from_db()
        assert order.week_reminder_sent
        assert mentor_order.week_reminder_sent
        assert not order.day_reminder_sent

    def test_week_then_day_as_the_class_gets_closer(self):
        session = self.session(timedelta(days=5))
        self.enroll(session, "wendy")
        run()

        session.start_date = timezone.now() + timedelta(hours=20)
        session.save()
        run()

        assert [m.subject for m in mail.outbox] == [GUARDIAN_WEEK, GUARDIAN_DAY]

    def test_nothing_due_is_not_an_error(self):
        assert "sent 0 email(s)" in run()
        assert mail.outbox == []

    def test_skips_past_far_off_and_inactive(self):
        past = self.session(-timedelta(hours=2))
        far = self.session(timedelta(days=10))
        hidden = self.session(timedelta(days=5), is_active=False)
        live = self.session(timedelta(days=5))
        for session in [past, far, hidden]:
            self.enroll(session, f"g{session.pk}")
            self.sign_up(session, self.mentor(f"m{session.pk}"))
        self.enroll(live, "cancelled", is_active=False)
        self.sign_up(live, self.mentor("dropped"), is_active=False)
        self.sign_up(live, self.mentor("gone"))
        self.users.filter(username="gone").update(is_active=False)

        run()

        assert mail.outbox == []

    def test_two_kids_get_two_emails_with_their_own_names(self):
        session = self.session(timedelta(days=5))
        self.enroll(session, "pat", student_name="Ada")
        self.enroll(session, "pat", student_name="Grace")

        run()

        bodies = [m.body for m in mail.outbox]
        assert [m.to[0] for m in mail.outbox] == ["pat@example.com"] * 2
        assert any("Ada" in b and "Grace" not in b for b in bodies)
        assert any("Grace" in b and "Ada" not in b for b in bodies)

    def test_mentor_lists_stay_separate(self):
        week = self.session(timedelta(days=5))
        day = self.session(timedelta(hours=20))
        self.sign_up(week, self.mentor("mwen"))
        self.sign_up(day, self.mentor("mday"))

        run()

        assert sent() == [
            ("mday@example.com", MENTOR_DAY),
            ("mwen@example.com", MENTOR_WEEK),
        ]

    def test_mentor_who_signs_up_late_still_gets_one(self):
        session = self.session(timedelta(days=5))
        self.sign_up(session, self.mentor("early"))
        run()
        self.sign_up(session, self.mentor("late"))
        run()

        assert sent() == [
            ("early@example.com", MENTOR_WEEK),
            ("late@example.com", MENTOR_WEEK),
        ]

    def test_limit_leaves_the_rest_for_the_next_run(self):
        session = self.session(timedelta(hours=20))
        for name in ["a1", "a2", "a3"]:
            self.enroll(session, name)

        out = run("--limit", "2")
        assert [m.to[0] for m in mail.outbox] == ["a1@example.com", "a2@example.com"]
        assert "1 over the limit of 2" in out

        assert "sent 1 email(s)" in run("--limit", "2")
        assert mail.outbox[-1].to == ["a3@example.com"]

    @override_settings(EMAIL_DAILY_LIMIT=4)
    def test_default_limit_is_half_the_daily_limit(self):
        session = self.session(timedelta(hours=20))
        for name in ["a1", "a2", "a3"]:
            self.enroll(session, name)

        run()

        assert [m.to[0] for m in mail.outbox] == ["a1@example.com", "a2@example.com"]

    def test_dry_run_sends_and_changes_nothing(self):
        session = self.session(timedelta(days=5))
        order = self.enroll(session, "wendy")

        out = run("--dry-run")

        assert "would send guardian week to wendy@example.com" in out
        assert mail.outbox == []
        order.refresh_from_db()
        assert not order.week_reminder_sent

    def test_suppressed_address_is_marked_and_not_sent(self):
        session = self.session(timedelta(days=5))
        order = self.enroll(session, "wendy")
        EmailSuppression.objects.create(
            email="wendy@example.com",
            reason=EmailSuppression.BOUNCE,
        )

        run()

        assert mail.outbox == []
        order.refresh_from_db()
        assert order.week_reminder_sent

    def test_failed_send_does_not_stop_the_run(self):
        session = self.session(timedelta(days=5))
        self.enroll(session, "a1")
        self.enroll(session, "a2")
        calls = []

        def flaky(**kwargs):
            calls.append(kwargs["recipients"][0])
            if len(calls) == 1:
                message = "boom"
                raise RuntimeError(message)
            return util.email(**kwargs)

        patch = mock.patch(
            "coderdojochi.management.commands.send_reminders.email",
            side_effect=flaky,
        )
        with patch, self.assertLogs("coderdojochi.management", "ERROR"):
            run()

        assert calls == ["a1@example.com", "a2@example.com"]
        assert [m.to[0] for m in mail.outbox] == ["a2@example.com"]
        # The failed one was claimed, so it is not retried.
        assert not Order.objects.filter(week_reminder_sent=False).exists()

    def test_merge_fields_fill_the_template(self):
        session = self.session(timedelta(days=5))
        self.enroll(session, "wendy", student_name="Ada")

        run()

        body = mail.outbox[0].body
        assert "Wendy" in body
        assert "Intro to Python" in body
        assert "*|" not in body

    # #811: one "how was your first class?" email per student, after the class ends.
    def attended(self, starts_in, guardian="pat", student="Ada"):
        session = self.session(starts_in)
        order = self.enroll(session, guardian, student_name=student)
        order.check_in = session.start_date
        order.save()
        return order

    def first_class_emails(self):
        return [m for m in mail.outbox if m.subject == FIRST_CLASS]

    def test_first_class_email_after_class_ends(self):
        # The course runs 3 hours, so a class that started 4 hours ago has ended.
        self.attended(-timedelta(hours=4))

        run()
        run()

        emails = self.first_class_emails()
        assert [m.to[0] for m in emails] == ["pat@example.com"]
        assert "Ada" in emails[0].body
        assert "*|" not in emails[0].body
        assert "/unsubscribe/" in emails[0].body

    def test_no_first_class_email_while_class_is_running(self):
        self.attended(-timedelta(hours=1))
        run()
        assert self.first_class_emails() == []

    def test_no_first_class_email_for_a_returning_student(self):
        first = self.attended(-timedelta(days=30))
        later = self.session(-timedelta(hours=4))
        Order.objects.create(
            guardian=first.guardian,
            session=later,
            student=first.student,
            check_in=later.start_date,
        )
        run()
        assert self.first_class_emails() == []

    def test_cancelled_earlier_order_does_not_count(self):
        # A cancelled order that still has a check-in time isn't an attended class.
        cancelled = self.attended(-timedelta(days=30))
        cancelled.is_active = False
        cancelled.save()
        later = self.session(-timedelta(hours=4))
        Order.objects.create(
            guardian=cancelled.guardian,
            session=later,
            student=cancelled.student,
            check_in=later.start_date,
        )
        run()
        assert [m.to[0] for m in self.first_class_emails()] == ["pat@example.com"]

    def test_no_first_class_email_without_check_in(self):
        self.enroll(self.session(-timedelta(hours=4)), "pat")
        run()
        assert self.first_class_emails() == []

    def test_first_class_email_honors_unsubscribe(self):
        self.attended(-timedelta(hours=4))
        EmailSuppression.objects.create(
            email="pat@example.com",
            reason=EmailSuppression.USER_UNSUBSCRIBE,
        )
        run()
        assert self.first_class_emails() == []

    # #762: a birthday email to volunteers, once a year.
    def test_birthday_email_to_volunteer_once(self):
        today = timezone.localdate()
        mentor = self.mentor("bday")
        mentor.birthday = today.replace(year=1990)
        mentor.save()
        other = self.mentor("notyet")
        other.birthday = today.replace(year=1990) + timedelta(days=1)
        other.save()

        run()
        run()

        assert [m.to[0] for m in mail.outbox if m.subject == BIRTHDAY] == [
            "bday@example.com",
        ]
        mentor.refresh_from_db()
        assert mentor.birthday_email_year == today.year

    def test_birthday_email_honors_unsubscribe(self):
        mentor = self.mentor("bday")
        mentor.birthday = timezone.localdate().replace(year=1990)
        mentor.save()
        EmailSuppression.objects.create(
            email="bday@example.com",
            reason=EmailSuppression.USER_UNSUBSCRIBE,
        )
        run()
        assert mail.outbox == []

    def test_feb_29_birthday_on_feb_28_in_other_years(self):
        mentor = self.mentor("leap")
        mentor.birthday = date(2000, 2, 29)
        mentor.save()
        assert list(birthdays_due(date(2027, 2, 28))) == [mentor]
        assert list(birthdays_due(date(2028, 2, 28))) == []
        assert list(birthdays_due(date(2028, 2, 29))) == [mentor]
