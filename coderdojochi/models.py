from django.db import models

from datetime import date

from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext as _
from django.utils import formats

from django.template.defaultfilters import slugify

MentorType = (
    ('mentor', 'mentor'),
    ('gaurdian', 'gaurdian'),
)

class CDCUser(AbstractUser):
    role = models.CharField(choices=MentorType, max_length=10, blank=True, null=True)
    admin_notes = models.TextField(blank=True, null=True)


class Mentor(models.Model):
    user = models.ForeignKey(CDCUser)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

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
    phone = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

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
    photo_release = models.BooleanField('Photo Consent', help_text="I hereby give permission to CoderDojoChi to use the student's image and/or likeness in promotional materials.")
    consent = models.BooleanField('General Consent', help_text="I hereby give consent for the student signed up above to participate in CoderDojoChi.")
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)
    active = models.BooleanField(default=True)

    def is_registered_for_session(self, session):
        try:
            order = Order.objects.get(student=self, session=session)
            is_registered = True
        except:
            is_registered = False

        return is_registered

    def get_age(self):
        today = date.today()
        birthday = self.birthday
        return today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))

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
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    class Meta:
        verbose_name = _("course")
        verbose_name_plural = _("courses")

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Course, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.code + ' | ' + self.title

class Session(models.Model):
    course = models.ForeignKey(Course)
    additional_info = models.TextField(blank=True, null=True, help_text="Basic HTML allowed")
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    capacity = models.IntegerField(blank=True, null=True)
    teacher = models.ForeignKey(Mentor, blank=True, null=True, related_name="session_teacher")
    mentors = models.ManyToManyField(Mentor, blank=True, null=True, related_name="session_mentors")
    active = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    class Meta:
        verbose_name = _("session")
        verbose_name_plural = _("sessions")

    def get_absolute_url(self):
        return '/class/' + str(self.start_date.year) + '/' + str(self.start_date.month) + '/' + str(self.start_date.day) + '/'  + self.course.slug + '/' + str(self.id)

    def get_current_students(self):
        students = Order.objects.filter(session=self).values('student')
        return students

    def __unicode__(self):
        return self.course.title + ' | ' + formats.date_format(self.start_date, "SHORT_DATETIME_FORMAT")

class Order(models.Model):
    guardian = models.ForeignKey(Guardian)
    session = models.ForeignKey(Session)
    student = models.ForeignKey(Student)
    active = models.BooleanField(default=True)
    ip = models.CharField(max_length=255, blank=True, null=True)
    check_in = models.DateTimeField(blank=True, null=True)
    affiliate = models.CharField(max_length=255, blank=True, null=True)
    order_number = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    class Meta:
        verbose_name = _("order")
        verbose_name_plural = _("orders")

    def __unicode__(self):
        return self.student.first_name + ' ' + self.student.last_name + ' | ' + self.session.course.title
