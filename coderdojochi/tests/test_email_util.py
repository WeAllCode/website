import json
import re
import tempfile
from datetime import timedelta
from http import HTTPStatus
from io import StringIO
from pathlib import Path
from unittest import mock

from anymail.message import AnymailMessage
from anymail.utils import UNSET
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from coderdojochi.models import EmailSuppression
from coderdojochi.models import Location
from coderdojochi.models import Meeting
from coderdojochi.models import MeetingType
from coderdojochi.models import Mentor
from coderdojochi.util import email
from coderdojochi.util import unsubscribe_email_from_token
from coderdojochi.util import unsubscribe_token

TEMPLATE = "class_reminder_guardian_one_week"
DAILY_LIMIT = 90


def _is_unset(value):
    return value is UNSET or not value


def _has_asm(message):
    esp_extra = getattr(message, "esp_extra", None)
    return isinstance(esp_extra, dict) and "asm" in esp_extra


def _unsubscribe_path(address):
    return reverse("email-unsubscribe", kwargs={"token": unsubscribe_token(address)})


class EmailTest(TestCase):
    def setUp(self):
        self.enterContext(mock.patch("coderdojochi.util.time.sleep"))

    def test_one_message_per_recipient_with_own_merge_data(self):
        email(
            subject="Reminder",
            template_name=TEMPLATE,
            recipients=["ada@example.com", "grace@example.com"],
            merge_data={
                "ada@example.com": {"first_name": "Ada"},
                "grace@example.com": {"first_name": "Grace"},
            },
            merge_global_data={"class_title": "Intro to Python"},
            unsub_group_id=1234,
        )

        first, second = mail.outbox
        assert first.to == ["ada@example.com"]
        assert "Ada" in first.body
        assert "Grace" not in first.body
        assert "Grace" in second.body
        assert "Ada" not in second.body
        assert "Intro to Python" in first.body
        for message in mail.outbox:
            assert "*|" not in message.body
            assert not _has_asm(message)
            assert "asm_global_unsubscribe" not in message.body
            assert _is_unset(getattr(message, "merge_data", None))
            assert _is_unset(getattr(message, "merge_global_data", None))

    def test_leftover_tags_are_stripped(self):
        # The template also uses order_id, student_first_name and more, with no data.
        email(subject="Reminder", template_name=TEMPLATE, recipients=["a@example.com"])

        assert len(mail.outbox) == 1
        assert "*|" not in mail.outbox[0].body

    def test_mutable_default_is_not_changed(self):
        global_data = {"class_title": "Intro"}
        email(
            subject="Hi",
            template_name=TEMPLATE,
            recipients=["a@example.com"],
            merge_global_data=global_data,
        )
        assert global_data == {"class_title": "Intro"}

    def test_over_daily_limit_sends_nothing(self):
        recipients = [f"user{i}@example.com" for i in range(DAILY_LIMIT + 1)]

        with self.assertRaises(ValueError):  # noqa: PT027
            email(subject="Hi", template_name=TEMPLATE, recipients=recipients)

        assert mail.outbox == []

    def test_suppressed_recipient_is_skipped(self):
        EmailSuppression.objects.create(
            email="Gone@Example.com",
            reason=EmailSuppression.BOUNCE,
        )

        email(
            subject="Hi",
            template_name=TEMPLATE,
            recipients=["gone@example.com", "here@example.com"],
        )

        assert [m.to for m in mail.outbox] == [["here@example.com"]]

    def _send_both(self, address):
        for template in ("class_announcement_mentor", TEMPLATE):
            email(subject="Hi", template_name=template, recipients=[address])
        return [m.subject for m in mail.outbox]

    def test_group_unsubscribe_blocks_only_announcements(self):
        for reason in (
            EmailSuppression.GROUP_UNSUBSCRIBE,
            EmailSuppression.USER_UNSUBSCRIBE,
        ):
            mail.outbox = []
            EmailSuppression.objects.all().delete()
            EmailSuppression.objects.create(email="opt@example.com", reason=reason)

            self._send_both("opt@example.com")

            assert [m.to for m in mail.outbox] == [["opt@example.com"]]
            assert "*|" not in mail.outbox[0].body
            assert "Unsubscribe from these announcements" not in mail.outbox[0].body

    def test_bounce_blocks_all_mail(self):
        EmailSuppression.objects.create(
            email="bounce@example.com",
            reason=EmailSuppression.BOUNCE,
        )

        self._send_both("bounce@example.com")

        assert mail.outbox == []

    def test_suppression_counts_before_the_limit(self):
        recipients = [f"user{i}@example.com" for i in range(DAILY_LIMIT + 1)]
        EmailSuppression.objects.create(
            email="user0@example.com",
            reason=EmailSuppression.UNSUBSCRIBE,
        )

        email(subject="Hi", template_name=TEMPLATE, recipients=recipients)

        assert len(mail.outbox) == DAILY_LIMIT

    def test_announcement_has_per_recipient_unsubscribe_link(self):
        email(
            subject="New class",
            template_name="class_announcement_mentor",
            recipients=["ada@example.com"],
        )

        # The token embeds a timestamp (signing.dumps), so a token computed here
        # can differ from the one in the email by a second (#1621). Decode the
        # email's own link instead of comparing strings.
        body = mail.outbox[0].body
        prefix = "http://testserver" + reverse(
            "email-unsubscribe", kwargs={"token": "X"}
        )
        prefix = prefix.removesuffix("X/")
        match = re.search(re.escape(prefix) + r"([^/\s]+)/", body)
        assert match, f"no unsubscribe link in {body!r}"
        assert unsubscribe_email_from_token(match.group(1)) == "ada@example.com"

    def test_failed_send_is_reported_and_others_still_sent(self):
        real_send = AnymailMessage.send

        def flaky_send(message, *args, **kwargs):
            if message.to == ["bad@example.com"]:
                raise RuntimeError
            return real_send(message, *args, **kwargs)

        with (
            mock.patch.object(AnymailMessage, "send", flaky_send),
            mock.patch("coderdojochi.util.sentry_sdk.capture_exception") as capture,
            self.assertLogs("coderdojochi.util", level="ERROR") as logs,
        ):
            email(
                subject="Hi",
                template_name=TEMPLATE,
                recipients=["bad@example.com", "good@example.com"],
            )

        assert [m.to for m in mail.outbox] == [["good@example.com"]]
        capture.assert_called_once()
        assert any("not sent" in ln and "bad@example.com" in ln for ln in logs.output)

    @override_settings(EMAIL_BACKEND="anymail.backends.sendgrid.EmailBackend")
    def test_sendgrid_keeps_categories_and_asm(self):
        with mock.patch.object(AnymailMessage, "send", autospec=True) as send:
            email(
                subject="Hi",
                template_name=TEMPLATE,
                recipients=["a@example.com"],
                unsub_group_id=42,
            )

        message = send.call_args.args[0]
        assert message.esp_extra == {
            "categories": [TEMPLATE],
            "asm": {"group_id": 42},
        }


