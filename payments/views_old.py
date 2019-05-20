import calendar
import logging
import operator
from collections import Counter
from datetime import date, timedelta
from functools import reduce

import arrow
import stripe
from coderdojochi.forms import (CDCModelForm, ContactForm, DonationForm,
                                GuardianForm, MentorForm, StudentForm)
from coderdojochi.models import (Donation, Equipment, EquipmentType, Guardian,
                                 Meeting, MeetingOrder, Mentor, MentorOrder,
                                 Order, PartnerPasswordAccess, Session,
                                 Student)
from coderdojochi.util import email
from dateutil.relativedelta import relativedelta
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
from django.utils.html import strip_tags
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from djstripe.models import Charge, Customer

# this will assign User to our custom CDCUser
User = get_user_model()


def donate(request, template_name="donate.html"):
    return render(
        request,
        template_name
    )


@csrf_exempt
def donate_charge(request):

    donor_name = request.POST['donor-name']
    donor_email = request.POST['donor-email']
    donor_phone = request.POST['donor-phone']
    donor_amount = request.POST['donor-amount']
    donor_statement = f"Donation to We All Code from {donor_name}"
    stripe_token = request.POST['stripeToken']
    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        charge = stripe.Charge.create(
            amount=int(float(donor_amount) * 100),
            currency='usd',
            card=stripe_token,
            description=donor_statement,
            metadata={
                'name': donor_name,
                'email': donor_email,
                'receipt_email': donor_email,
                'statement_descriptor': donor_statement,
            }
        )
        messages.success(
            request, f"Thank you for your donation of <i>${donor_amount}</i>!")

    except stripe.error.StripeError as e:
        messages.error(
            request,
            f"There was an error processing your payment: {e}. "
            f" Please try again, or contact us if you're having trouble."
        )

    else:
        # TODO: Save to model? Send Receipt? Something...
        messages.success(
            request,
            "Else command worked"
        )

    return redirect('donate')
