# -*- coding: utf-8 -*-
import arrow
import datetime

from django.core.mail import get_connection
from django.utils import timezone
from django_cron import CronJobBase, Schedule

from coderdojochi.models import Mentor, MentorOrder, Order, Session
from coderdojochi.views import sendSystemEmail


class UpdateWaitlists(CronJobBase):
    RUN_EVERY_MINS = 60

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'coderdojochi.UpdateWaitlists'

    def do(self):
        date_12_hours_ago = timezone.now() - datetime.timedelta(hours=12)

        orders = Order.objects.filter(
            active=True,
            session__start_date__gte=timezone.now()
        )

        for order in orders:
            # if waitlist offer sent over 12 hours ago revoke it
            if (order.waitlisted and order.waitlist_offer_sent_at and
               order.waitlist_offer_sent_at < date_12_hours_ago):
                order.waitlisted = False
                order.waitlisted_at = None
                order.waitlist_offer_sent_at = None
                order.active = False
                order.save()

                # send waitlist offer to next waitlisted order (if present)
                next_waitlist_order = Order.objects.filter(
                    active=True,
                    waitlisted=True,
                    session=order.session
                ).order_by('waitlisted_at').first()

                if next_waitlist_order:
                    # TODO: Send offer email to next_waitlist_order.guardian
                    # nwo = next_waitlist_order
                    # sendSystemEmail(
                    #     False,
                    #     'You are next on the waitlist! Enroll now!',
                    #     'coderdojochi-waitlist-offer-guardian',
                    #     {
                    #         'first_name': nwo.guardian.user.first_name,
                    #         'last_name': nwo.guardian.user.last_name,
                    #         'student_first_name': nwo.student.first_name,
                    #         'student_last_name': nwo.student.last_name,
                    #         'class_code': nwo.session.course.code,
                    #         'class_title': nwo.session.course.title,
                    #         'class_description': nwo.session.course.description,
                    #         'class_start_date': arrow.get(
                    #             nwo.session.start_date
                    #         ).format('dddd, MMMM D, YYYY'),
                    #         'class_start_time': arrow.get(nwo.session.start_date).format('h:mma'),
                    #         'class_end_date': arrow.get(
                    #             nwo.session.end_date
                    #         ).format('dddd, MMMM D, YYYY'),
                    #         'class_end_time': arrow.get(nwo.session.end_date).format('h:mma'),
                    #         'class_location_name': nwo.session.location.name,
                    #         'class_location_address': nwo.session.location.address,
                    #         'class_location_address2': nwo.session.location.address2,
                    #         'class_location_city': nwo.session.location.city,
                    #         'class_location_state': nwo.session.location.state,
                    #         'class_location_zip': nwo.session.location.zip,
                    #         'class_additional_info': nwo.session.additional_info,
                    #         'class_url': nwo.session.get_absolute_url(),
                    #         'class_ics_url': nwo.session.get_ics_url()
                    #     },
                    #     nwo.guardian.user.email
                    # )

                    next_waitlist_order.waitlist_offer_sent_at = timezone.now()
                    next_waitlist_order.save()

        mentor_orders = MentorOrder.objects.filter(
            active=True,
            session__start_date__gte=timezone.now()
        )

        for mentor_order in mentor_orders:
            # if waitlist offer sent over 12 hours ago revoke it
            if (mentor_order.waitlisted and mentor_order.waitlist_offer_sent_at and
               mentor_order.waitlist_offer_sent_at < date_12_hours_ago):
                mentor_order.waitlisted = False
                mentor_order.waitlisted_at = None
                mentor_order.waitlist_offer_sent_at = None
                mentor_order.active = False
                mentor_order.save()

                # send waitlist offer to next waitlisted mentor_order (if present)
                next_waitlist_mentor_order = MentorOrder.objects.filter(
                    active=True,
                    waitlisted=True,
                    session=mentor_order.session
                ).order_by('waitlisted_at').first()

                if next_waitlist_mentor_order:
                    # TODO: Send offer email to next_waitlist_mentor_order.mentor
                    # nwmo = next_waitlist_mentor_order
                    # sendSystemEmail(
                    #     False,
                    #     'You are next on the waitlist! Enroll now!',
                    #     'coderdojochi-waitlist-offer-mentor',
                    #     {
                    #         'first_name': nwmo.mentor.user.first_name,
                    #         'last_name': nwmo.mentor.user.last_name,
                    #         'class_code': nwmo.session.course.code,
                    #         'class_title': nwmo.session.course.title,
                    #         'class_description': nwmo.session.course.description,
                    #         'class_start_date': arrow.get(
                    #             nwmo.session.mentor_start_date
                    #         ).format('dddd, MMMM D, YYYY'),
                    #         'class_start_time': arrow.get(nwmo.session.mentor_start_date).format('h:mma'),
                    #         'class_end_date': arrow.get(
                    #             nwmo.session.mentor_end_date
                    #         ).format('dddd, MMMM D, YYYY'),
                    #         'class_end_time': arrow.get(nwmo.session.mentor_end_date).format('h:mma'),
                    #         'class_location_name': nwmo.session.location.name,
                    #         'class_location_address': nwmo.session.location.address,
                    #         'class_location_address2': nwmo.session.location.address2,
                    #         'class_location_city': nwmo.session.location.city,
                    #         'class_location_state': nwmo.session.location.state,
                    #         'class_location_zip': nwmo.session.location.zip,
                    #         'class_additional_info': nwmo.session.additional_info,
                    #         'class_url': nwmo.session.get_absolute_url(),
                    #         'class_ics_url': nwmo.session.get_ics_url()
                    #     },
                    #     nwmo.mentor.user.email
                    # )

                    next_waitlist_mentor_order.waitlist_offer_sent_at = timezone.now()
                    next_waitlist_mentor_order.save()


