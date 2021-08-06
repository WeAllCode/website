from os import stat
from django.db import models

from .common import CommonInfo, Salesforce


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

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        sf = Salesforce()

        sf.add_location(
            name=self.name,
            address=self.address,
            city=self.city,
            state=self.state,
            zip=self.zip,
            is_active=self.is_active,
            ext_id=self.id,
        )
