# -*- coding: utf-8 -*-

import arrow
import calendar
import logging
import operator

from collections import Counter
from datetime import date, timedelta
from icalendar import Calendar, Event, vText
from paypal.standard.forms import PayPalPaymentsForm

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.core.mail import EmailMultiAlternatives, get_connection
from django.db.models import (
    Case,
    Count,
    IntegerField,
    When,
)
from django.http import (
    HttpResponse,
    HttpResponseRedirect,
)
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.functional import cached_property
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View, TemplateView

from coderdojochi.util import email
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
from coderdojochi.forms import (
    CDCModelForm,
    ContactForm,
    GuardianForm,
    MentorForm,
    StudentForm,
    DonationForm
)
from coderdojochi.mixins import RoleRedirectMixin
from coderdojochi.views.ics import IcsView

logger = logging.getLogger("mechanize")

# this will assign User to our custom CDCUser
User = get_user_model()


class MeetingsView(TemplateView):
    template_name = "meetings.html"

    @cached_property
    def upcoming_meetings(self):
        return Meeting.objects.filter(
            is_active=True,
            is_public=True,
            end_date__gte=timezone.now()
        ).order_by('start_date')[:3]


class MeetingDetailView(TemplateView):
    template_name = "meeting-detail.html"

    def dispatch(self, request, *args, **kwargs):
        meeting_obj = get_object_or_404(Meeting, id=kwargs['meeting_id'])
        kwargs['meeting'] = meeting_obj
        # Replace meeting_detail_short functionality
        if all([k not in kwargs for k in ['year', 'month', 'day', 'slug']]):
            return redirect(meeting_obj.get_absolute_url())
        return super(MeetingDetailView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(MeetingDetailView, self).get_context_data(**kwargs)
        user = self.request.user
        meeting_obj = kwargs['meeting']
        context['meeting'] = meeting_obj

        if user.is_authenticated() and user.role == 'mentor':
            mentor = get_object_or_404(Mentor, user=self.request.user)
            active_meeting_orders = MeetingOrder.objects.filter(
                meeting=meeting_obj,
                is_active=True
            )
            context['active_meeting_orders'] = active_meeting_orders
            context['mentor_signed_up'] = active_meeting_orders.filter(
                mentor=mentor
            ).exists()
        return context


@method_decorator(login_required, name='dispatch')
class MeetingSignUpView(TemplateView):
    template_name = "meeting-sign-up.html"

    def post(self, request, *args, **kwargs):
        meeting = get_object_or_404(
            Meeting,
            id=kwargs['meeting_id']
        )
        mentor = get_object_or_404(
            Mentor,
            user=request.user
        )
        meeting_orders = MeetingOrder.objects.filter(
            meeting=meeting,
            is_active=True
        )

        user_meeting_order = meeting_orders.filter(mentor=mentor)

        if user_meeting_order.exists():
            meeting_order = get_object_or_404(
                MeetingOrder,
                meeting=meeting,
                mentor=mentor
            )
            meeting_order.is_active = False
            meeting_order.save()
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
                meeting=meeting
            )

            meeting_order.ip = ip
            meeting_order.is_active = True
            meeting_order.save()

            messages.success(
                request,
                'Success! See you there!'
            )

            self.confirmation_email(
                request=request,
                meeting=meeting,
                meeting_order=meeting_order
            )

        return HttpResponseRedirect(
            reverse(
                'meeting_detail',
                args=(
                    meeting.start_date.year,
                    meeting.start_date.month,
                    meeting.start_date.day,
                    meeting.meeting_type.slug,
                    meeting.id
                )
            )
        )

    def get_context_data(self, **kwargs):
        context = super(MeetingSignUpView, self).get_context_data(**kwargs)

        context['meeting'] = get_object_or_404(
            Meeting,
            id=context['meeting_id']
        )
        context['mentor'] = get_object_or_404(
            Mentor,
            user=self.request.user
        )
        context['meeting_orders'] = MeetingOrder.objects.filter(
            meeting=context['meeting'],
            is_active=True
        )

        user_meeting_order = context['meeting_orders'].filter(
            mentor=context['mentor']
        )
        context['user_signed_up'] = True if user_meeting_order.count() else False

        return context

    def confirmation_email(self, **kwargs):
        email(
            subject='Upcoming mentor meeting confirmation',
            template_name='meeting-confirm-mentor',
            context={
                'first_name': kwargs['request'].user.first_name,
                'last_name': kwargs['request'].user.last_name,
                'meeting_title': kwargs['meeting'].meeting_type.title,
                'meeting_description': (
                    kwargs['meeting'].meeting_type.description
                ),
                'meeting_start_date': arrow.get(
                    kwargs['meeting'].start_date
                ).to('local').format('dddd, MMMM D, YYYY'),
                'meeting_start_time': arrow.get(
                    kwargs['meeting'].start_date
                ).to('local').format('h:mma'),
                'meeting_end_date': arrow.get(
                    kwargs['meeting'].end_date
                ).to('local').format('dddd, MMMM D, YYYY'),
                'meeting_end_time': arrow.get(
                    kwargs['meeting'].end_date
                ).to('local').format('h:mma'),
                'meeting_location_name': kwargs['meeting'].location.name,
                'meeting_location_street': kwargs['meeting'].location.street,
                'meeting_location_city': kwargs['meeting'].location.city,
                'meeting_location_state': kwargs['meeting'].location.state,
                'meeting_location_zip': kwargs['meeting'].location.zip,
                'meeting_additional_info': kwargs['meeting'].additional_info,
                'meeting_url': kwargs['meeting'].get_absolute_url(),
                'meeting_ics_url': kwargs['meeting'].get_ics_url(),
                'microdata_start_date': arrow.get(
                    kwargs['meeting'].start_date
                ).to('local').isoformat(),
                'microdata_end_date': arrow.get(
                    kwargs['meeting'].end_date
                ).to('local').isoformat(),
                'order': kwargs['meeting_order'],
            },
            recipients=[kwargs['request'].user.email],
            preheader=u'Thanks for signing up for our next meeting, '
                      '{}. We look forward to seeing you '
                      'there.'.format(kwargs['request'].user.first_name),
        )


class MeetingIcsView(IcsView):
    event_type = 'meeting'
    event_kwarg = 'meeeting_id'
    event_class = Meeting

    def get_summary(self, request, event_obj):
        event_name = u'{} - '.format(
            event_obj.meeting_type.code
        ) if event_obj.meeting_type.code else ''
        event_name += event_obj.meeting_type.title
        return u'CoderDojoChi: {}'.format(event_name)

    def get_dtstart(self, request, event_obj):
        return arrow.get(event_obj.start_date).format('YYYYMMDDTHHmmss')

    def get_dtend(self, request, event_obj):
        return arrow.get(event_obj.end_date).format('YYYYMMDDTHHmmss')

    def get_description(self, request, event_obj):
        return strip_tags(event_obj.meeting_type.description)
