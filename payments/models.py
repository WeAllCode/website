from coderdojochi.models import Session, Student
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Donation(models.Model):
    customer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="customer",
        blank=True,
        null=True,
    )
    name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    email = models.EmailField()
    stripe_customer_id = models.CharField(
        max_length=350,
    )
    stripe_payment_id = models.CharField(
        max_length=350,
    )
    amount = models.PositiveIntegerField()
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.email

    def get_absolute_url(self):
        return reverse("Donation_detail", kwargs={"pk": self.pk})

    def get_formatted_amount(self):
        return "{:.2f}".format(self.amount / 100)


class Payment(models.Model):
    customer = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="customer",
    )
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name="session",
    )
    stripe_customer_id = models.CharField(
        max_length=350,
    )
    stripe_payment_id = models.CharField(
        max_length=350,
    )
    amount = models.PositiveIntegerField()
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.customer.first_name

    def get_formatted_amount(self):
        return "{:.2f}".format(self.amount / 100)
