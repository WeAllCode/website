import calendar
import logging
import operator
from collections import Counter
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMultiAlternatives, get_connection
from django.db.models import Case, Count, IntegerField, When
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

import arrow
from coderdojochi.forms import (
    CDCModelForm,
    ContactForm,
    DonationForm,
    GuardianForm,
    MentorForm,
    StudentForm,
)
from coderdojochi.models import (
    Donation,
    Equipment,
    EquipmentType,
    Guardian,
    Meeting,
    MeetingOrder,
    Mentor,
    MentorOrder,
    Order,
    PartnerPasswordAccess,
    Session,
    Student,
)
from coderdojochi.util import email
from icalendar import Calendar, Event, vText
from paypal.standard.forms import PayPalPaymentsForm
from functools import reduce

logger = logging.getLogger("mechanize")

# this will assign User to our custom CDCUser
User = get_user_model()


def home(request, template_name="home.html"):
    upcoming_classes = Session.objects.filter(
        is_active=True,
        end_date__gte=timezone.now(),
    ).order_by('start_date')

    if (
        not request.user.is_authenticated or
        not request.user.role == 'mentor'
    ):
        upcoming_classes = upcoming_classes.filter(is_public=True)

    upcoming_classes = upcoming_classes[:3]

    return render(request, template_name, {
        'upcoming_classes': upcoming_classes
    })


@login_required
def welcome(request, template_name="welcome.html"):
    keepGoing = True

    user = request.user
    account = False
    add_student = False
    students = False
    form = False
    role = user.role if user.role else False

    next_url = False

    if 'next' in request.GET:
        next_url = request.GET['next']

    if request.method == 'POST':
        if role:
            if role == 'mentor':
                form = MentorForm(
                    request.POST,
                    instance=get_object_or_404(Mentor, user=user)
                )

            else:
                account = get_object_or_404(Guardian, user=user)

                if not account.phone or not account.zip:
                    form = GuardianForm(request.POST, instance=account)

                else:
                    form = StudentForm(request.POST)

                    if form.is_valid():
                        new_student = form.save(commit=False)
                        new_student.guardian = account
                        new_student.save()
                        messages.success(request, 'Student Registered.')

                    else:
                        keepGoing = False

                    if keepGoing:
                        if next_url:
                            if 'enroll' in request.GET:
                                return redirect(
                                    f"{next_url}?enroll=True&student={new_student.id}"
                                )

                            else:
                                return redirect(next_url)

                        else:
                            return redirect('welcome')

            if keepGoing:
                if form.is_valid():
                    form.save()
                    messages.success(request, 'Profile information saved.')

                    if next_url:
                        if 'enroll' in request.GET:
                            return redirect(
                                f"{next_url}?enroll=True"
                            )

                        else:
                            return redirect(next_url)

                    else:
                        return redirect('dojo')

                else:
                    keepGoing = False

        else:
            if request.POST.get('role') == 'mentor':
                role = 'mentor'
                mentor, created = Mentor.objects.get_or_create(user=user)
                mentor.user.first_name = user.first_name
                mentor.user.last_name = user.last_name
                mentor.save()
                user.role = role
            else:
                role = 'guardian'
                guardian, created = Guardian.objects.get_or_create(user=user)
                guardian.user.first_name = user.first_name
                guardian.user.last_name = user.last_name
                guardian.save()
                user.role = role

            user.save()

            merge_vars = {
                'user': request.user.username,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name
            }

            if role == 'mentor':
                # check for next upcoming meeting
                next_meeting = Meeting.objects.filter(
                    is_active=True,
                    is_public=True
                ).order_by('start_date').first()

                if next_meeting:
                    merge_vars[
                        'next_intro_meeting_url'
                    ] = next_meeting.get_absolute_url()

                    merge_vars[
                        'next_intro_meeting_ics_url'
                    ] = next_meeting.get_ics_url()

                email(
                    subject='Welcome!',
                    template_name='welcome-mentor',
                    merge_global_data=merge_vars,
                    recipients=[request.user.email],
                    preheader='Your adventure awaits!',
                )

                next_url = f"?next={next_url}" if next_url else reverse('dojo')

                return redirect(next_url)
            else:
                # check for next upcoming class
                next_class = Session.objects.filter(
                    is_active=True
                ).order_by('start_date').first()

                if next_class:
                    merge_vars[
                        'next_class_url'
                    ] = next_class.get_absolute_url()

                    merge_vars[
                        'next_class_ics_url'
                    ] = next_class.get_ics_url()

                email(
                    subject='Welcome!',
                    template_name='welcome-guardian',
                    merge_global_data=merge_vars,
                    recipients=[request.user.email],
                    preheader='Your adventure awaits!',
                )

                next_url = f"?next={next_url}" if next_url else reverse('welcome')

                return redirect(next_url)

    if role and keepGoing:
        if role == 'mentor':
            mentor = get_object_or_404(Mentor, user=user)
            account = mentor
            form = MentorForm(instance=account)

        if role == 'guardian':
            guardian = get_object_or_404(Guardian, user=user)
            account = guardian
            if not account.phone or not account.zip:
                form = GuardianForm(instance=account)
            else:
                add_student = True
                form = StudentForm(initial={'guardian': guardian.pk})

    if account and account.user.first_name and keepGoing:
        if role == 'mentor':
            if next_url:
                return redirect(next_url)
            else:
                return redirect('dojo')
        else:
            students = account.get_students(
            ) if account.get_students().count() else False

    if keepGoing:
        next_url = request.GET['next'] if 'next' in request.GET else False

    return render(request, template_name, {
        'role': role,
        'account': account,
        'form': form,
        'add_student': add_student,
        'students': students,
        'next_url': next_url
    })


def sessions(request, year=False, month=False, template_name="sessions.html"):
    now = timezone.now()
    year = int(year) if year else now.year
    month = int(month) if month else now.month
    calendar_date = date(day=1, month=month, year=year)
    prev_date = calendar_date - relativedelta(months=1)
    next_date = calendar_date + relativedelta(months=1)

    all_sessions = Session.objects.filter(
        is_active=True,
        end_date__gte=timezone.now()
    ).order_by('start_date')

    if (
        not request.user.is_authenticated or
        not request.user.role == 'mentor'
    ):
        all_sessions = all_sessions.filter(is_public=True)

    sessions = all_sessions.filter(
        start_date__year=year,
        start_date__month=month
    ).order_by('start_date')

    return render(request, template_name, {
        'all_sessions': all_sessions,
        'sessions': sessions,
        'calendar_date': calendar_date,
        'prev_date': prev_date,
        'next_date': next_date,
    })


def session_detail_enroll(
    request,
    year,
    month,
    day,
    slug,
    session_id,
    template_name="session-detail.html"
):
    return session_detail(
        request,
        year,
        month,
        day,
        slug,
        session_id,
        template_name,
        enroll=True,
    )


