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
from django.http import HttpResponse, HttpResponseRedirect
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
from coderdojochi.forms import (
    CDCModelForm,
    ContactForm,
    DonationForm,
    GuardianForm,
    MentorForm,
    StudentForm,
)
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
from coderdojochi.views.general import IcsView
from icalendar import Calendar, Event, vText
from paypal.standard.forms import PayPalPaymentsForm

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

        if user.is_authenticated and user.role == 'mentor':
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


class MeetingIcsView(IcsView):
    event_type = 'meeting'
    event_kwarg = 'meeeting_id'
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
