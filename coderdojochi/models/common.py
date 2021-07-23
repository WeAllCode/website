from django.conf import settings
from django.db import models

from simple_salesforce import Salesforce

from coderdojochi.settings import SALESFORCE_TOKEN


class CommonInfo(models.Model):
    # Auto create/update
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        abstract = True


def salesforce_login():
    return Salesforce(
        username=settings.SALESFORCE_USER,
        password=settings.SALESFORCE_PASSWORD,
        security_token=settings.SALESFORCE_TOKEN,
        domain="cs201",
    )
