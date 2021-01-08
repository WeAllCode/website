from django.db import models

from .common import CommonInfo
from .race_ethnicity import RaceEthnicity
from .user import CDCUser


class Guardian(CommonInfo):
    user = models.ForeignKey(CDCUser, on_delete=models.CASCADE,)
    is_active = models.BooleanField(default=True,)
    phone = models.CharField(max_length=50, blank=True,)
    zip = models.CharField(max_length=20, blank=True, null=True,)
    birthday = models.DateTimeField(blank=False, null=True,)
    gender = models.CharField(max_length=255, blank=False, null=True,)
    race_ethnicity = models.ManyToManyField(RaceEthnicity, blank=False,)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

    @property
    def first_name(self):
        return self.user.first_name

    @property
    def last_name(self):
        return self.user.last_name

    @property
    def email(self):
        return self.user.email

    def get_students(self):
        from .student import Student

        return Student.objects.filter(guardian=self, is_active=True,)

