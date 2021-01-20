from django.db import models

from .common import CommonInfo


class Location(CommonInfo):

    name = models.CharField(
        max_length=255,
    )

    address = models.CharField(
        blank=True,
        null=True,
        max_length=255,
    )

    city = models.CharField(
        blank=True,
        null=True,
        max_length=255,
    )

    state = models.CharField(
        blank=True,
        null=True,
        max_length=2,
    )

    zip = models.CharField(
        blank=True,
        null=True,
        max_length=20,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.name
