from docutils.nodes import description

from django.db import models
from django.utils.translation import gettext_lazy as _

CHAIR = 'Chair'
VICE_CHAIR = 'Vice Chair'
SECRETARY = 'Secretary'
TREASURER = 'Treasurer'
DIRECTOR = 'Director'

ROLE_CHOICES = [
    (CHAIR, 'Chair'),
    (VICE_CHAIR, 'Vice Chair'),
    (SECRETARY, 'Secretary'),
    (TREASURER, 'Treasurer'),
    (DIRECTOR, 'Director'),
]


class BoardMember(models.Model):

    name = models.CharField(
        max_length=255,
    )

    role = models.CharField(
        choices=ROLE_CHOICES,
        max_length=255,
        default=DIRECTOR,
    )

    description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    linkedin = models.URLField(
        max_length=200,
        blank=True,
        null=True,
    )

    image = models.ImageField(
        upload_to='board/',
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _("Board Member")
        verbose_name_plural = _("Board Members")

    def __str__(self):
        return self.name


class AssociateBoardMember(models.Model):

    name = models.CharField(
        max_length=255,
    )

    role = models.CharField(
        choices=ROLE_CHOICES,
        max_length=255,
        default=DIRECTOR,
    )

    description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    linkedin = models.URLField(
        max_length=200,
        blank=True,
        null=True,
    )

    image = models.ImageField(
        upload_to='associate-board/',
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _("Associate Board Member")
        verbose_name_plural = _("Associate Board Members")

    def __str__(self):
        return self.name
