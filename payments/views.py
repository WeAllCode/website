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


class DonateView(FormView):
    template_name = 'donate.html'
    form_class = DonateForm
    success_url = reverse_lazy('donate')

    def get_initial(self):
        initial = self.initial.copy()

        if self.request.user.is_authenticated:
            initial['email'] = self.request.user.email
            initial['name'] = self.request.user.get_full_name()

        return initial

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        # form.send_email()
        data = form.cleaned_data
        stripe_token = self.request.POST['stripeToken']
        stripe.api_key = settings.STRIPE_SECRET_KEY
        user_email = self.request.POST['email']
        amount = int(float(data['amount'] * 100))
        is_registered_customer = Donation.objects.filter(
            email=user_email).exists()

        if self.request.user.is_authenticated & is_registered_customer:
            print("User is authenticated and registered customer")
            # user = Donation.objects.get(email=user_email)
            # customer = stripe.Customer.retrieve(user.stripe_customer_id)

            # try:

            #     donation = Donation(
            #         email=stripe_customer.email,
            #         amount=amount,
            #         stripe_customer_id=stripe_customer.id
            #     )
            #     donation.save()

            #     charge = stripe.Charge.create(
            #         amount=amount,
            #         currency='usd',
            #         customer=stripe_customer.id,
            #         description='Donation to We All Code',
            #         receipt_email=data['email'],
            #         statement_descriptor='Donation to WeAllCode'
            #     )

            #     messages.success(
            #         self.request, f"Thank you for your donation of <i>${data['amount']}</i>!")

            # except stripe.error.StripeError as e:
            #     messages.error(
            #         self.request,
            #         f"There was an error processing your payment: {e}. "
            #         f" Please try again, or contact us if you're having trouble."
            #     )
        else:
            print("User anonymous and not stripe user")

            try:

                stripe_customer = stripe.Customer.create(
                    card=stripe_token,
                    email=user_email,
                    description=user_email
                )

                donation = Donation(
                    email=stripe_customer.email,
                    amount=amount,
                    stripe_customer_id=stripe_customer.id
                )
                donation.save()

                charge = stripe.Charge.create(
                    amount=amount,
                    currency='usd',
                    customer=stripe_customer.id,
                    description='Donation to We All Code',
                    receipt_email=data['email'],
                    statement_descriptor='Donation to WeAllCode'
                )

                messages.success(
                    self.request, f"Thank you for your donation of <i>${data['amount']}</i>!")

            except stripe.error.StripeError as e:
                messages.error(
                    self.request,
                    f"There was an error processing your payment: {e}. "
                    f" Please try again, or contact us if you're having trouble."
                )

        return HttpResponseRedirect(self.get_success_url())

    # if not self.request.user.is_authenticated:
    #     customer = stripe.Customer.create(
    #         name=data['name'],
    #         email=data['email'],
    #         description=data['name'],
    #         source=stripe_token
    #     )
    #     donation = Donation(
    #         email=customer.email,
    #         stripe_customer_id=customer.id
    #     )
    #     donation.save()

    # try:
    #     charge = stripe.Charge.create(
    #         amount=int(float(data['amount']) * 100),
    #         currency='usd',
    #         customer=customer,
    #         description='Donation to We All Code',
    #         receipt_email=data['email'],
    #         statement_descriptor='Donation to WeAllCode'
    #     )
    #     messages.success(
    #         self.request, f"Thank you for your donation of <i>${data['amount']}</i>!")

    # except stripe.error.StripeError as e:
    #     messages.error(
    #         self.request,
    #         f"There was an error processing your payment: {e}. "
    #         f" Please try again, or contact us if you're having trouble."
    #     )

    # else:
    # TODO: Save to model? Send Receipt? Something...
    # if self.request.user.is_authenticated:
    #     user = self.request.user
    #     customer, created = Customer.get_or_create(subscriber=user)
    # else:
    #     new_user = {
    #         'name': data['name'],
    #         'email': data['email']
    #     }
    #     customer, created = Customer.get_or_create(
    #         subscriber=new_user
    #     )
    # if not self.request.user.is_authenticated:

    # messages.success(
    #     self.request,
    #     "Else command worked"
    # )
