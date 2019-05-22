from decimal import *

import stripe
from coderdojochi.models import CDCUser
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic.edit import FormView

from .forms import DonateForm
from .models import Donation

stripe.api_key = settings.STRIPE_SECRET_KEY


class Amount:
    # A class to format the amount.
    # Params (amount)
    def __init__(self, amount):
        self.pennies = float(amount)
        self.pennies = round(self.pennies) * 100
        self.pennies = int(self.pennies)

    def __str__(self):
        # Format to dollars
        return "{:.2f}".format(self.pennies / 100)


class DonateView(FormView):
    template_name = 'donate.html'
    form_class = DonateForm
    success_url = reverse_lazy('donate')

    # Populate the form is user is authenticated.
    def get_initial(self):
        initial = self.initial.copy()

        if self.request.user.is_authenticated:
            initial['email'] = self.request.user.email
            initial['name'] = self.request.user.get_full_name()

        return initial

    # An already registered customer is making a donation
    def donation_is_registered_customer(self, email, name, amount):
        customer = None
        # Get the user from Donation model with email
        user = Donation.objects.filter(email=email).first()

        # Check if user exists in our Database
        user_email_exists = CDCUser.objects.filter(email=email).exists()

        # If the user exists attach it to customer
        if user_email_exists:
            customer = CDCUser.objects.get(email=email)

        try:
            # Charge the user on Stripe.
            charge = stripe.Charge.create(
                amount=amount.pennies,
                currency='usd',
                customer=user.stripe_customer_id,
                description='Donation to We All Code',
                receipt_email=user.email,
                statement_descriptor='Donation to WeAllCode'
            )

            # Save the donation to the model.
            donation = Donation(
                customer=customer,
                email=user.email,
                name=user.name,
                amount=amount.pennies,
                stripe_customer_id=user.stripe_customer_id,
                stripe_payment_id=charge.id
            )
            donation.save()

            # On Charge success alert the user.
            messages.success(
                self.request,
                f"Thank you for your donation of <i>${ amount }</i>!"
            )

            # On Charge error alert the user.
        except stripe.error.StripeError as e:
            messages.error(
                self.request,
                f"There was an error processing your payment: {e}. "
                f" Please try again, or contact us if you're having trouble."
            )

    # A new customer is making a donation.
    def donation_is_new_customer(self, token, email, name, amount):
        customer = None
        try:
            # Register him as a Stripe Customer first.
            stripe_customer = stripe.Customer.create(
                card=token,
                email=email,
                name=name,
                description="We All Code Customer"
            )

            # Check if user is authenticated
            if self.request.user.is_authenticated:
                customer = self.request.user

            # Check if user exists in our Database
            user_email_exists = CDCUser.objects.filter(email=email).exists()

            if user_email_exists:
                customer = CDCUser.objects.get(email=email)

            # Charge the user.
            charge = stripe.Charge.create(
                amount=amount.pennies,
                currency='usd',
                customer=stripe_customer.id,
                description='Donation to We All Code',
                receipt_email=email,
                statement_descriptor='Donation to WeAllCode'
            )

            # Save the Donation to the model
            donation = Donation(
                customer=customer,
                email=stripe_customer.email,
                amount=amount.pennies,
                name=name,
                stripe_customer_id=stripe_customer.id,
                stripe_payment_id=charge.id
            )
            donation.save()

            messages.success(
                self.request,
                f"Thank you for your donation of <i>${ amount }</i>!"
            )

        except stripe.error.StripeError as e:
            messages.error(
                self.request,
                f"There was an error processing your payment: {e}. "
                f" Please try again, or contact us if you're having trouble."
            )

    def form_valid(self, form):

        # Clean up the submited data.
        data = form.cleaned_data

        # Stripe token is retrieved from Stripe.JS
        stripe_token = self.request.POST['stripeToken']

        # User email retrieved from form
        user_email = self.request.POST['email']

        # Name retrieved from form
        name = self.request.POST['name']

        # Amount class atached to the amount var
        amount = Amount(data['amount'])

        # Check if the user exists in Donation model. Returns bool
        is_registered_customer = Donation.objects.filter(
            email=user_email
        ).exists()

        # If true call the function for a registered customer
        if is_registered_customer:
            self.donation_is_registered_customer(
                user_email,
                name,
                amount,
            )
        else:
            # Else call the function for a new customer.
            self.donation_is_new_customer(
                stripe_token,
                user_email,
                name,
                amount,
            )

        return HttpResponseRedirect(self.get_success_url())
