from datetime import timedelta

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .common import CommonInfo


class Course(CommonInfo):

    WEEKEND = "WE"
    CAMP = "CA"
    SPECIAL = "SP"

    COURSE_TYPE_CHOICES = [
        (WEEKEND, "Weekend"),
        (CAMP, "Camp"),
        (SPECIAL, "Special"),
    ]

    code = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    course_type = models.CharField(
        "type",
        max_length=2,
        choices=COURSE_TYPE_CHOICES,
        default=WEEKEND,
    )
    title = models.CharField(
        max_length=255,
    )
    slug = models.SlugField(
        max_length=40,
        blank=True,
        null=True,
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Basic HTML allowed",
    )
    duration = models.DurationField(
        default=timedelta(hours=3),
        help_text="HH:MM:ss",
    )
    minimum_age = models.IntegerField(
        default=7,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    maximum_age = models.IntegerField(
        default=18,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    is_active = models.BooleanField(
        default=True,
    )

    def __str__(self):
        if self.code:
            return f"{self.code} | {self.title}"

        return f"{self.title}"