class SendReminders(CronJobBase):
    RUN_AT_TIMES = ['10:00', '14:00']

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'coderdojochi.SendReminders'

    def do(self):
        orders_within_a_week = Order.objects.filter(
            active=True,
            week_reminder_sent=False,
            session__start_date__lte=(
                timezone.now() + datetime.timedelta(days=7)
            ),
            session__start_date__gte=(
                timezone.now() + datetime.timedelta(days=1)
            ),
        ).exclude(waitlisted=True)
        orders_within_a_day = Order.objects.filter(
            active=True,
            day_reminder_sent=False,
            session__start_date__lte=(
                timezone.now() + datetime.timedelta(days=1)
            ),
            session__start_date__gte=(
                timezone.now() - datetime.timedelta(days=2)
            ),
        ).exclude(waitlisted=True)
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

        # uses SMTP server specified in settings.py
        connection = get_connection()

        # If you don't open the connection manually,
        # Django will automatically open, then tear down the connection
        # in msg.send()
        connection.open()

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
                    'class_start_time': arrow.get(
                        order.session.start_date
                    ).format('h:mma'),
                    'class_end_date': arrow.get(
                        order.session.end_date
                    ).format('dddd, MMMM D, YYYY'),
                    'class_end_time': arrow.get(
                        order.session.end_date
                    ).format('h:mma'),
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
                    'class_start_time': arrow.get(
                        order.session.start_date
                    ).format('h:mma'),
                    'class_end_date': arrow.get(
                        order.session.end_date
                    ).format('dddd, MMMM D, YYYY'),
                    'class_end_time': arrow.get(
                        order.session.end_date
                    ).format('h:mma'),
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
                id__in=MentorOrder.objects.filter(
                    session=session
                ).values('mentor__id')
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
                        'class_start_time': arrow.get(
                            session.mentor_start_date
                        ).format('h:mma'),
                        'class_end_date': arrow.get(
                            session.mentor_end_date
                        ).format('dddd, MMMM D, YYYY'),
                        'class_end_time': arrow.get(
                            session.mentor_end_date
                        ).format('h:mma'),
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
                id__in=MentorOrder.objects.filter(
                    session=session
                ).values('mentor__id')
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
                        'class_start_time': arrow.get(
                            session.mentor_start_date
                        ).format('h:mma'),
                        'class_end_date': arrow.get(
                            session.mentor_end_date
                        ).format('dddd, MMMM D, YYYY'),
                        'class_end_time': arrow.get(
                            session.mentor_end_date
                        ).format('h:mma'),
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

        # Cleanup
        connection.close()
