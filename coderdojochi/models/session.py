from datetime import timedelta

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls.base import reverse
from django.utils import formats
from django.utils.functional import cached_property

from .common import CommonInfo


class Session(CommonInfo):
    from .course import Course
    from .location import Location
    from .mentor import Mentor
    from .student import Student

    MALE = "male"
    FEMALE = "female"

    GENDER_LIMITATION_CHOICES = (
        (MALE, "Male"),
        (FEMALE, "Female"),
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        limit_choices_to={"is_active": True},
    )
    start_date = models.DateTimeField()
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        limit_choices_to={"is_active": True},
    )
    capacity = models.IntegerField(
        default=20,
    )
    mentor_capacity = models.IntegerField(
        default=10,
    )
    instructor = models.ForeignKey(
        Mentor,
        on_delete=models.CASCADE,
        related_name="session_instructor",
        limit_choices_to={
            "user__groups__name": "Instructor",
            "is_active": True,
            "user__is_active": True,
            "background_check": True,
            "avatar_approved": True,
        },
        help_text=(
            "A mentor with 'Instructor' role, is active (user and mentor), background check passed, and avatar"
            " approved."
        ),
    )

    assistant = models.ManyToManyField(
        Mentor,
        blank=True,
        related_name="session_assistant",
        limit_choices_to={
            "user__groups__name": "Assistant",
            "is_active": True,
            "user__is_active": True,
            "background_check": True,
            "avatar_approved": True,
        },
        help_text=(
            "A mentor with 'Assistant' role, is active (user and mentor), background check passed, and avatar approved."
        ),
    )

    # Pricing
    cost = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
    )
    minimum_cost = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
    )
    maximum_cost = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
    )

    # Extra
    additional_info = models.TextField(blank=True, null=True, help_text="Basic HTML allowed")
    waitlist_mentors = models.ManyToManyField(
        Mentor,
        blank=True,
        related_name="session_waitlist_mentors",
    )
    waitlist_students = models.ManyToManyField(
        Student,
        blank=True,
        related_name="session_waitlist_students",
    )
    external_enrollment_url = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="When provided, local enrollment is disabled.",
    )

    is_active = models.BooleanField(
        default=False,
        help_text="Session is active.",
    )
    is_public = models.BooleanField(
        default=False,
        help_text="Session is a public session.",
    )
    password = models.CharField(
        blank=True,
        max_length=255,
    )
    partner_message = models.TextField(
        blank=True,
    )
    announced_date_mentors = models.DateTimeField(
        blank=True,
        null=True,
    )
    announced_date_guardians = models.DateTimeField(
        blank=True,
        null=True,
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
    mentors_week_reminder_sent = models.BooleanField(
        default=False,
    )
    mentors_day_reminder_sent = models.BooleanField(
        default=False,
    )
    gender_limitation = models.CharField(
        help_text="Limits the class to be only one gender.",
        max_length=255,
        choices=GENDER_LIMITATION_CHOICES,
        blank=True,
        null=True,
    )
    override_minimum_age_limitation = models.IntegerField(
        "Min Age",
        help_text="Only update this if different from the default.",
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    override_maximum_age_limitation = models.IntegerField(
        "Max Age",
        help_text="Only update this if different from the default.",
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    online_video_link = models.URLField(
        "Online Video Link",
        help_text="Zoom link with password.",
        blank=True,
        null=True,
    )
    online_video_meeting_id = models.CharField(
        "Online Video Meeting ID",
        help_text="XXX XXXX XXXX",
        max_length=255,
        blank=True,
        null=True,
    )
    online_video_meeting_password = models.CharField(
        "Online Video Meeting Password",
        help_text="Plain text password shared by Zoom",
        max_length=255,
        blank=True,
        null=True,
    )
    online_video_description = models.TextField(
        "Online Video Description",
        help_text="Information on how to connect to the video call. Basic HTML allowed.",
        blank=True,
        null=True,
    )

    # kept for older records
    old_end_date = models.DateTimeField(
        blank=True,
        null=True,
    )
    old_mentor_start_date = models.DateTimeField(
        blank=True,
        null=True,
    )
    old_mentor_end_date = models.DateTimeField(
        blank=True,
        null=True,
    )

    @property
    def end_date(self):
        # Some records have a defined record with the end date,
        # rather than use the course's duration.
        # We're keeping this for old records.
        if self.old_end_date:
            return self.old_end_date

        return self.start_date + self.course.duration

    @property
    def mentor_start_date(self):
        # Some records have a defined record with the mentor start date,
        # rather than do the math.
        # We're keeping this for old records.
        if self.old_mentor_start_date:
            return self.old_mentor_start_date

        return self.start_date - timedelta(hours=1)

    @property
    def mentor_end_date(self):
        # Some records have a defined record with the mentor start date,
        # rather than do the math.
        # We're keeping this for old records.
        if self.old_mentor_end_date:
            return self.old_mentor_end_date

        return self.end_date + timedelta(hours=1)

    @property
    def minimum_age(self):
        if self.override_minimum_age_limitation is not None:
            return self.override_minimum_age_limitation

        return self.course.minimum_age

    @property
    def maximum_age(self):
        if self.override_maximum_age_limitation is not None:
            return self.override_maximum_age_limitation

        return self.course.maximum_age

    def __str__(self):
        date = formats.date_format(self.start_date, "SHORT_DATETIME_FORMAT")
        return f"{self.course.title} | {date}"

    def save(self, *args, **kwargs):
        # Mentor Capacity Check
        if self.mentor_capacity is None:
            self.mentor_capacity = int(self.capacity / 2)

        if self.mentor_capacity < 0:
            self.mentor_capacity = 0

        # Capacity check
        if self.capacity < 0:
            self.capacity = 0

        super(Session, self).save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("session-detail", args=[str(self.id)])

    def get_sign_up_url(self):
        return reverse("session-sign-up", args=[str(self.id)])

    def get_calendar_url(self):
        return reverse("session-calendar", args=[str(self.id)])

    def is_guardian_announced(self):
        return self.announced_date_guardians is not None

    is_guardian_announced.boolean = True
    is_guardian_announced.short_description = "Is Announced"
    is_guardian_announced.admin_order_field = "announced_date_guardians"

    def get_mentor_orders(self):
        from .mentor_order import MentorOrder

        return MentorOrder.objects.filter(
            session=self,
            is_active=True,
        ).order_by("mentor__user__last_name")

    def get_checked_in_mentor_orders(self):
        from .mentor_order import MentorOrder

        return MentorOrder.objects.filter(session=self, is_active=True, check_in__isnull=False).order_by(
            "mentor__user__last_name"
        )

    def get_current_orders(self, checked_in=None):
        from .order import Order

        if checked_in is not None:
            if checked_in:
                orders = (
                    Order.objects.filter(is_active=True, session=self)
                    .exclude(check_in=None)
                    .order_by("student__last_name")
                )
            else:
                orders = Order.objects.filter(is_active=True, session=self, check_in=None).order_by(
                    "student__last_name"
                )
        else:
            orders = Order.objects.filter(is_active=True, session=self).order_by("check_in", "student__last_name")

        return orders

    def get_active_student_count(self):
        from .order import Order

        return Order.objects.filter(is_active=True, session=self).values("student").count()

    def get_checked_in_students(self):
        from .order import Order

        return Order.objects.filter(is_active=True, session=self).exclude(check_in=None).values("student")


class PartnerPasswordAccess(CommonInfo):
    from .user import CDCUser

    user = models.ForeignKey(
        CDCUser,
        on_delete=models.CASCADE,
    )
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
    )

    class Meta:
        db_table = "partner_password_access"
