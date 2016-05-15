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
        original_mentor = Mentor.objects.get(pk=instance.pk)
    except ObjectDoesNotExist:
        return

    if not instance.avatar or instance.avatar == original_mentor.avatar:
        return

    instance.avatar_approved = False

    msg = EmailMultiAlternatives(
        subject='Mentor Avatar Changed',
        body='Mentor with email ' + instance.user.email + ' changed their avatar image.  Please approve (' + instance.get_approve_avatar_url() + ') or reject (' + instance.get_reject_avatar_url() + ').',
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[v for k,v in settings.ADMINS]
    )
    msg.attach_alternative('<h1>Is this avatar okay?</h1><img src="' + instance.avatar.thumbnail.url + '"><h2><a href="' + instance.get_approve_avatar_url() + '">Approve</a></h2><h2><a href="' + instance.get_reject_avatar_url() + '">Reject</a></h2>', 'text/html')

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

