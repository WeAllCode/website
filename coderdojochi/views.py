from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext, Context
from django.template.loader import get_template
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.core.mail import EmailMessage, EmailMultiAlternatives, send_mail
from django.core.urlresolvers import reverse
from django.contrib import messages, auth
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
from django import forms

from coderdojochi.models import Mentor, Guardian, Student, Course, Session, Order, Meeting, Donation
from coderdojochi.forms import MentorForm, GuardianForm, StudentForm, ContactForm

from calendar import HTMLCalendar

from icalendar import Calendar, Event, vCalAddress, vText

from datetime import date, timedelta
from itertools import groupby
from collections import Counter
import operator

from django.utils import timezone
from django.utils.html import conditional_escape as esc
from django.utils.safestring import mark_safe

from django.utils.translation import ugettext_lazy as _

from paypal.standard.forms import PayPalPaymentsForm

import arrow, os, pytz, tempfile

# this will assign User to our custom CDCUser
User = get_user_model()

import calendar

def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month / 12
    month = month % 12 + 1
    day = min(sourcedate.day,calendar.monthrange(year,month)[1])

    return date(year,month,day)

def home(request, template_name="home.html"):

    upcoming_classes = Session.objects.filter(active=True, end_date__gte=timezone.now()).order_by('start_date')

    if not request.user.is_authenticated() or not request.user.role == 'mentor':
        upcoming_classes = upcoming_classes.filter(public=True)

    upcoming_classes = upcoming_classes[:3]

    return render_to_response(template_name, {
        'upcoming_classes': upcoming_classes
    }, context_instance=RequestContext(request))

@login_required
def welcome(request, template_name="welcome.html"):

    keepGoing = True

    user = request.user
    account = False
    add_student = False
    students = False
    form = False
    role = user.role if user.role else False


    next = False

    if 'next' in request.GET:
        next = request.GET['next']

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
                        messages.add_message(request, messages.SUCCESS, 'Student Registered.')
                    else:
                        keepGoing = False

                    if keepGoing:
                        if next:
                            if 'enroll' in request.GET:
                                return HttpResponseRedirect(next + '?enroll=True&student=' + str(new_student.id))
                            else:
                                return HttpResponseRedirect(next)
                        else:
                            return HttpResponseRedirect(reverse('welcome'))

            if keepGoing:
                if form.is_valid():
                    form.save()
                    messages.add_message(request, messages.SUCCESS, 'Profile information saved.')

                    if next:
                        if 'enroll' in request.GET:
                            return HttpResponseRedirect(next + '?enroll=True')
                        else:
                            return HttpResponseRedirect(next)
                    else:
                        return HttpResponseRedirect(reverse('dojo'))
                else:
                    keepGoing = False
        else:
            if request.POST.get('role') == 'mentor':
                role = 'mentor'
                mentor, created = Mentor.objects.get_or_create(user=user)
                mentor.first_name = user.first_name
                mentor.last_name = user.last_name
                mentor.save()
                user.role = role
            else:
                role = 'guardian'
                guardian, created = Guardian.objects.get_or_create(user=user)
                guardian.first_name = user.first_name
                guardian.last_name = user.last_name
                guardian.save()
                user.role = role

            user.save()


            merge_vars = {
                'user': request.user.username,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name
            }

            if next:
                next = '?next=' + next
            else:
                next = ''

            if role == 'mentor':

                # check for next upcoming meeting
                next_meeting = Meeting.objects.filter(active=True, public=True).order_by('start_date').first()

                if next_meeting:
                    merge_vars['next_intro_meeting_url'] = next_meeting.get_absolute_url()
                    merge_vars['next_intro_meeting_ics_url'] = next_meeting.get_ics_url()

                sendSystemEmail(request, 'Welcome!', 'coderdojochi-welcome-mentor', merge_vars)

                return HttpResponseRedirect(next)
            else:

                # check for next upcoming class
                next_class = Session.objects.filter(active=True).order_by('start_date').first()

                if next_class:
                    merge_vars['next_class_url'] = next_class.get_absolute_url()
                    merge_vars['next_class_ics_url'] = next_class.get_ics_url()

                sendSystemEmail(request, 'Welcome!', 'coderdojochi-welcome-guardian', merge_vars)

                return HttpResponseRedirect(reverse('welcome') + next)

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

    if account and account.first_name and keepGoing:
        if role == 'mentor':
            if next:
                return HttpResponseRedirect(next)
            else:
                return HttpResponseRedirect(reverse('dojo'))
        else:
            students = account.get_students() if account.get_students().count() else False

    if keepGoing:
        if 'next' in request.GET:
            next = request.GET['next']
        else:
            next = False

    return render_to_response(template_name, {
        'role': role,
        'account': account,
        'form': form,
        'add_student': add_student,
        'students': students,
        'next': next
    }, context_instance=RequestContext(request))

