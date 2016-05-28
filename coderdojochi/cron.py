# -*- coding: utf-8 -*-

import arrow
import datetime

from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone
from django_cron import CronJobBase, Schedule

from coderdojochi.models import Mentor, MentorOrder, Order, Session
from coderdojochi.views import sendSystemEmail


class SendReminders(CronJobBase):
    RUN_AT_TIMES = ['10:00', '14:00']

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'coderdojochi.send_reminders'

    def do(self):
        orders_within_a_week = Order.objects.filter(
            active=True,
            week_reminder_sent=False,
            session__start_date__lte=timezone.now() + datetime.timedelta(days=7),
            session__start_date__gte=timezone.now() + datetime.timedelta(days=1)
        )
        orders_within_a_day = Order.objects.filter(
            active=True,
            day_reminder_sent=False,
            session__start_date__lte=timezone.now() + datetime.timedelta(days=1),
            session__start_date__gte=timezone.now() - datetime.timedelta(days=2)
        )
        sessions_within_a_week = Session.objects.filter(
            active=True,
            mentors_week_reminder_sent=False,
            start_date__lte=timezone.now() + datetime.timedelta(days=7),
            start_date__gte=timezone.now() + datetime.timedelta(days=1)
        )
        sessions_within_a_day = Session.objects.filter(
            active=True,
            mentors_day_reminder_sent=False,
            start_date__lte=timezone.now() + datetime.timedelta(days=1),
            start_date__gte=timezone.now() - datetime.timedelta(days=2)
        )

        for order in orders_within_a_week:
            sendSystemEmail(
                False,
                'Upcoming class reminder',
                'coderdojochi-class-reminder-guardian',
                {
                    'first_name': order.guardian.user.first_name,
                    'last_name': order.guardian.user.last_name,
                    'student_first_name': order.student.first_name,
                    'student_last_name': order.student.last_name,
                    'class_code': order.session.course.code,
                    'class_title': order.session.course.title,
                    'class_description': order.session.course.description,
                    'class_start_date': arrow.get(
                        order.session.start_date
                    ).format('dddd, MMMM D, YYYY'),
                    'class_start_time': arrow.get(order.session.start_date).format('h:mma'),
                    'class_end_date': arrow.get(
                        order.session.end_date
                    ).format('dddd, MMMM D, YYYY'),
                    'class_end_time': arrow.get(order.session.end_date).format('h:mma'),
                    'class_location_name': order.session.location.name,
                    'class_location_address': order.session.location.address,
                    'class_location_address2': order.session.location.address2,
                    'class_location_city': order.session.location.city,
                    'class_location_state': order.session.location.state,
                    'class_location_zip': order.session.location.zip,
                    'class_additional_info': order.session.additional_info,
                    'class_url': order.session.get_absolute_url(),
                    'class_ics_url': order.session.get_ics_url()
                },
                order.guardian.user.email
            )
            order.week_reminder_sent = True
            order.save()

        for order in orders_within_a_day:
            sendSystemEmail(
                False,
                'Upcoming class reminder',
                'coderdojochi-class-reminder-guardian-24-hour',
                {
                    'first_name': order.guardian.user.first_name,
                    'last_name': order.guardian.user.last_name,
                    'student_first_name': order.student.first_name,
                    'student_last_name': order.student.last_name,
                    'class_code': order.session.course.code,
                    'class_title': order.session.course.title,
                    'class_description': order.session.course.description,
                    'class_start_date': arrow.get(
                        order.session.start_date
                    ).format('dddd, MMMM D, YYYY'),
                    'class_start_time': arrow.get(order.session.start_date).format('h:mma'),
                    'class_end_date': arrow.get(
                        order.session.end_date
                    ).format('dddd, MMMM D, YYYY'),
                    'class_end_time': arrow.get(order.session.end_date).format('h:mma'),
                    'class_location_name': order.session.location.name,
                    'class_location_address': order.session.location.address,
                    'class_location_address2': order.session.location.address2,
                    'class_location_city': order.session.location.city,
                    'class_location_state': order.session.location.state,
                    'class_location_zip': order.session.location.zip,
                    'class_additional_info': order.session.additional_info,
                    'class_url': order.session.get_absolute_url(),
                    'class_ics_url': order.session.get_ics_url()
                },
                order.guardian.user.email
            )
            order.day_reminder_sent = True
            order.save()

        for session in sessions_within_a_week:
            session_mentors = Mentor.objects.filter(
                id__in=MentorOrder.objects.filter(session=session).values('mentor__id')
            )
            for mentor in session_mentors:
                sendSystemEmail(
                    False,
                    'Upcoming class reminder',
                    'coderdojochi-class-reminder-mentor',
                    {
                        'first_name': mentor.user.first_name,
                        'last_name': mentor.user.last_name,
                        'class_code': session.course.code,
                        'class_title': session.course.title,
                        'class_description': session.course.description,
                        'class_start_date': arrow.get(
                            session.mentor_start_date
                        ).format('dddd, MMMM D, YYYY'),
                        'class_start_time': arrow.get(session.mentor_start_date).format('h:mma'),
                        'class_end_date': arrow.get(
                            session.mentor_end_date
                        ).format('dddd, MMMM D, YYYY'),
                        'class_end_time': arrow.get(session.mentor_end_date).format('h:mma'),
                        'class_location_name': session.location.name,
                        'class_location_address': session.location.address,
                        'class_location_address2': session.location.address2,
                        'class_location_city': session.location.city,
                        'class_location_state': session.location.state,
                        'class_location_zip': session.location.zip,
                        'class_additional_info': session.additional_info,
                        'class_url': session.get_absolute_url(),
                        'class_ics_url': session.get_ics_url()
                    },
                    mentor.user.email
                )
            session.mentors_week_reminder_sent = True
            session.save()

        for session in sessions_within_a_day:
            session_mentors = Mentor.objects.filter(
                id__in=MentorOrder.objects.filter(session=session).values('mentor__id')
            )
            for mentor in session_mentors:
                sendSystemEmail(
                    False,
                    'Upcoming class reminder',
                    'coderdojochi-class-reminder-mentor-24-hour',
                    {
                        'first_name': mentor.user.first_name,
                        'last_name': mentor.user.last_name,
                        'class_code': session.course.code,
                        'class_title': session.course.title,
                        'class_description': session.course.description,
                        'class_start_date': arrow.get(
                            session.mentor_start_date
                        ).format('dddd, MMMM D, YYYY'),
                        'class_start_time': arrow.get(session.mentor_start_date).format('h:mma'),
                        'class_end_date': arrow.get(
                            session.mentor_end_date
                        ).format('dddd, MMMM D, YYYY'),
                        'class_end_time': arrow.get(session.mentor_end_date).format('h:mma'),
                        'class_location_name': session.location.name,
                        'class_location_address': session.location.address,
                        'class_location_address2': session.location.address2,
                        'class_location_city': session.location.city,
                        'class_location_state': session.location.state,
                        'class_location_zip': session.location.zip,
                        'class_additional_info': session.additional_info,
                        'class_url': session.get_absolute_url(),
                        'class_ics_url': session.get_ics_url(),
                    },
                    mentor.user.email
                )
            session.mentors_day_reminder_sent = True
            session.save()

