# -*- coding: utf-8 -*-

import sys
import arrow
import calendar
from collections import Counter
from datetime import date, timedelta
from icalendar import Calendar, Event, vText
import operator
from paypal.standard.forms import PayPalPaymentsForm

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.mail import get_connection, EmailMessage, EmailMultiAlternatives
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.db.models import Count, Case, When
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.utils.html import strip_tags
from django.views.decorators.csrf import csrf_exempt

from coderdojochi.util import local_to_utc
from coderdojochi.models import (Mentor, Guardian, Student, Session, Order, MentorOrder,
                                 Meeting, MeetingOrder, Donation, CDCUser, EquipmentType, Equipment)
from coderdojochi.forms import MentorForm, GuardianForm, StudentForm, ContactForm

# this will assign User to our custom CDCUser
User = get_user_model()


def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month / 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])

    return date(year, month, day)


def home(request, template_name="home.html"):
    upcoming_classes = Session.objects.filter(
        active=True,
        end_date__gte=timezone.now()
    ).order_by('start_date')

    if not request.user.is_authenticated() or not request.user.role == 'mentor':
        upcoming_classes = upcoming_classes.filter(public=True)

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
                form = MentorForm(request.POST, instance=get_object_or_404(Mentor, user=user))
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
                                return HttpResponseRedirect(u'{}?enroll=True&student={}'.format(next_url, new_student.id))
                            else:
                                return HttpResponseRedirect(next_url)
                        else:
                            return HttpResponseRedirect(reverse('welcome'))

            if keepGoing:
                if form.is_valid():
                    form.save()
                    messages.success(request, 'Profile information saved.')

                    if next_url:
                        if 'enroll' in request.GET:
                            return HttpResponseRedirect(u'{}?enroll=True'.format(next_url))
                        else:
                            return HttpResponseRedirect(next_url)
                    else:
                        return HttpResponseRedirect(reverse('dojo'))
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
                    active=True,
                    public=True
                ).order_by('start_date').first()

                if next_meeting:
                    merge_vars['next_intro_meeting_url'] = next_meeting.get_absolute_url()
                    merge_vars['next_intro_meeting_ics_url'] = next_meeting.get_ics_url()

                sendSystemEmail(request, 'Welcome!', 'coderdojochi-welcome-mentor', merge_vars)

                next_url = u'?next={}'.format(next_url) if next_url else reverse('dojo')

                return HttpResponseRedirect(next_url)
            else:
                # check for next upcoming class
                next_class = Session.objects.filter(active=True).order_by('start_date').first()

                if next_class:
                    merge_vars['next_class_url'] = next_class.get_absolute_url()
                    merge_vars['next_class_ics_url'] = next_class.get_ics_url()

                sendSystemEmail(request, 'Welcome!', 'coderdojochi-welcome-guardian', merge_vars)

                next_url = u'?next={}'.format(next_url) if next_url else reverse('welcome')

                return HttpResponseRedirect(next_url)

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
                return HttpResponseRedirect(next_url)
            else:
                return HttpResponseRedirect(reverse('dojo'))
        else:
            students = account.get_students() if account.get_students().count() else False

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
    prev_date = add_months(calendar_date, -1)
    next_date = add_months(calendar_date, 1)

    all_sessions = Session.objects.filter(
        active=True,
        end_date__gte=timezone.now()
    ).order_by('start_date')

    if not request.user.is_authenticated() or not request.user.role == 'mentor':
        all_sessions = all_sessions.filter(public=True)

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


def session_detail_enroll(request, year, month, day, slug, session_id, template_name="session-detail.html"):
    return session_detail(request, year, month, day, slug, session_id, template_name, enroll=True)


def session_detail(request, year, month, day, slug, session_id, template_name="session-detail.html", enroll=False):
    session_obj = get_object_or_404(Session, id=session_id)
    mentor_signed_up = False
    account = False
    students = False
    active_mentors = Mentor.objects.filter(id__in=MentorOrder.objects.filter(session=session_obj, active=True).values('mentor__id'))

    if request.method == 'POST':
        if 'waitlist' in request.POST:

            if request.POST['waitlist'] == 'student':
                student = Student.objects.get(id=int(request.POST['account_id']))

                if request.POST['remove'] == 'true':
                    session_obj.waitlist_students.remove(student)
                    session_obj.save()
                    messages.success(
                        request,
                        'You have been removed from the waitlist. Thanks for letting us know.'
                    )
                else:
                    session_obj.waitlist_students.add(student)
                    session_obj.save()
                    messages.success(request, 'Added to waitlist successfully.')
            else:
                mentor = Mentor.objects.get(id=int(request.POST['account_id']))

                if request.POST['remove'] == 'true':
                    session_obj.waitlist_mentors.remove(mentor)
                    session_obj.save()
                    messages.success(
                        request,
                        'You have been removed from the waitlist. Thanks for letting us know.'
                    )
                else:
                    session_obj.waitlist_mentors.add(mentor)
                    session_obj.save()
                    messages.success(request, 'Added to waitlist successfully.')
        else:
            messages.error(request, 'Invalid request, please try again.')

        return HttpResponseRedirect(session_obj.get_absolute_url())

    upcoming_classes = Session.objects.filter(
        active=True,
        end_date__gte=timezone.now()
    ).order_by('start_date')

    if not request.user.is_authenticated() or not request.user.role == 'mentor':
        upcoming_classes = upcoming_classes.filter(public=True)

    if request.user.is_authenticated():
        if not request.user.role:
            messages.warning(request, 'Please select one of the following options to continue.')

            url = u'{}?next={}'.format(reverse('welcome'), session_obj.get_absolute_url())

            if 'enroll' in request.GET:
                url += '&enroll=True'

            return HttpResponseRedirect(url)

        if request.user.role == 'mentor':
            mentor = get_object_or_404(Mentor, user=request.user)
            account = mentor
            session_orders = MentorOrder.objects.filter(session=session_obj, active=True)
            mentor_signed_up = True if session_orders.filter(mentor=account).count() else False
            spots_remaining = session_obj.get_mentor_capacity() - session_orders.count()

            if enroll or 'enroll' in request.GET:
                return HttpResponseRedirect(session_obj.get_absolute_url() + '/sign-up/')
        else:
            guardian = get_object_or_404(Guardian, user=request.user)
            account = guardian
            students = guardian.get_students() if guardian.get_students().count() else False
            spots_remaining = session_obj.capacity - session_obj.get_current_students().count()

            if enroll or 'enroll' in request.GET:
                if not students:
                    return HttpResponseRedirect(
                        u'{}?next={}&enroll=True'.format(
                            reverse('welcome'),
                            session_obj.get_absolute_url()
                        )
                    )
                else:
                    if 'student' in request.GET:
                        return HttpResponseRedirect(
                            u'{}/sign-up/{}'.format(
                                session_obj.get_absolute_url(),
                                request.GET['student']
                            )
                        )

    else:
        spots_remaining = session_obj.capacity - session_obj.get_current_students().count()

    return render(request, template_name, {
        'session': session_obj,
        'active_mentors': active_mentors,
        'mentor_signed_up': mentor_signed_up,
        'students': students,
        'account': account,
        'upcoming_classes': upcoming_classes,
        'spots_remaining': spots_remaining
    })


