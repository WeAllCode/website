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
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.html import strip_tags
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, ListView, RedirectView, TemplateView, View

import arrow
from accounts.forms import GuardianForm, MentorForm
from icalendar import Calendar, Event, vText
from paypal.standard.forms import PayPalPaymentsForm

from coderdojochi.forms import CDCForm, CDCModelForm, ContactForm, DonationForm, SignupForm, StudentForm
from coderdojochi.mixins import RoleRedirectMixin
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
from coderdojochi.views.general import CalendarView

logger = logging.getLogger(__name__)

# this will assign User to our custom CDCUser
User = get_user_model()


class MeetingsView(ListView):
    model = Meeting
    template_name = "meetings.html"

    def get_queryset(self):
        objects = self.model.objects.filter(
            end_date__gte=timezone.now()
        )

        if not self.request.user.is_authenticated:
            objects = objects.filter(is_public=True)

        if not self.request.user.is_staff:
            objects = objects.filter(is_active=True)

        return objects


class MeetingDetailRedirectView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse('meeting-detail', args=(kwargs['pk'],))


class MeetingDetailView(DetailView):
    model = Meeting
    template_name = "meeting-detail.html"

    def get_queryset(self):
        objects = self.model.objects.filter()

        if not self.request.user.is_authenticated:
            objects = objects.filter(is_public=True)

        if not self.request.user.is_staff:
            objects = objects.filter(is_active=True)

        return objects

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except Http404:
            return redirect('meetings')

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user

        if user.is_authenticated and user.role == 'mentor':
            mentor = get_object_or_404(Mentor, user=self.request.user)

            active_meeting_orders = MeetingOrder.objects.filter(
                meeting=self.object,
                is_active=True
            )
            context['active_meeting_orders'] = active_meeting_orders
            context['mentor_signed_up'] = active_meeting_orders.filter(
                mentor=mentor
            ).exists()

        return context


class MeetingCalendarRedirectView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse('meeting-calendar', args=(kwargs['pk'],))


class MeetingCalendarView(CalendarView):
    event_type = 'meeting'
    event_kwarg = 'pk'
    event_class = Meeting

    def get_summary(self, request, event_obj):
        event_name = f"{event_obj.meeting_type.code} - " if event_obj.meeting_type.code else ''
        event_name += event_obj.meeting_type.title
        return f"CoderDojoChi: {event_name}"

    def get_dtstart(self, request, event_obj):
        return arrow.get(event_obj.start_date).format('YYYYMMDDTHHmmss')

    def get_dtend(self, request, event_obj):
        return arrow.get(event_obj.end_date).format('YYYYMMDDTHHmmss')

    def get_description(self, event_obj):
        return strip_tags(event_obj.meeting_type.description)


def meeting_sign_up(request, pk, template_name="meeting-sign-up.html"):
    meeting_obj = get_object_or_404(Meeting, pk=pk)

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

            merge_global_data = {
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'order_id': meeting_order.id,
                'meeting_title': meeting_obj.meeting_type.title,
                'meeting_description': meeting_obj.meeting_type.description,
                'meeting_start_date': arrow.get(meeting_obj.start_date).to('local').format('dddd, MMMM D, YYYY'),
                'meeting_start_time': arrow.get(meeting_obj.start_date).to('local').format('h:mma'),
                'meeting_end_date': arrow.get(meeting_obj.end_date).to('local').format('dddd, MMMM D, YYYY'),
                'meeting_end_time': arrow.get(meeting_obj.end_date).to('local').format('h:mma'),
                'meeting_location_name': meeting_obj.location.name,
                'meeting_location_address': meeting_obj.location.address,
                'meeting_location_city': meeting_obj.location.city,
                'meeting_location_state': meeting_obj.location.state,
                'meeting_location_zip': meeting_obj.location.zip,
                'meeting_additional_info': meeting_obj.additional_info,
                'meeting_url': f"{settings.SITE_URL}{meeting_obj.get_absolute_url()}",
                'meeting_calendar_url': f"{settings.SITE_URL}{meeting_obj.get_calendar_url()}",
                'microdata_start_date': arrow.get(meeting_obj.start_date).to('local').isoformat(),
                'microdata_end_date': arrow.get(meeting_obj.end_date).to('local').isoformat(),
            }

            email(
                subject='Upcoming mentor meeting confirmation',
                template_name='meeting-confirm-mentor',
                merge_global_data=merge_global_data,
                recipients=[request.user.email],
                preheader=(
                    f"Thanks for signing up for our next meeting, {request.user.first_name}. "
                    f"We look forward to seeing there."
                ),
            )

        return redirect('meeting-detail', meeting_obj.id)

    return render(request, template_name, {
        'meeting': meeting_obj,
        'user_signed_up': user_signed_up
    })


def meeting_announce(request, pk):
    if not request.user.is_staff:
        messages.error(
            request,
            'You do not have permission to access this page.'
        )
        return redirect('home')

    meeting_obj = get_object_or_404(Meeting, pk=pk)

    if not meeting_obj.announced_date:
        merge_data = {}
        merge_global_data = {
            'meeting_title': meeting_obj.meeting_type.title,
            'meeting_description': meeting_obj.meeting_type.description,
            'meeting_start_date': arrow.get(meeting_obj.start_date).to('local').format('dddd, MMMM D, YYYY'),
            'meeting_start_time': arrow.get(meeting_obj.start_date).to('local').format('h:mma'),
            'meeting_end_date': arrow.get(meeting_obj.end_date).to('local').format('dddd, MMMM D, YYYY'),
            'meeting_end_time': arrow.get(meeting_obj.end_date).to('local').format('h:mma'),
            'meeting_location_name': meeting_obj.location.name,
            'meeting_location_address': meeting_obj.location.address,
            'meeting_location_city': meeting_obj.location.city,
            'meeting_location_state': meeting_obj.location.state,
            'meeting_location_zip': meeting_obj.location.zip,
            'meeting_additional_info': meeting_obj.additional_info,
            'meeting_url': f"{settings.SITE_URL}{meeting_obj.get_absolute_url()}",
            'meeting_calendar_url': f"{settings.SITE_URL}{meeting_obj.get_calendar_url()}",
        }

        mentors = Mentor.objects.filter(
            is_active=True,
            user__is_active=True,
        )

        recipients = []
        for mentor in mentors:
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
            preheader='A new meeting has been announced. Come join us for some amazing fun!',
        )

        meeting_obj.announced_date = timezone.now()
        meeting_obj.save()

        messages.success(
            request,
            f"Meeting announced to {mentors.count()} mentors."
        )
    else:
        messages.warning(
            request,
            'Meeting already announced.'
        )

    return redirect('cdc-admin')
