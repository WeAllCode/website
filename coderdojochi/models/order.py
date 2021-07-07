# from django.db import models

from .common import CommonInfo
import salesforce

class Order(salesforce.models.SalesforceModel):
    # Order(CommonInfo)
    from .guardian import Guardian
    from .session import Session
    from .student import Student

    # guardian = salesforce.models.ForeignKey(
    #     Guardian,
    #     on_delete=salesforce.models.PROTECT,

    # )
    CURRENT = "current"
    FORMER = "former"

    STATUS_CHOICES = [
        (CURRENT, "current"),
        (FORMER, "former"),
    ]

    session = salesforce.models.ForeignKey(
        Session,
        db_column="hed__Course_Offering__c",
        on_delete=salesforce.models.PROTECT,
    )
    student = salesforce.models.ForeignKey(
        Student,
        on_delete=salesforce.models.PROTECT,
        db_column="hed__Contact__c"
    )
    is_active = salesforce.models.CharField(
        choices=STATUS_CHOICES,
        max_length=255,
        blank=True,
        null=True,
        db_column="hed__Status__c",
    )
    ip = salesforce.models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_column="IP__c",
    )
    check_in = salesforce.models.DateTimeField(
        blank=True,
        null=True,
        db_column="Check_in__c",
    )
    # alternate_guardian = salesforce.models.CharField(
    #     max_length=255,
    #     blank=True,
    #     null=True,
    # )
    affiliate = salesforce.models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    order_number = salesforce.models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    week_reminder_sent = salesforce.models.BooleanField(
        default=False,
    )
    day_reminder_sent = salesforce.models.BooleanField(
        default=False,
    )

    def __str__(self):
        return f"{self.student.full_name} | {self.session.course.title}"

    class Meta:
        db_table = "hed__Course_Enrollment__c"

    def is_checked_in(self):
        return self.check_in is not None

    is_checked_in.boolean = True

    def get_student_age(self):
        return self.student.get_age(self.session.start_date)

    get_student_age.short_description = "Age"

    def get_student_gender(self):
        return self.student.get_clean_gender().title()

    get_student_gender.short_description = "Gender"
