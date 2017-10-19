import arrow
from background_task import background

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import get_connection, send_mail
from django.shortcuts import (
    get_object_or_404,
    redirect,
)
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import View

from coderdojochi.models import (
    Guardian,
    Meeting,
    Mentor,
    Session,
)
from coderdojochi.util import email

annoucement_decorators = [never_cache, login_required]


@method_decorator(annoucement_decorators, name='dispatch')
class MeetingAnnounceView(View):
    def get(self, request, meeting_id):
        if not request.user.is_staff:
            messages.error(
                request,
                'You do not have permission to access this page.'
            )
            return redirect('home')

        meeting_obj = get_object_or_404(
            Meeting,
            id=meeting_id
        )

        if not meeting_obj.announced_date_mentors:
            sendMeetingAnnouncement(
                request.user.email,
                meeting_obj.id,
                verbose_name='Announce Meeting {} to Mentors'.format(meeting_obj)
            )

            messages.success(
                request,
                'Meeting announcement in progress!  You will receive an email upon completion.'
            )
        else:
            messages.warning(
                request,
                'Meeting already announced.'
            )

        return redirect('cdc_admin')


@method_decorator(annoucement_decorators, name='dispatch')
class SessionAnnounceMentorsView(View):
    def get(self, request, session_id):
        if not request.user.is_staff:
            messages.error(
                request,
                'You do not have permission to access this page.'
            )
            return redirect('home')

        session_obj = get_object_or_404(
            Session,
            id=session_id
        )

        if not session_obj.announced_date_mentors:
            sendSessionAnnouncementMentor(
                request.user.email,
                session_obj.id,
                verbose_name='Announce Session {} to Mentors'.format(session_obj)
            )

            messages.success(
                request,
                'Session announcement in progress!  You will receive an email upon completion.'
            )
        else:
            messages.warning(
                request,
                'Session already announced.'
            )

        return redirect('cdc_admin')


@method_decorator(annoucement_decorators, name='dispatch')
class SessionAnnounceGuardiansView(View):
    def get(self, request, session_id):
        if not request.user.is_staff:
            messages.error(
                request,
                'You do not have permission to access this page.'
            )
            return redirect('home')

        session_obj = get_object_or_404(
            Session,
            id=session_id
        )

        if not session_obj.announced_date_guardians:
            sendSessionAnnouncementGuardian(
                request.user.email,
                session_obj.id,
                verbose_name='Announce Session {} to Guardians'.format(session_obj)
            )

            messages.success(
                request,
                'Session announcement in progress!  You will receive an email upon completion.'
            )
        else:
            messages.warning(
                request,
                'Session already announced.'
            )

        return redirect('cdc_admin')


@background(schedule=30)
def sendMeetingAnnouncement(confirm_email, meeting_id):
    meeting_obj = get_object_or_404(
        Session,
        id=meeting_id
    )

    # uses SMTP server specified in settings.py
    connection = get_connection()

    # If you don't open the connection manually,
    # Django will automatically open, then tear down the
    # connection in msg.send()
    connection.open()

    active_mentors = Mentor.objects.filter(
        is_active=True,
        user__is_active=True,
    )

    for mentor in active_mentors:
        email(
            subject='New meeting announced!',
            template_name='meeting-announcement-mentor',
            context={
                'first_name': mentor.user.first_name,
                'last_name': mentor.user.last_name,
                'meeting_title': meeting_obj.meeting_type.title,
                'meeting_description': (
                    meeting_obj.meeting_type.description
                ),
                'meeting_start_date': arrow.get(
                    meeting_obj.start_date
                ).to('local').format('dddd, MMMM D, YYYY'),
                'meeting_start_time': arrow.get(
                    meeting_obj.start_date
                ).to('local').format('h:mma'),
                'meeting_end_date': arrow.get(
                    meeting_obj.end_date
                ).to('local').format('dddd, MMMM D, YYYY'),
                'meeting_end_time': arrow.get(
                    meeting_obj.end_date
                ).to('local').format('h:mma'),
                'meeting_location_name': meeting_obj.location.name,
                'meeting_location_address': meeting_obj.location.address,
                'meeting_location_address2': meeting_obj.location.address2,
                'meeting_location_city': meeting_obj.location.city,
                'meeting_location_state': meeting_obj.location.state,
                'meeting_location_zip': meeting_obj.location.zip,
                'meeting_additional_info': meeting_obj.additional_info,
                'meeting_url': meeting_obj.get_absolute_url(),
                'meeting_ics_url': meeting_obj.get_ics_url()
            },
            recipients=[mentor.user.email],
            preheader='A new meeting has been announced. '
                      'Come join us for some amazing fun!',
        )

    # Cleanup
    connection.close()

    meeting_obj.announced_date_mentors = timezone.now()
    meeting_obj.save()

    send_announcement_completion_email(
        confirm_email,
        str(meeting_obj),
        active_mentors.count()
    )


