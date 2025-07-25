from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse

from .common import CommonInfo


class Donation(CommonInfo):
    from .session import Session
    from .user import CDCUser

    user = models.ForeignKey(
        CDCUser,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    session = models.ForeignKey(
        Session,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    first_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    last_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    referral_code = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    email = models.EmailField(
        blank=True,
        null=True,
    )
    amount = models.IntegerField()
    is_verified = models.BooleanField(
        default=False,
    )
    receipt_sent = models.BooleanField(
        default=False,
    )

    def __str__(self):
        return f"{self.email} | ${self.amount}"

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return reverse(
            f"admin:{content_type.app_label}_{content_type.model}_change",
            args=(self.id,),
        )

    def get_first_name(self):
        if self.user:
            return self.user.first_name
        return self.first_name

    get_first_name.short_description = "First Name"

    def get_last_name(self):
        if self.user:
            return self.user.last_name
        return self.last_name

    get_last_name.short_description = "Last Name"

    def get_email(self):
        if self.user:
            return self.user.email
        return self.email

    get_email.short_description = "Email"