def validate_partner_session_access(request, session_id):
    authed_sessions = request.session.get('authed_partner_sessions')

    if authed_sessions and session_id in authed_sessions:
        if request.user.is_authenticated:
            PartnerPasswordAccess.objects.get_or_create(
                session_id=session_id,
                user=request.user
            )

        return True

    if request.user.is_authenticated:
        try:
            PartnerPasswordAccess.objects.get(
                session_id=session_id,
                user_id=request.user.id
            )

        except PartnerPasswordAccess.DoesNotExist:
            return False

        else:
            return True

    else:
        return False


def session_detail_short(request, session_id):
    session_obj = get_object_or_404(Session, id=session_id)
    return redirect(session_obj.get_absolute_url())


def session_detail(
    request,
    year,
    month,
    day,
    slug,
    session_id,
    template_name="session-detail.html",
    enroll=False,
):
    session_obj = get_object_or_404(Session, id=session_id)
    if session_obj.password:
        if not validate_partner_session_access(request, session_id):
            view_kwargs = {
                'year': year,
                'month': month,
                'day': day,
                'slug': slug,
                'session_id': session_id
            }
            url = reverse('session_password', kwargs=view_kwargs)
            return HttpResponseRedirect(url)

    mentor_signed_up = False
    account = False
    students = False
    active_mentors = Mentor.objects.filter(
        id__in=MentorOrder.objects.filter(
            session=session_obj,
            is_active=True
        ).values('mentor__id')
    )

    if request.method == 'POST':
        if 'waitlist' in request.POST:

            if request.POST['waitlist'] == 'student':
                student = Student.objects.get(
                    id=int(request.POST['account_id'])
                )

                if request.POST['remove'] == 'true':
                    session_obj.waitlist_students.remove(student)
                    session_obj.save()
                    messages.success(
                        request,
                        'You have been removed from the waitlist. '
                        'Thanks for letting us know.'
                    )

                else:
                    session_obj.waitlist_students.add(student)
                    session_obj.save()
                    messages.success(
                        request,
                        'Added to waitlist successfully.'
                    )
            else:
                mentor = Mentor.objects.get(
                    id=int(request.POST['account_id'])
                )

                if request.POST['remove'] == 'true':
                    session_obj.waitlist_mentors.remove(mentor)
                    session_obj.save()
                    messages.success(
                        request,
                        'You have been removed from the waitlist. '
                        'Thanks for letting us know.'
                    )
                else:
                    session_obj.waitlist_mentors.add(mentor)
                    session_obj.save()
                    messages.success(
                        request,
                        'Added to waitlist successfully.'
                    )
        else:
            messages.error(request, 'Invalid request, please try again.')

        return redirect(session_obj.get_absolute_url())

    upcoming_classes = Session.objects.filter(
        is_active=True,
        end_date__gte=timezone.now()
    ).order_by('start_date')

    if (
        not request.user.is_authenticated or
        not request.user.role == 'mentor'
    ):
        upcoming_classes = upcoming_classes.filter(is_public=True)

    if request.user.is_authenticated:
        if not request.user.role:
            messages.warning(
                request,
                'Please select one of the following options to continue.'
            )

            url = f"{reverse('welcome')}?next={session_obj.get_absolute_url()}"

            if 'enroll' in request.GET:
                url += '&enroll=True'

            return redirect(url)

        if request.user.role == 'mentor':
            mentor = get_object_or_404(Mentor, user=request.user)
            account = mentor
            session_orders = MentorOrder.objects.filter(
                session=session_obj,
                is_active=True,
            )
            mentor_signed_up = True if session_orders.filter(
                mentor=account
            ).count() else False

            spots_remaining = (
                session_obj.get_mentor_capacity() - session_orders.count()
            )

            if enroll or 'enroll' in request.GET:
                return redirect(
                    f"{session_obj.get_absolute_url()}/sign-up/"
                )

        else:
            guardian = get_object_or_404(Guardian, user=request.user)
            account = guardian
            students = guardian.get_students(
            ) if guardian.get_students().count() else False

            spots_remaining = (
                session_obj.capacity -
                session_obj.get_current_students().count()
            )

            if enroll or 'enroll' in request.GET:
                if not students:
                    return HttpResponseRedirect(
                        f"{reverse('welcome')}?next={session_obj.get_absolute_url()}&enroll=True"
                    )
                else:
                    if 'student' in request.GET:
                        return redirect(
                            f"{session_obj.get_absolute_url()}/sign-up/{request.GET['student']}"
                        )

    else:
        spots_remaining = (
            session_obj.capacity -
            session_obj.get_current_students().count()
        )

    return render(
        request,
        template_name,
        {
            'session': session_obj,
            'active_mentors': active_mentors,
            'mentor_signed_up': mentor_signed_up,
            'students': students,
            'account': account,
            'upcoming_classes': upcoming_classes,
            'spots_remaining': spots_remaining,
        }
    )