def sessions(request, year=False, month=False, template_name="sessions.html"):

    now = timezone.now()

    year = int(year) if year else now.year
    month = int(month) if month else now.month

    calendar_date = date(day=1, month=month, year=year)
    prev_date = add_months(calendar_date,-1)
    next_date = add_months(calendar_date,1)

    all_sessions = Session.objects.filter(active=True, end_date__gte=timezone.now()).order_by('start_date')

    if not request.user.is_authenticated() or not request.user.role == 'mentor':
        all_sessions = all_sessions.filter(public=True)

    sessions = all_sessions.filter(start_date__year=year, start_date__month=month).order_by('start_date')
    cal = SessionsCalendar(sessions).formatmonth(year, month)

    return render_to_response(template_name,{
        'all_sessions': all_sessions,
        'sessions': sessions,
        'calendar': mark_safe(cal),
        'calendar_date': calendar_date,
        'prev_date': prev_date,
        'next_date': next_date
    }, context_instance=RequestContext(request))


def session_detail_enroll(request, year, month, day, slug, session_id, template_name="session-detail.html"):
    return session_detail(request, year, month, day, slug, session_id, template_name, enroll=True)

def session_detail(request, year, month, day, slug, session_id, template_name="session-detail.html", enroll=False):
    session_obj = get_object_or_404(Session, id=session_id)
    mentor_signed_up = False
    account = False
    students = False

    if request.method == 'POST':
        if 'waitlist' in request.POST:

            if request.POST['waitlist'] == 'student':
                student = Student.objects.get(id=int(request.POST['account_id']))

                if request.POST['remove'] == 'true':
                    session_obj.waitlist_students.remove(student)
                    session_obj.save()
                    messages.add_message(request, messages.SUCCESS, 'You have been removed from the waitlist. Thanks for letting us know.')
                else:
                    session_obj.waitlist_students.add(student)
                    session_obj.save()
                    messages.add_message(request, messages.SUCCESS, 'Added to waitlist successfully.')
            else:
                mentor = Mentor.objects.get(id=int(request.POST['account_id']))

                if request.POST['remove'] == 'true':
                    session_obj.waitlist_mentors.remove(mentor)
                    session_obj.save()
                    messages.add_message(request, messages.SUCCESS, 'You have been removed from the waitlist. Thanks for letting us know.')
                else:
                    session_obj.waitlist_mentors.add(mentor)
                    session_obj.save()
                    messages.add_message(request, messages.SUCCESS, 'Added to waitlist successfully.')
        else:
            messages.add_message(request, messages.ERROR, 'Invalid request, please try again.')

        return HttpResponseRedirect(session_obj.get_absolute_url())

    upcoming_classes = Session.objects.filter(active=True, end_date__gte=timezone.now()).order_by('start_date')

    if not request.user.is_authenticated() or not request.user.role == 'mentor':
        upcoming_classes = upcoming_classes.filter(public=True)

    if request.user.is_authenticated():

        if not request.user.role:
            messages.add_message(request, messages.WARNING, 'Please select one of the following options to continue.')

            url = reverse('welcome') + '?next=' + session_obj.get_absolute_url()

            if 'enroll' in request.GET:
                url += '&enroll=True'

            return HttpResponseRedirect(url)

        if request.user.role == 'mentor':
            mentor = get_object_or_404(Mentor, user=request.user)
            account = mentor
            mentor_signed_up = True if mentor in session_obj.mentors.all() else False
            spots_remaining = session_obj.get_mentor_capacity() - session_obj.mentors.all().count()

            if enroll or 'enroll' in request.GET:
                return HttpResponseRedirect(session_obj.get_absolute_url() + '/sign-up/')

        else:
            guardian = get_object_or_404(Guardian, user=request.user)
            account = guardian
            students = guardian.get_students() if guardian.get_students().count() else False
            spots_remaining = session_obj.capacity - session_obj.get_current_students().all().count()

            if enroll or 'enroll' in request.GET:
                if not students:
                    return HttpResponseRedirect(reverse('welcome') + '?next=' + session_obj.get_absolute_url() + '&enroll=True')
                else:
                    if 'student' in request.GET:
                        return HttpResponseRedirect(session_obj.get_absolute_url() + '/sign-up/' + request.GET['student'])

    else:
        spots_remaining = session_obj.capacity - session_obj.get_current_students().all().count()

    # only allow mentors to view non-public sessions
    # if not session_obj.public:
    #     if not request.user.is_authenticated() or request.user.role == 'guardian':
    #         messages.add_message(request, messages.ERROR, 'Sorry, the class you requested is not available at this time.')
    #         return HttpResponseRedirect(reverse('sessions'))

    return render_to_response(template_name,{
        'session': session_obj,
        'mentor_signed_up': mentor_signed_up,
        'students': students,
        'account': account,
        'upcoming_classes': upcoming_classes,
        'spots_remaining': spots_remaining
    }, context_instance=RequestContext(request))


