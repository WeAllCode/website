from datetime import timedelta

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from simple_salesforce import format_soql

from .common import CommonInfo, salesforce_login


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

    def save(self, *args, **kwargs):
        print("===============================================fsfs=f=====================")
        sf = salesforce_login()
        query = "SELECT Id FROM hed__Course__c WHERE Name = {} and hed__Course_ID__c = {}"
        formatted = format_soql(query, self.title, self.code)
        results = sf.query(formatted)
        num_courses = results["totalSize"]

        if not num_courses:
            sf.hed__Course__c.create(
                {
                    "Name": self.title,
                    "Active__c": self.is_active,
                    "hed__Course_ID__c": self.code,
                    "Course_Type__c": self.course_type,
                    "hed__Description__c": self.description,
                    "hed__Account__c": "0017h00000ZfotKAAR",
                    "Duration__c": self.duration.__str__(),
                    "Minimum_Age__c": self.minimum_age,
                    "Maximum_Age__c": self.maximum_age,
                }
            )
        else:
            id = results["records"][0]["Id"]
            sf.hed__Course__c.update(
                id,
                {
                    "Name": self.title,
                    "Active__c": self.is_active,
                    "hed__Course_ID__c": self.code,
                    "Course_Type__c": self.course_type,
                    "hed__Description__c": self.description,
                    "Duration__c": self.duration.__str__(),
                    "Minimum_Age__c": self.minimum_age,
                    "Maximum_Age__c": self.maximum_age,
                },
            )
        super().save(*args, **kwargs)