@login_required
def session_sign_up(
    request,
    year,
    month,
    day,
    slug,
    session_id,
    student_id=False,
    template_name="session-sign-up.html",
):
    session_obj = get_object_or_404(Session, id=session_id)
    student = False
    guardian = False

    if not request.user.role:
        messages.warning(
            request,
            'Please select one of the following options to continue.'
        )

        return HttpResponseRedirect(
            f"{reverse('welcome')}?next={session_obj.get_absolute_url()}"
        )

    if request.user.role == 'mentor':

        mentor = get_object_or_404(Mentor, user=request.user)

        if not mentor.background_check:
            messages.warning(
                request,
                (
                    'You cannot sign up for a class until you '
                    '<a href="https://app.verifiedvolunteers.com/promoorder/6a34f727-3728-4f1a-b80b-7eb3265a3b93" '
                    'target="_blank">'
                    'fill out the background search form'
                    '</a>.'
                )
            )
            return redirect('dojo')

        session_orders = MentorOrder.objects.filter(
            session=session_obj,
            is_active=True
        )

        user_signed_up = True if session_orders.filter(
            mentor=mentor
        ).count() else False

        if not user_signed_up:
            if session_obj.get_mentor_capacity() <= session_orders.count():
                messages.error(
                    request,
                    'Sorry this class is at mentor capacity. '
                    'Please check back soon and/or join us for '
                    'another upcoming class!'
                )
                return redirect(session_obj.get_absolute_url())
    else:
        student = get_object_or_404(Student, id=student_id)
        guardian = get_object_or_404(Guardian, user=request.user)
        user_signed_up = True if student.is_registered_for_session(
            session_obj
        ) else False

        # are there session limitations?
        if (
            not student.is_within_gender_limitation(
                session_obj.gender_limitation
            )
        ):
            messages.error(
                request,
                f"Sorry, this class is limited to {session_obj.gender_limitation} this time around."
            )

            return HttpResponseRedirect(
                session_obj.get_absolute_url()
            )

        if (
            not student.is_within_age_range(
                session_obj.min_age_limitation,
                session_obj.max_age_limitation,
                session_obj.start_date
            )
        ):
            messages.error(
                request,
                (
                    f"Sorry, this class is limited to students between ages {session_obj.min_age_limitation} and "
                    f"{session_obj.max_age_limitation}."
                )
            )

            return redirect(
                session_obj.get_absolute_url()
            )

        if not user_signed_up:
            if (
                session_obj.capacity <=
                session_obj.get_current_students().count()
            ):
                messages.error(
                    request,
                    'Sorry this class has sold out. '
                    'Please sign up for the wait list and/or check back later.'
                )
                return redirect(
                    session_obj.get_absolute_url()
                )

    if request.method == 'POST':
        if user_signed_up:
            if request.user.role == 'mentor':
                order = get_object_or_404(
                    MentorOrder,
                    mentor=mentor,
                    session=session_obj,
                )

            else:
                order = get_object_or_404(
                    Order,
                    student=student,
                    session=session_obj,
                    is_active=True,
                )

            order.is_active = False
            order.save()

            messages.success(
                request,
                'Thanks for letting us know!'
            )

        else:
            if not settings.DEBUG:
                ip = (
                    request.META['HTTP_X_FORWARDED_FOR'] or
                    request.META['REMOTE_ADDR']
                )

            else:
                ip = request.META['REMOTE_ADDR']

            if request.user.role == 'mentor':
                order, created = MentorOrder.objects.get_or_create(
                    mentor=mentor,
                    session=session_obj,
                )
                order.ip = ip
                order.is_active = True
                order.save()
            else:
                order, created = Order.objects.get_or_create(
                    guardian=guardian,
                    student=student,
                    session=session_obj,
                )
                order.ip = ip
                order.is_active = True
                order.save()

            # we dont want guardians getting 7 day reminder
            # email if they sign up within 9 days
            if session_obj.start_date < timezone.now() + timedelta(days=9):
                order.week_reminder_sent = True

            # or 24 hours notice if signed up within 48 hours
            if session_obj.start_date < timezone.now() + timedelta(days=2):
                order.week_reminder_sent = True
                order.day_reminder_sent = True

            order.save()

            messages.success(
                request,
                'Success! See you there!'
            )

            if request.user.role == 'mentor':
                email(
                    subject='Mentoring confirmation for {} class'.format(
                        arrow.get(
                            session_obj.mentor_start_date
                        ).to('local').format('MMMM D'),
                    ),
                    template_name='class-confirm-mentor',
                    merge_global_data={
                        'first_name': request.user.first_name,
                        'last_name': request.user.last_name,
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
                            session_obj.mentor_end_date
                        ).to('local').format('dddd, MMMM D, YYYY'),
                        'class_end_time': arrow.get(
                            session_obj.mentor_end_date
                        ).to('local').format('h:mma'),
                        'class_location_name': session_obj.location.name,
                        'class_location_address': session_obj.location.address,
                        'class_location_address2': (
                            session_obj.location.address2
                        ),
                        'class_location_city': session_obj.location.city,
                        'class_location_state': session_obj.location.state,
                        'class_location_zip': session_obj.location.zip,
                        'class_additional_info': session_obj.additional_info,
                        'class_url': session_obj.get_absolute_url(),
                        'class_ics_url': session_obj.get_ics_url(),
                        'microdata_start_date': arrow.get(
                            session_obj.mentor_start_date
                        ).to('local').isoformat(),
                        'microdata_end_date': arrow.get(
                            session_obj.mentor_end_date
                        ).to('local').isoformat(),
                        'order': order,
                    },
                    recipients=[request.user.email],
                    preheader='It\'s time to use your powers for good.',
                )

            else:
                email(
                    subject=f"Upcoming class confirmation for {student.first_name} {student.last_name}",
                    template_name='class-confirm-guardian',
                    merge_global_data={
                        'first_name': request.user.first_name,
                        'last_name': request.user.last_name,
                        'student_first_name': student.first_name,
                        'student_last_name': student.last_name,
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
                        'class_location_address2': (
                            session_obj.location.address2
                        ),
                        'class_location_city': session_obj.location.city,
                        'class_location_state': session_obj.location.state,
                        'class_location_zip': session_obj.location.zip,
                        'class_additional_info': session_obj.additional_info,
                        'class_url': session_obj.get_absolute_url(),
                        'class_ics_url': session_obj.get_ics_url(),
                        'microdata_start_date': arrow.get(
                            session_obj.start_date
                        ).to('local').isoformat(),
                        'microdata_end_date': arrow.get(
                            session_obj.end_date
                        ).to('local').isoformat(),
                        'order': order,
                    },
                    recipients=[request.user.email],
                    preheader='Magical wizards have generated this '
                              'confirmation. All thanks to the mystical '
                              'power of coding.',
                )

        return redirect(session_obj.get_absolute_url())

    return render(
        request,
        template_name,
        {
            'session': session_obj,
            'user_signed_up': user_signed_up,
            'student': student,
        }
    )


def session_ics(request, year, month, day, slug, session_id):

    session_obj = get_object_or_404(
        Session,
        id=session_id,
    )

    cal = Calendar()

    cal['prodid'] = '-//CoderDojoChi//coderdojochi.org//'
    cal['version'] = '2.0'
    cal['calscale'] = 'GREGORIAN'

    event = Event()

    start_date = arrow.get(session_obj.start_date).format('YYYYMMDDTHHmmss')
    end_date = arrow.get(session_obj.end_date).format('YYYYMMDDTHHmmss')

    event['uid'] = f"CLASS{session_obj.id:04}@coderdojochi.org"
    event['summary'] = f"CoderDojoChi: {session_obj.course.code} - {session_obj.course.title}"
    event['dtstart'] = f"{start_date}Z"
    event['dtend'] = f"{end_date}Z"
    event['dtstamp'] = start_date

    if request.user.is_authenticated and request.user.role == 'mentor':

        mentor_start_date = arrow.get(
            session_obj.mentor_start_date
        ).format('YYYYMMDDTHHmmss')

        mentor_end_date = arrow.get(
            session_obj.mentor_end_date
        ).format('YYYYMMDDTHHmmss')

        event['dtstart'] = f"{mentor_start_date}Z"
        event['dtend'] = f"{mentor_end_date}Z"
        event['dtstamp'] = mentor_start_date

    location = (
        f"{session_obj.location.name}, {session_obj.location.address}, {session_obj.location.address2}, "
        f"{session_obj.location.city}, {session_obj.location.state} {session_obj.location.zip}"
    )

    event['location'] = vText(location)

    event['url'] = session_obj.get_absolute_url()
    event['description'] = strip_tags(session_obj.course.description)

    # A value of 5 is the normal or "MEDIUM" priority.
    # see: https://tools.ietf.org/html/rfc5545#section-3.8.1.9
    event['priority'] = 5

    cal.add_component(event)

    event_slug = f"coderdojochi-class_{date}".format(
        date=arrow.get(
            session_obj.start_date
        ).to('local').format('MM-DD-YYYY_HH-mma')
    )

    # Return the ICS formatted calendar
    response = HttpResponse(
        cal.to_ical(),
        content_type='text/calendar',
        charset='utf-8'
    )

    response['Content-Disposition'] = f"attachment;filename={event_slug}.ics"

    return response


