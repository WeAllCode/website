from django.db import models
from django.utils import timezone

from .common import CommonInfo
from .race_ethnicity import RaceEthnicity


class Student(CommonInfo):
    from .guardian import Guardian

    guardian = models.ForeignKey(
        Guardian,
        on_delete=models.CASCADE,
    )
    first_name = models.CharField(
        max_length=255,
    )
    last_name = models.CharField(
        max_length=255,
    )
    birthday = models.DateField()
    gender = models.CharField(
        max_length=255,
    )
    race_ethnicity = models.ManyToManyField(
        RaceEthnicity,
        blank=True,
    )
    school_name = models.CharField(
        max_length=255,
        null=True,
    )
    school_type = models.CharField(
        max_length=255,
        null=True,
    )
    medical_conditions = models.TextField(
        blank=True,
        null=True,
    )
    medications = models.TextField(
        blank=True,
        null=True,
    )
    photo_release = models.BooleanField(
        "Photo Consent",
        help_text=(
            "I hereby give permission to We All Code to use "
            "the student's image and/or likeness in promotional materials."
        ),
        default=False,
    )
    consent = models.BooleanField(
        "General Consent",
        help_text=(
            "I hereby give consent for the student signed up "
            "above to participate in We All Code."
        ),
        default=False,
    )
    is_active = models.BooleanField(
        default=True,
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

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
        return (
            date.year
            - self.birthday.year
            - (
                (date.month, date.day)
                < (self.birthday.month, self.birthday.day)
            )
        )

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

    def get_clean_gender_short(self):
        gender = self.get_clean_gender()

        if gender == "male":
            return "m"
        elif gender == "female":
            return "f"
        else:
            return "o"

    get_clean_gender_short.short_description = "Clean Gender Short"

    # returns True if the student age is between minimum_age and maximum_age
    def is_within_age_range(
        self, minimum_age, maximum_age, date=timezone.now()
    ):
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
