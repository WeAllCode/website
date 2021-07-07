# from django.db import models
from django.utils import timezone

import salesforce

from .common import CommonInfo
from .race_ethnicity import RaceEthnicity


class Student(salesforce.models.SalesforceModel):
    from .guardian import Guardian

    guardian = salesforce.models.ForeignKey(
        Guardian,
        on_delete=salesforce.models.PROTECT,
    )
    first_name = salesforce.models.CharField(
        db_column = "FirstName",
        max_length=255,
    )
    last_name = salesforce.models.CharField(
        db_column="LastName",
        max_length=255,
    )
    birthday = salesforce.models.DateField(
        db_column = "Birthdate"
    )
    gender = salesforce.models.CharField(
        db_column="Gender__c",
        max_length=255,
    )
    # race_ethnicity = salesforce.models.ManyToManyField(
    #     RaceEthnicity,
    #     # db_column = "hed__Race__c",
    #     blank=True,
    # )
    # race_ethnicity = models.ManyToManyField(
    #     RaceEthnicity,
    #     blank=True,
    # )
    school_name = salesforce.models.CharField(
        max_length=255,
        null=True,
    )
    school_type = salesforce.models.CharField(
        max_length=255,
        null=True,
    )
    medical_conditions = salesforce.models.TextField(
        db_column="Medical__c",
        blank=True,
        null=True,
    )
    medications = salesforce.models.TextField(
        db_column='Medications__c',
        blank=True,
        null=True,
    )
    photo_release = salesforce.models.BooleanField(
        "Photo Consent",
        help_text=(
            "I hereby give permission to We All Code to use "
            "the student's image and/or likeness in promotional materials."
        ),
        db_column="Photo_Release__c",
    )
    consent = salesforce.models.BooleanField(
        "General Consent",
        help_text=("I hereby give consent for the student signed up " "above to participate in We All Code."),
        db_column="Consent__c",
    )
    is_active = salesforce.models.BooleanField(
        db_column="Active__c",
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        db_table = "Contact"
        
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def is_registered_for_session(self, session):
        from .order import Order

        try:
            Order.objects.get(
                is_active=True,
                student=self,
                session=session,
            )
            is_registered = True
        except Exception:
            is_registered = False

        return is_registered

    def get_age(self, date=timezone.now()):
        return date.year - self.birthday.year - ((date.month, date.day) < (self.birthday.month, self.birthday.day))

    get_age.short_description = "Age"

    def get_clean_gender(self):
        MALE = ["male", "m", "boy", "nino", "masculino"]
        FEMALE = ["female", "f", "girl", "femail", "femal", "femenino"]

        if self.gender.lower() in MALE:
            return "male"
        elif self.gender.lower() in FEMALE:
            return "female"
        else:
            return "other"

    get_clean_gender.short_description = "Clean Gender"

    # returns True if the student age is between minimum_age and maximum_age
    def is_within_age_range(self, minimum_age, maximum_age, date=timezone.now()):
        age = self.get_age(date)

        if age >= minimum_age and age <= maximum_age:
            return True
        else:
            return False

    def is_within_gender_limitation(self, limitation):
        if limitation:
            if self.get_clean_gender() in [limitation.lower(), "other"]:
                return True
            else:
                return False
        else:
            return True
