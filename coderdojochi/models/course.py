from datetime import timedelta

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

import salesforce

from .common import CommonInfo


class Course(salesforce.models.SalesforceModel):
    # class Course(CommonInfo):

    WEEKEND = "WE"
    CAMP = "CA"
    SPECIAL = "SP"

    COURSE_TYPE_CHOICES = [
        (WEEKEND, "Weekend"),
        (CAMP, "Camp"),
        (SPECIAL, "Special"),
    ]

    """

    id = salesforce.models.CharField(max_length=18, primary_key=True, db_column="Id", editable=False, serialize=False, auto_created=True)
    name = salesforce.models.CharField(default="", db_column="Name", max_length=200)
    institution_type = salesforce.models.CharField(default="", db_column="Institution_Type__c", max_length=30)
    school_id = salesforce.models.CharField(default="", unique=True, db_column='School_ID__c', max_length=6)
    city = salesforce.models.CharField(default="", db_column='City__c', max_length=100)
    state = salesforce.models.CharField(default="", db_column='State__c', max_length=2)
    website_id = salesforce.models.IntegerField(default=0, unique=True, db_column='Website_ID__c')

    """

    id = salesforce.models.CharField(
        max_length=18,
        primary_key=True,
        db_column="Id",
        editable=False,
        serialize=False,
        auto_created=True,
    )

    title = salesforce.models.CharField(
        default="",
        db_column="Name",
        max_length=200,
    )

    # title = models.CharField(
    #     max_length=255,
    # )

    code = salesforce.models.CharField(
        default="",
        db_column="hed__Course_ID__c",
        max_length=100,
    )

    # code = models.CharField(
    #     max_length=255,
    #     blank=True,
    #     null=True,
    # )

    course_type = models.CharField(
        "type",
        max_length=2,
        choices=COURSE_TYPE_CHOICES,
        default=WEEKEND,
    )

    # slug = models.SlugField(
    #     max_length=40,
    #     blank=True,
    #     null=True,
    # )

    description = salesforce.models.TextField(
        db_column="hed__Extended_Description__c",
        blank=True,
        null=True,
    )

    # description = models.TextField(
    #     blank=True,
    #     null=True,
    #     help_text="Basic HTML allowed",
    # )

    # TODO: update db_column
    duration = salesforce.models.DurationField(
        default=timedelta(hours=3),
        help_text="HH:MM:ss",
    )
    
    # TODO: update db_column
    minimum_age = salesforce.models.IntegerField(
        default=7,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    # TODO: update db_column
    maximum_age = salesforce.models.IntegerField(
        default=18,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    # TODO: update db_column
    is_active = salesforce.models.BooleanField(
        default=True,
    )

    # Auto create/update
    # TODO: update db_column
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    # TODO: update db_column
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        if self.code:
            return f"{self.code} | {self.title}"

        return f"{self.title}"
