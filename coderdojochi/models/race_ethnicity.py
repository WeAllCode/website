from django.db import models

from .common import CommonInfo


class RaceEthnicity(CommonInfo):
    race_ethnicity = models.CharField(max_length=255,)
    is_visible = models.BooleanField(default=False,)

    class Meta:
        verbose_name = "Race/Ethnicity"
        verbose_name_plural = "Race/Ethnicities"

    def __str__(self):
        return self.race_ethnicity
