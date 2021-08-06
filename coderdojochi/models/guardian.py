from django.db import models

from .common import CommonInfo, Salesforce
from .race_ethnicity import RaceEthnicity
from .user import CDCUser


class Guardian(CommonInfo):
    HISPANIC = "Hispanic"
    NOT_HISPANIC = "Not Hispanic"

    ETHNICITY = [
        (HISPANIC, "Hispanic"),
        (NOT_HISPANIC, "Not Hispanic"),
    ]

    WHITE = "White"
    BLACK = "Black"
    ASIAN = "Asian"
    AMERICAN_INDIAN = "American Indian"
    NATIVE_HAWAIIN = "Native Hawaiin"
    MIDDLE_EASTERN = "Middle Eastern"

    RACES = [
        (WHITE, "White"),
        (BLACK, "Black"),
        (ASIAN, "Asian"),
        (AMERICAN_INDIAN, "American Indian"),
        (NATIVE_HAWAIIN, "Native Hawaiin"),
        (MIDDLE_EASTERN, "Middle Eastern"),
    ]

    user = models.ForeignKey(
        CDCUser,
        on_delete=models.CASCADE,
    )
    is_active = models.BooleanField(
        default=True,
    )
    phone = models.CharField(
        max_length=50,
        blank=True,
    )
    zip = models.CharField(
        max_length=20,
        blank=True,
        null=True,
    )
    birthday = models.DateField(
        blank=False,
        null=True,
    )
    gender = models.CharField(
        max_length=255,
        blank=False,
        null=True,
    )
    ethnicity = models.CharField(
        choices=ETHNICITY,
        max_length=12,
        default="",
    )
    race = models.CharField(
        choices=RACES,
        max_length=15,
        default="",
    )

    def __str__(self):
        return self.full_name

    @property
    def first_name(self):
        return self.user.first_name

    @property
    def last_name(self):
        return self.user.last_name

    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"

    @property
    def email(self):
        return self.user.email

    def get_students(self):
        from .student import Student

        return Student.objects.filter(
            guardian=self,
            is_active=True,
        )

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

        sf = Salesforce()

        if self.birthday and self.zip:
            sf.upsert_contact(
                first_name=self.first_name,
                last_name=self.last_name,
                birthdate=self.birthday,
                gender=self.gender,
                email=self.email,
                race=self.race,
                ethnicity=self.ethnicity,
                role="guardian",
                active=self.is_active,
                zip_code=self.zip.replace('-',''),
                phone=self.phone,
                ext_id=self.id,
            )
