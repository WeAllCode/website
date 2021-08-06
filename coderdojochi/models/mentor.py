import os

from django.db import models
from django.urls import reverse

from stdimage.models import StdImageField

from ..notifications import NewMentorBgCheckNotification, NewMentorNotification, NewMentorOrderNotification
from .common import CommonInfo, Salesforce
from .race_ethnicity import RaceEthnicity
from .user import CDCUser


def generate_filename(instance, filename):
    # file will be uploaded to MEDIA_ROOT/avatar/<username>
    filename, file_extension = os.path.splitext(filename)
    return f"avatar/{instance.user.username}{file_extension.lower()}"


# TODO: Add MentorManager
class Mentor(CommonInfo):
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
    bio = models.TextField(
        blank=True,
        null=True,
    )
    is_active = models.BooleanField(
        default=True,
    )
    # Add background check field
    background_check = models.BooleanField(
        default=False,
    )
    # Add ispublic field
    is_public = models.BooleanField(
        default=False,
    )
    avatar = StdImageField(
        upload_to=generate_filename,
        blank=True,
        variations={
            "thumbnail": {
                "width": 500,
                "height": 500,
                "crop": True,
            },
        },
    )
    avatar_approved = models.BooleanField(
        default=False,
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
    work_place = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    phone = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    home_address = models.CharField(
        max_length=255,
        blank=True,
        null=True,
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

    def save(self, *args, **kwargs):
        if self.pk is None:
            NewMentorNotification(self).send()
        else:
            orig = Mentor.objects.get(pk=self.pk)
            if orig.avatar != self.avatar:
                self.avatar_approved = False

            if self.background_check is True and orig.background_check != self.background_check:
                NewMentorBgCheckNotification(self).send()

        super(Mentor, self).save(*args, **kwargs)

    def get_approve_avatar_url(self):
        return reverse(
            "mentor-approve-avatar",
            args=[
                str(self.id),
            ],
        )

    def get_reject_avatar_url(self):
        return reverse(
            "mentor-reject-avatar",
            args=[
                str(self.id),
            ],
        )

    def get_absolute_url(self):
        return reverse(
            "mentor-detail",
            args=[
                str(self.id),
            ],
        )

    def get_avatar(self):
        if (
            self.avatar
            and self.avatar.storage.exists(self.avatar.name)
            and self.avatar.storage.exists(self.avatar.thumbnail.name)
        ):
            return self.avatar

        # Gravatar
        import hashlib
        from urllib.parse import urlencode

        # https://en.gravatar.com/site/implement/images/

        email = self.email.encode("utf-8").lower()
        email_encoded = hashlib.md5(email).hexdigest()

        thumbnail_params = urlencode(
            {
                "d": "mp",
                "r": "g",
                "s": str(320),
            }
        )
        full_params = urlencode(
            {
                "d": "mp",
                "r": "g",
                "s": str(500),
            }
        )
        slug_url = f"https://www.gravatar.com/avatar/{email_encoded}"

        avatar = {
            "url": f"{slug_url}?{full_params}",
            "thumbnail": {
                "url": f"{slug_url}?{thumbnail_params}",
            },
        }

        return avatar

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

        sf = Salesforce()

        if self.birthday:
            sf.upsert_contact(
                first_name=self.first_name,
                last_name=self.last_name,
                birthdate=self.birthday,
                gender=self.gender,
                email=self.email,
                race=self.race,
                ethnicity=self.ethnicity,
                role="mentor",
                active=self.is_active,
                work_place=self.work_place,
                ext_id=self.id,
            )