def meetings(request, template_name="meetings.html"):

    upcoming_meetings = Meeting.objects.filter(
        is_active=True,
        is_public=True,
        end_date__gte=timezone.now()
    ).order_by('start_date')

    return render(request, template_name, {
        'upcoming_meetings': upcoming_meetings
    })


def meeting_detail_short(request, meeting_id):
    meeting_obj = get_object_or_404(Meeting, id=meeting_id)
    return redirect(meeting_obj.get_absolute_url())


def meeting_detail(
    request,
    year,
    month,
    day,
    slug,
    meeting_id,
    template_name="meeting-detail.html"
):
    meeting_obj = get_object_or_404(Meeting, id=meeting_id)
    mentor_signed_up = False
    active_meeting_orders = None

    if request.user.is_authenticated:

        mentor = Mentor.objects.filter(user=request.user)

        if mentor.exists():
            mentor = mentor.first()
        else:
            return redirect('welcome')

        active_meeting_orders = MeetingOrder.objects.filter(
            meeting=meeting_obj,
            is_active=True
        )

        mentor_meeting_order = active_meeting_orders.filter(mentor=mentor)
        mentor_signed_up = True if mentor_meeting_order.count() else False

    return render(request, template_name, {
        'meeting': meeting_obj,
        'active_meeting_orders': active_meeting_orders,
        'mentor_signed_up': mentor_signed_up,
    })


@login_required
def meeting_sign_up(
    request,
    year,
    month,
    day,
    slug,
    meeting_id,
    student_id=False,
    template_name="meeting-sign-up.html"
):
    meeting_obj = get_object_or_404(
        Meeting,
        id=meeting_id
    )

    mentor = get_object_or_404(
        Mentor,
        user=request.user
    )

    meeting_orders = MeetingOrder.objects.filter(
        meeting=meeting_obj,
        is_active=True
    )

    user_meeting_order = meeting_orders.filter(mentor=mentor)
    user_signed_up = True if user_meeting_order.count() else False

    if request.method == 'POST':

        if user_signed_up:
            meeting_order = get_object_or_404(
                MeetingOrder,
                meeting=meeting_obj,
                mentor=mentor
            )
            meeting_order.is_active = False
            meeting_order.save()

            messages.success(
                request,
                'Thanks for letting us know!'
            )

        else:
            if not settings.DEBUG:
                ip = (
                    request.META['HTTP_X_FORWARDED_FOR'] or
                    request.META['REMOTE_ADDR']
                )
            else:
                ip = request.META['REMOTE_ADDR']

            meeting_order, created = MeetingOrder.objects.get_or_create(
                mentor=mentor,
                meeting=meeting_obj
            )

            meeting_order.ip = ip
            meeting_order.is_active = True
            meeting_order.save()

            messages.success(
                request,
                'Success! See you there!'
            )

            email(
                subject='Upcoming mentor meeting confirmation',
                template_name='meeting-confirm-mentor',
                merge_global_data={
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name,
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
                    'meeting_ics_url': meeting_obj.get_ics_url(),
                    'microdata_start_date': arrow.get(
                        meeting_obj.start_date
                    ).to('local').isoformat(),
                    'microdata_end_date': arrow.get(
                        meeting_obj.end_date
                    ).to('local').isoformat(),
                    'order': meeting_order,
                },
                recipients=[request.user.email],
                preheader=(
                    f"Thanks for signing up for our next meeting, {request.user.first_name}. "
                    f"We look forward to seeing there."
                ),
            )

        return HttpResponseRedirect(
            reverse(
                'meeting_detail',
                args=(
                    meeting_obj.start_date.year,
                    meeting_obj.start_date.month,
                    meeting_obj.start_date.day,
                    meeting_obj.meeting_type.slug,
                    meeting_obj.id
                )
            )
        )

    return render(request, template_name, {
        'meeting': meeting_obj,
        'user_signed_up': user_signed_up
    })


def meeting_announce(request, meeting_id):
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

        merge_data = {}
        recipients = []
        merge_global_data = {
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
        }

        for mentor in Mentor.objects.filter(
            is_active=True,
            user__is_active=True,
        ):
            recipients.append(mentor.user.email)
            merge_data[mentor.user.email] = {
                'first_name': mentor.user.first_name,
                'last_name': mentor.user.last_name,
            }

        email(
            subject='New meeting announced!',
            template_name='meeting-announcement-mentor',
            merge_data=merge_data,
            merge_global_data=merge_global_data,
            recipients=recipients,
            preheader='A new meeting has been announced. '
                      'Come join us for some amazing fun!',
        )

        meeting_obj.announced_date_mentors = timezone.now()
        meeting_obj.save()

        messages.success(
            request,
            'Meeting announced!'
        )
    else:
        messages.warning(
            request,
            'Meeting already announced.'
        )

    return redirect('cdc_admin')


def meeting_ics(request, year, month, day, slug, meeting_id):
    meeting_obj = get_object_or_404(Meeting, id=meeting_id)

    cal = Calendar()

    cal['prodid'] = '-//CoderDojoChi//coderdojochi.org//'
    cal['version'] = '2.0'

    event = Event()

    start_date = arrow.get(meeting_obj.start_date).format('YYYYMMDDTHHmmss')
    end_date = arrow.get(meeting_obj.end_date).format('YYYYMMDDTHHmmss')

    event['uid'] = f"MEETING{meeting_obj.id:04}@coderdojochi.org"

    event_name = f"{meeting_obj.meeting_type.code} - " if meeting_obj.meeting_type.code else ''
    event_name += meeting_obj.meeting_type.title

    event['summary'] = f"CoderDojoChi: {event_name}"
    event['dtstart'] = f"{start_date}Z"
    event['dtend'] = f"{end_date}Z"
    event['dtstamp'] = start_date

    location = (
        f"{meeting_obj.location.name}, {meeting_obj.location.address} {meeting_obj.location.address2}, "
        f"{meeting_obj.location.city}, {meeting_obj.location.state} {meeting_obj.location.zip}"
    )

    event['location'] = vText(location)
    event['url'] = meeting_obj.get_absolute_url()
    event['description'] = strip_tags(meeting_obj.meeting_type.description)

    # A value of 5 is the normal or "MEDIUM" priority.
    # see: https://tools.ietf.org/html/rfc5545#section-3.8.1.9
    event['priority'] = 5

    cal.add_component(event)
    event_slug = "coderdojochi-meeting-{date}".format(
        date=arrow.get(
            meeting_obj.start_date
        ).to('local').format('MM-DD-YYYY-HH:mma')
    )

    # Return the ICS formatted calendar
    response = HttpResponse(
        cal.to_ical(),
        content_type='text/calendar',
        charset='utf-8'
    )
    response['Content-Disposition'] = f"attachment;filename={event_slug}.ics"

    return response


