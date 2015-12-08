from django.conf import settings

from django.db import models

from datetime import datetime, timedelta

from django.core.validators import RegexValidator

from django.contrib.auth.models import AbstractUser

from django.utils.translation import ugettext as _
from django.utils import formats, timezone

from django.template.defaultfilters import slugify

Roles = (
    ('mentor', 'mentor'),
    ('guardian', 'guardian'),
)

class CDCUser(AbstractUser):
    role = models.CharField(choices=Roles, max_length=10, blank=True, null=True)
    admin_notes = models.TextField(blank=True, null=True)

    def get_absolute_url(self):
        return settings.SITE_URL + '/dojo'

class Mentor(models.Model):
    user = models.ForeignKey(CDCUser)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    has_attended_intro_meeting = models.BooleanField(default=False)
    public = models.BooleanField(default=False)

    def get_approve_avatar_url(self):
        return settings.SITE_URL + '/mentors/' + str(self.id) + '/approve-avatar/'

    def get_reject_avatar_url(self):
        return settings.SITE_URL + '/mentors/' + str(self.id) + '/reject-avatar/'

    def get_absolute_url(self):
        return settings.SITE_URL + '/mentors/' + str(self.id) + '/'

    class Meta:
        verbose_name = _("mentors")
        verbose_name_plural = _("mentors")

    def __unicode__(self):
        return self.user.username

class Guardian(models.Model):
    user = models.ForeignKey(CDCUser)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    active = models.BooleanField(default=True)
    phone = models.CharField(max_length=50, blank=True)
    zip = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_students(self):
        students = Student.objects.filter(guardian=self)
        return students

    class Meta:
        verbose_name = _("guardian")
        verbose_name_plural = _("guardians")

    def __unicode__(self):
        return self.user.username

class Student(models.Model):
    guardian = models.ForeignKey(Guardian)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    birthday = models.DateTimeField()
    gender = models.CharField(max_length=255)
    medical_conditions = models.TextField(blank=True, null=True)
    medications = models.TextField(blank=True, null=True)
    photo_release = models.BooleanField('Photo Consent', help_text="I hereby give permission to CoderDojoChi to use the student's image and/or likeness in promotional materials.", default=False)
    consent = models.BooleanField('General Consent', help_text="I hereby give consent for the student signed up above to participate in CoderDojoChi.", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    def is_registered_for_session(self, session):
        try:
            order = Order.objects.get(active=True, student=self, session=session)
            is_registered = True
        except:
            is_registered = False

        return is_registered

    def get_age(self):
        today = timezone.now()
        birthday = self.birthday
        return today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))

    def get_clean_gender(self):
        if self.gender.lower() in ['male', 'm', 'boy', 'nino', 'masculino']:
            return 'male'
        elif self.gender.lower() in ['female', 'f', 'girl', 'femail', 'femal', 'femenino']:
            return 'female'
        else:
            return 'other'

    class Meta:
        verbose_name = _("student")
        verbose_name_plural = _("students")

    def __unicode__(self):
        return self.last_name + ', ' + self.first_name

class Course(models.Model):
    code = models.CharField(max_length=255, blank=True, null=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=40, blank=True, null=True)
    description = models.TextField(blank=True, null=True, help_text="Basic HTML allowed")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        verbose_name = _("course")
        verbose_name_plural = _("courses")

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Course, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.code + ' | ' + self.title