@login_required
def session_sign_up(request, year, month, day, slug, session_id, student_id=False, template_name="session-sign-up.html"):

    session_obj = get_object_or_404(Session, id=session_id)
    student = False
    guardian = False

    if not request.user.role:
        messages.add_message(request, messages.WARNING, 'Please select one of the following options to continue.')
        return HttpResponseRedirect(reverse('welcome') + '?next=' + session_obj.get_absolute_url())

    if request.user.role == 'mentor':

        mentor = get_object_or_404(Mentor, user=request.user)

        if not mentor.background_check:
            messages.add_message(request, messages.WARNING, 'You cannot sign up for a class until after attending a mentor meeting. Please RSVP below.')
            return HttpResponseRedirect(reverse('dojo') + '?highlight=meetings')

        user_signed_up = True if mentor in session_obj.mentors.all() else False

        if not user_signed_up:
            if session_obj.get_mentor_capacity() <= session_obj.mentors.all().count():
                messages.add_message(request, messages.ERROR, 'Sorry this class is at mentor capacity.  Please check back soon and/or join us for another upcoming class!')
                return HttpResponseRedirect(session_obj.get_absolute_url())

    else:
        student = get_object_or_404(Student, id=student_id)
        guardian = get_object_or_404(Guardian, user=request.user)
        user_signed_up = True if student.is_registered_for_session(session_obj) else False

        if not user_signed_up:
            if session_obj.capacity <= session_obj.get_current_students().all().count():
                messages.add_message(request, messages.ERROR, 'Sorry this class has sold out. Please sign up for the wait list and/or check back later.')
                return HttpResponseRedirect(session_obj.get_absolute_url())

    undo = False

    if request.method == 'POST':

        if request.user.role == 'mentor':
            if user_signed_up:
                session_obj.mentors.remove(mentor)
                undo = True
            else:
                session_obj.mentors.add(mentor)
        else:
            if user_signed_up:
                order = get_object_or_404(Order, student=student, session=session_obj, active=True)
                order.active = False
                order.save()
                undo = True
            else:
                if not settings.DEBUG:
                    ip = request.META['HTTP_X_FORWARDED_FOR'] or request.META['REMOTE_ADDR']
                else:
                    ip = request.META['REMOTE_ADDR']

                order = Order.objects.create(guardian=guardian, student=student, session=session_obj, ip=ip)

                # we dont want guardians getting 7 day reminder email if they sign up within 9 days
                if session_obj.start_date < timezone.now() + timedelta(days=9):
                    order.week_reminder_sent = True

                # or 24 hours notice if signed up within 48 hours
                if session_obj.start_date < timezone.now() + timedelta(days=2):
                    order.week_reminder_sent = True
                    order.day_reminder_sent = True

                order.save()

        session_obj.save()

        if undo:
            messages.add_message(request, messages.SUCCESS, 'Thanks for letting us know!')
        else:
            messages.add_message(request, messages.SUCCESS, 'Success! See you there!')


            if request.user.role == 'mentor':

                sendSystemEmail(request, 'Upcoming class confirmation', 'coderdojochi-class-confirm-mentor', {
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
                })

            else:

                sendSystemEmail(request, 'Upcoming class confirmation', 'coderdojochi-class-confirm-guardian', {
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
                })

        return HttpResponseRedirect(session_obj.get_absolute_url())

    # only allow mentors to view non-public sessions
    # if not session_obj.public:
    #     if not request.user.is_authenticated() or guardian:
    #         messages.add_message(request, messages.ERROR, 'Sorry, the class you requested is not available at this time.')
    #         return HttpResponseRedirect(reverse('sessions'))

    return render_to_response(template_name,{
        'session': session_obj,
        'user_signed_up': user_signed_up,
        'student': student,
    }, context_instance=RequestContext(request))

