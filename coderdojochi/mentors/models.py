import os
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext as _

from stdimage.models import StdImageField

from coderdojochi.models import (
    CDCUser
)


def generate_filename(instance, filename):
    # file will be uploaded to MEDIA_ROOT/avatar/<username>
    filename, file_extension = os.path.splitext(filename)
    return u'avatar/{}{}'.format(
        instance.user.username,
        file_extension.lower()
    )


class Mentor(models.Model):
    user = models.ForeignKey(
        CDCUser
    )
    bio = models.TextField(
        blank=True,
        null=True,
    )
    is_active = models.BooleanField(
        default=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )
    background_check = models.BooleanField(
        default=False,
    )
    is_public = models.BooleanField(
        default=False,
    )
    avatar = StdImageField(
        upload_to=generate_filename,
        blank=True,
        variations={
            'thumbnail': {
                'width': 500,
                'height': 500,
                'crop': True,
            }
        },
    )
    avatar_approved = models.BooleanField(
        default=False,
    )

    class Meta:
        verbose_name = _("mentors")
        verbose_name_plural = _("mentors")

    def __unicode__(self):
        return u'{} {}'.format(self.user.first_name, self.user.last_name)

    def get_approve_avatar_url(self):
        return u'{}/mentor/{}/approve-avatar/'.format(
            settings.SITE_URL,
            self.id
        )

    def get_reject_avatar_url(self):
        return u'{}/mentor/{}/reject-avatar/'.format(
            settings.SITE_URL,
            self.id
        )

    def get_absolute_url(self):
        return u'{}/mentor/{}/'.format(
            settings.SITE_URL,
            self.id
        )

    def save(self, *args, **kwargs):
        if self.pk is not None:
            orig = Mentor.objects.get(pk=self.pk)
            if orig.avatar != self.avatar:
                self.avatar_approved = False

        super(Mentor, self).save(*args, **kwargs)


