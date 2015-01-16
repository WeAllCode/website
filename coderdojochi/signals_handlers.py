from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver

from avatar.signals import avatar_updated

from coderdojochi.models import Mentor 

@receiver(avatar_updated)
def avatar_updated_handler(sender, user, avatar, **kwargs):
    
    mentor = Mentor.objects.get(user=user)
    mentor.public = False
    mentor.save()

    msg = EmailMultiAlternatives(
        subject='Mentor Avatar Changed',
        body='Mentor with email ' + mentor.user.email + ' changed their avatar image.  Please approve (' + mentor.get_approve_avatar_url() + ') or reject (' + mentor.get_reject_avatar_url() + ').',
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[v for k,v in settings.ADMINS]
    )
    msg.attach_alternative('<h1>Is this avatar okay?</h1><img src="' + avatar.avatar_url(400) + '"><h2><a href="' + mentor.get_approve_avatar_url() + '">Allow</a></h2><h2><a href="' + mentor.get_reject_avatar_url() + '">Deny</a></h2>', 'text/html')

    msg.send()