def session_ics(request, year, month, day, slug, session_id):

    session_obj = get_object_or_404(Session, id=session_id)

    cal = Calendar()

    cal.add('prodid', '-//CoderDojoChi//coderdojochi.org//')
    cal.add('version', '2.0')

    event = Event()

    start_date_arrow = arrow.get(session_obj.start_date)

    event.add('summary', 'CoderDojoChi:  ' + session_obj.course.code + ' - ' + session_obj.course.title)
    event.add('dtstart', start_date_arrow.naive)
    event.add('dtend', arrow.get(session_obj.end_date).naive)
    event.add('dtstamp', start_date_arrow.datetime)

    if request.user.is_authenticated() and request.user.role == 'mentor':

        mentor_start_date_arrow = arrow.get(session_obj.mentor_start_date)
        event.add('dtstart', mentor_start_date_arrow.naive)
        event.add('dtend', arrow.get(session_obj.mentor_end_date).naive)
        event.add('dtstamp', mentor_start_date_arrow.datetime)

    event['location'] = vText(session_obj.location.name + ', ' + session_obj.location.address + ', ' + session_obj.location.address2 + ', ' + session_obj.location.city + ', ' + session_obj.location.state + ', ' + session_obj.location.zip)

    # A value of 5 is the normal or "MEDIUM" priority.
    # see: https://tools.ietf.org/html/rfc5545#section-3.8.1.9
    event.add('priority', 5)

    cal.add_component(event)

    response = HttpResponse(cal.to_ical().replace('\r\n', '\n').strip(), content_type="text/calendar")
    response['Filename'] = session_obj.course.slug + '-' + arrow.get(session_obj.start_date).format('MM-DD-YYYY-HH:mm') + '.ics'
    response['Content-Disposition'] = 'attachment; filename=coderdojochi-' + arrow.get(session_obj.start_date).format('MM-DD-YYYY-HH:mma') + '.ics'

    return response


def meeting_detail(request, year, month, day, meeting_id, template_name="meeting-detail.html"):
    meeting_obj = get_object_or_404(Meeting, id=meeting_id)

    mentor_signed_up = False

    if request.user.is_authenticated():
        mentor = get_object_or_404(Mentor, user=request.user)
        mentor_signed_up = True if mentor in meeting_obj.mentors.all() else False

    return render_to_response(template_name,{
        'meeting': meeting_obj,
        'mentor_signed_up': mentor_signed_up,
    }, context_instance=RequestContext(request))


@login_required
def meeting_sign_up(request, year, month, day, meeting_id, student_id=False, template_name="meeting-sign-up.html"):

    meeting_obj = get_object_or_404(Meeting, id=meeting_id)

    mentor = get_object_or_404(Mentor, user=request.user)
    user_signed_up = True if mentor in meeting_obj.mentors.all() else False

    undo = False

    if request.method == 'POST':

        if user_signed_up:
            meeting_obj.mentors.remove(mentor)
            undo = True
        else:
            meeting_obj.mentors.add(mentor)

        meeting_obj.save()

        if undo:
            messages.add_message(request, messages.SUCCESS, 'Thanks for letting us know!')
        else:
            messages.add_message(request, messages.SUCCESS, 'Success! See you there!')

            sendSystemEmail(request, 'Upcoming mentor meeting confirmation', 'coderdojochi-meeting-confirm-mentor', {
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
            })

        return HttpResponseRedirect(reverse('meeting_detail', args=(meeting_obj.start_date.year, meeting_obj.start_date.month, meeting_obj.start_date.day, meeting_obj.id)))

    return render_to_response(template_name,{
        'meeting': meeting_obj,
        'user_signed_up': user_signed_up
    }, context_instance=RequestContext(request))


def meeting_announce(request, meeting_id):

    if not request.user.is_staff:
        messages.add_message(request, messages.ERROR, 'You do not have permission to access this page.')
        return HttpResponseRedirect(reverse('home'))

    meeting_obj = get_object_or_404(Meeting, id=meeting_id)

    if not meeting_obj.announced_date:

        for mentor in Mentor.objects.filter(active=True):
            sendSystemEmail(request, 'Upcoming mentor meeting', 'coderdojochi-meeting-announcement-mentor', {
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
            }, mentor.user.email)

        meeting_obj.announced_date = timezone.now()
        meeting_obj.save()

        messages.add_message(request, messages.SUCCESS, 'Meeting announced!')
    else:
        messages.add_message(request, messages.WARNING, 'Meeting already announced.')

    return HttpResponseRedirect(reverse('cdc_admin'))

