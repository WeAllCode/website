from django.db import models

from .common import CommonInfo


class EmailContent(CommonInfo):
    nickname = models.CharField(
        max_length=255,
    )

    subject = models.CharField(
        max_length=255,
    )

    body = models.TextField(
        blank=True,
        null=True,
        help_text="Basic HTML allowed",
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        verbose_name = "email content"
        verbose_name_plural = "email content"

    def __str__(self):
        return f"{self.nickname} | {self.subject}"