class Location(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    address2 = models.CharField(max_length=255, blank=True, null=True, verbose_name="Address 2")
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    zip = models.CharField(max_length=20)

    def __unicode__(self):
        return self.name

def session_default_start_time():
    now = timezone.now()
    start = now.replace(hour=10, minute=0, second=0, microsecond=0)
    return start if start > now else start + timedelta(days=1)

def session_default_end_time():
    now = timezone.now()
    start = now.replace(hour=13, minute=0, second=0, microsecond=0)
    return start if start > now else start + timedelta(days=1)

class Session(models.Model):
    course = models.ForeignKey(Course)
    start_date = models.DateTimeField(default=session_default_start_time())
    end_date = models.DateTimeField(default=session_default_end_time())
    mentor_start_date = models.DateTimeField(default=session_default_start_time() - timedelta(hours=1))
    mentor_end_date = models.DateTimeField(default=session_default_end_time() + timedelta(hours=1))
    location = models.ForeignKey(Location)
    capacity = models.IntegerField(default=20)
    mentor_capacity = models.IntegerField(blank=True, null=True)
    additional_info = models.TextField(blank=True, null=True, help_text="Basic HTML allowed")
    teacher = models.ForeignKey(Mentor, related_name="session_teacher")
    mentors = models.ManyToManyField(Mentor, blank=True, null=True, related_name="session_mentors")
    waitlist_mentors = models.ManyToManyField(Mentor, blank=True, null=True, related_name="session_waitlist_mentors")
    waitlist_students = models.ManyToManyField(Student, blank=True, null=True, related_name="session_waitlist_students")
    external_enrollment_url = models.CharField(max_length=255, blank=True, null=True, help_text="When provided, local enrollment is disabled.")
    active = models.BooleanField(default=False, help_text="Session is active.")
    public = models.BooleanField(default=False, help_text="Session is a public session.")
    announced_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image_url = models.CharField(max_length=255, blank=True, null=True)
    bg_image = models.ImageField(blank=True, null=True)
    mentors_week_reminder_sent = models.BooleanField(default=False)
    mentors_day_reminder_sent = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("session")
        verbose_name_plural = _("sessions")

    def get_absolute_url(self):
        return settings.SITE_URL + '/class/' + self.start_date.strftime("%Y/%m/%d") + '/'  + self.course.slug + '/' + str(self.id)

    def get_signup_url(self):
        return settings.SITE_URL + '/class/' + self.start_date.strftime("%Y/%m/%d") + '/'  + self.course.slug + '/' + str(self.id) + '/sign-up/'

    def get_ics_url(self):
        return settings.SITE_URL + '/class/' + self.start_date.strftime("%Y/%m/%d") + '/'  + self.course.slug + '/' + str(self.id) + '/calendar/'

    def get_current_orders(self, checked_in=None):
        if checked_in != None:
            if checked_in:
                orders = Order.objects.filter(active=True, session=self).exclude(check_in=None).order_by('student__last_name')
            else:
                orders = Order.objects.filter(active=True, session=self, check_in=None).order_by('student__last_name')
        else:
            orders = Order.objects.filter(active=True, session=self).order_by('check_in', 'student__last_name')

        return orders

    def get_current_students(self, checked_in=None):
        if checked_in != None:
            if checked_in:
                orders = Order.objects.filter(active=True, session=self).exclude(check_in=None).values('student')
            else:
                orders = Order.objects.filter(active=True, session=self, check_in=None).values('student')
        else:
            orders = Order.objects.filter(active=True, session=self).values('student')

        return orders

    def get_checked_in_students(self):
        return Order.objects.filter(active=True, session=self).exclude(check_in=None).values('student')

    def get_mentor_capacity(self):
        if self.mentor_capacity:
            return self.mentor_capacity
        else:
            return self.capacity / 2


    def __unicode__(self):
        return self.course.title + ' | ' + formats.date_format(self.start_date, "SHORT_DATETIME_FORMAT")

class MeetingType(models.Model):
    code = models.CharField(max_length=255, blank=True, null=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=40, blank=True, null=True)
    description = models.TextField(blank=True, null=True, help_text="Basic HTML allowed")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("meeting type")
        verbose_name_plural = _("meeting types")

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(MeetingType, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.code + ' | ' + self.title


class Meeting(models.Model):
    meeting_type = models.ForeignKey(MeetingType)
    additional_info = models.TextField(blank=True, null=True, help_text="Basic HTML allowed")
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    location = models.ForeignKey(Location)
    mentors = models.ManyToManyField(Mentor, blank=True, null=True, related_name="meeting_mentors")
    external_enrollment_url = models.CharField(max_length=255, blank=True, null=True, help_text="When provided, local enrollment is disabled.")
    public = models.BooleanField(default=False)
    active = models.BooleanField(default=False)
    image_url = models.CharField(max_length=255, blank=True, null=True)
    bg_image = models.ImageField(blank=True, null=True)
    announced_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("meeting")
        verbose_name_plural = _("meetings")

    def get_absolute_url(self):
        return settings.SITE_URL + '/meeting/' + str(self.start_date.year) + '/' + str(self.start_date.month) + '/' + str(self.start_date.day) + '/'  + str(self.id)

    def get_signup_url(self):
        return settings.SITE_URL + '/meeting/' + str(self.start_date.year) + '/' + str(self.start_date.month) + '/' + str(self.start_date.day) + '/'  + str(self.id) + '/sign-up/'

    def get_ics_url(self):
        return settings.SITE_URL + '/meeting/' + str(self.start_date.year) + '/' + str(self.start_date.month) + '/' + str(self.start_date.day) + '/'  + str(self.id) + '/calendar/'

    def __unicode__(self):
        return self.meeting_type.title + ' | ' + formats.date_format(self.start_date, "SHORT_DATETIME_FORMAT")

class Order(models.Model):
    guardian = models.ForeignKey(Guardian)
    session = models.ForeignKey(Session)
    student = models.ForeignKey(Student)
    active = models.BooleanField(default=True)
    ip = models.CharField(max_length=255, blank=True, null=True)
    check_in = models.DateTimeField(blank=True, null=True)
    alternate_guardian = models.CharField(max_length=255, blank=True, null=True)
    affiliate = models.CharField(max_length=255, blank=True, null=True)
    order_number = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    week_reminder_sent = models.BooleanField(default=False)
    day_reminder_sent = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("order")
        verbose_name_plural = _("orders")

    def __unicode__(self):
        return self.student.first_name + ' ' + self.student.last_name + ' | ' + self.session.course.title

class EquipmentType(models.Model):
    name = models.CharField(max_length=255,blank=False,null=False)

    def __unicode__(self):
        return self.name

EquiptmentConditions = (
    ('working', 'Working'),
    ('issue', 'Issue'),
    ('unusable', 'Unusable'),
)

class Equipment(models.Model):
    equipment_type = models.ForeignKey(EquipmentType)
    make = models.CharField(max_length=255)
    model = models.CharField(max_length=255)
    location = models.ForeignKey(Location)
    asset_tag = models.CharField(max_length=255)
    aquisition_date = models.DateTimeField(blank=False,null=False)
    condition = models.CharField(max_length=255, choices=EquiptmentConditions)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("equiptment")
        verbose_name_plural = _("equiptment")

    def __unicode__(self):
        return self.equipment_type.name + ' | ' + self.make + ' ' + self.model + ' | ' + str(self.aquisition_date)


class EmailContent(models.Model):
    nickname = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    body = models.TextField(blank=True, null=True, help_text="Basic HTML allowed")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("email content")
        verbose_name_plural = _("email content")

    def __unicode__(self):
        return self.nickname + ' | ' + self.subject

class Donation(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField()
    amount = models.IntegerField()
    verified = models.BooleanField(default=False)
    receipt_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("donation")
        verbose_name_plural = _("donations")

    def __unicode__(self):
        return self.email + ' | $' + str(self.amount)