def volunteer(request, template_name="volunteer.html"):
    mentors = Mentor.objects.select_related('user').filter(
        is_active=True,
        is_public=True,
        background_check=True,
        avatar_approved=True,
    ).annotate(
        session_count=Count('mentororder')
    ).order_by('-user__role', '-session_count')

    upcoming_meetings = Meeting.objects.filter(
        is_active=True,
        is_public=True,
        end_date__gte=timezone.now()
    ).order_by('start_date')[:3]

    return render(request, template_name, {
        'mentors': mentors,
        'upcoming_meetings': upcoming_meetings
    })


def faqs(request, template_name="faqs.html"):
    return render(request, template_name)


@login_required
def dojo(request):
    if not request.user.role:
        if 'next' in request.GET:
            return HttpResponseRedirect(
                f"{reverse('welcome')}?next={request.GET['next']}"
            )
        else:
            messages.warning(
                request,
                'Tell us a little about yourself before going on to your dojo.'
            )
            return redirect('welcome')

    if request.user.role == 'mentor':
        return dojo_mentor(request)

    if request.user.role == 'guardian':
        return dojo_guardian(request)


# TODO: upcoming classes needs to be all upcoming classes with a
#       choice to RSVP in dojo page
# TODO: upcoming meetings needs to be all upcoming meetings with a
#       choice to RSVP in dojo page
@login_required
def dojo_mentor(request, template_name='mentor/dojo.html'):

    highlight = (
        request.GET['highlight'] if 'highlight' in request.GET else False
    )

    context = {
        'user': request.user,
        'highlight': highlight,
    }

    mentor = get_object_or_404(Mentor, user=request.user)

    orders = MentorOrder.objects.select_related().filter(
        is_active=True,
        mentor=mentor,
    )

    upcoming_sessions = orders.filter(
        is_active=True,
        session__end_date__gte=timezone.now()
    ).order_by('session__start_date')

    past_sessions = orders.filter(
        is_active=True,
        session__end_date__lte=timezone.now()
    ).order_by('session__start_date')

    meeting_orders = MeetingOrder.objects.select_related().filter(
        mentor=mentor
    )

    upcoming_meetings = meeting_orders.filter(
        is_active=True,
        meeting__is_public=True,
        meeting__end_date__gte=timezone.now()
    ).order_by('meeting__start_date')

    context['account_complete'] = False

    if (
        mentor.user.first_name and
        mentor.user.last_name and
        mentor.avatar and
        mentor.background_check and
        past_sessions.count() > 0
    ):
        context['account_complete'] = True

    if request.method == 'POST':
        form = MentorForm(
            request.POST,
            request.FILES,
            instance=mentor
        )

        user_form = CDCModelForm(
            request.POST,
            request.FILES,
            instance=mentor.user
        )

        if (
            form.is_valid() and
            user_form.is_valid()
        ):
            form.save()
            user_form.save()
            messages.success(
                request,
                'Profile information saved.'
            )

            return redirect('dojo')

        else:
            messages.error(
                request,
                'There was an error. Please try again.'
            )

    else:
        form = MentorForm(instance=mentor)
        user_form = CDCModelForm(instance=mentor.user)

    context['mentor'] = mentor
    context['upcoming_sessions'] = upcoming_sessions
    context['upcoming_meetings'] = upcoming_meetings
    context['past_sessions'] = past_sessions

    context['mentor'] = mentor
    context['form'] = form
    context['user_form'] = user_form

    return render(request, template_name, context)


@login_required
def dojo_guardian(request, template_name='guardian/dojo.html'):

    highlight = (
        request.GET['highlight'] if 'highlight' in request.GET else False
    )

    context = {
        'user': request.user,
        'highlight': highlight,
    }

    guardian = get_object_or_404(
        Guardian,
        user=request.user
    )

    students = Student.objects.filter(
        is_active=True,
        guardian=guardian,
    )

    student_orders = Order.objects.filter(
        student__in=students,
    )

    upcoming_orders = student_orders.filter(
        is_active=True,
        session__end_date__gte=timezone.now(),
    ).order_by('session__start_date')

    past_orders = student_orders.filter(
        is_active=True,
        session__end_date__lte=timezone.now(),
    ).order_by('session__start_date')

    if request.method == 'POST':
        form = GuardianForm(
            request.POST,
            instance=guardian
        )

        user_form = CDCModelForm(
            request.POST,
            instance=guardian.user
        )

        if form.is_valid() and user_form.is_valid():
            form.save()
            user_form.save()
            messages.success(
                request,
                'Profile information saved.'
            )

            return redirect('dojo')

        else:
            messages.error(
                request,
                'There was an error. Please try again.'
            )

    else:
        form = GuardianForm(instance=guardian)
        user_form = CDCModelForm(instance=guardian.user)

    context['students'] = students
    context['upcoming_orders'] = upcoming_orders
    context['past_orders'] = past_orders
    context['guardian'] = guardian
    context['form'] = form
    context['user_form'] = user_form

    return render(request, template_name, context)


def mentors(request, template_name="mentors.html"):
    mentors = Mentor.objects.filter(
        is_active=True,
        is_public=True,
        background_check=True,
        avatar_approved=True,
    ).order_by('user__date_joined')

    # mentors = Mentor.objects.filter(
    #     is_active=True,
    #     is_public=True
    # ).order_by('user__date_joined')

    return render(request, template_name, {
        'mentors': mentors
    })


def mentor_detail(
    request,
    mentor_id=False,
    template_name="mentor-detail.html"
):

    mentor = get_object_or_404(Mentor, id=mentor_id)

    if not mentor.is_public:
        messages.error(
            request,
            'Invalid mentor ID.'
        )

        return redirect('mentors')

    return render(
        request,
        template_name,
        {
            'mentor': mentor
        }
    )


@login_required
def mentor_approve_avatar(request, mentor_id=False):
    mentor = get_object_or_404(Mentor, id=mentor_id)

    if not request.user.is_staff:
        messages.error(
            request,
            'You do not have permissions to moderate content.'
        )

        return HttpResponseRedirect(
            f"{reverse('account_login')}?next={mentor.get_approve_avatar_url()}"
        )

    mentor.avatar_approved = True
    mentor.save()

    if mentor.background_check:
        messages.success(
            request,
            f"{mentor.user.first_name} {mentor.user.last_name}'s avatar approved and their account is now public."
        )

        return HttpResponseRedirect(
            f"{reverse('mentors')}{mentor.id}"
        )

    else:
        messages.success(
            request,
            (
                f"{mentor.user.first_name}{mentor.user.last_name}'s avatar approved but they have yet "
                f"to fill out the 'background search' form."
            )
        )

        return redirect('mentors')


@login_required
def mentor_reject_avatar(request, mentor_id=False):
    mentor = get_object_or_404(Mentor, id=mentor_id)

    if not request.user.is_staff:
        messages.error(
            request,
            'You do not have permissions to moderate content.'
        )

        return HttpResponseRedirect(
            f"{reverse('account_login')}?next={mentor.get_reject_avatar_url()}"
        )

    mentor.avatar_approved = False
    mentor.save()

    email(
        subject='Your CoderDojoChi avatar...',
        template_name='class-announcement-mentor',
        merge_global_data={
            'site_url': settings.SITE_URL,
        },
        recipients=[mentor.user.email],
    )

    messages.warning(
        request,
        (
            f"{mentor.user.first_name} {mentor.user.last_name}'s avatar rejected and their account "
            f"is no longer public. An email notice has been sent to the mentor."
        )
    )

    return redirect('mentors')


