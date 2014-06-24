from django.db import models

from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext as _
from django.utils import formats

from django.template.defaultfilters import slugify

MentorType = (
    ('mentor', 'mentor'),
    ('student', 'student'),
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

class Student(models.Model):
    user = models.ForeignKey(CDCUser)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    class Meta:
        verbose_name = _("student")
        verbose_name_plural = _("students")

    def __unicode__(self):
        return self.user.username

class Class(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=40, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    capacity = models.IntegerField(blank=True, null=True)
    teacher = models.ForeignKey(Mentor, blank=True, null=True, related_name="class_teacher")
    mentors = models.ManyToManyField(Mentor, blank=True, null=True, related_name="class_mentors")
    students = models.ManyToManyField(Student, blank=True, null=True)
    active = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    class Meta:
        verbose_name = _("class")
        verbose_name_plural = _("classes")

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Class, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return '/class/' + str(self.start_date.year) + '/' + str(self.start_date.month) + '/' + str(self.start_date.day) + '/'  + self.slug

    def __unicode__(self):
        return self.title + ' | ' + formats.date_format(self.start_date, "SHORT_DATETIME_FORMAT")
