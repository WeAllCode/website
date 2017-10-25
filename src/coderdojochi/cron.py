# -*- coding: utf-8 -*-

import arrow
import datetime

# from django.conf import settings
from django.core.mail import get_connection
from django.utils import timezone
from django_cron import CronJobBase, Schedule

from coderdojochi.models import (
    MentorOrder,
    Order,
    Session
)
from coderdojochi.util import email


class SendReminders(CronJobBase):
    RUN_AT_TIMES = ['10:00', '14:00']

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'coderdojochi.send_reminders'

    def do(self):
        orders_within_a_week = Order.objects.filter(
            is_active=True,
            week_reminder_sent=False,
            session__start_date__lte=(
                timezone.now() + datetime.timedelta(days=7)
            ),
            session__start_date__gte=(
                timezone.now() + datetime.timedelta(days=1)
            ),
        )
        orders_within_a_day = Order.objects.filter(
            is_active=True,
            day_reminder_sent=False,
            session__start_date__lte=(
                timezone.now() + datetime.timedelta(days=1)
            ),
            session__start_date__gte=(
                timezone.now() - datetime.timedelta(days=2)
            ),
        )
        sessions_within_a_week = Session.objects.filter(
            is_active=True,
            mentors_week_reminder_sent=False,
            start_date__lte=timezone.now() + datetime.timedelta(days=7),
            start_date__gte=timezone.now() + datetime.timedelta(days=1)
        )
        sessions_within_a_day = Session.objects.filter(
            is_active=True,
            mentors_day_reminder_sent=False,
            start_date__lte=timezone.now() + datetime.timedelta(days=1),
            start_date__gte=timezone.now() - datetime.timedelta(days=2)
        )

        # uses SMTP server specified in settings.py
        connection = get_connection()

        # If you don't open the connection manually,
        # Django will automatically open, then tear down the connection
        # in msg.send()
        connection.open()

        for order in orders_within_a_week:
            email(
                subject='Upcoming class reminder',
                template_name='class-reminder-guardian-one-week',
                context={
                    'first_name': order.guardian.user.first_name,
                    'last_name': order.guardian.user.last_name,
                    'student_first_name': order.student.first_name,
                    'student_last_name': order.student.last_name,
                    'class_code': order.session.course.code,
                    'class_title': order.session.course.title,
                    'class_description': order.session.course.description,
                    'class_start_date': arrow.get(
                        order.session.start_date
                    ).to('local').format('dddd, MMMM D, YYYY'),
                    'class_start_time': arrow.get(
                        order.session.start_date
                    ).to('local').format('h:mma'),
                    'class_end_date': arrow.get(
                        order.session.end_date
                    ).to('local').format('dddd, MMMM D, YYYY'),
                    'class_end_time': arrow.get(
                        order.session.end_date
                    ).to('local').format('h:mma'),
                    'class_location_name': order.session.location.name,
                    'class_location_street': order.session.location.street,
                    'class_location_city': order.session.location.city,
                    'class_location_state': order.session.location.state,
                    'class_location_zip': order.session.location.zip,
                    'class_additional_info': order.session.additional_info,
                    'class_url': order.session.get_absolute_url(),
                    'class_ics_url': order.session.get_ics_url(),
                    'microdata_start_date': arrow.get(
                        order.session.start_date
                    ).to('local').isoformat(),
                    'microdata_end_date': arrow.get(
                        order.session.end_date
                    ).to('local').isoformat(),
                    'order': order,
                },
                recipients=[order.guardian.user.email],
                preheader='Your class is just a few days away!',
            )

            order.week_reminder_sent = True
            order.save()

        for order in orders_within_a_day:
            email(
                subject='Your CoderDojoChi is coming up!',
                template_name='class-reminder-guardian-24-hour',
                context={
                    'first_name': order.guardian.user.first_name,
                    'last_name': order.guardian.user.last_name,
                    'student_first_name': order.student.first_name,
                    'student_last_name': order.student.last_name,
                    'class_code': order.session.course.code,
                    'class_title': order.session.course.title,
                    'class_description': order.session.course.description,
                    'class_start_date': arrow.get(
                        order.session.start_date
                    ).to('local').format('dddd, MMMM D, YYYY'),
                    'class_start_time': arrow.get(
                        order.session.start_date
                    ).to('local').format('h:mma'),
                    'class_end_date': arrow.get(
                        order.session.end_date
                    ).to('local').format('dddd, MMMM D, YYYY'),
                    'class_end_time': arrow.get(
                        order.session.end_date
                    ).to('local').format('h:mma'),
                    'class_location_name': order.session.location.name,
                    'class_location_street': order.session.location.street,
                    'class_location_city': order.session.location.city,
                    'class_location_state': order.session.location.state,
                    'class_location_zip': order.session.location.zip,
                    'class_additional_info': order.session.additional_info,
                    'class_url': order.session.get_absolute_url(),
                    'class_ics_url': order.session.get_ics_url(),
                    'microdata_start_date': arrow.get(
                        order.session.start_date
                    ).to('local').isoformat(),
                    'microdata_end_date': arrow.get(
                        order.session.end_date
                    ).to('local').isoformat(),
                    'order': order,
                },
                recipients=[order.guardian.user.email],
                preheader='Your class is just hours away!',
            )

            order.day_reminder_sent = True
            order.save()

        for session in sessions_within_a_week:
            orders = MentorOrder.objects.filter(session=session)

            for order in orders:
                email(
                    subject='Your CoderDojoChi class is in less than a week!',
                    template_name='class-reminder-mentor-one-week',
                    context={
                        'first_name': order.mentor.user.first_name,
                        'last_name': order.mentor.user.last_name,
                        'class_code': order.session.course.code,
                        'class_title': order.session.course.title,
                        'class_description': order.session.course.description,
                        'class_start_date': arrow.get(
                            order.session.mentor_start_date
                        ).to('local').format('dddd, MMMM D, YYYY'),
                        'class_start_time': arrow.get(
                            order.session.mentor_start_date
                        ).to('local').format('h:mma'),
                        'class_end_date': arrow.get(
                            order.session.mentor_end_date
                        ).to('local').format('dddd, MMMM D, YYYY'),
                        'class_end_time': arrow.get(
                            order.session.mentor_end_date
                        ).to('local').format('h:mma'),
                        'class_location_name': order.session.location.name,
                        'class_location_street':
                            order.session.location.street,
                        'class_location_city': order.session.location.city,
                        'class_location_state': order.session.location.state,
                        'class_location_zip': order.session.location.zip,
                        'class_additional_info': order.session.additional_info,
                        'class_url': order.session.get_absolute_url(),
                        'class_ics_url': order.session.get_ics_url(),
                        'microdata_start_date': arrow.get(
                            order.session.start_date
                        ).to('local').isoformat(),
                        'microdata_end_date': arrow.get(
                            order.session.end_date
                        ).to('local').isoformat(),
                        'order': order,
                    },
                    recipients=[order.mentor.user.email],
                    preheader='The class is just a few days away!',
                )

            session.mentors_week_reminder_sent = True
            session.save()

        for session in sessions_within_a_day:
            orders = MentorOrder.objects.filter(session=session)

            for order in orders:
                email(
                    subject='Your CoderDojoChi class is tomorrow!',
                    template_name='class-reminder-mentor-24-hour',
                    context={
                        'first_name': order.mentor.user.first_name,
                        'last_name': order.mentor.user.last_name,
                        'class_code': order.session.course.code,
                        'class_title': order.session.course.title,
                        'class_description': order.session.course.description,
                        'class_start_date': arrow.get(
                            order.session.mentor_start_date
                        ).to('local').format('dddd, MMMM D, YYYY'),
                        'class_start_time': arrow.get(
                            order.session.mentor_start_date
                        ).to('local').format('h:mma'),
                        'class_end_date': arrow.get(
                            order.session.mentor_end_date
                        ).to('local').format('dddd, MMMM D, YYYY'),
                        'class_end_time': arrow.get(
                            order.session.mentor_end_date
                        ).to('local').format('h:mma'),
                        'class_location_name': order.session.location.name,
                        'class_location_street':
                            order.session.location.street,
                        'class_location_city': order.session.location.city,
                        'class_location_state': order.session.location.state,
                        'class_location_zip': order.session.location.zip,
                        'class_additional_info': order.session.additional_info,
                        'class_url': order.session.get_absolute_url(),
                        'class_ics_url': order.session.get_ics_url(),
                        'microdata_start_date': arrow.get(
                            order.session.start_date
                        ).to('local').isoformat(),
                        'microdata_end_date': arrow.get(
                            order.session.end_date
                        ).to('local').isoformat(),
                        'order': order,
                    },
                    recipients=[order.mentor.user.email],
                    preheader='The class is just a few hours away!',
                )

            session.mentors_day_reminder_sent = True
            session.save()

        # Cleanup
        connection.close()