@login_required
def student_detail(
    request,
    student_id=False,
    template_name="student-detail.html"
):
    access = True

    if request.user.role == 'guardian' and student_id:
        # for the specific student redirect to admin page
        try:
            student = Student.objects.get(id=student_id, is_active=True)
        except ObjectDoesNotExist:
            return redirect('dojo')

        try:
            guardian = Guardian.objects.get(user=request.user, is_active=True)
        except ObjectDoesNotExist:
            return redirect('dojo')

        if not student.guardian == guardian:
            access = False

        form = StudentForm(instance=student)
    else:
        access = False

    if not access:
        return redirect('dojo')
        messages.error(
            request,
            'You do not have permissions to edit this student.'
        )

    if request.method == 'POST':
        if 'delete' in request.POST:
            student.is_active = False
            student.save()
            messages.success(
                request,
                f"Student \"{student.first_name} {student.last_name}\" Deleted."
            )
            return redirect('dojo')

        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student Updated.')
            return redirect('dojo')

    return render(
        request,
        template_name,
        {
            'form': form
        }
    )


def donate(request, template_name="donate.html"):
    if request.method == 'POST':

        # if new donation form submit
        if (
            'first_name' in request.POST and
            'last_name' in request.POST and
            'email' in request.POST and
            'amount' in request.POST
        ):
            donation = Donation(
                first_name=request.POST['first_name'],
                last_name=request.POST['last_name'],
                email=request.POST['email'],
                amount=request.POST['amount'],
            )

            if 'referral_code' in request.POST and request.POST['referral_code']:
                donation.referral_code = request.POST['referral_code']

            donation.save()

            return HttpResponse(donation.id)

        else:
            return HttpResponse('fail')

    referral_heading = None
    referral_code = None
    referral_disclaimer = None

    if 'zirmed' in request.get_full_path():
        referral_heading = 'Join ZirMed and donate to CoderDojoChi!'
        referral_code = 'ZIRMED'
        referral_disclaimer = 'ZirMed is an organization dedicated to doing things and we can talk about it here.'

    paypal_dict = {
        'business': settings.PAYPAL_BUSINESS_ID,
        'amount': '25',
        'item_name': 'CoderDojoChi Donation',
        'cmd': '_donations',
        'lc': 'US',
        'invoice': '',
        'currency_code': 'USD',
        'no_note': '0',
        'cn': 'Add a message for CoderDojoChi to read:',
        'no_shipping': '1',
        'address_override': '1',
        'first_name': '',
        'last_name': '',
        'notify_url': request.build_absolute_uri(reverse('paypal-ipn')),
        'return_url': request.build_absolute_uri('return'),
        'cancel_return': request.build_absolute_uri('cancel'),
        'bn': 'PP-DonationsBF:btn_donateCC_LG.gif:NonHosted'
    }

    form = PayPalPaymentsForm(initial=paypal_dict)

    return render(request, template_name, {
        'form': form,
        'referral_heading': referral_heading,
        'referral_code': referral_code,
        'referral_disclaimer': referral_disclaimer
    })


@csrf_exempt
def donate_cancel(request):
    messages.error(
        request,
        (
            f"Looks like you cancelled the donation process. "
            f"Please feel free to <a href='{reverse('contact')}'>contact us</a> "
            f"if you need any help."
        )
    )

    return redirect('donate')


@csrf_exempt
def donate_return(request):
    messages.success(
        request,
        'Your donation is being processed. '
        'You should receive a confirmation email shortly. Thanks again!'
    )
    return redirect('donate')


def contact(request, template_name="contact.html"):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        human = True

        if form.is_valid():
            if request.POST['human']:
                messages.error(request, 'Bad robot.')
                human = False

            if human:
                msg = EmailMultiAlternatives(
                    subject=f"{request.POST['name']} | CoderDojoChi Contact Form",
                    body=request.POST['body'],
                    from_email=f"CoderDojoChi<{settings.DEFAULT_FROM_EMAIL}>",
                    reply_to=[
                        f"{request.POST['name']}<{request.POST['email']}>"
                    ],
                    to=[settings.CONTACT_EMAIL]
                )

                msg.attach_alternative(
                    request.POST['body'].replace(
                        "\r\n",
                        "<br />"
                    ).replace(
                        "\n",
                        "<br />"
                    ),
                    'text/html'
                )

                msg.send()

                messages.success(
                    request,
                    "Thank you for contacting us! We will respond as soon as possible."
                )

            form = ContactForm()
        else:
            messages.error(
                request,
                "There was an error. Please try again."
            )
    else:
        form = ContactForm()

    return render(
        request,
        template_name,
        {
            'form': form
        }
    )


def privacy(request, template_name="privacy.html"):
    return render(request, template_name)


@login_required
def cdc_admin(request, template_name="admin.html"):
    if not request.user.is_staff:
        messages.error(
            request,
            'You do not have permission to access this page.'
        )
        return redirect('sessions')

    sessions = Session.objects.select_related().annotate(
        num_orders=Count(
            'order'
        ),

        num_attended=Count(
            Case(
                When(
                    order__check_in__isnull=False,
                    then=1
                )
            )
        ),

        is_future=Case(
            When(
                end_date__gte=timezone.now(),
                then=1
            ),
            default=0,
            output_field=IntegerField(),
        )
    ).order_by(
        '-start_date'
    )

    meetings = Meeting.objects.select_related().annotate(
        num_orders=Count(
            'meetingorder'
        ),

        num_attended=Count(
            Case(
                When(
                    meetingorder__check_in__isnull=False,
                    then=1
                )
            )
        ),

        is_future=Case(
            When(
                end_date__gte=timezone.now(),
                then=1
            ),
            default=0,
            output_field=IntegerField(),
        )

    ).order_by(
        '-start_date'
    )

    orders = Order.objects.select_related()

    total_past_orders = orders.filter(is_active=True)
    total_past_orders_count = total_past_orders.count()
    total_checked_in_orders = orders.filter(
        is_active=True,
        check_in__isnull=False
    )
    total_checked_in_orders_count = total_checked_in_orders.count()

    # Genders
    gender_count = list(
        Counter(
            e.student.get_clean_gender() for e in total_checked_in_orders
        ).items()
    )
    gender_count = sorted(
        list(dict(gender_count).items()),
        key=operator.itemgetter(1)
    )

    # Ages
    ages = sorted(
        list(
            e.student.get_age(e.session.start_date) for e in total_checked_in_orders
        )
    )
    age_count = sorted(
        list(dict(
            list(
                Counter(ages).items()
            )
        ).items()),
        key=operator.itemgetter(0)
    )

    # Average Age
    average_age = int(
        round(
            sum(ages) / float(len(ages))
        )
    )

    return render(
        request,
        template_name,
        {
            'age_count': age_count,
            'average_age': average_age,
            'gender_count': gender_count,
            'meetings': meetings,
            # 'past_meetings_count': past_meetings_count,
            # 'past_sessions': past_sessions,
            # 'past_sessions_count': past_sessions_count,
            'sessions': sessions,
            'total_checked_in_orders_count': total_checked_in_orders_count,
            'total_past_orders_count': total_past_orders_count,
            # 'upcoming_meetings': upcoming_meetings,
            # 'upcoming_meetings_count': upcoming_meetings_count,
            # 'upcoming_sessions': upcoming_sessions,
            # 'upcoming_sessions_count': upcoming_sessions_count,
        }
    )


