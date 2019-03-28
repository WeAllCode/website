import calendar
import logging
import operator
from collections import Counter
from datetime import date, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMultiAlternatives, get_connection
from django.db.models import Case, Count, IntegerField, When
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.html import strip_tags
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, View

import arrow
from accounts.forms import GuardianForm, MentorForm
from icalendar import Calendar, Event, vText
from paypal.standard.forms import PayPalPaymentsForm

from coderdojochi.forms import CDCModelForm, ContactForm, DonationForm, StudentForm
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

logger = logging.getLogger(__name__)

# this will assign User to our custom CDCUser
User = get_user_model()


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        upcoming_classes = Session.objects.filter(
            is_active=True,
            end_date__gte=timezone.now(),
        ).order_by('start_date')

        if (not self.request.user.is_authenticated or not self.request.user.role == 'mentor'):
            upcoming_classes = upcoming_classes.filter(is_public=True)

        context['upcoming_classes'] = upcoming_classes[:3]

        return context


class AboutView(TemplateView):
    template_name = "about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Number of active mentors
        context['mentor_count'] = Mentor.objects.filter(
            is_active=True,
            is_public=True,
        ).count()

        # Number of served students based on checkin counts
        context['students_served_count'] = Order.objects.exclude(
            is_active=False,
            check_in=None
        ).count()

        return context


class PrivacyView(TemplateView):
    template_name = "privacy.html"


