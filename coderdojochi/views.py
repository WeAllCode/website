from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext, Context
from django.template.loader import get_template
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required

from coderdojochi.models import Mentor, Guardian, Student, Course, Session, Order
from coderdojochi.forms import MentorForm, GuardianForm

from calendar import HTMLCalendar
from datetime import date, datetime, timedelta
from itertools import groupby

from django.utils.html import conditional_escape as esc
from django.utils.safestring import mark_safe

import calendar

# this will assign User to our custom CDCUser
User = get_user_model()


def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month / 12
    month = month % 12 + 1
    day = min(sourcedate.day,calendar.monthrange(year,month)[1])

    return date(year,month,day)

def home(request, template_name="home.html"):

    return render_to_response(template_name,{}, context_instance=RequestContext(request))

def welcome(request, template_name="welcome.html"):

    user = request.user
    account = False
    form = False
    role = user.role if user.role else False

    if request.method == 'POST':
        if role:
            if role == 'mentor':
                form = MentorForm(request.POST, instance=get_object_or_404(Mentor, user=user))
            else:
                form = GuardianForm(request.POST, instance=get_object_or_404(Guardian, user=user))

            if form.is_valid():
                form.save()
                messages.add_message(request, messages.SUCCESS, 'Profile information saved.')
                return HttpResponseRedirect(reverse('dojo'))
            else:
                messages.add_message(request, messages.ERROR, 'There was an error. Please try again.')
        else:
            if request.POST.get('role') == 'mentor':
                mentor = Mentor(user=user)
                mentor.save()
                user.role = 'mentor'
            else:
                guardian = Guardian(user=user)
                guardian.save()
                user.role = 'guardian'

        user.save()
        return HttpResponseRedirect(reverse('welcome'))

    if role:
        if role == 'mentor':
            mentor = get_object_or_404(Mentor, user=user)
            account = mentor
            form = MentorForm(instance=account)

        if role == 'guardian':
            guardian = get_object_or_404(Guardian, user=user)
            account = guardian
            form = GuardianForm(instance=account)


    if account and account.first_name:
        return HttpResponseRedirect(reverse('dojo'))

    return render_to_response(template_name, {
        'role': role,
        'account': account,
        'form': form
    }, context_instance=RequestContext(request))

def sessions(request, year=False, month=False, template_name="sessions.html"):

    now = datetime.now()

    year = int(year) if year else now.year
    month = int(month) if month else now.month

    calendar_date = date(day=1, month=month, year=year)
    prev_date = add_months(calendar_date,-1)
    next_date = add_months(calendar_date,1)

    all_sessions = Session.objects.filter(active=True).order_by('start_date')
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


def session_detail(request, year, month, day, slug, template_name="session-detail.html"):
    session_obj = get_object_or_404(Session, course__slug=slug, start_date__year=year, start_date__month=month, start_date__day=day)

    if request.user.is_authenticated():

        if request.user.role == 'mentor':
            mentor = get_object_or_404(Mentor, user=request.user)
            user_signed_up = True if mentor in session_obj.mentors.all() else False
        else:
            student = get_object_or_404(Student, user=request.user)
            user_signed_up = True if student in session_obj.student.all() else False
    else:
        user_signed_up = False


    return render_to_response(template_name,{
        'session': session_obj,
        'user_signed_up': user_signed_up
    }, context_instance=RequestContext(request))

def session_sign_up(request, year, month, day, slug, template_name="session-sign-up.html"):
    session_obj = get_object_or_404(Session, slug=slug, start_date__year=year, start_date__month=month, start_date__day=day)

    if request.user.role == 'mentor':
        mentor = get_object_or_404(Mentor, user=request.user)
        user_signed_up = True if mentor in session_obj.mentors.all() else False
    else:
        student = get_object_or_404(Student, user=request.user)
        user_signed_up = True if student in session_obj.student.all() else False

    undo = False

    if request.method == 'POST':
        if request.user.role == 'mentor':
            mentor = get_object_or_404(Mentor, user=request.user)
            if mentor in session_obj.mentors.all():
                session_obj.mentors.remove(mentor)
                undo = True
            else:
                session_obj.mentors.add(mentor)
        else:
            student = get_object_or_404(Student, user=request.user)
            if student in session_obj.get_current_students().all():
                session_obj.students.remove(student)
                undo = True
            else:
                session_obj.students.add(student)

        session_obj.save()

        if undo:
            messages.add_message(request, messages.SUCCESS, 'You are no longer attending the class. Thanks for letting us know!')
        else:
            messages.add_message(request, messages.SUCCESS, 'Sign up successful, see you there!')

        return HttpResponseRedirect(reverse('session_detail', args=(session_obj.start_date.year, session_obj.start_date.month, session_obj.start_date.day, session_obj.course.slug)))

    return render_to_response(template_name,{
        'session': session_obj,
        'user_signed_up': user_signed_up
    }, context_instance=RequestContext(request))


def volunteer(request, template_name="volunteer.html"):

    return render_to_response(template_name,{}, context_instance=RequestContext(request))

def faqs(request, template_name="faqs.html"):

    return render_to_response(template_name,{}, context_instance=RequestContext(request))

@login_required
def dojo(request, template_name="dojo.html"):

    context = {}

    if request.user.role:

        if request.user.role == 'mentor':
            mentor = get_object_or_404(Mentor, user=request.user)
            account = mentor

            mentor_sessions = Session.objects.filter(mentors=mentor)
            upcoming_sessions = mentor_sessions.filter(active=True).order_by('start_date')
            past_sessions = mentor_sessions.exclude(active=True).order_by('start_date')


            if request.method == 'POST':
                form = MentorForm(request.POST, instance=account)
                if form.is_valid():
                    form.save()
                    messages.add_message(request, messages.SUCCESS, 'Profile information saved.')
                    return HttpResponseRedirect(reverse('dojo'))
                else:
                    messages.add_message(request, messages.ERROR, 'There was an error. Please try again.')
            else:
                form = MentorForm(instance=account)

            context['upcoming_sessions'] = upcoming_sessions
            context['past_sessions'] = past_sessions

        if request.user.role == 'guardian':
            guardian = get_object_or_404(Guardian, user=request.user)
            account = guardian

            students = Student.objects.filter(guardian=guardian)
            student_orders = Order.objects.filter(student__in=students)
            upcoming_orders = student_orders.filter(active=True).order_by('session__start_date')
            past_orders = student_orders.exclude(active=True).order_by('session__start_date')

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
