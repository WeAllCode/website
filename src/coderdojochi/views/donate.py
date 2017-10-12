from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.generic import View, TemplateView

from paypal.standard.forms import PayPalPaymentsForm

from coderdojochi.models import Donation


class DonateView(TemplateView):
    form_class = PayPalPaymentsForm
    template_name = "donate.html"

    def post(self, request):
        if (
            'first_name' not in request.POST or
            'last_name' not in request.POST or
            'email' not in request.POST or
            'amount' not in request.POST
        ):
            messages.error(
                request,
                'First name, last name, email and amount are required fields.'
            )

            return redirect('donate')

        donation = Donation(
            first_name=request.POST['first_name'],
            last_name=request.POST['last_name'],
            email=request.POST['email'],
            amount=request.POST['amount'],
        )

        donation.save()

        return HttpResponse(donation.id)

    def get_context_data(self, **kwargs):
        context = super(DonateView, self).get_context_data(**kwargs)

        context['form'] = self.form_class(initial={
            'business': settings.PAYPAL_BUSINESS_ID,
            'amount': '25',
            'item_name': 'CoderDojoChi Donation',
            'cmd': '_donations',
            'lc': 'US',
            'invoice': '',
            'currency_code': 'USD',
            'no_note': '0',
            'cn': 'Add a message for CoderDojoChi to read:',
            'no_shipping': '1',
            'address_override': '1',
            'first_name': '',
            'last_name': '',
            'notify_url': u'{}{}'.format(
                settings.SITE_URL,
                reverse('paypal-ipn')
            ),
            'return_url': u'{}/donate/return'.format(
                settings.SITE_URL
            ),
            'cancel_return': u'{}/donate/cancel'.format(
                settings.SITE_URL
            ),
            'bn': 'PP-DonationsBF:btn_donateCC_LG.gif:NonHosted'
        })

        return context


class DonateCancelView(View):
    def get(self, request):
        messages.error(
            request,
            u'Looks like you cancelled the donation process. '
            u'Please feel free to <a href="/{}">contact us</a> '
            u'if you need any help.'.format(
                reverse('contact')
            )
        )

        return redirect('donate')


class DonateReturnView(View):
    def get(self, request):
        messages.success(
            request,
            'Your donation is being processed. '
            'You should receive a confirmation email shortly. Thanks again!'
        )

        return redirect('donate')
