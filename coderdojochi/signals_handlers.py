from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver
from django.shortcuts import get_object_or_404

from avatar.signals import avatar_updated

from coderdojochi.models import Mentor, Donation

from coderdojochi.views import sendSystemEmail

from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received

import arrow


@receiver(avatar_updated)
def avatar_updated_handler(sender, user, avatar, **kwargs):
    
    mentor = Mentor.objects.get(user=user)
    mentor.public = False
    mentor.save()

    # create thumbnail for email
    avatar.create_thumbnail(400, quality=80)

    msg = EmailMultiAlternatives(
        subject='Mentor Avatar Changed',
        body='Mentor with email ' + mentor.user.email + ' changed their avatar image.  Please approve (' + mentor.get_approve_avatar_url() + ') or reject (' + mentor.get_reject_avatar_url() + ').',
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[v for k,v in settings.ADMINS]
    )
    msg.attach_alternative('<h1>Is this avatar okay?</h1><img src="' + avatar.avatar_url(400) + '"><h2><a href="' + mentor.get_approve_avatar_url() + '">Approve</a></h2><h2><a href="' + mentor.get_reject_avatar_url() + '">Reject</a></h2>', 'text/html')

    msg.send()


def donate_callback(sender, **kwargs):
    
    ipn_obj = sender

    if ipn_obj.payment_status == ST_PP_COMPLETED:
        donation = get_object_or_404(Donation, id=ipn_obj.invoice)
        donation.verified = True
        
        if not donation.receipt_sent:
            sendSystemEmail(False, 'Thank you!', 'coderdojochi-donation-receipt', {
                'first_name': donation.first_name,
                'last_name': donation.last_name,
                'email': donation.email,
                'amount': '$' + str(donation.amount),
                'transaction_date': arrow.get(donation.created_at).format('MMMM D, YYYY h:ss a'),
                'transaction_id': donation.id
            }, donation.email, [v for k,v in settings.ADMINS])

            donation.receipt_sent = True

        donation.save()
        

valid_ipn_received.connect(donate_callback)

    