def meeting_ics(request, year, month, day, meeting_id):

    meeting_obj = get_object_or_404(Meeting, id=meeting_id)

    cal = Calendar()

    cal.add('prodid', '-//CoderDojoChi//coderdojochi.org//')
    cal.add('version', '2.0')

    event = Event()

    start_date_arrow = arrow.get(meeting_obj.start_date)

    event.add('summary', meeting_obj.meeting_type.code + ' - ' + meeting_obj.meeting_type.title)
    event.add('dtstart', start_date_arrow.naive)
    event.add('dtend', arrow.get(meeting_obj.end_date).naive)
    event.add('dtstamp', start_date_arrow.datetime)

    organizer = vCalAddress('MAILTO:info@coderdojochi.org')

    organizer.params['cn'] = vText('CoderDojoChi')
    organizer.params['role'] = vText('Organization')
    event['organizer'] = organizer
    event['location'] = vText(meeting_obj.location.name + ' ' + meeting_obj.location.address + ' ' + meeting_obj.location.address2 + ' ' + meeting_obj.location.city + ', ' + meeting_obj.location.state + ' ' + meeting_obj.location.zip)
    event['uid'] = 'MEETING00' + str(meeting_obj.id) + '@coderdojochi.org'
    event.add('priority', 5)

    cal.add_component(event)

    response = HttpResponse(cal.to_ical().replace('\r\n', '\n').strip(), content_type="text/calendar")
    response['Filename'] = meeting_obj.meeting_type.slug + '-' + arrow.get(meeting_obj.start_date).format('MM-DD-YYYY-HH:mm') + '.ics'
    response['Content-Disposition'] = 'attachment; filename=coderdojochi-' + arrow.get(meeting_obj.start_date).format('MM-DD-YYYY-HH:mma') + '.ics'

    return response


def volunteer(request, template_name="volunteer.html"):

    mentors = Mentor.objects.filter(active=True, public=True).order_by('user__date_joined')

    upcoming_meetings = Meeting.objects.filter(active=True, public=True, end_date__gte=timezone.now()).order_by('start_date')[:3]

    return render_to_response(template_name, {
        'mentors': mentors,
        'upcoming_meetings': upcoming_meetings
    }, context_instance=RequestContext(request))

def faqs(request, template_name="faqs.html"):

    return render_to_response(template_name,{}, context_instance=RequestContext(request))

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

            mentor_sessions = Session.objects.filter(mentors=mentor)
            upcoming_sessions = mentor_sessions.filter(active=True, end_date__gte=timezone.now()).order_by('start_date')
            past_sessions = mentor_sessions.filter(active=True, end_date__lte=timezone.now()).order_by('start_date')

            upcoming_meetings = Meeting.objects.filter(active=True, public=True, end_date__gte=timezone.now()).order_by('start_date')


            if request.method == 'POST':
                form = MentorForm(request.POST, request.FILES, instance=account)
                if form.is_valid():
                    form.save()
                    messages.add_message(request, messages.SUCCESS, 'Profile information saved.')
                    return HttpResponseRedirect(reverse('dojo'))
                else:
                    messages.add_message(request, messages.ERROR, 'There was an error. Please try again.')
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
            upcoming_orders = student_orders.filter(active=True, session__end_date__gte=timezone.now()).order_by('session__start_date')
            past_orders = student_orders.filter(active=True, session__end_date__lte=timezone.now()).order_by('session__start_date')

            if request.method == 'POST':
                form = GuardianForm(request.POST, instance=account)
                if form.is_valid():
                    form.save()
                    messages.add_message(request, messages.SUCCESS, 'Profile information saved.')
                    return HttpResponseRedirect(reverse('dojo'))
                else:
                    messages.add_message(request, messages.ERROR, 'There was an error. Please try again.')
            else:
                form = GuardianForm(instance=account)

            context['students'] = students
            context['upcoming_orders'] = upcoming_orders
            context['past_orders'] = past_orders


        context['account'] = account
        context['form'] = form

    else:
        if 'next' in request.GET:
            return HttpResponseRedirect(reverse('welcome') + '?next=' + request.GET['next'])
        else:
            messages.add_message(request, messages.WARNING, 'Tell us a little about yourself before going on to your dojo')
            return HttpResponseRedirect(reverse('welcome'))


    return render_to_response(template_name, context, context_instance=RequestContext(request))


class SessionsCalendar(HTMLCalendar):

    def __init__(self, sessions):
        super(SessionsCalendar, self).__init__()
        self.sessions = self.group_by_day(sessions)

    def formatday(self, day, weekday):
        if day != 0:
            cssclass = self.cssclasses[weekday]
            if date.today() == date(self.year, self.month, day):
                cssclass += ' today'
            if day in self.sessions:
                cssclass += ' filled'
                body = []
                for cdc_session in self.sessions[day]:
                    remaining_spots = cdc_session.capacity - cdc_session.get_current_students().all().count()
                    dayclass = 'unavailable' if not remaining_spots else 'available'
                    body.append('<a class="' + dayclass + '" href="%s">' % cdc_session.get_absolute_url())
                    if cdc_session.course.code:
                        body.append(esc(cdc_session.course.code) + ': ')
                    body.append(esc(cdc_session.course.title))
                    body.append('</a>')
                return self.day_cell(cssclass, '%d %s' % (day, ''.join(body)))
            return self.day_cell(cssclass, day)
        return self.day_cell('noday', '&nbsp;')

    def formatmonth(self, year, month):
        self.year, self.month = year, month
        return super(SessionsCalendar, self).formatmonth(year, month)

    def group_by_day(self, sessions):
        field = lambda cdc_session: cdc_session.start_date.day
        return dict(
            [(day, list(items)) for day, items in groupby(sessions, field)]
        )

    def day_cell(self, cssclass, body):
        return '<td class="%s">%s</td>' % (cssclass, body)

