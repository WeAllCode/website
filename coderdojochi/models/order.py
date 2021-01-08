from django.db import models

from .common import CommonInfo


class Order(CommonInfo):
    from .guardian import Guardian
    from .session import Session
    from .student import Student

    guardian = models.ForeignKey(Guardian, on_delete=models.CASCADE,)
    session = models.ForeignKey(Session, on_delete=models.CASCADE,)
    student = models.ForeignKey(Student, on_delete=models.CASCADE,)
    is_active = models.BooleanField(default=True,)
    ip = models.CharField(max_length=255, blank=True, null=True,)
    check_in = models.DateTimeField(blank=True, null=True,)
    alternate_guardian = models.CharField(max_length=255, blank=True, null=True,)
    affiliate = models.CharField(max_length=255, blank=True, null=True,)
    order_number = models.CharField(max_length=255, blank=True, null=True,)
    week_reminder_sent = models.BooleanField(default=False,)
    day_reminder_sent = models.BooleanField(default=False,)

    def __str__(self):
        return f"{self.student.first_name} {self.student.last_name} | {self.session.course.title}"

    def is_checked_in(self):
        return self.check_in is not None

    is_checked_in.boolean = True

    def get_student_age(self):
        return self.student.get_age(self.session.start_date)

    get_student_age.short_description = "Age"

    def get_student_gender(self):
        return self.student.get_clean_gender().title()

    get_student_gender.short_description = "Gender"

