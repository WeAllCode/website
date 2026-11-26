"""Email class reminders a week and a day before each session.

Also sends the "how was your first class?" email to families (#811) and a birthday
email to volunteers (#762). Both are optional mail: the unsubscribe link stops them.

Run by wac-reminders.timer on the prod VM (10:00 and 14:00 America/Chicago). Each
order is claimed (its *_reminder_sent flag set) before its email goes out, so a rerun
or an overlapping run never sends the same reminder twice.
"""

import logging
from datetime import timedelta

import arrow
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from coderdojochi.models import Mentor
from coderdojochi.models import MentorOrder
from coderdojochi.models import Order
from coderdojochi.util import email
from coderdojochi.util import email_daily_limit

logger = logging.getLogger(__name__)

# Week reminders go out 2-7 days ahead, so a late sign-up doesn't get both on one day.
WEEK_WINDOW = (timedelta(days=2), timedelta(days=7))
# Day reminders go out 0-1 days ahead, never after the class has started.
DAY_WINDOW = (timedelta(0), timedelta(days=1))

# (kind, model, sent flag, window, template, subject, preheader). Day reminders go
# first, so they win when the per-run limit is reached.
REMINDERS = [
    (
        "guardian day",
        Order,
        "day_reminder_sent",
        DAY_WINDOW,
        "class_reminder_guardian_24_hour",
        "Your class is coming up!",
        "Your class is just hours away!",
    ),
    (
        "mentor day",
        MentorOrder,
        "day_reminder_sent",
        DAY_WINDOW,
        "class_reminder_mentor_24_hour",
        "Your We All Code class is tomorrow!",
        "The class is just a few hours away!",
    ),
    (
        "guardian week",
        Order,
        "week_reminder_sent",
        WEEK_WINDOW,
        "class_reminder_guardian_one_week",
        "Upcoming class reminder",
        "Your class is just a few days away!",
    ),
    (
        "mentor week",
        MentorOrder,
        "week_reminder_sent",
        WEEK_WINDOW,
        "class_reminder_mentor_one_week",
        "Your We All Code class is in less than a week!",
        "The class is just a few days away!",
    ),
]


# First-class emails go out at the first run at least this long after the class ends,
# and not at all once the class is more than FIRST_CLASS_MAX_AGE old.
FIRST_CLASS_DELAY = timedelta(minutes=20)
FIRST_CLASS_MAX_AGE = timedelta(days=2)
FIRST_CLASS_TEMPLATE = "first_class_guardian"
FIRST_CLASS_SUBJECT = "Thanks for coming to your first class!"
BIRTHDAY_TEMPLATE = "birthday_mentor"
BIRTHDAY_SUBJECT = "Happy birthday from We All Code!"


def _date(value):
    return arrow.get(value).to(settings.TIME_ZONE).format("dddd, MMMM D, YYYY")


def _time(value):
    return arrow.get(value).to(settings.TIME_ZONE).format("h:mma")


def _iso(value):
    return arrow.get(value).to(settings.TIME_ZONE).isoformat()


def _session_fields(session, start, end):
    return {
        "class_code": session.course.code,
        "class_title": session.course.title,
        "class_description": session.course.description,
        "class_start_date": _date(start),
        "class_start_time": _time(start),
        "class_end_date": _date(end),
        "class_end_time": _time(end),
        "class_location_name": session.location.name,
        "class_location_address": session.location.address,
        "class_location_city": session.location.city,
        "class_location_state": session.location.state,
        "class_location_zip": session.location.zip,
        "class_additional_info": session.additional_info,
        "class_url": f"{settings.SITE_URL}{session.get_absolute_url()}",
        "class_calendar_url": f"{settings.SITE_URL}{session.get_calendar_url()}",
        "microdata_start_date": _iso(session.start_date),
        "microdata_end_date": _iso(session.end_date),
        "online_video_link": session.online_video_link,
        "online_video_description": session.online_video_description,
    }


def merge_fields(order):
    """Return (recipient, merge data) for an Order or a MentorOrder."""
    session = order.session
    if isinstance(order, MentorOrder):
        person = order.mentor
        fields = _session_fields(
            session, session.mentor_start_date, session.mentor_end_date
        )
    else:
        person = order.guardian
        fields = _session_fields(session, session.start_date, session.end_date)
        fields["student_first_name"] = order.student.display_first_name
        fields["student_last_name"] = order.student.last_name
    fields["first_name"] = person.first_name
    fields["last_name"] = person.last_name
    fields["order_id"] = order.id
    return person.email, fields


def due(model, flag, window, now):
    """Active orders for active sessions starting inside `window`, not yet reminded."""
    if model is Order:
        people = {
            "guardian__is_active": True,
            "guardian__user__is_active": True,
            "student__is_active": True,
        }
        related = ("session__course", "session__location", "guardian__user", "student")
    else:
        people = {"mentor__is_active": True, "mentor__user__is_active": True}
        related = ("session__course", "session__location", "mentor__user")
    return (
        model.objects.filter(
            is_active=True,
            session__is_active=True,
            session__start_date__gt=now + window[0],
            session__start_date__lte=now + window[1],
            **{flag: False},
            **people,
        )
        .select_related(*related)
        .order_by("session__start_date", "id")
    )