@login_required
def session_sign_up(request, year, month, day, slug, session_id, student_id=False, template_name="session-sign-up.html"):
    session_obj = get_object_or_404(Session, id=session_id)
    student = False
    guardian = False

    if not request.user.role:
        messages.warning(request, 'Please select one of the following options to continue.')
        return HttpResponseRedirect(u'{}?next={}'.format(reverse('welcome'), session_obj.get_absolute_url()))

    if request.user.role == 'mentor':

        mentor = get_object_or_404(Mentor, user=request.user)

        if not mentor.background_check:
            messages.warning(
                request,
                u'You cannot sign up for a class until you <a href="{}" target="_blank">fill out the background search form</a>.'.format(
                    'https://app.verifiedvolunteers.com/promoorder/6a34f727-3728-4f1a-b80b-7eb3265a3b93'
                )
            )
            return HttpResponseRedirect(reverse('dojo'))

        session_orders = MentorOrder.objects.filter(session=session_obj, active=True)
        user_signed_up = True if session_orders.filter(mentor=mentor).count() else False

        if not user_signed_up:
            if session_obj.get_mentor_capacity() <= session_orders.count():
                messages.error(
                    request,
                    'Sorry this class is at mentor capacity. Please check back soon and/or join us for another upcoming class!'
                )
                return HttpResponseRedirect(session_obj.get_absolute_url())
    else:
        student = get_object_or_404(Student, id=student_id)
        guardian = get_object_or_404(Guardian, user=request.user)
        user_signed_up = True if student.is_registered_for_session(session_obj) else False

        if not user_signed_up:
            if session_obj.capacity <= session_obj.get_current_students().count():
                messages.error(
                    request,
                    'Sorry this class has sold out. Please sign up for the wait list and/or check back later.'
                )
                return HttpResponseRedirect(session_obj.get_absolute_url())

    if request.method == 'POST':
        if user_signed_up:
            if request.user.role == 'mentor':
                order = get_object_or_404(MentorOrder, mentor=mentor, session=session_obj)
            else:
                order = get_object_or_404(Order, student=student, session=session_obj, active=True)

            order.active = False
            order.save()

            messages.success(request, 'Thanks for letting us know!')

        else:
            if not settings.DEBUG:
                ip = request.META['HTTP_X_FORWARDED_FOR'] or request.META['REMOTE_ADDR']
            else:
                ip = request.META['REMOTE_ADDR']

            if request.user.role == 'mentor':
                order, created = MentorOrder.objects.get_or_create(
                    mentor=mentor,
                    session=session_obj
                )
                order.ip = ip
                order.active = True
                order.save()
            else:
                order, created = Order.objects.get_or_create(
                    guardian=guardian,
                    student=student,
                    session=session_obj
                )
                order.ip = ip
                order.active = True
                order.save()

            # we dont want guardians getting 7 day reminder email if they sign up within 9 days
            if session_obj.start_date < timezone.now() + timedelta(days=9):
                order.week_reminder_sent = True

            # or 24 hours notice if signed up within 48 hours
            if session_obj.start_date < timezone.now() + timedelta(days=2):
                order.week_reminder_sent = True
                order.day_reminder_sent = True

            order.save()

            messages.success(request, 'Success! See you there!')

            if request.user.role == 'mentor':
                sendSystemEmail(
                    request,
                    'Upcoming class confirmation',
                    'coderdojochi-class-confirm-mentor',
                    {
                        'first_name': request.user.first_name,
                        'last_name': request.user.last_name,
                        'class_code': session_obj.course.code,
                        'class_title': session_obj.course.title,
                        'class_description': session_obj.course.description,
                        'class_start_date': arrow.get(session_obj.mentor_start_date).format('dddd, MMMM D, YYYY'),
                        'class_start_time': arrow.get(session_obj.mentor_start_date).format('h:mma'),
                        'class_end_date': arrow.get(session_obj.mentor_end_date).format('dddd, MMMM D, YYYY'),
                        'class_end_time': arrow.get(session_obj.mentor_end_date).format('h:mma'),
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
                )

            else:
                sendSystemEmail(
                    request,
                    'Upcoming class confirmation',
                    'coderdojochi-class-confirm-guardian',
                    {
                        'first_name': request.user.first_name,
                        'last_name': request.user.last_name,
                        'student_first_name': student.first_name,
                        'student_last_name': student.last_name,
                        'class_code': session_obj.course.code,
                        'class_title': session_obj.course.title,
                        'class_description': session_obj.course.description,
                        'class_start_date': arrow.get(session_obj.start_date).format('dddd, MMMM D, YYYY'),
                        'class_start_time': arrow.get(session_obj.start_date).format('h:mma'),
                        'class_end_date': arrow.get(session_obj.end_date).format('dddd, MMMM D, YYYY'),
                        'class_end_time': arrow.get(session_obj.end_date).format('h:mma'),
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
                )

        return HttpResponseRedirect(session_obj.get_absolute_url())

    return render(request, template_name, {
        'session': session_obj,
        'user_signed_up': user_signed_up,
        'student': student,
    })


def session_ics(request, year, month, day, slug, session_id):

    session_obj = get_object_or_404(Session, id=session_id)

    cal = Calendar()

    cal['prodid'] = '-//CoderDojoChi//coderdojochi.org//'
    cal['version'] = '2.0'
    cal['calscale'] = 'GREGORIAN'

    event = Event()

    start_date = local_to_utc(session_obj.start_date).format('YYYYMMDDTHHmmss')
    end_date = local_to_utc(session_obj.end_date).format('YYYYMMDDTHHmmss')

    event['uid'] = u'CLASS{:04}@coderdojochi.org'.format(session_obj.id)
    event['summary'] = u'CoderDojoChi: {} - {}'.format(
        session_obj.course.code,
        session_obj.course.title
    )
    event['dtstart'] = '{}Z'.format(start_date)
    event['dtend'] = '{}Z'.format(end_date)
    event['dtstamp'] = start_date

    if request.user.is_authenticated() and request.user.role == 'mentor':

        mentor_start_date = local_to_utc(session_obj.mentor_start_date).format('YYYYMMDDTHHmmss')

        mentor_end_date = local_to_utc(session_obj.mentor_end_date).format('YYYYMMDDTHHmmss')


        event['dtstart'] = '{}Z'.format(mentor_start_date)
        event['dtend'] = '{}Z'.format(mentor_end_date)
        event['dtstamp'] = mentor_start_date

    location = u'{}, {}, {}, {}, {} {}'.format(session_obj.location.name,
                                               session_obj.location.address,
                                               session_obj.location.address2,
                                               session_obj.location.city,
                                               session_obj.location.state,
                                               session_obj.location.zip
                                              )

    event['location'] = vText(location)

    event['url'] = session_obj.get_absolute_url()
    event['description'] = strip_tags(session_obj.course.description)

    # A value of 5 is the normal or "MEDIUM" priority.
    # see: https://tools.ietf.org/html/rfc5545#section-3.8.1.9
    event['priority'] = 5

    cal.add_component(event)

    event_slug = u'coderdojochi-class-{}'.format(
        arrow.get(session_obj.start_date).format('MM-DD-YYYY-HH:mma')
    )

    # Return the ICS formatted calendar
    response = HttpResponse(cal.to_ical(),
                            content_type='text/calendar',
                            charset='utf-8')
    response['Content-Disposition'] = u'attachment;filename={}.ics'.format(event_slug)

    return response


def meeting_detail(request, year, month, day, slug, meeting_id, template_name="meeting-detail.html"):
    meeting_obj = get_object_or_404(Meeting, id=meeting_id)
    mentor_signed_up = False
    active_meeting_orders = None

    if request.user.is_authenticated():
        mentor = get_object_or_404(Mentor, user=request.user)

        active_meeting_orders = MeetingOrder.objects.filter(meeting=meeting_obj, active=True)
        mentor_meeting_order = active_meeting_orders.filter(mentor=mentor)
        mentor_signed_up = True if mentor_meeting_order.count() else False

    return render(request, template_name, {
        'meeting': meeting_obj,
        'active_meeting_orders': active_meeting_orders,
        'mentor_signed_up': mentor_signed_up,
    })


@login_required
def meeting_sign_up(request, year, month, day, slug, meeting_id, student_id=False, template_name="meeting-sign-up.html"):
    meeting_obj = get_object_or_404(Meeting, id=meeting_id)
    mentor = get_object_or_404(Mentor, user=request.user)
    meeting_orders = MeetingOrder.objects.filter(meeting=meeting_obj, active=True)
    user_meeting_order = meeting_orders.filter(mentor=mentor)
    user_signed_up = True if user_meeting_order.count() else False

    if request.method == 'POST':

        if user_signed_up:
            meeting_order = get_object_or_404(MeetingOrder, meeting=meeting_obj, mentor=mentor)
            meeting_order.active = False
            meeting_order.save()

            messages.success(request, 'Thanks for letting us know!')

        else:
            if not settings.DEBUG:
                ip = request.META['HTTP_X_FORWARDED_FOR'] or request.META['REMOTE_ADDR']
            else:
                ip = request.META['REMOTE_ADDR']

            meeting_order, created = MeetingOrder.objects.get_or_create(
                mentor=mentor,
                meeting=meeting_obj
            )
            meeting_order.ip = ip
            meeting_order.active = True
            meeting_order.save()

            messages.success(request, 'Success! See you there!')

            sendSystemEmail(
                request,
                'Upcoming mentor meeting confirmation',
                'coderdojochi-meeting-confirm-mentor',
                {
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name,
                    'meeting_title': meeting_obj.meeting_type.title,
                    'meeting_description': meeting_obj.meeting_type.description,
                    'meeting_start_date': arrow.get(meeting_obj.start_date).format('dddd, MMMM D, YYYY'),
                    'meeting_start_time': arrow.get(meeting_obj.start_date).format('h:mma'),
                    'meeting_end_date': arrow.get(meeting_obj.end_date).format('dddd, MMMM D, YYYY'),
                    'meeting_end_time': arrow.get(meeting_obj.end_date).format('h:mma'),
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
            )

        return HttpResponseRedirect(
            reverse('meeting_detail', args=(
                meeting_obj.start_date.year,
                meeting_obj.start_date.month,
                meeting_obj.start_date.day,
                meeting_obj.meeting_type.slug,
                meeting_obj.id
            ))
        )

    return render(request, template_name, {
        'meeting': meeting_obj,
        'user_signed_up': user_signed_up
    })


def meeting_announce(request, meeting_id):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return HttpResponseRedirect(reverse('home'))

    meeting_obj = get_object_or_404(Meeting, id=meeting_id)

    if not meeting_obj.announced_date:

        # uses SMTP server specified in settings.py
        connection = get_connection()

        # If you don't open the connection manually, Django will automatically open,
        # then tear down the connection in msg.send()
        connection.open()

        for mentor in Mentor.objects.filter(active=True):
            sendSystemEmail(
                request,
                'Upcoming mentor meeting',
                'coderdojochi-meeting-announcement-mentor',
                {
                    'first_name': mentor.user.first_name,
                    'last_name': mentor.user.last_name,
                    'meeting_title': meeting_obj.meeting_type.title,
                    'meeting_description': meeting_obj.meeting_type.description,
                    'meeting_start_date': arrow.get(meeting_obj.start_date).format('dddd, MMMM D, YYYY'),
                    'meeting_start_time': arrow.get(meeting_obj.start_date).format('h:mma'),
                    'meeting_end_date': arrow.get(meeting_obj.end_date).format('dddd, MMMM D, YYYY'),
                    'meeting_end_time': arrow.get(meeting_obj.end_date).format('h:mma'),
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
                mentor.user.email
            )

        # Cleanup
        connection.close()

        meeting_obj.announced_date = timezone.now()
        meeting_obj.save()

        messages.success(request, 'Meeting announced!')
    else:
        messages.warning(request, 'Meeting already announced.')

    return HttpResponseRedirect(reverse('cdc_admin'))


def meeting_ics(request, year, month, day, slug, meeting_id):
    meeting_obj = get_object_or_404(Meeting, id=meeting_id)

    cal = Calendar()

    cal['prodid'] = '-//CoderDojoChi//coderdojochi.org//'
    cal['version'] = '2.0'

    event = Event()

    start_date = local_to_utc(meeting_obj.start_date).format('YYYYMMDDTHHmmss')
    end_date = local_to_utc(meeting_obj.end_date).format('YYYYMMDDTHHmmss')

    event['uid'] = u'MEETING{:04}@coderdojochi.org'.format(meeting_obj.id)

    event_name = u'{} - '.format(meeting_obj.meeting_type.code) if meeting_obj.meeting_type.code else ''

    event_name += meeting_obj.meeting_type.title

    event['summary'] = u'CoderDojoChi: {}'.format(event_name)
    event['dtstart'] = '{}Z'.format(start_date)
    event['dtend'] = '{}Z'.format(end_date)
    event['dtstamp'] = start_date

    location = u'{}, {}, {}, {}, {} {}'.format(meeting_obj.location.name,
                                              meeting_obj.location.address,
                                              meeting_obj.location.address2,
                                              meeting_obj.location.city,
                                              meeting_obj.location.state,
                                              meeting_obj.location.zip
                                              )

    event['location'] = vText(location)
    event['url'] = meeting_obj.get_absolute_url()
    event['description'] = strip_tags(meeting_obj.meeting_type.description)

    # A value of 5 is the normal or "MEDIUM" priority.
    # see: https://tools.ietf.org/html/rfc5545#section-3.8.1.9
    event['priority'] = 5

    cal.add_component(event)
    event_slug = u'coderdojochi-meeting-{}'.format(
        arrow.get(meeting_obj.start_date).format('MM-DD-YYYY-HH:mma')
    )

    # Return the ICS formatted calendar
    response = HttpResponse(cal.to_ical(),
                            content_type='text/calendar',
                            charset='utf-8')
    response['Content-Disposition'] = u'attachment;filename={}.ics'.format(event_slug)
    return response


def volunteer(request, template_name="volunteer.html"):
    mentors = Mentor.objects.select_related('user').filter(
        active=True,
        public=True,
        background_check=True,
        avatar_approved=True,
    ).annotate(
        session_count=Count('mentororder')
    ).order_by('-user__role', '-session_count')

    upcoming_meetings = Meeting.objects.filter(
        active=True,
        public=True,
        end_date__gte=timezone.now()
    ).order_by('start_date')[:3]

    return render(request, template_name, {
        'mentors': mentors,
        'upcoming_meetings': upcoming_meetings
    })


def faqs(request, template_name="faqs.html"):
    return render(request, template_name)


@login_required
def dojo(request, template_name="dojo.html"):
    highlight = request.GET['highlight'] if 'highlight' in request.GET else False

    context = {
        'user': request.user,
        'highlight': highlight,
    }

    if request.user.role:
        if request.user.role == 'mentor':
            mentor = get_object_or_404(Mentor, user=request.user)
            account = mentor
            mentor_sessions = Session.objects.filter(id__in=MentorOrder.objects.filter(mentor=mentor, active=True).values('session__id'))

            upcoming_sessions = mentor_sessions.filter(
                active=True,
                end_date__gte=timezone.now()
            ).order_by('start_date')
            past_sessions = mentor_sessions.filter(
                active=True,
                end_date__lte=timezone.now()
            ).order_by('start_date')
            upcoming_meetings = Meeting.objects.filter(
                active=True,
                public=True,
                end_date__gte=timezone.now()
            ).order_by('start_date')

            if request.method == 'POST':
                form = MentorForm(request.POST, request.FILES, instance=account)
                if form.is_valid():
                    form.save()
                    messages.success(request, 'Profile information saved.')
                    return HttpResponseRedirect(reverse('dojo'))
                else:
                    messages.error(request, 'There was an error. Please try again.')
            else:
                form = MentorForm(instance=account)

            context['upcoming_sessions'] = upcoming_sessions
            context['upcoming_meetings'] = upcoming_meetings
            context['past_sessions'] = past_sessions

        if request.user.role == 'guardian':
            guardian = get_object_or_404(Guardian, user=request.user)
            account = guardian
            students = Student.objects.filter(guardian=guardian)
            student_orders = Order.objects.filter(student__in=students)
            upcoming_orders = student_orders.filter(
                active=True,
                session__end_date__gte=timezone.now()
            ).order_by('session__start_date')
            past_orders = student_orders.filter(
                active=True,
                session__end_date__lte=timezone.now()
            ).order_by('session__start_date')

            if request.method == 'POST':
                form = GuardianForm(request.POST, instance=account)
                if form.is_valid():
                    form.save()
                    messages.success(request, 'Profile information saved.')
                    return HttpResponseRedirect(reverse('dojo'))
                else:
                    messages.error(request, 'There was an error. Please try again.')
            else:
                form = GuardianForm(instance=account)

            context['students'] = students
            context['upcoming_orders'] = upcoming_orders
            context['past_orders'] = past_orders

        context['account'] = account
        context['form'] = form
    else:
        if 'next' in request.GET:
            return HttpResponseRedirect(u'{}?next={}'.format(reverse('welcome'), request.GET['next']))
        else:
            messages.warning(
                request,
                'Tell us a little about yourself before going on to your dojo.'
            )
            return HttpResponseRedirect(reverse('welcome'))

    return render(request, template_name, context)


def mentors(request, template_name="mentors.html"):
    mentors = Mentor.objects.filter(
        active=True,
        public=True,
        background_check=True,
        avatar_approved=True,
    ).order_by('user__date_joined')

    # mentors = Mentor.objects.filter(active=True, public=True).order_by('user__date_joined')

    return render(request, template_name, {
        'mentors': mentors
    })


def mentor_detail(request, mentor_id=False, template_name="mentor-detail.html"):

    mentor = get_object_or_404(Mentor, id=mentor_id)

    if not mentor.public:
        messages.error(request, 'Invalid mentor ID.')
        return HttpResponseRedirect(reverse('mentors'))

    return render(request, template_name, {
        'mentor': mentor
    })


@login_required
def mentor_approve_avatar(request, mentor_id=False):
    mentor = get_object_or_404(Mentor, id=mentor_id)

    if not request.user.is_staff:
        messages.error(request, 'You do not have permissions to moderate content.')

        return HttpResponseRedirect(
            u'{}?next={}'.format(
                reverse('account_login'),
                mentor.get_approve_avatar_url()
            )
        )

    mentor.avatar_approved = True
    mentor.save()

    if mentor.background_check:
        messages.success(
            request,
            u'{}{}\'s avatar approved and their account is now public.'.format(
                mentor.user.first_name,
                mentor.user.last_name
            )
        )
        return HttpResponseRedirect(u'{}{}'.format(reverse('mentors'), mentor.id))
    else:
        messages.success(
            request,
            u'{}{}\'s avatar approved but they have yet to fill out the \'background search\' form.'.format(
                mentor.user.first_name,
                mentor.user.last_name
            )
        )
        return HttpResponseRedirect(reverse('mentors'))


@login_required
def mentor_reject_avatar(request, mentor_id=False):
    mentor = get_object_or_404(Mentor, id=mentor_id)

    if not request.user.is_staff:
        messages.error(request, 'You do not have permissions to moderate content.')

        return HttpResponseRedirect(
            u'{}?next={}'.format(
                reverse('account_login'),
                mentor.get_reject_avatar_url()
            )
        )

    mentor.avatar_approved = False
    mentor.save()

    msg = EmailMultiAlternatives(
        subject='CoderDojoChi | Avatar Rejected',
        body=u'Unfortunately your recent avatar image was rejected. Please upload a new image as soon as you get a chance. {}/dojo/'.format(
            settings.SITE_URL),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[mentor.user.email]
    )
    msg.attach_alternative(u'<p>Unfortunately your recent avatar image was rejected. Please upload a new image as soon as you get a chance.</p><p><a href="{}/dojo/">Click here to upload a new avatar now.</a></p><p>Thank you!<br>The CoderDojoChi Team</p>'.format(
        settings.SITE_URL
    ), 'text/html')
    msg.send()

    messages.warning(
        request,
        u'{} {}\'s avatar rejected and their account is no longer public. An email notice has been sent to the mentor.'.format(
            mentor.user.first_name,
            mentor.user.last_name
        )
    )

    return HttpResponseRedirect(reverse('mentors'))


@login_required
def student_detail(request, student_id=False, template_name="student-detail.html"):
    access = True

    if request.user.role == 'guardian' and student_id:
        student = get_object_or_404(Student, id=student_id)
        guardian = get_object_or_404(Guardian, user=request.user)

        if not student.guardian == guardian:
            access = False

        form = StudentForm(instance=student)
    else:
        access = False

    if not access:
        return HttpResponseRedirect(reverse('dojo'))
        messages.error(request, 'You do not have permissions to edit this student.')

    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student Updated.')
            return HttpResponseRedirect(reverse('dojo'))

    return render(request, template_name, {
        'form': form
    })


def donate(request, template_name="donate.html"):
    if request.method == 'POST':

        # if new donation form submit
        if ('first_name' in request.POST and 'last_name' in request.POST and 'email' in request.POST and 'amount' in request.POST):
            donation = Donation(
                first_name=request.POST['first_name'],
                last_name=request.POST['last_name'],
                email=request.POST['email'],
                amount=request.POST['amount']
            )
            donation.save()
            return HttpResponse(donation.id)
        else:
            return HttpResponse('fail')

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
        'notify_url': u'{}{}'.format(settings.SITE_URL, reverse('paypal-ipn')),
        'return_url':  u'{}/donate/return'.format(settings.SITE_URL),
        'cancel_return': u'{}/donate/cancel'.format(settings.SITE_URL),
        'bn': 'PP-DonationsBF:btn_donateCC_LG.gif:NonHosted'
    }

    form = PayPalPaymentsForm(initial=paypal_dict)

    return render(request, template_name, {
        'form': form
    })


@csrf_exempt
def donate_cancel(request):
    messages.error(
        request,
        u'Looks like you cancelled the donation process. '
        'Please feel free to <a href="/{}">contact us</a> if you need any help.'.format(
            reverse('contact')
        )
    )
    return HttpResponseRedirect(reverse('donate'))


@csrf_exempt
def donate_return(request):
    messages.success(
        request,
        'Your donation is being processed. '
        'You should receive a confirmation email shortly. Thanks again!'
    )
    return HttpResponseRedirect(reverse('donate'))


def about(request, template_name="about.html"):
    mentor_count = Mentor.objects.filter(active=True, public=True).count()
    students_served = Order.objects.exclude(check_in=None).count()

    return render(request, template_name, {
        'mentor_count': mentor_count,
        'students_served': students_served
    })


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
                    subject=u'{} | CoderDojoChi Contact Form'.format(request.POST['name']),
                    body=request.POST['body'],
                    from_email=u'CoderDojoChi<{}>'.format(settings.DEFAULT_FROM_EMAIL),
                    reply_to=[
                        u'{}<{}>'.format(request.POST['name'], request.POST['email'])
                    ],
                    to=[settings.CONTACT_EMAIL]
                )

                msg.attach_alternative(
                    request.POST['body'].replace("\r\n", "<br />").replace("\n", "<br />"),
                    'text/html'
                )

                msg.send()

                messages.success(
                    request,
                    'Thank you for contacting us! We will respond as soon as possible.'
                )

            form = ContactForm()
        else:
            messages.error(request, 'There was an error. Please try again.')
    else:
        form = ContactForm()

    return render(request, template_name, {
        'form': form
    })


def privacy(request, template_name="privacy.html"):
    return render(request, template_name)


@login_required
def cdc_admin(request, template_name="cdc-admin.html"):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return HttpResponseRedirect(reverse('sessions'))

    sessions = Session.objects.all()

    upcoming_sessions = sessions.filter(
        active=True,
        end_date__gte=timezone.now()
    ).order_by('start_date')
    upcoming_sessions_count = upcoming_sessions.count()

    if 'all_upcoming_sessions' not in request.GET:
        upcoming_sessions = upcoming_sessions[:3]

    past_sessions = sessions.filter(
        active=True,
        end_date__lte=timezone.now()
    ).order_by('-start_date')
    past_sessions_count = past_sessions.count()

    if 'all_past_sessions' not in request.GET:
        past_sessions = past_sessions[:3]

    meetings = Meeting.objects.all()

    upcoming_meetings = meetings.filter(
        active=True,
        end_date__gte=timezone.now()
    ).order_by('start_date')
    upcoming_meetings_count = upcoming_meetings.count()

    if 'all_upcoming_meetings' not in request.GET:
        upcoming_meetings = upcoming_meetings[:3]

    past_meetings = meetings.filter(
        active=True,
        end_date__lte=timezone.now()
    ).order_by('-start_date')
    past_meetings_count = past_meetings.count()

    if 'all_past_meetings' not in request.GET:
        past_meetings = past_meetings[:3]

    return render(request, template_name, {
        'upcoming_sessions': upcoming_sessions,
        'upcoming_sessions_count': upcoming_sessions_count,
        'past_sessions': past_sessions,
        'past_sessions_count': past_sessions_count,
        'upcoming_meetings': upcoming_meetings,
        'upcoming_meetings_count': upcoming_meetings_count,
        'past_meetings': past_meetings,
        'past_meetings_count': past_meetings_count
    })


@login_required
def session_stats(request, session_id, template_name="session-stats.html"):

    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return HttpResponseRedirect(reverse('sessions'))

    session_obj = get_object_or_404(Session, id=session_id)

    current_orders_checked_in = session_obj.get_current_orders(checked_in=True)

    students_checked_in = current_orders_checked_in.values('student')

    if students_checked_in:
        attendance_percentage = round(
            (float(current_orders_checked_in.count()) /
             float(session_obj.get_current_students().count())) * 100
        )
    else:
        attendance_percentage = False

    # Genders
    gender_count = list(
        Counter(
            e.student.get_clean_gender() for e in session_obj.get_current_orders()
        ).iteritems()
    )
    gender_count = sorted(dict(gender_count).items(), key=operator.itemgetter(1))

    # Ages
    ages = sorted(list(e.student.get_age() for e in session_obj.get_current_orders()))
    age_count = sorted(dict(list(Counter(ages).iteritems())).items(), key=operator.itemgetter(1))

    # Average Age
    average_age = False
    if current_orders_checked_in:
        student_ages = []
        for order in current_orders_checked_in:
            student_ages.append(order.get_student_age())
        average_age = reduce(lambda x, y: x + y, student_ages) / len(student_ages)

    return render(request, template_name, {
        'session': session_obj,
        'students_checked_in': students_checked_in,
        'attendance_percentage': attendance_percentage,
        'average_age': average_age,
        'age_count': age_count,
        'gender_count': gender_count
    })


@login_required
def session_check_in(request, session_id, template_name="session-check-in.html"):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return HttpResponseRedirect(reverse('sessions'))


    if request.method == 'POST':
        if 'order_id' in request.POST:
            order = get_object_or_404(Order, id=request.POST['order_id'])

            if order.check_in:
                order.check_in = None
            else:
                order.check_in = timezone.now()

            if (u'{} {}'.format(order.guardian.user.first_name, order.guardian.user.last_name) != request.POST['order_alternate_guardian']):
                order.alternate_guardian = request.POST['order_alternate_guardian']

            order.save()
        else:
            messages.error(request, 'Invalid Order')

    # Get current session
    session = get_object_or_404(Session, id=session_id)

    # Active Session
    active_session = True if timezone.now() < session.end_date else False

    # get the orders
    orders = Order.objects.select_related().filter(session_id=session_id).annotate(
        num_attended=Count(Case(When(student__order__check_in__isnull=False, then=1))),
        num_missed=Count(Case(When(student__order__check_in__isnull=True, then=1)))
    )

    if active_session:
        active_orders = orders.filter(active=True).order_by('student__first_name')
    else:
        active_orders = orders.filter(active=True, check_in__isnull=False).order_by('student__first_name')

    inactive_orders = orders.filter(active=False).order_by('-updated_at');

    no_show_orders = orders.filter(active=True, check_in__isnull=True)

    checked_in_orders = orders.filter(active=True, check_in__isnull=False)

    # Genders
    gender_count = sorted(
        dict(
            list(
                Counter(
                    e.student.get_clean_gender() for e in active_orders
                ).iteritems()
            )
        ).items(),
        key=operator.itemgetter(1)
    )

    # Ages
    ages = sorted(list(e.get_student_age() for e in active_orders))
    age_count = sorted(dict(list(Counter(ages).iteritems())).items(), key=operator.itemgetter(0))
    # age_count = sorted(dict(list(Counter(ages).iteritems())).items(), key=operator.itemgetter(1), reverse=True)

    # Average Age
    average_age = int(round(sum(ages) / float(len(ages)))) if orders else 0

    return render(request, template_name, {
        'session': session,
        'active_session': active_session,
        'active_orders': active_orders,
        'inactive_orders': inactive_orders,
        'no_show_orders': no_show_orders,
        'gender_count': gender_count,
        'age_count': age_count,
        'average_age': average_age,
        'checked_in_orders': checked_in_orders,
    })


@login_required
def session_check_in_mentors(request, session_id, template_name="session-check-in-mentors.html"):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return HttpResponseRedirect(reverse('sessions'))

    if request.method == 'POST':
        if 'order_id' in request.POST:
            order = get_object_or_404(MentorOrder, id=request.POST['order_id'])

            if order.check_in:
                order.check_in = None
            else:
                order.check_in = timezone.now()

            order.save()
        else:
            messages.error(request, 'Invalid Order')

    session = get_object_or_404(Session, id=session_id)

    # Active Session
    active_session = True if timezone.now() < session.end_date else False

    # get the orders
    orders = MentorOrder.objects.select_related().filter(session_id=session_id)

    if active_session:
        active_orders = orders.filter(active=True).order_by('mentor__user__first_name')
    else:
        active_orders = orders.filter(active=True, check_in__isnull=False).order_by('mentor__user__first_name')

    inactive_orders = orders.filter(active=False).order_by('-updated_at');

    no_show_orders = orders.filter(active=True, check_in__isnull=True)

    checked_in_orders = orders.filter(active=True, check_in__isnull=False)

    return render(request, template_name, {
        'session': session,
        'active_session': active_session,
        'active_orders': active_orders,
        'inactive_orders': inactive_orders,
        'no_show_orders': no_show_orders,
        'checked_in_orders': checked_in_orders,
    })


@login_required
def meeting_check_in(request, meeting_id, template_name="meeting-check-in.html"):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return HttpResponseRedirect(reverse('dojo'))

    meeting_obj = get_object_or_404(Meeting, id=meeting_id)
    current_mentor_orders_checked_in = meeting_obj.get_current_orders(checked_in=True)
    mentors_checked_in = current_mentor_orders_checked_in.values('mentor')

    if request.method == 'POST':
        if 'order_id' in request.POST:
            order = get_object_or_404(MeetingOrder, id=request.POST['order_id'])

            if order.check_in:
                order.check_in = None
            else:
                order.check_in = timezone.now()

            order.save()
        else:
            messages.error(request, 'Invalid Order')

    return render(request, template_name, {
        'meeting': meeting_obj,
        'mentors_checked_in': mentors_checked_in
    })


def session_announce(request, session_id):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return HttpResponseRedirect(reverse('home'))

    session_obj = get_object_or_404(Session, id=session_id)

    if not session_obj.announced_date:

        # uses SMTP server specified in settings.py
        connection = get_connection()

        # If you don't open the connection manually, Django will automatically open,
        # then tear down the connection in msg.send()
        connection.open()

        # send mentor announcements
        for mentor in Mentor.objects.filter(active=True):

            sendSystemEmail(
                request,
                'Upcoming class',
                'coderdojochi-class-announcement-mentor',
                {
                    'first_name': mentor.user.first_name,
                    'last_name': mentor.user.last_name,
                    'class_code': session_obj.course.code,
                    'class_title': session_obj.course.title,
                    'class_description': session_obj.course.description,
                    'class_start_date': arrow.get(session_obj.mentor_start_date).format('dddd, MMMM D, YYYY'),
                    'class_start_time': arrow.get(session_obj.mentor_start_date).format('h:mma'),
                    'class_end_date': arrow.get(session_obj.end_date).format('dddd, MMMM D, YYYY'),
                    'class_end_time': arrow.get(session_obj.end_date).format('h:mma'),
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
                mentor.user.email
            )


        for guardian in Guardian.objects.filter(active=True):
            sendSystemEmail(
                request,
                'Upcoming class',
                'coderdojochi-class-announcement-guardian',
                {
                    'first_name': guardian.user.first_name,
                    'last_name': guardian.user.last_name,
                    'class_code': session_obj.course.code,
                    'class_title': session_obj.course.title,
                    'class_description': session_obj.course.description,
                    'class_start_date': arrow.get(session_obj.start_date).format('dddd, MMMM D, YYYY'),
                    'class_start_time': arrow.get(session_obj.start_date).format('h:mma'),
                    'class_end_date': arrow.get(session_obj.end_date).format('dddd, MMMM D, YYYY'),
                    'class_end_time': arrow.get(session_obj.end_date).format('h:mma'),
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
                guardian.user.email
            )

        # Cleanup
        connection.close()

        session_obj.announced_date = timezone.now()
        session_obj.save()

        messages.success(request, 'Session announced!')
    else:
        messages.warning(request, 'Session already announced.')

    return HttpResponseRedirect(reverse('cdc_admin'))


@login_required
def dashboard(request, template_name="admin-dashboard.html"):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return HttpResponseRedirect(reverse('sessions'))

    orders = Order.objects.select_related()

    past_sessions = Session.objects.select_related().filter(
        active=True,
        end_date__lte=timezone.now()
    ).annotate(
        num_orders=Count('order'),
        num_attended=Count(Case(When(order__check_in__isnull=False, then=1)))
    ).order_by('-start_date')

    total_past_orders = orders.filter(active=True)
    total_past_orders_count = total_past_orders.count()
    total_checked_in_orders = orders.filter(active=True, check_in__isnull=False)
    total_checked_in_orders_count = total_checked_in_orders.count()

    # Genders
    gender_count = list(
        Counter(
            e.student.get_clean_gender() for e in total_checked_in_orders
        ).iteritems()
    )
    gender_count = sorted(dict(gender_count).items(), key=operator.itemgetter(1))

    # Ages
    ages = sorted(list(e.student.get_age() for e in total_checked_in_orders))
    age_count = sorted(dict(list(Counter(ages).iteritems())).items(), key=operator.itemgetter(1))

    # Average Age
    average_age = int(round(sum(ages) / float(len(ages))))

    return render(request, template_name, {
        'past_sessions': past_sessions,
        'gender_count': gender_count,
        'age_count': age_count,
        'average_age': average_age,
        'total_past_orders_count': total_past_orders_count,
        'total_checked_in_orders_count': total_checked_in_orders_count,
    })


@csrf_exempt
# the "service" that computers run to self update
def check_system(request):
    # set up variables
    runUpdate = True;
    responseString = ""
    cmdString = 'sh -c "$(curl -fsSL https://raw.githubusercontent.com/CoderDojoChi/linux-update/master/update.sh)"'
    halfday = timedelta(hours=12)
    #halfday = timedelta(seconds=15)

    if Session.objects.filter(active=True, start_date__lte=timezone.now(), mentor_end_date__gte=timezone.now()).count():
        runUpdate = False;

    # uuid is posted from the computer using a bash script (see https://raw.githubusercontent.com/CoderDojoChi/linux-update/master/etc/init.d/coderdojochi-phonehome
    uuid = request.POST.get('uuid');

    if uuid:
        equipmentType = EquipmentType.objects.get(name="Laptop")
        if equipmentType:
            equipment, created = Equipment.objects.get_or_create(
                uuid=uuid,
                defaults={'equipment_type': equipmentType}
            )
            # check for blank values of last_system_update.  If blank, assume we need to run it
            if not equipment.last_system_update:
                equipment.force_update_on_next_boot = True

            # do we need to update?
            if runUpdate and (equipment.force_update_on_next_boot or (timezone.now() - equipment.last_system_update > halfday)):
                responseString = cmdString
                equipment.last_system_update = timezone.now()
                equipment.force_update_on_next_boot = False

            # update the last_system_update_check_in to now
            equipment.last_system_update_check_in = timezone.now()
            equipment.save()

    return HttpResponse(responseString)

def sendSystemEmail(request, subject, template_name, merge_vars, email=False, bcc=False):

    if not email and request:
        email = request.user.email

    user = CDCUser.objects.filter(email=email).first()

    if not user.is_active:
        if settings.DEBUG:
            print >>sys.stderr, u'Not active user. {}'.format(user.email)
        return

    merge_vars['current_year'] = timezone.now().year
    merge_vars['company'] = 'CoderDojoChi'
    merge_vars['site_url'] = settings.SITE_URL

    try:
        msg = EmailMessage(
            subject=subject,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email]
        )

        if bcc:
            msg.bcc = bcc

        msg.template_name = template_name
        msg.global_merge_vars = merge_vars
        msg.inline_css = True
        msg.use_template_subject = True
        # msg.async = True

        if settings.DEBUG:
            print >>sys.stderr, 'Sending \'{}\' to {}'.format(subject, email)

        msg.send()

    except Exception, e:

        if settings.DEBUG:
            print >>sys.stderr, u'{}'.format(msg)

        response = msg.mandrill_response[0]

        reject_reasons = [
            'hard-bounce',
            'soft-bounce',
            'spam',
            'unsub',
        ]

        if response['status'] == u'rejected' and response['reject_reason'] in reject_reasons:
            if settings.DEBUG:
                print >>sys.stderr, u'user: {}, {}'.format(user.email, response['reject_reason'])

            user.is_active = False
            user.admin_notes = u'User \'{}\' when checked on {}'.format(response['reject_reason'], timezone.now())
            user.save()
        else:
            if settings.DEBUG:
                print >>sys.stderr, u'user: {}, {}'.format(user.email, response['reject_reason'])

            raise e
