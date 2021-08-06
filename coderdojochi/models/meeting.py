from django.db import models
from django.urls import reverse
from django.utils import formats

from .common import CommonInfo, Salesforce
from .location import Location
from .mentor import Mentor


class MeetingType(CommonInfo):
    code = models.CharField(
        max_length=255,
        blank=True,
        null=True,
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

    def __str__(self):
        if self.code:
            return f"{self.code} | {self.title}"

        return f"{self.title}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        sf = Salesforce()

        sf.add_meeting_type(
            code=self.code,
            title=self.title,
            slug=self.slug,
            description=self.description,
            ext_id=f"{self.code}{self.id}",
        )


class Meeting(CommonInfo):
    meeting_type = models.ForeignKey(
        MeetingType,
        on_delete=models.CASCADE,
    )
    additional_info = models.TextField(
        blank=True,
        null=True,
        help_text="Basic HTML allowed",
    )
    start_date = models.DateTimeField(
        blank=True,
        null=True,
    )
    end_date = models.DateTimeField(
        blank=True,
        null=True,
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
    )
    external_enrollment_url = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="When provided, local enrollment is disabled.",
    )
    is_public = models.BooleanField(
        default=False,
    )
    is_active = models.BooleanField(
        default=False,
    )
    image_url = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    bg_image = models.ImageField(
        blank=True,
        null=True,
    )
    announced_date = models.DateTimeField(
        blank=True,
        null=True,
    )

    def __str__(self):
        if self.start_date:
            date = formats.date_format(self.start_date, "SHORT_DATETIME_FORMAT")
            return f"{self.meeting_type.title} | {date}"
        return ""

    def get_absolute_url(self):
        return reverse("meeting-detail", args=[str(self.id)])

    def get_sign_up_url(self):
        return reverse("meeting-register", args=[str(self.id)])

    def get_calendar_url(self):
        return reverse("meeting-calendar", args=[str(self.id)])

    def get_current_orders(self, checked_in=None):
        if checked_in is not None:
            if checked_in:
                orders = (
                    MeetingOrder.objects.filter(
                        is_active=True,
                        meeting=self,
                    )
                    .exclude(
                        check_in=None,
                    )
                    .order_by("mentor__user__last_name")
                )
            else:
                orders = MeetingOrder.objects.filter(
                    is_active=True,
                    meeting=self,
                    check_in=None,
                ).order_by("mentor__user__last_name")

        else:
            orders = MeetingOrder.objects.filter(is_active=True, meeting=self,).order_by(
                "check_in",
                "mentor__user__last_name",
            )

        return orders

    def get_current_mentors(self):
        return Mentor.objects.filter(
            id__in=MeetingOrder.objects.filter(is_active=True, meeting=self,).values(
                "mentor__id",
            )
        )

    def get_mentor_count(self):
        return MeetingOrder.objects.filter(meeting__id=self.id).count()

    get_mentor_count.short_description = "Mentors"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        sf = Salesforce()

        sf.add_meeting(
            meeting_type=self.meeting_type,
            additional_info=self.additional_info,
            start_date=self.start_date,
            end_date=self.end_date,
            location=self.location,
            external_enrollment_url=self.external_enrollment_url,
            is_public=self.is_public,
            is_active=self.is_active,
            ext_id=self.id,
            announced_date=self.announced_date,
        )


class MeetingOrder(CommonInfo):
    mentor = models.ForeignKey(
        Mentor,
        on_delete=models.CASCADE,
    )
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
    )
    is_active = models.BooleanField(
        default=True,
    )
    ip = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    check_in = models.DateTimeField(
        blank=True,
        null=True,
    )
    affiliate = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    order_number = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    week_reminder_sent = models.BooleanField(
        default=False,
    )
    day_reminder_sent = models.BooleanField(
        default=False,
    )

    def __str__(self):
        return f"{self.mentor.full_name} | {self.meeting.meeting_type.title}"

    def is_checked_in(self):
        return self.check_in is not None

    is_checked_in.boolean = True