def claim(order, flag):
    """Set the flag only if it is still unset; True means this run owns the reminder."""
    return bool(
        type(order).objects.filter(pk=order.pk, **{flag: False}).update(**{flag: True})
    )


def first_class_due(now):
    """Checked-in orders for a student's first attended class, ended FIRST_CLASS_DELAY ago."""
    candidates = (
        Order.objects.filter(
            is_active=True,
            check_in__isnull=False,
            first_class_email_sent=False,
            session__start_date__gt=now - FIRST_CLASS_MAX_AGE,
            session__start_date__lte=now,
            guardian__is_active=True,
            guardian__user__is_active=True,
            student__is_active=True,
        )
        .select_related(
            "session__course", "session__location", "guardian__user", "student"
        )
        .order_by("session__start_date", "id")
    )
    for order in candidates:
        if order.session.end_date + FIRST_CLASS_DELAY > now:
            continue
        earlier = Order.objects.filter(
            student=order.student,
            check_in__isnull=False,
            session__start_date__lt=order.session.start_date,
        )
        if not earlier.exists():
            yield order


def birthdays_due(today):
    """Active volunteers whose birthday is today and who haven't had this year's email.

    A Feb 29 birthday is celebrated on Feb 28 in other years.
    """
    days = [(today.month, today.day)]
    is_leap = today.year % 4 == 0 and (today.year % 100 != 0 or today.year % 400 == 0)
    if (today.month, today.day) == (2, 28) and not is_leap:
        days.append((2, 29))
    mentors = Mentor.objects.none()
    for month, day in days:
        mentors |= Mentor.objects.filter(birthday__month=month, birthday__day=day)
    return (
        mentors.filter(is_active=True, user__is_active=True)
        .exclude(birthday_email_year=today.year)
        .select_related("user")
        .order_by("id")
    )


def claim_birthday(mentor, year):
    return bool(
        Mentor.objects.filter(pk=mentor.pk)
        .exclude(birthday_email_year=year)
        .update(birthday_email_year=year)
    )


class Command(BaseCommand):
    help = (
        "Email class reminders (a week and a day before), first-class follow-ups"
        " and volunteer birthday emails."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List who would get a reminder; send nothing, change nothing.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help=(
                "Most emails to send this run (default: half of EMAIL_DAILY_LIMIT,"
                " since the timer runs twice a day). The rest wait for the next run."
            ),
        )

    def handle(self, *args, **options):
        self.dry_run = options["dry_run"]
        self.limit = options["limit"]
        if self.limit is None:
            self.limit = email_daily_limit() // 2
        self.sent = 0
        self.left = 0
        now = timezone.now()

        for kind, model, flag, window, template, subject, preheader in REMINDERS:
            for order in due(model, flag, window, now):
                recipient, fields = merge_fields(order)
                self.deliver(
                    kind,
                    recipient,
                    fields,
                    order.session,
                    claim=lambda order=order, flag=flag: claim(order, flag),
                    template=template,
                    subject=subject,
                    preheader=preheader,
                )

        for order in first_class_due(now):
            recipient, fields = merge_fields(order)
            self.deliver(
                "first class",
                recipient,
                fields,
                order.session,
                claim=lambda order=order: claim(order, "first_class_email_sent"),
                template=FIRST_CLASS_TEMPLATE,
                subject=FIRST_CLASS_SUBJECT,
                preheader="We hope your student had a great time!",
            )

        today = timezone.localdate(now)
        for mentor in birthdays_due(today):
            self.deliver(
                "birthday",
                mentor.email,
                {"first_name": mentor.first_name, "last_name": mentor.last_name},
                "birthday",
                claim=lambda mentor=mentor: claim_birthday(mentor, today.year),
                template=BIRTHDAY_TEMPLATE,
                subject=BIRTHDAY_SUBJECT,
                preheader="Thank you for everything you do.",
            )

        verb = "would send" if self.dry_run else "sent"
        summary = f"send_reminders: {verb} {self.sent} email(s)"
        if self.left:
            summary += (
                f"; {self.left} over the limit of {self.limit}, left for the next run"
            )
            logger.warning(summary)
        self.stdout.write(summary)

    def deliver(self, kind, recipient, fields, about, *, claim, **message):
        if self.sent >= self.limit:
            self.left += 1
            return
        if self.dry_run:
            self.stdout.write(f"would send {kind} to {recipient} ({about})")
            self.sent += 1
            return
        if not recipient or not claim():
            return
        self.sent += 1
        try:
            email(
                merge_data={recipient: fields},
                recipients=[recipient],
                unsub_group_id=settings.SENDGRID_UNSUB_CLASSANNOUNCE,
                template_name=message["template"],
                subject=message["subject"],
                preheader=message["preheader"],
            )
        except Exception:
            # Already claimed, so it is not retried: one missed email beats a resend
            # loop. Logged at ERROR, which reaches Sentry.
            logger.exception("send_reminders: %s to %s failed", kind, recipient)
