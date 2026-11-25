"""Email class reminders a week and a day before each session.

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
        fields["student_first_name"] = order.student.first_name
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


class Command(BaseCommand):
    help = "Email class reminders to guardians and mentors (a week and a day before)."

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
        dry_run = options["dry_run"]
        limit = options["limit"]
        if limit is None:
            limit = email_daily_limit() // 2
        now = timezone.now()
        sent = 0
        left = 0

        for kind, model, flag, window, template, subject, preheader in REMINDERS:
            for order in due(model, flag, window, now):
                if sent >= limit:
                    left += 1
                    continue
                recipient, fields = merge_fields(order)
                if dry_run:
                    self.stdout.write(
                        f"would send {kind} to {recipient} ({order.session})"
                    )
                    sent += 1
                    continue
                if not recipient or not claim(order, flag):
                    continue
                sent += 1
                try:
                    email(
                        subject=subject,
                        template_name=template,
                        merge_data={recipient: fields},
                        recipients=[recipient],
                        preheader=preheader,
                        unsub_group_id=settings.SENDGRID_UNSUB_CLASSANNOUNCE,
                    )
                except Exception:
                    # Already claimed, so it is not retried: one missed reminder beats a
                    # resend loop. Logged at ERROR, which reaches Sentry.
                    logger.exception("send_reminders: %s to %s failed", kind, recipient)

        verb = "would send" if dry_run else "sent"
        summary = f"send_reminders: {verb} {sent} reminder(s)"
        if left:
            summary += f"; {left} over the limit of {limit}, left for the next run"
            logger.warning(summary)
        self.stdout.write(summary)
