import os

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils import formats, timezone
from django.utils.translation import ugettext as _

from stdimage.models import StdImageField

ROLE_CHOICES = (
    ('mentor', 'mentor'),
    ('guardian', 'guardian'),
)


class CDCUser(AbstractUser):
    role = models.CharField(
        choices=ROLE_CHOICES,
        max_length=10,
        blank=True,
        null=True,
    )
    admin_notes = models.TextField(
        blank=True,
        null=True,
    )

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.last_login = timezone.now()
        super(CDCUser, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('account_home')


def generate_filename(instance, filename):
    # file will be uploaded to MEDIA_ROOT/avatar/<username>
    filename, file_extension = os.path.splitext(filename)
    return f"avatar/{instance.user.username}{file_extension.lower()}"


class RaceEthnicity(models.Model):
    race_ethnicity = models.CharField(
        max_length=255,
    )
    is_visible = models.BooleanField(
        default=False,
    )

    class Meta:
        verbose_name = _("race ethnicity")
        verbose_name_plural = _("race ethnicities")

    def __str__(self):
        return self.race_ethnicity


class Mentor(models.Model):
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
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )
    background_check = models.BooleanField(
        default=False,
    )
    is_public = models.BooleanField(
        default=False,
    )
    avatar = StdImageField(
        upload_to=generate_filename,
        blank=True,
        variations={
            'thumbnail': {
                'width': 500,
                'height': 500,
                'crop': True,
            }
        },
    )
    avatar_approved = models.BooleanField(
        default=False,
    )
    birthday = models.DateTimeField(
        blank=False,
        null=True,
    )
    gender = models.CharField(
        max_length=255,
        blank=False,
        null=True,
    )
    race_ethnicity = models.ManyToManyField(
        RaceEthnicity,
        blank=False,
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

    class Meta:
        verbose_name = _("mentors")
        verbose_name_plural = _("mentors")

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

    def full_name(self):
        return __str__()

    def save(self, *args, **kwargs):
        if self.pk is not None:
            orig = Mentor.objects.get(pk=self.pk)
            if orig.avatar != self.avatar:
                self.avatar_approved = False

        super(Mentor, self).save(*args, **kwargs)

    def get_approve_avatar_url(self):
        return reverse('mentor-approve-avatar', args=[str(self.id)])

    def get_reject_avatar_url(self):
        return reverse('mentor-reject-avatar', args=[str(self.id)])

    def get_absolute_url(self):
        return reverse('mentor-detail', args=[str(self.id)])

    @property
    def first_name(self):
        return self.user.first_name

    @property
    def last_name(self):
        return self.user.last_name


class Guardian(models.Model):
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
    birthday = models.DateTimeField(
        blank=False,
        null=True,
    )
    gender = models.CharField(
        max_length=255,
        blank=False,
        null=True,
    )
    race_ethnicity = models.ManyToManyField(
        RaceEthnicity,
        blank=False,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = _("guardian")
        verbose_name_plural = _("guardians")

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
        return Student.objects.filter(
            guardian=self,
            is_active=True,
        )


class Student(models.Model):
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
    birthday = models.DateTimeField()
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
        'Photo Consent',
        help_text=(
            'I hereby give permission to We All Code to use '
            'the student\'s image and/or likeness in promotional materials.'
        ),
        default=False,
    )
    consent = models.BooleanField(
        'General Consent',
        help_text=(
            'I hereby give consent for the student signed up '
            'above to participate in We All Code.'
        ),
        default=False,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )
    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        verbose_name = _("student")
        verbose_name_plural = _("students")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def is_registered_for_session(self, session):
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
        return date.year - self.birthday.year - (
            (date.month, date.day) < (self.birthday.month, self.birthday.day)
        )
    get_age.short_description = 'Age'

    def get_clean_gender(self):
        MALE = ['male', 'm', 'boy', 'nino', 'masculino']
        FEMALE = ['female', 'f', 'girl', 'femail', 'femal', 'femenino']

        if self.gender.lower() in MALE:
            return 'male'
        elif self.gender.lower() in FEMALE:
            return 'female'
        else:
            return 'other'
    get_clean_gender.short_description = 'Clean Gender'

    # returns True if the student age is between min_age and max_age
    def is_within_age_range(self, min_age, max_age, date=timezone.now()):
        age = self.get_age(date)

        if age >= min_age and age <= max_age:
            return True
        else:
            return False

    def is_within_gender_limitation(self, limitation):
        if limitation:
            if self.get_clean_gender() in [limitation.lower(), 'other']:
                return True
            else:
                return False
        else:
            return True


class Course(models.Model):
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
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = _("course")
        verbose_name_plural = _("courses")

    def __str__(self):
        if self.code:
            return f"{self.code} | {self.title}"
        else:
            return f"{self.title}"

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Course, self).save(*args, **kwargs)