def mentors(request, template_name="mentors.html"):

    mentors = Mentor.objects.filter(active=True, public=True).order_by('user__date_joined')

    return render_to_response(template_name, {
        'mentors': mentors
    }, context_instance=RequestContext(request))

def mentor_detail(request, mentor_id=False, template_name="mentor-detail.html"):

    mentor = get_object_or_404(Mentor, id=mentor_id)

    if not mentor.public:
        messages.add_message(request, messages.ERROR, 'Invalid mentor ID :(')
        return HttpResponseRedirect(reverse('mentors'));

    return render_to_response(template_name, {
        'mentor': mentor
    }, context_instance=RequestContext(request))

@login_required
def mentor_approve_avatar(request, mentor_id=False):

    mentor = get_object_or_404(Mentor, id=mentor_id)

    if not request.user.is_staff:
        messages.add_message(request, messages.ERROR, 'You do not have permissions to moderate content.')
        return HttpResponseRedirect(reverse('account_login') + '?next=' + mentor.get_approve_avatar_url())

    if mentor.background_check:
        mentor.avatar_approved = False
        mentor.save()
        messages.add_message(
            request,
            messages.SUCCESS,
            mentor.first_name + " " + mentor.last_name + "'s avatar approved and their account is now public."
        )
        return HttpResponseRedirect(reverse('mentors') + str(mentor.id));
    else:
        messages.add_message(
            request,
            messages.WARNING,
            mentor.first_name + " " + mentor.last_name + "'s avatar approved but they have yet to attend an introductory meeting."
        )
        return HttpResponseRedirect(reverse('mentors'));

@login_required
def mentor_reject_avatar(request, mentor_id=False):

    mentor = get_object_or_404(Mentor, id=mentor_id)

    if not request.user.is_staff:
        messages.add_message(request, messages.ERROR, 'You do not have permissions to moderate content.')
        return HttpResponseRedirect(reverse('account_login') + '?next=' + mentor.get_reject_avatar_url())

    mentor.avatar_approved = False
    mentor.save()

    msg = EmailMultiAlternatives(
        subject='CoderDojoChi | Avatar Rejected',
        body='Unfortunately your recent avatar image was rejected.  Please upload a new image as soon as you get a chance. ' + settings.SITE_URL + '/dojo/',
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[mentor.user.email]
    )
    msg.attach_alternative('<p>Unfortunately your recent avatar image was rejected.  Please upload a new image as soon as you get a chance.</p><p><a href="' + settings.SITE_URL + '/dojo/">Click here to upload a new avatar now.</a></p><p>Thank you!<br>The CoderDojoChi Team</p>', 'text/html')
    msg.send()

    messages.add_message(
        request,
        messages.WARNING,
        mentor.first_name + " " + mentor.last_name + "'s avatar rejected and their account is no longer public. An email notice has been sent to the mentor."
    )

    return HttpResponseRedirect(reverse('mentors'));

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
        messages.add_message(request, messages.ERROR, 'You do not have permissions to edit this student.')


    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, 'Student Updated.')
            return HttpResponseRedirect(reverse('dojo'))

    return render_to_response(template_name, {
        'form': form
    }, context_instance=RequestContext(request))

def donate(request, template_name="donate.html"):

    if request.method == 'POST':

        # if new donation form submit
        if 'first_name' in request.POST and 'last_name' in request.POST and 'email' in request.POST and 'amount' in request.POST:
            donation = Donation(first_name=request.POST['first_name'], last_name=request.POST['last_name'], email=request.POST['email'], amount=request.POST['amount'])
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
        'notify_url': settings.SITE_URL + reverse('paypal-ipn'),
        'return_url': settings.SITE_URL + '/donate/return',
        'cancel_return': settings.SITE_URL + '/donate/cancel',
        'bn': 'PP-DonationsBF:btn_donateCC_LG.gif:NonHosted'
    }

    form = PayPalPaymentsForm(initial=paypal_dict)

    return render_to_response(template_name, {
        'site_url': settings.SITE_URL,
        'form': form
    }, context_instance=RequestContext(request))

