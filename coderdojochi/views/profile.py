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
from django.utils.html import strip_tags
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

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


class DojoMentorView(TemplateView):
    template_name = 'mentor/dojo.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(DojoMentorView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(DojoMentorView, self).get_context_data(**kwargs)
        context['highlight'] = self.request.GET.get('highlight', False)
        mentor = get_object_or_404(Mentor, user=self.request.user)
        context['mentor'] = mentor

        orders = MentorOrder.objects.select_related().filter(
            is_active=True,
            mentor=context['mentor'],
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
        return context

    def post(self, request, *args, **kwargs):
        mentor = get_object_or_404(Mentor, user=request.user)

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

            return redirect('account_home')

        else:
            messages.error(
                request,
                'There was an error. Please try again.'
            )
