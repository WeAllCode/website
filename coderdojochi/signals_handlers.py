# -*- coding: utf-8 -*-

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import get_object_or_404

from coderdojochi.models import Mentor, Donation

from coderdojochi.views import sendSystemEmail

from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received

import arrow


@receiver(post_save, sender=Mentor, dispatch_uid="update_avatar_approved_status")
def avatar_updated_handler(sender, instance, **kwargs):
    try:
        original_mentor = Mentor.objects.get(id=instance.id)
    except ObjectDoesNotExist:
        return

    if not instance.avatar:
        return

    instance.avatar_approved = False

    msg = EmailMultiAlternatives(
        subject='Mentor Avatar Changed',
        body=u'Mentor with email {} changed their avatar image.  Please approve ({}) or reject ({}).'.format(instance.user.email, instance.get_approve_avatar_url(), instance.get_reject_avatar_url()),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.CONTACT_EMAIL]
    )

    msg.attach_alternative(
        u'<h1>Is this avatar okay?</h1><img src="{}"><h2><a href="{}">Approve</a></h2><h2><a href="{}">Reject</a></h2>'.format(
            instance.avatar.thumbnail.url,
            instance.get_approve_avatar_url(),
            instance.get_reject_avatar_url()
        ),
        'text/html'
    )

    msg.send()


def donate_callback(sender, **kwargs):
    ipn_obj = sender

    if ipn_obj.payment_status == ST_PP_COMPLETED:
        donation = get_object_or_404(Donation, id=ipn_obj.invoice)
        donation.verified = True

        if not donation.receipt_sent:
            sendSystemEmail(
                False,
                'Thank you!',
                'coderdojochi-donation-receipt',
                {
                    'first_name': donation.first_name,
                    'last_name': donation.last_name,
                    'email': donation.email,
                    'amount': u'${}'.format(donation.amount),
                    'transaction_date': arrow.get(donation.created_at).format('MMMM D, YYYY h:ss a'),
                    'transaction_id': donation.id
                },
                donation.email,
                [v for k,v in settings.ADMINS]
            )

            donation.receipt_sent = True

        donation.save()


valid_ipn_received.connect(donate_callback)

