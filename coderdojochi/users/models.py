import os
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import ugettext as _


ROLE_CHOICES = (
    ('mentor', 'mentor'),
    ('guardian', 'guardian'),
)


class CDCUser(AbstractUser):
    role = models.CharField(
        choices=ROLE_CHOICES,
        max_length=10,
        blank=True,
        null=True,
    )
    admin_notes = models.TextField(
        blank=True,
        null=True,
    )

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.last_login = timezone.now()
        super(CDCUser, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return '{}/dojo'.format(
            settings.SITE_URL
        )
