from django.contrib import admin
from import_export.admin import ImportExportActionModelAdmin, ImportExportMixin

from .models import Donation


@admin.register(Donation)
class DonationAdmin(ImportExportMixin, ImportExportActionModelAdmin):

    list_per_page = 10

    list_display = [
        'id',
        'email',
        'formatted_amount',
    ]

    ordering = [
        'created_at',
    ]

    search_fields = [
        'email'
    ]

    view_on_site = False

    def formatted_amount(self, obj):
        return "$ %.2f" % (obj.amount / 100)
