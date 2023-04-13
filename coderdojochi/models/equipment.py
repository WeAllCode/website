from django.db import models

from .common import CommonInfo


class EquipmentType(CommonInfo):
    name = models.CharField(
        max_length=255,
        blank=False,
        null=False,
    )

    def __str__(self):
        return self.name


class Equipment(CommonInfo):
    WORKING = "working"
    ISSUE = "issue"
    UNUSABLE = "unusable"
    EQUIPMENT_CONDITIONS = [
        (WORKING, "Working"),
        (ISSUE, "Issue"),
        (UNUSABLE, "Unusable"),
    ]

    uuid = models.CharField(
        max_length=255,
        verbose_name="UUID",
        default="000-000-000-000",
        null=False,
    )

    equipment_type = models.ForeignKey(
        EquipmentType,
        on_delete=models.CASCADE,
    )

    make = models.CharField(
        max_length=255,
    )

    model = models.CharField(
        max_length=255,
    )

    asset_tag = models.CharField(
        max_length=255,
    )

    acquisition_date = models.DateTimeField(
        blank=True,
        null=True,
    )

    condition = models.CharField(
        max_length=255,
        choices=EQUIPMENT_CONDITIONS,
    )

    notes = models.TextField(
        blank=True,
        null=True,
    )

    last_system_update_check_in = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Last Check In",
    )

    last_system_update = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Last Update",
    )

    force_update_on_next_boot = models.BooleanField(
        default=False,
        verbose_name="Force Update",
    )

    class Meta:
        verbose_name = "equipment"
        verbose_name_plural = "equipment"

    def __str__(self):
        return (
            f"{self.equipment_type.name} | {self.make} {self.model} |"
            f" {self.acquisition_date}"
        )
