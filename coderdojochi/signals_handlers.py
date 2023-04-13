from email.mime.image import MIMEImage

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import pre_save
from django.dispatch import receiver

from coderdojochi.models import Mentor
from coderdojochi.util import email


@receiver(pre_save, sender=Mentor)
def avatar_updated_handler(sender, instance, **kwargs):
    try:
        original_mentor = Mentor.objects.get(id=instance.id)
    except ObjectDoesNotExist:
        return

    if not instance.avatar:
        return

    if original_mentor.avatar != instance.avatar:
        instance.avatar_approved = False

        img = MIMEImage(instance.avatar.read())
        img.add_header("Content-Id", "avatar")
        img.add_header("Content-Disposition", "inline", filename="avatar")

        email(
            subject=f"{instance.full_name} | Mentor Avatar Changed",
            template_name="avatar_changed_mentor",
            merge_global_data={
                "first_name": instance.first_name,
                "last_name": instance.last_name,
                "image": "avatar",
                "approve_url": (
                    f"{settings.SITE_URL}{instance.get_approve_avatar_url()}"
                ),
                "reject_url": (
                    f"{settings.SITE_URL}{instance.get_reject_avatar_url()}"
                ),
            },
            recipients=[settings.CONTACT_EMAIL],
            preheader="Mentor Avatar Changed",
            attachments=[img],
            mixed_subtype="related",
        )