@override_settings(SECURE_SSL_REDIRECT=False)
class UnsubscribeViewTest(TestCase):
    def test_get_shows_confirm_without_unsubscribing(self):
        response = self.client.get(_unsubscribe_path("Ada@Example.com"))

        assert response.status_code == HTTPStatus.OK
        assert b"<form" in response.content
        assert not EmailSuppression.objects.exists()

    def test_post_with_valid_token_suppresses(self):
        url = _unsubscribe_path("Ada@Example.com")

        response = self.client.post(url)
        self.client.post(url)

        assert response.status_code == HTTPStatus.OK
        suppression = EmailSuppression.objects.get()
        assert suppression.email == "ada@example.com"
        assert suppression.reason == EmailSuppression.USER_UNSUBSCRIBE

    def test_bad_token_is_rejected(self):
        url = reverse("email-unsubscribe", kwargs={"token": "ada@example.com:forged"})

        assert self.client.get(url).status_code == HTTPStatus.BAD_REQUEST
        assert self.client.post(url).status_code == HTTPStatus.BAD_REQUEST
        assert not EmailSuppression.objects.exists()


class LoadSuppressionsTest(TestCase):
    def test_loads_lists_and_is_idempotent(self):
        data = {
            "unsubscribes": [{"email": "Un@Example.com"}, "un@example.com"],
            "bounces": ["bounce@example.com", {"email": "both@example.com"}],
            "spam_reports": [{"email": "both@example.com"}],
            "group_suppressions": {"123": ["group@example.com", "un@example.com"]},
        }
        tmp = self.enterContext(tempfile.TemporaryDirectory())
        path = Path(tmp) / "suppressions.json"
        path.write_text(json.dumps(data))

        out = StringIO()
        call_command("load_suppressions", str(path), stdout=out)

        rows = dict(EmailSuppression.objects.values_list("email", "reason"))
        assert rows == {
            "un@example.com": EmailSuppression.UNSUBSCRIBE,
            "bounce@example.com": EmailSuppression.BOUNCE,
            "both@example.com": EmailSuppression.SPAM_REPORT,
            "group@example.com": EmailSuppression.GROUP_UNSUBSCRIBE,
        }
        assert "4 created, 0 skipped" in out.getvalue()

        out = StringIO()
        call_command("load_suppressions", str(path), stdout=out)
        assert EmailSuppression.objects.count() == len(rows)
        assert "0 created, 4 skipped" in out.getvalue()


