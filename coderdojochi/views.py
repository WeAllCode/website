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

from coderdojochi.models import Class, Mentor, Student
from coderdojochi.forms import MentorForm

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

def classes(request, year=False, month=False, template_name="classes.html"):

    now = datetime.now()

    year = int(year) if year else now.year
    month = int(month) if month else now.month

    calendar_date = date(day=1, month=month, year=year)
    prev_date = add_months(calendar_date,-1)
    next_date = add_months(calendar_date,1)

    all_classes = Class.objects.filter(active=True).order_by('start_date')
    classes = all_classes.filter(start_date__year=year, start_date__month=month).order_by('start_date')
    cal = ClassesCalendar(classes).formatmonth(year, month)

    return render_to_response(template_name,{
        'all_classes': all_classes,
        'classes': classes,
        'calendar': mark_safe(cal),
        'calendar_date': calendar_date,
        'prev_date': prev_date,
        'next_date': next_date
    }, context_instance=RequestContext(request))


def class_detail(request, year, month, day, slug, template_name="class-detail.html"):
    class_obj = get_object_or_404(Class, slug=slug, start_date__year=year, start_date__month=month, start_date__day=day)

    if request.user.role == 'mentor':
        mentor = get_object_or_404(Mentor, user=request.user)
        user_signed_up = True if mentor in class_obj.mentors.all() else False
    else:
        student = get_object_or_404(Student, user=request.user)
        user_signed_up = True if student in class_obj.student.all() else False


    return render_to_response(template_name,{
        'class': class_obj,
        'user_signed_up': user_signed_up
    }, context_instance=RequestContext(request))

def class_sign_up(request, year, month, day, slug, template_name="class-sign-up.html"):
    class_obj = get_object_or_404(Class, slug=slug, start_date__year=year, start_date__month=month, start_date__day=day)

    if request.user.role == 'mentor':
        mentor = get_object_or_404(Mentor, user=request.user)
        user_signed_up = True if mentor in class_obj.mentors.all() else False
    else:
        student = get_object_or_404(Student, user=request.user)
        user_signed_up = True if student in class_obj.student.all() else False

    undo = False

    if request.method == 'POST':
        if request.user.role == 'mentor':
            mentor = get_object_or_404(Mentor, user=request.user)
            if mentor in class_obj.mentors.all():
                class_obj.mentors.remove(mentor)
                undo = True
            else:
                class_obj.mentors.add(mentor)
        else:
            student = get_object_or_404(Student, user=request.user)
            if student in class_obj.students.all():
                class_obj.students.remove(student)
                undo = True
            else:
                class_obj.students.add(student)

        class_obj.save()

        if undo:
            messages.add_message(request, messages.SUCCESS, 'You are no longer attending the class. Thanks for letting us know!')
        else:
            messages.add_message(request, messages.SUCCESS, 'Sign up successful, see you there!')

        return HttpResponseRedirect(reverse('class_detail', args=(class_obj.start_date.year, class_obj.start_date.month, class_obj.start_date.day, class_obj.slug)))

    return render_to_response(template_name,{
        'class': class_obj,
        'user_signed_up': user_signed_up
    }, context_instance=RequestContext(request))


def volunteer(request, template_name="volunteer.html"):

    return render_to_response(template_name,{}, context_instance=RequestContext(request))

def faqs(request, template_name="faqs.html"):

    return render_to_response(template_name,{}, context_instance=RequestContext(request))

@login_required
def dojo(request, template_name="dojo.html"):

    if request.user.role == 'mentor':
        mentor = get_object_or_404(Mentor, user=request.user)
        mentor_classes = Class.objects.filter(mentors=mentor)
        upcoming_classes = mentor_classes.filter(active=True).order_by('start_date')
        past_classes = mentor_classes.exclude(active=True).order_by('start_date')
        account = mentor

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
    else:
        student = get_object_or_404(Student, user=request.user)
        student_classes = Class.objects.filter(students=student)
        upcoming_classes = upcoming_classes.filter(active=True).order_by('start_date')
        past_classes = upcoming_classes.exclude(active=True).order_by('start_date')
        account = student
        form = False

    return render_to_response(template_name, {
        'account': account,
        'upcoming_classes': upcoming_classes,
        'past_classes': past_classes,
        'form': form
    }, context_instance=RequestContext(request))


class ClassesCalendar(HTMLCalendar):

    def __init__(self, classes):
        super(ClassesCalendar, self).__init__()
        self.classes = self.group_by_day(classes)

    def formatday(self, day, weekday):
        if day != 0:
            cssclass = self.cssclasses[weekday]
            if date.today() == date(self.year, self.month, day):
                cssclass += ' today'
            if day in self.classes:
                cssclass += ' filled'
                body = []
                for cdc_class in self.classes[day]:
                    remaining_spots = cdc_class.capacity - cdc_class.students.all().count()
                    dayclass = 'unavailable' if not remaining_spots else 'available'
                    body.append('<a class="' + dayclass + '" href="%s">' % cdc_class.get_absolute_url())
                    body.append(esc(cdc_class.title))
                    body.append('</a>')
                return self.day_cell(cssclass, '%d %s' % (day, ''.join(body)))
            return self.day_cell(cssclass, day)
        return self.day_cell('noday', '&nbsp;')

    def formatmonth(self, year, month):
        self.year, self.month = year, month
        return super(ClassesCalendar, self).formatmonth(year, month)

    def group_by_day(self, classes):
        field = lambda cdc_class: cdc_class.start_date.day
        return dict(
            [(day, list(items)) for day, items in groupby(classes, field)]
        )

    def day_cell(self, cssclass, body):
        return '<td class="%s">%s</td>' % (cssclass, body)
