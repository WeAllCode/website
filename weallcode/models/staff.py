from django.db import models

from .common import CommonInfo


class StaffMemberManager(models.Manager):
    def get_sorted(self):
        """
        Reordering by role.
        """
        return (
            self.get_queryset()
            .filter(
                is_active=True,
                departure_date__isnull=True,
            )
            .order_by("join_date", "name")
        )


class StaffMember(CommonInfo):
    role = models.CharField(
        max_length=255,
    )

    image = models.ImageField(
        upload_to="staff/",
        blank=True,
        null=True,
    )

    objects = StaffMemberManager()

    def __str__(self):
        return self.name
