from django.db import models

from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext as _

from django.template.defaultfilters import slugify


class CDCUser(AbstractUser):
    admin_notes = models.TextField(blank=True, null=True)

MemberType = (
    ('mentor', 'mentor'),
    ('helper', 'helper'),
    ('advisor', 'advisor'),
)

class Member(models.Model):
    user = models.ForeignKey(CDCUser)
    role = models.CharField(choices=MemberType, max_length=10, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    active = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    class Meta:
        verbose_name = _("member")
        verbose_name_plural = _("members")

    def __unicode__(self):
        return self.user.username

class Student(models.Model):
    user = models.ForeignKey(CDCUser)

    active = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    class Meta:
        verbose_name = _("student")
        verbose_name_plural = _("students")

    def __unicode__(self):
        return self.user.username


class Class(models.Model):
    title = models.CharField(max_length=255)
    date = models.DateTimeField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    capacity = models.IntegerField(blank=True, null=True)
    teacher = models.ForeignKey(Member, blank=True, null=True, related_name="class_teacher")
    mentors = models.ManyToManyField(Member, blank=True, null=True, related_name="class_mentors")
    students = models.ManyToManyField(Student, blank=True, null=True)

    active = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    class Meta:
        verbose_name = _("class")
        verbose_name_plural = _("classes")

    def __unicode__(self):
        return self.date + '|' + self.title
