from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property


class CDCUser(AbstractUser):

    MENTOR = "mentor"
    GUARDIAN = "guardian"

    ROLE_CHOICES = [
        (MENTOR, "mentor"),
        (GUARDIAN, "guardian"),
    ]

    role = models.CharField(choices=ROLE_CHOICES, max_length=10, blank=True, null=True,)

    admin_notes = models.TextField(blank=True, null=True,)

    @cached_property
    def name(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.last_login = timezone.now()
        super(CDCUser, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("account_home")