@override_settings(SECURE_SSL_REDIRECT=False)
class MeetingAnnounceTest(TestCase):
    def setUp(self):
        staff = get_user_model().objects.create_user(
            username="staff",
            email="staff@example.com",
            is_staff=True,
        )
        self.client.force_login(staff)
        start = timezone.now() + timedelta(days=7)
        self.meeting = Meeting.objects.create(
            meeting_type=MeetingType.objects.create(
                code="M",
                title="Mentor meeting",
                slug="mentor-meeting",
            ),
            location=Location.objects.create(
                name="HQ",
                address="1 Main",
                city="Chicago",
                state="IL",
                zip="60601",
            ),
            start_date=start,
            end_date=start + timedelta(hours=2),
        )
        self.url = reverse("meeting-announce", kwargs={"pk": self.meeting.pk})

    def test_announced_date_is_saved_before_sending(self):
        seen = []

        def fake_email(**kwargs):
            seen.append(Meeting.objects.get(pk=self.meeting.pk).announced_date)

        with mock.patch("coderdojochi.views.meetings.email", side_effect=fake_email):
            self.client.get(self.url)

        assert len(seen) == 1
        assert seen[0] is not None

    def test_refused_send_clears_announced_date(self):
        refuse = mock.patch(
            "coderdojochi.views.meetings.email",
            side_effect=ValueError("over limit"),
        )
        with refuse:
            self.client.get(self.url)

        self.meeting.refresh_from_db()
        assert self.meeting.announced_date is None

    @override_settings(EMAIL_DAILY_LIMIT=1)
    def test_over_limit_is_not_marked_announced(self):
        users = get_user_model().objects
        for name in ["ada", "grace", "gone"]:
            Mentor.objects.create(
                user=users.create_user(username=name, email=f"{name}@example.com"),
            )
        # Suppressed addresses don't count toward the limit.
        EmailSuppression.objects.create(
            email="gone@example.com",
            reason=EmailSuppression.BOUNCE,
        )

        response = self.client.get(self.url)

        self.meeting.refresh_from_db()
        assert self.meeting.announced_date is None
        assert mail.outbox == []
        notices = [str(m) for m in get_messages(response.wsgi_request)]
        assert notices == [
            "2 recipients exceeds the daily email limit of 1; nothing sent."
        ]