@login_required
@never_cache
def session_stats(request, session_id, template_name="session-stats.html"):

    if not request.user.is_staff:
        messages.error(
            request,
            'You do not have permission to access this page.'
        )
        return redirect('sessions')

    session_obj = get_object_or_404(
        Session,
        id=session_id
    )

    current_orders_checked_in = session_obj.get_current_orders(
        checked_in=True
    )

    students_checked_in = current_orders_checked_in.values('student')

    if students_checked_in:
        attendance_percentage = round(
            (
                float(current_orders_checked_in.count()) /
                float(session_obj.get_current_students().count())
            ) * 100
        )

    else:
        attendance_percentage = False

    # Genders
    gender_count = list(
        Counter(
            e.student.get_clean_gender()
            for e in session_obj.get_current_orders()
        ).items()
    )

    gender_count = sorted(
        list(dict(gender_count).items()),
        key=operator.itemgetter(1)
    )

    # Ages
    ages = sorted(
        list(
            e.student.get_age(e.session.start_date) for e in session_obj.get_current_orders()
        )
    )

    age_count = sorted(
        list(dict(
            list(
                Counter(ages).items()
            )
        ).items()),
        key=operator.itemgetter(1)
    )

    # Average Age
    average_age = False
    if current_orders_checked_in:
        student_ages = []
        for order in current_orders_checked_in:
            student_ages.append(order.student.get_age(order.session.start_date))

        average_age = (
            reduce(
                lambda x, y: x + y,
                student_ages
            ) /
            len(student_ages)
        )

    return render(
        request,
        template_name,
        {
            'session': session_obj,
            'students_checked_in': students_checked_in,
            'attendance_percentage': attendance_percentage,
            'average_age': average_age,
            'age_count': age_count,
            'gender_count': gender_count
        }
    )


@login_required
@never_cache
def session_check_in(
    request,
    session_id,
    template_name="session-check-in.html"
):

    if not request.user.is_staff:
        messages.error(
            request,
            'You do not have permission to access this page.'
        )

        return redirect('sessions')

    if request.method == 'POST':
        if 'order_id' in request.POST:
            order = get_object_or_404(
                Order,
                id=request.POST['order_id']
            )

            if order.check_in:
                order.check_in = None
            else:
                order.check_in = timezone.now()

            if (
                f"{order.guardian.user.first_name} {order.guardian.user.last_name}" !=
                request.POST['order_alternate_guardian']
            ):
                order.alternate_guardian = request.POST[
                    'order_alternate_guardian'
                ]

            order.save()
        else:
            messages.error(request, 'Invalid Order')

    # Get current session
    session = get_object_or_404(Session, id=session_id)

    # Active Session
    active_session = True if timezone.now() < session.end_date else False

    # get the orders
    orders = Order.objects.select_related().filter(
        session_id=session_id
    ).annotate(
        num_attended=Count(
            Case(
                When(
                    student__order__check_in__isnull=False,
                    then=1
                )
            )
        ),
        num_missed=Count(
            Case(
                When(
                    student__order__check_in__isnull=True,
                    then=1
                )
            )
        )
    )

    if active_session:
        active_orders = orders.filter(
            is_active=True
        ).order_by(
            'student__first_name'
        )

    else:
        active_orders = orders.filter(
            is_active=True,
            check_in__isnull=False
        ).order_by(
            'student__first_name'
        )

    inactive_orders = orders.filter(
        is_active=False
    ).order_by('-updated_at')

    no_show_orders = orders.filter(
        is_active=True,
        check_in__isnull=True
    )

    checked_in_orders = orders.filter(
        is_active=True,
        check_in__isnull=False
    )

    # Genders
    gender_count = sorted(
        list(dict(
            list(
                Counter(
                    e.student.get_clean_gender() for e in active_orders
                ).items()
            )
        ).items()),
        key=operator.itemgetter(1)
    )

    # Ages
    ages = sorted(
        list(
            e.student.get_age(e.session.start_date) for e in active_orders
        )
    )

    age_count = sorted(
        list(dict(
            list(
                Counter(ages).items()
            )
        ).items()),
        key=operator.itemgetter(0)
    )

    # age_count = sorted(
    #     dict(
    #         list(
    #             Counter(ages).items()
    #         )
    #     ).items(),
    #     key=operator.itemgetter(1),
    #     reverse=True
    # )

    # Average Age
    average_age = int(
        round(
            sum(ages) / float(len(ages))
        )
    ) if orders and ages else 0

    return render(
        request,
        template_name,
        {
            'session': session,
            'active_session': active_session,
            'active_orders': active_orders,
            'inactive_orders': inactive_orders,
            'no_show_orders': no_show_orders,
            'gender_count': gender_count,
            'age_count': age_count,
            'average_age': average_age,
            'checked_in_orders': checked_in_orders,
        }
    )


@login_required
@never_cache
def session_check_in_mentors(
    request,
    session_id,
    template_name="session-check-in-mentors.html"
):

    if not request.user.is_staff:
        messages.error(
            request,
            'You do not have permission to access this page.'
        )
        return redirect('sessions')

    if request.method == 'POST':
        if 'order_id' in request.POST:
            order = get_object_or_404(
                MentorOrder,
                id=request.POST['order_id']
            )

            if order.check_in:
                order.check_in = None
            else:
                order.check_in = timezone.now()

            order.save()
        else:
            messages.error(
                request,
                'Invalid Order'
            )

    session = get_object_or_404(Session, id=session_id)

    # Active Session
    active_session = True if timezone.now() < session.end_date else False

    # get the orders
    orders = MentorOrder.objects.select_related().filter(
        session_id=session_id
    )

    if active_session:
        active_orders = orders.filter(
            is_active=True
        ).order_by(
            'mentor__user__first_name'
        )

    else:
        active_orders = orders.filter(
            is_active=True,
            check_in__isnull=False
        ).order_by(
            'mentor__user__first_name'
        )

    inactive_orders = orders.filter(
        is_active=False
    ).order_by('-updated_at')

    no_show_orders = orders.filter(
        is_active=True,
        check_in__isnull=True
    )

    checked_in_orders = orders.filter(
        is_active=True,
        check_in__isnull=False
    )

    return render(
        request,
        template_name,
        {
            'session': session,
            'active_session': active_session,
            'active_orders': active_orders,
            'inactive_orders': inactive_orders,
            'no_show_orders': no_show_orders,
            'checked_in_orders': checked_in_orders,
        }
    )


