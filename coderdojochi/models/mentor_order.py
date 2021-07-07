import os

#from django.db import models

from ..notifications import NewMentorOrderNotification
from .common import CommonInfo
import salesforce

class MentorOrder(salesforce.models.SalesforceModel):
    #class MentorOrder(CommonInfo):
    from .mentor import Mentor
    from .session import Session

    CURRENT = "current"
    FORMER = "former"

    STATUS_CHOICES = [
        (CURRENT, "current"),
        (FORMER, "former"),
    ]

    mentor = salesforce.models.ForeignKey(
        Mentor,
        on_delete=salesforce.models.PROTECT,
        db_column="hed__Contact__c",
    )
    session = salesforce.models.ForeignKey(
        Session,
        on_delete=salesforce.models.PROTECT,
        db_column="hed__Course_Offering__c"
    )
    is_active = salesforce.models.CharField(
        choices=STATUS_CHOICES,
        max_length=355,
        blank=True,
        null=True,
        db_column="hed__Status__c",
    )
    ip = salesforce.models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    check_in = salesforce.models.DateTimeField(
        blank=True,
        null=True,
        db_column="Check_in__c",
    )
    affiliate = salesforce.models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_column="Affiliate__c",
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
        return f"{self.mentor.full_name} | {self.session.course.title}"

    class Meta:
        db_table = "hed__Course_Enrollment__c"

    def is_checked_in(self):
        return self.check_in is not None

    is_checked_in.boolean = True

    def save(self, *args, **kwargs):
        num_orders = MentorOrder.objects.filter(mentor__id=self.mentor.id).count()

        if self.pk is None and num_orders == 0:
            NewMentorOrderNotification(self).send()

        super().save(*args, **kwargs)