@csrf_exempt
def donate_cancel(request):
    messages.add_message(request, messages.ERROR, 'Looks like you cancelled the donation process. Please feel free to <a href="/contact">contact us</a> if you need any help.')
    return HttpResponseRedirect(reverse('donate'))

@csrf_exempt
def donate_return(request):
    messages.add_message(request, messages.SUCCESS, 'Your donation is being processed.  You should receive a confirmation email shortly. Thanks again!')
    return HttpResponseRedirect(reverse('donate'))

def about(request, template_name="about.html"):

    mentor_count = Mentor.objects.filter(active=True, public=True).count()
    students_served = Order.objects.exclude(check_in=None).count()

    return render_to_response(template_name, {
        'mentor_count': mentor_count,
        'students_served': students_served
    }, context_instance=RequestContext(request))

def contact(request, template_name="contact.html"):

    if request.method == 'POST':
        form = ContactForm(request.POST)
        human = True

        if form.is_valid():

            if request.POST['human']:
                messages.add_message(request, messages.ERROR, 'Bad robot.')
                human = False

            if human:

                msg = EmailMultiAlternatives(
                    subject='CoderDojoChi | Contact Form Submission',
                    body='Contact Form Submission from ' + request.POST['name'] + ' (' + request.POST['email'] + '). ' + request.POST['body'],
                    from_email=request.POST['email'],
                    to=[settings.CONTACT_EMAIL]
                )

                msg.attach_alternative('<p>Contact Form Submission from ' + request.POST['name'] + ' (<a href="mailto:' + request.POST['email'] + '">' + request.POST['email'] + '</a>).</p><p>' + request.POST['body'] + '</p><p><small>You can reply to this email.</small></p>', 'text/html')

                msg.send()

                messages.add_message(request, messages.SUCCESS, 'Thank you for contacting us! We will respond as soon as possible.')

            form = ContactForm()
        else:
            messages.add_message(request, messages.ERROR, 'There was an error. Please try again.')
    else:
        form = ContactForm()

    return render_to_response(template_name, {
        'form': form
    }, context_instance=RequestContext(request))

def privacy(request, template_name="privacy.html"):

    return render_to_response(template_name,{}, context_instance=RequestContext(request))

@login_required
def cdc_admin(request, template_name="cdc-admin.html"):

    if not request.user.is_staff:
        messages.add_message(request, messages.ERROR, 'You do not have permission to access this page.')
        return HttpResponseRedirect(reverse('sessions'))

    sessions = Session.objects.all()

    upcoming_sessions = sessions.filter(active=True, end_date__gte=timezone.now()).order_by('start_date')
    upcoming_sessions_count = upcoming_sessions.count()

    if 'all_upcoming_sessions' not in request.GET:
        upcoming_sessions = upcoming_sessions[:3]

    past_sessions = sessions.filter(active=True, end_date__lte=timezone.now()).order_by('-start_date')
    past_sessions_count = past_sessions.count()

    if 'all_past_sessions' not in request.GET:
        past_sessions = past_sessions[:3]

    meetings = Meeting.objects.all()

    upcoming_meetings = meetings.filter(active=True, end_date__gte=timezone.now()).order_by('start_date')
    upcoming_meetings_count = upcoming_meetings.count()

    if 'all_upcoming_meetings' not in request.GET:
        upcoming_meetings = upcoming_meetings[:3]

    past_meetings = meetings.filter(active=True, end_date__lte=timezone.now()).order_by('-start_date')
    past_meetings_count = past_meetings.count()

    if 'all_past_meetings' not in request.GET:
        past_meetings = past_meetings[:3]


    return render_to_response(template_name,{
        'upcoming_sessions': upcoming_sessions,
        'upcoming_sessions_count': upcoming_sessions_count,
        'past_sessions': past_sessions,
        'past_sessions_count': past_sessions_count,
        'upcoming_meetings': upcoming_meetings,
        'upcoming_meetings_count': upcoming_meetings_count,
        'past_meetings': past_meetings,
        'past_meetings_count': past_meetings_count
    }, context_instance=RequestContext(request))


@login_required
def session_stats(request, session_id, template_name="session-stats.html"):

    if not request.user.is_staff:
        messages.add_message(request, messages.ERROR, 'You do not have permission to access this page.')
        return HttpResponseRedirect(reverse('sessions'))

    session_obj = get_object_or_404(Session, id=session_id)

    current_orders_checked_in = session_obj.get_current_orders(checked_in=True)

    students_checked_in = current_orders_checked_in.values('student')

    if students_checked_in:
        attendance_percentage = session_obj.get_current_students().count() /  current_orders_checked_in.count() * 100
    else:
        attendance_percentage = False

    # Genders

    # Average Age
    if current_orders_checked_in:
        student_ages = []
        for order in current_orders_checked_in:
            student_ages.append(order.student.get_age())
        average_age = reduce(lambda x, y: x + y, student_ages) / len(student_ages)
    else:
        average_age = False

    return render_to_response(template_name,{
        'session': session_obj,
        'students_checked_in': students_checked_in,
        'attendance_percentage': attendance_percentage,
        'average_age': average_age
    }, context_instance=RequestContext(request))