class Location(models.Model):
    name = models.CharField(
        max_length=255,
    )
    address = models.CharField(
        max_length=255,
    )
    city = models.CharField(
        max_length=255,
    )
    state = models.CharField(
        max_length=255,
    )
    zip = models.CharField(
        max_length=20,
    )

    def __str__(self):
        return self.name


GENDER_LIMITATION_CHOICES = (
    ('male', 'Male'),
    ('female', 'Female'),
)


class Session(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    mentor_start_date = models.DateTimeField()
    mentor_end_date = models.DateTimeField()
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
    )
    capacity = models.IntegerField(
        default=20,
    )
    mentor_capacity = models.IntegerField(
        blank=True,
        null=True,
    )
    additional_info = models.TextField(
        blank=True,
        null=True,
        help_text="Basic HTML allowed"
    )
    teacher = models.ForeignKey(
        Mentor,
        related_name="session_teacher",
        on_delete=models.CASCADE,
    )
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
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
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
        max_length=255,
        choices=GENDER_LIMITATION_CHOICES,
        blank=True,
        null=True,
    )
    min_age_limitation = models.IntegerField(
        default=7,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ],
    )
    max_age_limitation = models.IntegerField(
        default=17,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ],
    )

    class Meta:
        verbose_name = _("session")
        verbose_name_plural = _("sessions")

    def __str__(self):
        date = formats.date_format(self.start_date, 'SHORT_DATETIME_FORMAT')
        return f"{self.course.title} | {date}"

    def save(self, *args, **kwargs):
        if self.mentor_capacity is None:
            self.mentor_capacity = int(self.capacity / 2)

        super(Session, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('session-detail', args=[str(self.id)])

    def get_sign_up_url(self):
        return reverse('session-sign-up', args=[str(self.id)])

    def get_calendar_url(self):
        return reverse('session-calendar', args=[str(self.id)])

    def get_current_orders(self, checked_in=None):
        if checked_in is not None:
            if checked_in:
                orders = Order.objects.filter(
                    is_active=True,
                    session=self
                ).exclude(check_in=None).order_by('student__last_name')
            else:
                orders = Order.objects.filter(
                    is_active=True,
                    session=self,
                    check_in=None
                ).order_by('student__last_name')
        else:
            orders = Order.objects.filter(
                is_active=True,
                session=self
            ).order_by('check_in', 'student__last_name')

        return orders

    def get_mentor_orders(self):
        orders = MentorOrder.objects.filter(
            session=self,
            is_active=True,
        ).order_by('mentor__user__last_name')

        return orders

    def get_checked_in_mentor_orders(self):
        orders = MentorOrder.objects.filter(
            session=self,
            is_active=True,
            check_in__isnull=False
        ).order_by('mentor__user__last_name')
        return orders

    def get_current_students(self, checked_in=None):
        if checked_in is not None:
            if checked_in:
                orders = Order.objects.filter(
                    is_active=True,
                    session=self
                ).exclude(check_in=None).values('student')
            else:
                orders = Order.objects.filter(
                    is_active=True,
                    session=self,
                    check_in=None
                ).values('student')
        else:
            orders = Order.objects.filter(
                is_active=True,
                session=self
            ).values('student')

        return orders

    def get_checked_in_students(self):
        return Order.objects.filter(
            is_active=True,
            session=self
        ).exclude(check_in=None).values('student')

    def get_mentor_capacity(self):
        if self.mentor_capacity:
            return self.mentor_capacity
        else:
            return int(self.capacity / 2)

    def is_guardian_announced(self):
        return self.announced_date_guardians is not None
    is_guardian_announced.boolean = True
    is_guardian_announced.short_description = "Is Announced"
    is_guardian_announced.admin_order_field = 'announced_date_guardians'


class MeetingType(models.Model):
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
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = _("meeting type")
        verbose_name_plural = _("meeting types")

    def __str__(self):
        if self.code:
            return f'{self.code} | {self.title}'
        else:
            return f'{self.title}'

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(MeetingType, self).save(*args, **kwargs)


class Meeting(models.Model):
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
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = _("meeting")
        verbose_name_plural = _("meetings")

    def __str__(self):
        date = formats.date_format(self.start_date, "SHORT_DATETIME_FORMAT")
        return f'{self.meeting_type.title} | {date}'

    def get_absolute_url(self):
        return reverse('meeting-detail', args=[str(self.id)])

    def get_sign_up_url(self):
        return reverse('meeting-register', args=[str(self.id)])

    def get_calendar_url(self):
        return reverse('meeting-calendar', args=[str(self.id)])

    def get_current_orders(self, checked_in=None):
        if checked_in is not None:
            if checked_in:
                orders = MeetingOrder.objects.filter(
                    is_active=True,
                    meeting=self,
                ).exclude(
                    check_in=None,
                ).order_by(
                    'mentor__user__last_name'
                )
            else:
                orders = MeetingOrder.objects.filter(
                    is_active=True,
                    meeting=self,
                    check_in=None,
                ).order_by(
                    'mentor__user__last_name'
                )

        else:
            orders = MeetingOrder.objects.filter(
                is_active=True,
                meeting=self,
            ).order_by(
                'check_in',
                'mentor__user__last_name',
            )

        return orders

    def get_current_mentors(self):
        return Mentor.objects.filter(
            id__in=MeetingOrder.objects.filter(
                is_active=True,
                meeting=self,
            ).values(
                'mentor__id',
            )
        )

    def get_mentor_count(self):
        return MeetingOrder.objects.filter(meeting__id=self.id).count()
    get_mentor_count.short_description = 'Mentors'


class Order(models.Model):
    guardian = models.ForeignKey(
        Guardian,
        on_delete=models.CASCADE,
    )
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
    )
    student = models.ForeignKey(
        Student,
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
    alternate_guardian = models.CharField(
        max_length=255,
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
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )
    week_reminder_sent = models.BooleanField(
        default=False,
    )
    day_reminder_sent = models.BooleanField(
        default=False,
    )

    class Meta:
        verbose_name = _("order")
        verbose_name_plural = _("orders")

    def __str__(self):
        return f'{self.student.first_name} {self.student.last_name} | {self.session.course.title}'

    def is_checked_in(self):
        return self.check_in is not None
    is_checked_in.boolean = True

    def get_student_age(self):
        return self.student.get_age(self.session.start_date)
    get_student_age.short_description = 'Age'

    def get_student_gender(self):
        return self.student.get_clean_gender().title()
    get_student_gender.short_description = 'Gender'


class MentorOrder(models.Model):
    mentor = models.ForeignKey(
        Mentor,
        on_delete=models.CASCADE,
    )
    session = models.ForeignKey(
        Session,
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
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )
    week_reminder_sent = models.BooleanField(
        default=False,
    )
    day_reminder_sent = models.BooleanField(
        default=False,
    )

    class Meta:
        verbose_name = _("mentor order")
        verbose_name_plural = _("mentor orders")

    def __str__(self):
        return f"{self.mentor.user.first_name} {self.mentor.user.last_name} | {self.session.course.title}"

    def is_checked_in(self):
        return self.check_in is not None
    is_checked_in.boolean = True


class MeetingOrder(models.Model):
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
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )
    week_reminder_sent = models.BooleanField(
        default=False,
    )
    day_reminder_sent = models.BooleanField(
        default=False,
    )

    class Meta:
        verbose_name = _("meeting order")
        verbose_name_plural = _("meeting orders")

    def __str__(self):
        return f"{self.mentor.user.first_name} {self.mentor.user.last_name} | {self.meeting.meeting_type.title}"

    def is_checked_in(self):
        return self.check_in is not None
    is_checked_in.boolean = True