class WelcomeView(TemplateView):
    template_name = "welcome.html"

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        next_url = request.GET.get('next')
        kwargs['next_url'] = next_url
        # Check for redirect condition on mentor, otherwise pass as kwarg
        if (
            getattr(request.user, 'role', False) == 'mentor'
            and request.method == 'GET'
        ):
            mentor = get_object_or_404(Mentor, user=request.user)
            if mentor.user.first_name:
                return redirect(next_url if next_url else 'account_home')
            kwargs['mentor'] = mentor
        return super(WelcomeView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(WelcomeView, self).get_context_data(**kwargs)
        user = self.request.user
        mentor = kwargs.get('mentor')
        account = False
        role = getattr(user, 'role', False)

        context['role'] = role
        context['next_url'] = kwargs['next_url']

        if mentor:
            account = mentor
            context['form'] = MentorForm(instance=account)
        if role == 'guardian':
            guardian = get_object_or_404(Guardian, user=user)
            account = guardian
            if not account.phone or not account.zip:
                context['form'] = GuardianForm(instance=account)
            else:
                context['add_student'] = True
                context['form'] = StudentForm(initial={'guardian': guardian.pk})

            if account.user.first_name and account.get_students():
                context['students'] = account.get_students().count()

        context['account'] = account

        return context

    def post(self, request, *args, **kwargs):
        user = request.user
        role = getattr(user, 'role', False)
        next_url = kwargs['next_url']

        if role:
            if role == 'mentor':
                account = get_object_or_404(Mentor, user=user)
                return self.update_account(request, account, next_url)
            account = get_object_or_404(Guardian, user=user)

            if not account.phone or not account.zip:
                return self.update_account(request, account, next_url)

            return self.add_student(request, account, next_url)
        else:
            return self.create_new_user(request, user, next_url)

    def update_account(self, request, account, next_url):
        if isinstance(account, Mentor):
            form = MentorForm(request.POST, instance=account)
            role = 'mentor'
        else:
            form = GuardianForm(request.POST, instance=account)
            role = 'guardian'
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile information saved.')
            if next_url:
                if 'enroll' in request.GET:
                    next_url = f"{next_url}?enroll=True"
            else:
                next_url = 'account_home' if isinstance(account, Mentor) else 'welcome'
            return redirect(next_url)

        return render(request, self.template_name, {
            'form': form,
            'role': role,
            'account': account,
            'next_url': next_url
        })

    def add_student(self, request, account, next_url):
        form = StudentForm(request.POST)
        if form.is_valid():
            new_student = form.save(commit=False)
            new_student.guardian = account
            new_student.save()
            messages.success(request, 'Student Registered.')
            if next_url:
                if 'enroll' in request.GET:
                    next_url = f"{next_url}?enroll=True&student={new_student.id}"
            else:
                next_url = 'welcome'
            return redirect(next_url)

        return render(request, self.template_name, {
            'form': form,
            'role': 'guardian',
            'account': account,
            'next_url': next_url,
            'add_student': True
        })

    def create_new_user(self, request, user, next_url):
        if request.POST.get('role') == 'mentor':
            role = 'mentor'
            account, created = Mentor.objects.get_or_create(user=user)
        else:
            role = 'guardian'
            account, created = Guardian.objects.get_or_create(user=user)

        account.user.first_name = user.first_name
        account.user.last_name = user.last_name
        account.save()

        user.role = role
        user.save()

        merge_global_data = {
            'user': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name
        }

        next_url = f"?next={next_url}" if next_url else None

        if role == 'mentor':
            # check for next upcoming meeting
            next_meeting = Meeting.objects.filter(
                is_active=True,
                is_public=True
            ).order_by('start_date').first()

            if next_meeting:
                merge_global_data['next_intro_meeting_url'] = f"{settings.SITE_URL}{next_meeting.get_absolute_url()}"
                merge_global_data['next_intro_meeting_calendar_url'] = (
                    f"{settings.SITE_URL}{next_meeting.get_calendar_url()}"
                )
            if not next_url:
                next_url = reverse('account_home')
        else:
            # check for next upcoming class
            next_class = Session.objects.filter(
                is_active=True
            ).order_by('start_date').first()

            if next_class:
                merge_global_data['next_class_url'] = f"{settings.SITE_URL}{next_class.get_absolute_url()}"
                merge_global_data['next_class_calendar_url'] = f"{settings.SITE_URL}{next_class.get_calendar_url()}"

            if not next_url:
                next_url = reverse('welcome')

        email(
            subject='Welcome!',
            template_name=f"welcome-{role}",
            merge_global_data=merge_global_data,
            recipients=[user.email],
            preheader='Your adventure awaits!',
        )

        return redirect(next_url)


class CalendarView(View):
    event_type = None
    event_kwarg = "pk"
    event_class = None

    def get_summary(self, request, event_obj):
        raise NotImplementedError

    def get_dtstart(self, request, event_obj):
        raise NotImplementedError

    def get_dtend(self, request, event_obj):
        raise NotImplementedError

    def get_description(self, event_obj):
        raise NotImplementedError

    def get(self, request, *args, **kwargs):
        event_obj = get_object_or_404(
            self.event_class,
            id=kwargs[self.event_kwarg]
        )
        cal = Calendar()

        cal['prodid'] = '-//CoderDojoChi//coderdojochi.org//'
        cal['version'] = '2.0'
        cal['calscale'] = 'GREGORIAN'

        event = Event()

        event['uid'] = f"{self.event_type.upper()}{event_obj.id:04}@coderdojochi.org"
        event['summary'] = self.get_summary(request, event_obj)
        event['dtstart'] = self.get_dtstart(request, event_obj)
        event['dtend'] = self.get_dtend(request, event_obj)
        event['dtstamp'] = event['dtstart'][:-1]

        location = (
            f"{event_obj.location.name}, {event_obj.location.address}, "
            f"{event_obj.location.city}, {event_obj.location.state}, {event_obj.location.zip}"
        )

        event['location'] = vText(location)

        event['url'] = f"{settings.SITE_URL}{event_obj.get_absolute_url()}"
        event['description'] = self.get_description(event_obj)

        # A value of 5 is the normal or "MEDIUM" priority.
        # see: https://tools.ietf.org/html/rfc5545#section-3.8.1.9
        event['priority'] = 5

        cal.add_component(event)

        event_slug = "coderdojochi-{event_type}_{date}".format(
            event_type=self.event_type.lower(),
            date=arrow.get(
                event_obj.start_date
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
