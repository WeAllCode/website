from collections import defaultdict
from datetime import date
from itertools import chain

from django.db import models
from django.db.models import Case, When

CHAIR = "Chair"
VICE_CHAIR = "Vice Chair"
SECRETARY = "Secretary"
TREASURER = "Treasurer"
DIRECTOR = "Director"
PRESIDENT = "President"

ROLE_CHOICES = [
    (CHAIR, "Chair"),
    (VICE_CHAIR, "Vice Chair"),
    (SECRETARY, "Secretary"),
    (TREASURER, "Treasurer"),
    (DIRECTOR, "Director"),
    (PRESIDENT, "President"),
]


class CommonInfo(models.Model):
    name = models.CharField(
        max_length=255,
    )
    role = models.CharField(
        choices=ROLE_CHOICES,
        max_length=255,
        default=DIRECTOR,
    )
    image = models.ImageField(
        upload_to="staff/",
        blank=True,
        null=True,
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    linkedin = models.URLField(
        max_length=200,
        blank=True,
        null=True,
    )
    join_date = models.DateField("Join Date", default=date.today)
    departure_date = models.DateField("Departure Date", null=True, blank=True)
    is_active = models.BooleanField(
        default=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        abstract = True


class CommonBoardMemberManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

    def get_sorted(self):
        """
        Reordering by role.
        """

        roles = [CHAIR, VICE_CHAIR, TREASURER, SECRETARY, DIRECTOR]
        order = Case(*[When(role=role, then=pos) for pos, role in enumerate(roles)])
        return (
            self.get_queryset()
            .filter(is_active=True, departure_date__isnull=True, role__in=roles)
            .order_by(order, "join_date", "name")
        )
