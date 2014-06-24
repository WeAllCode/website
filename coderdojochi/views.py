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
from datetime import date, datetime
from itertools import groupby

from django.utils.html import conditional_escape as esc
from django.utils.safestring import mark_safe


# this will assign User to our custom CDCUser
User = get_user_model()


def home(request, template_name="home.html"):

    return render_to_response(template_name,{}, context_instance=RequestContext(request))

def classes(request, year=False, month=False, template_name="classes.html"):

    now = datetime.now()

    year = year if year else now.year
    month = month if month else now.month

    classes = Class.objects.filter(active=True, start_date__year=year, start_date__month=month).order_by('start_date')
    cal = ClassesCalendar(classes).formatmonth(year, month)

    return render_to_response(template_name,{
        'classes': classes,
        'calendar': mark_safe(cal)
    }, context_instance=RequestContext(request))


def class_detail(request, year, month, day, slug, template_name="class-detail.html"):
    class_obj = get_object_or_404(Class, slug=slug, start_date__year=year, start_date__month=month, start_date__day=day)
    return render_to_response(template_name,{
        'class': class_obj
    }, context_instance=RequestContext(request))


def volunteer(request, template_name="volunteer.html"):

    return render_to_response(template_name,{}, context_instance=RequestContext(request))

def faqs(request, template_name="faqs.html"):

    return render_to_response(template_name,{}, context_instance=RequestContext(request))

@login_required
def dojo(request, template_name="dojo.html"):

    if request.user.role == 'mentor':
        upcoming_classes = Class.objects.filter(mentors=request.user)
        account = Mentor.objects.get(user=request.user)

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
        upcoming_classes = Class.objects.filter(students=request.user)
        account = Student.objects.get(user=request.user)
        form = False

    return render_to_response(template_name, {
        'account': account,
        'upcoming_classes': upcoming_classes,
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
                body = ['<ul>']
                for cdc_class in self.classes[day]:
                    body.append('<li>')
                    body.append('<a href="%s">' % cdc_class.get_absolute_url())
                    body.append(esc(cdc_class.title))
                    body.append('</a></li>')
                body.append('</ul>')
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
