from decimal import *

import stripe
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic.edit import FormView

from .forms import DonateForm
from .models import Donation

# from djstripe.models import Customer

stripe.api_key = settings.STRIPE_SECRET_KEY


class Amount:
    def __init__(self, amount):
        self.pennies = int(float(amount) * 100)

    def __str__(self):
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

        # Get the user from Donation model with email
        user = Donation.objects.get(email=email)

        # Save the donation to the model.
        donation = Donation(
            email=user.email,
            name=user.name,
            amount=amount.pennies,
            stripe_customer_id=user.stripe_customer_id,
        )
        donation.save()

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

        try:
            # Register him as a Stripe Customer first.
            stripe_customer = stripe.Customer.create(
                card=token,
                email=email,
                name=name,
                description="We All Code Customer"
            )

            # Save the Donation to the model
            donation = Donation(
                email=stripe_customer.email,
                amount=amount.pennies,
                name=name,
                stripe_customer_id=stripe_customer.id
            )
            donation.save()

            # Charge the user.
            charge = stripe.Charge.create(
                amount=amount.pennies,
                currency='usd',
                customer=stripe_customer.id,
                description='Donation to We All Code',
                receipt_email=email,
                statement_descriptor='Donation to WeAllCode'
            )

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