@background(schedule=30)
def sendSessionAnnouncementMentor(confirm_email, session_id):
    session_obj = get_object_or_404(
        Session,
        id=session_id
    )

    # uses SMTP server specified in settings.py
    connection = get_connection()

    # If you don't open the connection manually,
    # Django will automatically open, then tear down the
    # connection in msg.send()
    connection.open()

    active_mentors = Mentor.objects.filter(
        is_active=True,
        user__is_active=True,
    )

    # send mentor announcements
    for mentor in active_mentors:
        email(
            subject='New CoderDojoChi class date announced! Come mentor!',
            template_name='class-announcement-mentor',
            context={
                'first_name': mentor.user.first_name,
                'last_name': mentor.user.last_name,
                'class_code': session_obj.course.code,
                'class_title': session_obj.course.title,
                'class_description': session_obj.course.description,
                'class_start_date': arrow.get(
                    session_obj.mentor_start_date
                ).to('local').format('dddd, MMMM D, YYYY'),
                'class_start_time': arrow.get(
                    session_obj.mentor_start_date
                ).to('local').format('h:mma'),
                'class_end_date': arrow.get(
                    session_obj.end_date
                ).to('local').format('dddd, MMMM D, YYYY'),
                'class_end_time': arrow.get(
                    session_obj.end_date
                ).to('local').format('h:mma'),
                'class_location_name': session_obj.location.name,
                'class_location_address': session_obj.location.address,
                'class_location_address2': session_obj.location.address2,
                'class_location_city': session_obj.location.city,
                'class_location_state': session_obj.location.state,
                'class_location_zip': session_obj.location.zip,
                'class_additional_info': session_obj.additional_info,
                'class_url': session_obj.get_absolute_url(),
                'class_ics_url': session_obj.get_ics_url()
            },
            recipients=[mentor.user.email],
            preheader='Help us make a huge difference! '
                      'A brand new class was just announced.',
        )

    # Cleanup
    connection.close()

    session_obj.announced_date_mentors = timezone.now()
    session_obj.save()

    send_announcement_completion_email(
        confirm_email,
        str(session_obj),
        active_mentors.count()
    )


@background(schedule=30)
def sendSessionAnnouncementGuardian(confirm_email, session_id):
    session_obj = get_object_or_404(
        Session,
        id=session_id
    )

    # uses SMTP server specified in settings.py
    connection = get_connection()

    # If you don't open the connection manually,
    # Django will automatically open, then tear down the
    # connection in msg.send()
    connection.open()

    active_guardians = Guardian.objects.filter(
        is_active=True,
        user__is_active=True,
    )

    for guardian in active_guardians:
        email(
            subject='New CoderDojoChi class date announced!',
            template_name='class-announcement-guardian',
            context={
                'first_name': guardian.user.first_name,
                'last_name': guardian.user.last_name,
                'class_code': session_obj.course.code,
                'class_title': session_obj.course.title,
                'class_description': session_obj.course.description,
                'class_start_date': arrow.get(
                    session_obj.start_date
                ).to('local').format('dddd, MMMM D, YYYY'),
                'class_start_time': arrow.get(
                    session_obj.start_date
                ).to('local').format('h:mma'),
                'class_end_date': arrow.get(
                    session_obj.end_date
                ).to('local').format('dddd, MMMM D, YYYY'),
                'class_end_time': arrow.get(
                    session_obj.end_date
                ).to('local').format('h:mma'),
                'class_location_name': session_obj.location.name,
                'class_location_address': session_obj.location.address,
                'class_location_address2': session_obj.location.address2,
                'class_location_city': session_obj.location.city,
                'class_location_state': session_obj.location.state,
                'class_location_zip': session_obj.location.zip,
                'class_additional_info': session_obj.additional_info,
                'class_url': session_obj.get_absolute_url(),
                'class_ics_url': session_obj.get_ics_url()
            },
            recipients=[guardian.user.email],
            preheader='We\'re super excited to bring you another class '
                      'date. Sign up to reserve your spot',
        )

    # Cleanup
    connection.close()

    session_obj.announced_date_guardians = timezone.now()
    session_obj.save()

    send_announcement_completion_email(
        confirm_email,
        str(session_obj),
        active_guardians.count(),
        guardians=True
    )


def send_announcement_completion_email(
    confirm_email,
    event_name,
    recipient_count,
    guardians=False
):
    send_mail(
        'Announcement Sent Successfully',
        'Announcement for {} sent successfully to {} {}'.format(
            event_name,
            recipient_count,
            'Guardians' if guardians else 'Volunteers'
        ),
        'CoderDojoChi<{}>'.format(
            settings.DEFAULT_FROM_EMAIL
        ),
        [confirm_email if confirm_email else settings.CONTACT_EMAIL],
        fail_silently=False,
    )
