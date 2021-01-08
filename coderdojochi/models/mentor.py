import os

from django.db import models
from django.urls import reverse

from stdimage.models import StdImageField

from ..notifications import NewMentorBgCheckNotification, NewMentorNotification, NewMentorOrderNotification
from .common import CommonInfo
from .race_ethnicity import RaceEthnicity
from .user import CDCUser


def generate_filename(instance, filename):
    # file will be uploaded to MEDIA_ROOT/avatar/<username>
    filename, file_extension = os.path.splitext(filename)
    return f"avatar/{instance.user.username}{file_extension.lower()}"


# TODO: Add MentorManager
class Mentor(CommonInfo):
    user = models.ForeignKey(CDCUser, on_delete=models.CASCADE,)
    bio = models.TextField(blank=True, null=True,)
    is_active = models.BooleanField(default=True,)
    background_check = models.BooleanField(default=False,)
    is_public = models.BooleanField(default=False,)
    avatar = StdImageField(
        upload_to=generate_filename, blank=True, variations={"thumbnail": {"width": 500, "height": 500, "crop": True,}},
    )
    avatar_approved = models.BooleanField(default=False,)
    birthday = models.DateTimeField(blank=False, null=True,)
    gender = models.CharField(max_length=255, blank=False, null=True,)
    race_ethnicity = models.ManyToManyField(RaceEthnicity, blank=False,)
    work_place = models.CharField(max_length=255, blank=True, null=True,)
    phone = models.CharField(max_length=255, blank=True, null=True,)
    home_address = models.CharField(max_length=255, blank=True, null=True,)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"

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
        return reverse("mentor-approve-avatar", args=[str(self.id)])

    def get_reject_avatar_url(self):
        return reverse("mentor-reject-avatar", args=[str(self.id)])

    def get_absolute_url(self):
        return reverse("mentor-detail", args=[str(self.id)])

    @property
    def first_name(self):
        return self.user.first_name

    @property
    def last_name(self):
        return self.user.last_name


