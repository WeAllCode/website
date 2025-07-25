from datetime import timedelta

import arrow
from django.conf import settings
from django.utils import timezone
from django_cron import (
    CronJobBase,
    Schedule,
)

from coderdojochi.models import (
    MentorOrder,
    Order,
    Session,
)
from coderdojochi.util import email


class SendReminders(CronJobBase):
    RUN_AT_TIMES = ["10:00", "14:00"]

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = "coderdojochi.send_reminders"

    def do(self):
        orders_within_a_week = Order.objects.filter(
            is_active=True,
            week_reminder_sent=False,
            session__start_date__lte=(timezone.now() + timedelta(days=7)),
            session__start_date__gte=(timezone.now() + timedelta(days=1)),
        )
        orders_within_a_day = Order.objects.filter(
            is_active=True,
            day_reminder_sent=False,
            session__start_date__lte=(timezone.now() + timedelta(days=1)),
            session__start_date__gte=(timezone.now() - timedelta(days=2)),
        )
        sessions_within_a_week = Session.objects.filter(
            is_active=True,
            mentors_week_reminder_sent=False,
            start_date__lte=(timezone.now() + timedelta(days=7)),
            start_date__gte=(timezone.now() + timedelta(days=1)),
        )
        sessions_within_a_day = Session.objects.filter(
            is_active=True,
            mentors_day_reminder_sent=False,
            start_date__lte=(timezone.now() + timedelta(days=1)),
            start_date__gte=(timezone.now() - timedelta(days=2)),
        )

        # Clear email send data
        merge_data = {}
        recipients = []

        for order in orders_within_a_week:
            recipients.append(order.guardian.email)
            merge_data[order.guardian.email] = {
                "first_name": order.guardian.first_name,
                "last_name": order.guardian.last_name,
                "student_first_name": order.student.first_name,
                "student_last_name": order.student.last_name,
                "class_code": order.session.course.code,
                "class_title": order.session.course.title,
                "class_description": order.session.course.description,
                "class_start_date": (
                    arrow.get(order.session.start_date)
                    .to("local")
                    .format("dddd, MMMM D, YYYY")
                ),
                "class_start_time": (
                    arrow.get(order.session.start_date)
                    .to("local")
                    .format("h:mma")
                ),
                "class_end_date": (
                    arrow.get(order.session.end_date)
                    .to("local")
                    .format("dddd, MMMM D, YYYY")
                ),
                "class_end_time": (
                    arrow.get(order.session.end_date)
                    .to("local")
                    .format("h:mma")
                ),
                "class_location_name": order.session.location.name,
                "class_location_address": order.session.location.address,
                "class_location_city": order.session.location.city,
                "class_location_state": order.session.location.state,
                "class_location_zip": order.session.location.zip,
                "class_additional_info": order.session.additional_info,
                "class_url": (
                    f"{settings.SITE_URL}{order.session.get_absolute_url()}"
                ),
                "class_calendar_url": (
                    f"{settings.SITE_URL}{order.session.get_calendar_url()}"
                ),
                "microdata_start_date": (
                    arrow.get(order.session.start_date).to("local").isoformat()
                ),
                "microdata_end_date": (
                    arrow.get(order.session.end_date).to("local").isoformat()
                ),
                "order_id": order.id,
                "online_video_link": order.session.online_video_link,
                "online_video_description": (
                    order.session.online_video_description
                ),
            }

        email(
            subject="Upcoming class reminder",
            template_name="class_reminder_guardian_one_week",
            merge_data=merge_data,
            recipients=recipients,
            preheader="Your class is just a few days away!",
            unsub_group_id=settings.SENDGRID_UNSUB_CLASSANNOUNCE,
        )

        for order in orders_within_a_week:
            order.week_reminder_sent = True
            order.save()

        # Clear email send data
        merge_data = {}
        recipients = []

        for order in orders_within_a_day:
            recipients.append(order.guardian.email)
            merge_data[order.guardian.email] = {
                "first_name": order.guardian.first_name,
                "last_name": order.guardian.last_name,
                "student_first_name": order.student.first_name,
                "student_last_name": order.student.last_name,
                "class_code": order.session.course.code,
                "class_title": order.session.course.title,
                "class_description": order.session.course.description,
                "class_start_date": (
                    arrow.get(order.session.start_date)
                    .to("local")
                    .format("dddd, MMMM D, YYYY")
                ),
                "class_start_time": (
                    arrow.get(order.session.start_date)
                    .to("local")
                    .format("h:mma")
                ),
                "class_end_date": (
                    arrow.get(order.session.end_date)
                    .to("local")
                    .format("dddd, MMMM D, YYYY")
                ),
                "class_end_time": (
                    arrow.get(order.session.end_date)
                    .to("local")
                    .format("h:mma")
                ),
                "class_location_name": order.session.location.name,
                "class_location_address": order.session.location.address,
                "class_location_city": order.session.location.city,
                "class_location_state": order.session.location.state,
                "class_location_zip": order.session.location.zip,
                "class_additional_info": order.session.additional_info,
                "class_url": (
                    f"{settings.SITE_URL}{order.session.get_absolute_url()}"
                ),
                "class_calendar_url": (
                    f"{settings.SITE_URL}{order.session.get_calendar_url()}"
                ),
                "microdata_start_date": (
                    arrow.get(order.session.start_date).to("local").isoformat()
                ),
                "microdata_end_date": (
                    arrow.get(order.session.end_date).to("local").isoformat()
                ),
                "order_id": order.id,
                "online_video_link": order.session.online_video_link,
                "online_video_description": (
                    order.session.online_video_description
                ),
            }

        email(
            subject="Your class is coming up!",
            template_name="class_reminder_guardian_24_hour",
            merge_data=merge_data,
            recipients=recipients,
            preheader="Your class is just hours away!",
            unsub_group_id=settings.SENDGRID_UNSUB_CLASSANNOUNCE,
        )

        for order in orders_within_a_day:
            order.day_reminder_sent = True
            order.save()

        for session in sessions_within_a_week:
            orders = MentorOrder.objects.filter(session=session)

            # Clear email send data
            merge_data = {}
            recipients = []

            for order in orders:
                recipients.append(order.mentor.email)
                merge_data[order.mentor.email] = {
                    "first_name": order.mentor.first_name,
                    "last_name": order.mentor.last_name,
                    "class_code": order.session.course.code,
                    "class_title": order.session.course.title,
                    "class_description": order.session.course.description,
                    "class_start_date": (
                        arrow.get(order.session.mentor_start_date)
                        .to("local")
                        .format("dddd, MMMM D, YYYY")
                    ),
                    "class_start_time": (
                        arrow.get(order.session.mentor_start_date)
                        .to("local")
                        .format("h:mma")
                    ),
                    "class_end_date": (
                        arrow.get(order.session.mentor_end_date)
                        .to("local")
                        .format("dddd, MMMM D, YYYY")
                    ),
                    "class_end_time": (
                        arrow.get(order.session.mentor_end_date)
                        .to("local")
                        .format("h:mma")
                    ),
                    "class_location_name": order.session.location.name,
                    "class_location_address": order.session.location.address,
                    "class_location_city": order.session.location.city,
                    "class_location_state": order.session.location.state,
                    "class_location_zip": order.session.location.zip,
                    "class_additional_info": order.session.additional_info,
                    "class_url": f"{settings.SITE_URL}{order.session.get_absolute_url()}",
                    "class_calendar_url": f"{settings.SITE_URL}{order.session.get_calendar_url()}",
                    "microdata_start_date": (
                        arrow.get(order.session.start_date)
                        .to("local")
                        .isoformat()
                    ),
                    "microdata_end_date": (
                        arrow.get(order.session.end_date)
                        .to("local")
                        .isoformat()
                    ),
                    "order_id": order.id,
                    "online_video_link": order.session.online_video_link,
                    "online_video_description": (
                        order.session.online_video_description
                    ),
                }

            email(
                subject="Your We All Code class is in less than a week!",
                template_name="class_reminder_mentor_one_week",
                merge_data=merge_data,
                recipients=recipients,
                preheader="The class is just a few days away!",
                unsub_group_id=settings.SENDGRID_UNSUB_CLASSANNOUNCE,
            )

            session.mentors_week_reminder_sent = True
            session.save()

        for session in sessions_within_a_day:
            orders = MentorOrder.objects.filter(session=session)

            for order in orders:
                recipients.append(order.mentor.email)
                merge_data[order.mentor.email] = {
                    "first_name": order.mentor.user.first_name,
                    "last_name": order.mentor.user.last_name,
                    "class_code": order.session.course.code,
                    "class_title": order.session.course.title,
                    "class_description": order.session.course.description,
                    "class_start_date": (
                        arrow.get(order.session.mentor_start_date)
                        .to("local")
                        .format("dddd, MMMM D, YYYY")
                    ),
                    "class_start_time": (
                        arrow.get(order.session.mentor_start_date)
                        .to("local")
                        .format("h:mma")
                    ),
                    "class_end_date": (
                        arrow.get(order.session.mentor_end_date)
                        .to("local")
                        .format("dddd, MMMM D, YYYY")
                    ),
                    "class_end_time": (
                        arrow.get(order.session.mentor_end_date)
                        .to("local")
                        .format("h:mma")
                    ),
                    "class_location_name": order.session.location.name,
                    "class_location_address": order.session.location.address,
                    "class_location_city": order.session.location.city,
                    "class_location_state": order.session.location.state,
                    "class_location_zip": order.session.location.zip,
                    "class_additional_info": order.session.additional_info,
                    "class_url": f"{settings.SITE_URL}{order.session.get_absolute_url()}",
                    "class_calendar_url": f"{settings.SITE_URL}{order.session.get_calendar_url()}",
                    "microdata_start_date": (
                        arrow.get(order.session.start_date)
                        .to("local")
                        .isoformat()
                    ),
                    "microdata_end_date": (
                        arrow.get(order.session.end_date)
                        .to("local")
                        .isoformat()
                    ),
                    "order_id": order.id,
                    "online_video_link": order.session.online_video_link,
                    "online_video_description": (
                        order.session.online_video_description
                    ),
                }

            email(
                subject="Your We All Code class is tomorrow!",
                template_name="class_reminder_mentor_24_hour",
                merge_data=merge_data,
                recipients=recipients,
                preheader="The class is just a few hours away!",
                unsub_group_id=settings.SENDGRID_UNSUB_CLASSANNOUNCE,
            )

            session.mentors_day_reminder_sent = True
            session.save()
