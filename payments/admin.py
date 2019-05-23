from django.contrib import admin
from import_export.admin import ImportExportActionModelAdmin, ImportExportMixin

from .models import Donation, Payment


@admin.register(Donation)
class DonationAdmin(ImportExportMixin, ImportExportActionModelAdmin):

    list_per_page = 10

    list_display = [
        'id',
        'stripe_payment_id',
        'email',
        'formatted_amount',
    ]

    ordering = [
        'created_at',
    ]

    search_fields = [
        'email'
    ]

    readonly_fields = (
        'name',
        'email',
        'customer',
        'stripe_customer_id',
        'stripe_payment_id',
        'amount',
        'created_at',
    )

    view_on_site = False

    def formatted_amount(self, obj):
        return "$ {:.2f}".format(obj.amount / 100)


@admin.register(Payment)
class PaymentAdmin(ImportExportMixin, ImportExportActionModelAdmin):

    list_per_page = 10

    list_display = [
        'stripe_payment_id',
        'customer',
        'session',
        'formatted_amount',
    ]

    ordering = [
        'created_at',
    ]

    search_fields = [
        'customer'
    ]

    # readonly_fields = (
    #     'customer',
    #     'session',
    #     'stripe_customer_id',
    #     'stripe_payment_id',
    #     'amount',
    #     'created_at',
    # )

    view_on_site = False

    def formatted_amount(self, obj):
        return "$ {:.2f}".format(obj.amount / 100)