@login_required
def session_check_in(request, session_id, template_name="session-check-in.html"):

    if not request.user.is_staff:
        messages.add_message(request, messages.ERROR, 'You do not have permission to access this page.')
        return HttpResponseRedirect(reverse('sessions'))

    session_obj = get_object_or_404(Session, id=session_id)

    current_orders_checked_in = session_obj.get_current_orders(checked_in=True)

    students_checked_in = current_orders_checked_in.values('student')

    if students_checked_in:
        attendance_percentage = round((float(current_orders_checked_in.count()) / float(session_obj.get_current_students().count())) * 100)
    else:
        attendance_percentage = 0

    # Genders
    gender_count = list(Counter(e.student.get_clean_gender() for e in session_obj.get_current_orders()).iteritems())
    gender_count = sorted(dict(gender_count).items(), key=operator.itemgetter(1))

    # Ages
    ages = sorted(list(e.student.get_age() for e in session_obj.get_current_orders()))
    age_count = list(Counter(ages).iteritems())
    age_count = sorted(dict(age_count).items(), key=operator.itemgetter(1))

    # Average Age
    average_age = 0
    if session_obj.get_current_orders():
        average_age = int(round(sum(ages) / float(len(ages))))

    if request.method == 'POST':

        if 'order_id' in request.POST:

            order = get_object_or_404(Order, id=request.POST['order_id'])

            if order.check_in:
                order.check_in = None
            else:
                order.check_in = timezone.now()

            if order.guardian.first_name + ' ' + order.guardian.last_name != request.POST['order_alternate_guardian']:
                order.alternate_guardian = request.POST['order_alternate_guardian']

            order.save()
        else:
            messages.add_message(request, messages.ERROR, 'Invalid Order')

    return render_to_response(template_name,{
        'session': session_obj,
        'gender_count': gender_count,
        'age_count': age_count,
        'average_age': average_age,
        'students_checked_in': students_checked_in,
        'attendance_percentage': attendance_percentage,
    }, context_instance=RequestContext(request))

@login_required
def session_check_in_mentors(request, session_id, template_name="session-check-in-mentors.html"):

    if not request.user.is_staff:
        messages.add_message(request, messages.ERROR, 'You do not have permission to access this page.')
        return HttpResponseRedirect(reverse('sessions'))

    session_obj = get_object_or_404(Session, id=session_id)

    return render_to_response(template_name,{
        'session': session_obj,
    }, context_instance=RequestContext(request))


def session_announce(request, session_id):

    if not request.user.is_staff:
        messages.add_message(request, messages.ERROR, 'You do not have permission to access this page.')
        return HttpResponseRedirect(reverse('home'))

    session_obj = get_object_or_404(Session, id=session_id)

    if not session_obj.announced_date:

        # send mentor announcements
        for mentor in Mentor.objects.filter(active=True):
            sendSystemEmail(request, 'Upcoming class', 'coderdojochi-class-announcement-mentor', {
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
            }, mentor.user.email)

        for guardian in Guardian.objects.filter(active=True):
            sendSystemEmail(request, 'Upcoming class', 'coderdojochi-class-announcement-guardian', {
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
            }, guardian.user.email)

        session_obj.announced_date = timezone.now()
        session_obj.save()

        messages.add_message(request, messages.SUCCESS, 'Session announced!')
    else:
        messages.add_message(request, messages.WARNING, 'Session already announced.')

    return HttpResponseRedirect(reverse('cdc_admin'))


def sendSystemEmail(request, subject, template_name, merge_vars, email=False, bcc=False):

    if not email:
        email = request.user.email

    merge_vars['current_year'] = timezone.now().year
    merge_vars['company'] = 'CoderDojoChi'
    merge_vars['site_url'] = settings.SITE_URL

    msg = EmailMessage(subject=subject, from_email=settings.DEFAULT_FROM_EMAIL,
                       to=[email])
    if bcc:
        msg.bcc = bcc

    msg.template_name = template_name
    msg.global_merge_vars = merge_vars
    msg.inline_css = True
    msg.use_template_subject = True
    msg.send()


def handler404(request):
    response = render_to_response('404.html', {}, context_instance=RequestContext(request))
    response.status_code = 404
    return response

def handler500(request):
    response = render_to_response('500.html', {}, context_instance=RequestContext(request))
    response.status_code = 500
    return response