@login_required
@never_cache
def session_donations(
    request,
    session_id,
    template_name="session-donations.html"
):
    # TODO: we should really turn this into a decorator
    if not request.user.is_staff:
        messages.error(
            request,
            'You do not have permission to access this page.'
        )
        return redirect('dojo')

    session = get_object_or_404(Session, id=session_id)

    default_form = DonationForm(initial={'session': session})
    default_form.fields['user'].queryset = User.objects.filter(
        id__in=Order.objects.filter(
            session=session
        ).values_list(
            'guardian__user__id', flat=True
        )
    )

    form = default_form

    donations = Donation.objects.filter(session=session)

    if request.method == 'POST':
        form = DonationForm(request.POST)
        if form.is_valid():
            form.save()
            form = default_form
            messages.success(
                request,
                'Donation added!'
            )

    return render(
        request,
        template_name,
        {
            'form': form,
            'session': session,
            'donations': donations
        }
    )


@login_required
@never_cache
def meeting_check_in(
    request,
    meeting_id,
    template_name="meeting-check-in.html"
):

    if not request.user.is_staff:
        messages.error(
            request,
            'You do not have permission to access this page.'
        )
        return redirect('dojo')

    if request.method == 'POST':
        if 'order_id' in request.POST:
            order = get_object_or_404(
                MeetingOrder,
                id=request.POST['order_id']
            )

            if order.check_in:
                order.check_in = None
            else:
                order.check_in = timezone.now()

            order.save()
        else:
            messages.error(request, 'Invalid Order')

    orders = MeetingOrder.objects.select_related().filter(
        meeting=meeting_id
    ).order_by(
        'mentor__user__first_name'
    )

    active_orders = orders.filter(
        is_active=True
    )

    inactive_orders = orders.filter(
        is_active=False
    )

    checked_in = orders.filter(
        is_active=True,
        check_in__isnull=False
    )

    return render(
        request,
        template_name,
        {
            'active_orders': active_orders,
            'inactive_orders': inactive_orders,
            'checked_in': checked_in,
        }
    )


@never_cache
def session_announce_mentors(request, session_id):
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
        merge_global_data = {
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
            'min_age_limitation': session_obj.min_age_limitation,
            'max_age_limitation': session_obj.max_age_limitation,
            'class_location_name': session_obj.location.name,
            'class_location_address': session_obj.location.address,
            'class_location_address2': session_obj.location.address2,
            'class_location_city': session_obj.location.city,
            'class_location_state': session_obj.location.state,
            'class_location_zip': session_obj.location.zip,
            'class_additional_info': session_obj.additional_info,
            'class_url': session_obj.get_absolute_url(),
            'class_ics_url': session_obj.get_ics_url()
        }
        merge_data = {}
        recipients = []
        # send mentor announcements
        for mentor in Mentor.objects.filter(
            is_active=True,
            user__is_active=True,
        ):
            recipients.append(mentor.user.email)
            merge_data[mentor.user.email] = {
                'first_name': mentor.user.first_name,
                'last_name': mentor.user.last_name,
            }

        email(
            subject='New CoderDojoChi class date announced! Come mentor!',
            template_name='class-announcement-mentor',
            merge_data=merge_data,
            merge_global_data=merge_global_data,
            recipients=recipients,
            preheader='Help us make a huge difference! '
                      'A brand new class was just announced.',
        )

        session_obj.announced_date_mentors = timezone.now()
        session_obj.save()

        messages.success(
            request,
            'Session announced!'
        )

    else:
        messages.warning(
            request,
            'Session already announced.'
        )

    return redirect('cdc_admin')


@never_cache
def session_announce_guardians(request, session_id):
    # if not request.user.is_staff:
    #     messages.error(
    #         request,
    #         'You do not have permission to access this page.'
    #     )
    #     return redirect('home')

    session_obj = get_object_or_404(
        Session,
        id=session_id
    )

    if not session_obj.announced_date_guardians:
        merge_data = {}
        recipients = []
        merge_global_data = {
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
            'min_age_limitation': session_obj.min_age_limitation,
            'max_age_limitation': session_obj.max_age_limitation,
            'class_location_name': session_obj.location.name,
            'class_location_address': session_obj.location.address,
            'class_location_address2': session_obj.location.address2,
            'class_location_city': session_obj.location.city,
            'class_location_state': session_obj.location.state,
            'class_location_zip': session_obj.location.zip,
            'class_additional_info': session_obj.additional_info,
            'class_url': session_obj.get_absolute_url(),
            'class_ics_url': session_obj.get_ics_url()
        }

        for guardian in Guardian.objects.filter(
            is_active=True,
            user__is_active=True,
        ):
            recipients.append(guardian.user.email)
            merge_data[guardian.user.email] = {
                'first_name': guardian.user.first_name,
                'last_name': guardian.user.last_name,
            }

        email(
            subject='New CoderDojoChi class date announced!',
            template_name='class-announcement-guardian',
            merge_data=merge_data,
            merge_global_data=merge_global_data,
            recipients=recipients,
            preheader='We\'re super excited to bring you another class '
                      'date. Sign up to reserve your spot',
        )

        session_obj.announced_date_guardians = timezone.now()
        session_obj.save()

        messages.success(
            request,
            'Session announced!'
        )

    else:
        messages.warning(
            request,
            'Session already announced.'
        )

    return redirect('cdc_admin')


@csrf_exempt
# the "service" that computers run to self update
def check_system(request):
    # set up variables
    runUpdate = True
    responseString = ""
    cmdString = (
        'sh -c "$(curl -fsSL '
        'https://raw.githubusercontent.com/CoderDojoChi'
        '/linux-update/master/update.sh)"'
    )
    halfday = timedelta(hours=12)
    # halfday = timedelta(seconds=15)

    if (
        Session.objects.filter(
            is_active=True,
            start_date__lte=timezone.now(),
            mentor_end_date__gte=timezone.now()
        ).count()
    ):
        runUpdate = False

    # uuid is posted from the computer using a bash script
    # see:
    # https://raw.githubusercontent.com/CoderDojoChi
    # /linux-update/master/etc/init.d/coderdojochi-phonehome
    uuid = request.POST.get('uuid')

    if uuid:
        equipmentType = EquipmentType.objects.get(name="Laptop")
        if equipmentType:
            equipment, created = Equipment.objects.get_or_create(
                uuid=uuid,
                defaults={
                    'equipment_type': equipmentType
                }
            )

            # check for blank values of last_system_update.
            # If blank, assume we need to run it
            if not equipment.last_system_update:
                equipment.force_update_on_next_boot = True

            # do we need to update?
            if (
                runUpdate and
                (
                    equipment.force_update_on_next_boot or
                    (timezone.now() - equipment.last_system_update > halfday)
                )
            ):
                responseString = cmdString
                equipment.last_system_update = timezone.now()
                equipment.force_update_on_next_boot = False

            # update the last_system_update_check_in to now
            equipment.last_system_update_check_in = timezone.now()
            equipment.save()

    return HttpResponse(responseString)