class EquipmentType(models.Model):
    name = models.CharField(max_length=255, blank=False, null=False)

    def __str__(self):
        return self.name


EQUIPTMENTCONDITIONS = (
    ('working', 'Working'),
    ('issue', 'Issue'),
    ('unusable', 'Unusable'),
)


class Equipment(models.Model):
    uuid = models.CharField(
        max_length=255,
        verbose_name="UUID",
        default='000-000-000-000',
        null=False,
    )
    equipment_type = models.ForeignKey(
        EquipmentType,
        on_delete=models.CASCADE,
    )
    make = models.CharField(
        max_length=255,
    )
    model = models.CharField(
        max_length=255,
    )
    asset_tag = models.CharField(
        max_length=255,
    )
    aquisition_date = models.DateTimeField(
        blank=True,
        null=True,
    )
    condition = models.CharField(
        max_length=255,
        choices=EQUIPTMENTCONDITIONS,
    )
    notes = models.TextField(
        blank=True,
        null=True,
    )
    last_system_update_check_in = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Last Check In",
    )
    last_system_update = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Last Update",
    )
    force_update_on_next_boot = models.BooleanField(
        default=False,
        verbose_name="Force Update",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = _("equipment")
        verbose_name_plural = _("equipment")

    def __str__(self):
        return f"{self.equipment_type.name} | {self.make} {self.model} | {self.aquisition_date}"


class EmailContent(models.Model):
    nickname = models.CharField(
        max_length=255,
    )
    subject = models.CharField(
        max_length=255,
    )
    body = models.TextField(
        blank=True,
        null=True,
        help_text="Basic HTML allowed",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )
    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        verbose_name = _("email content")
        verbose_name_plural = _("email content")

    def __str__(self):
        return f"{self.nickname} | {self.subject}"


class Donation(models.Model):
    user = models.ForeignKey(
        CDCUser,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    session = models.ForeignKey(
        Session,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    first_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    last_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    referral_code = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    email = models.EmailField(
        blank=True,
        null=True,
    )
    amount = models.IntegerField()
    is_verified = models.BooleanField(
        default=False,
    )
    receipt_sent = models.BooleanField(
        default=False,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = _("donation")
        verbose_name_plural = _("donations")

    def __str__(self):
        return f"{self.email} | ${self.amount}"

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return reverse(
            f"admin:{content_type.app_label}_{content_type.model}_change",
            args=(self.id,)
        )

    def get_first_name(self):
        if self.user:
            return self.user.first_name
        else:
            return self.first_name
    get_first_name.short_description = 'First Name'

    def get_last_name(self):
        if self.user:
            return self.user.last_name
        else:
            return self.last_name
    get_last_name.short_description = 'Last Name'

    def get_email(self):
        if self.user:
            return self.user.email
        else:
            return self.email
    get_email.short_description = 'Email'


class PartnerPasswordAccess(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        CDCUser,
        on_delete=models.CASCADE,
    )
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _("partner_password_access")
        db_table = _("partner_password_access")
