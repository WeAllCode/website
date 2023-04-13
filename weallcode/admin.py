from django.contrib import admin
from django.utils.html import format_html

from .models import (
    AssociateBoardMember,
    BoardMember,
    StaffMember,
)


@admin.register(StaffMember)
class StaffMemberAdmin(admin.ModelAdmin):
    def member_image(self, obj):
        return format_html(f'<img src="{obj.image.url}" width="100">')

    member_image.allow_tags = True

    list_display = [
        "member_image",
        "name",
        "role",
        "is_active",
    ]

    list_filter = [
        "is_active",
        "role",
    ]

    readonly_fields = [
        "member_image",
        "created_at",
        "updated_at",
    ]

    ordering = ["name"]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "role",
                    "join_date",
                    "departure_date",
                    "description",
                    "linkedin",
                    "image",
                    "member_image",
                    "is_active",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )


@admin.register(BoardMember)
class BoardMemberAdmin(admin.ModelAdmin):
    def member_image(self, obj):
        return format_html(f'<img src="{obj.image.url}" width="100">')

    member_image.allow_tags = True

    list_display = [
        "member_image",
        "name",
        "role",
        "join_date",
        "is_active",
    ]

    list_filter = [
        "is_active",
        "role",
    ]

    readonly_fields = [
        "member_image",
        "created_at",
        "updated_at",
    ]

    ordering = ["name"]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "role",
                    "join_date",
                    "departure_date",
                    "description",
                    "linkedin",
                    "image",
                    "member_image",
                    "is_active",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )


@admin.register(AssociateBoardMember)
class AssociateBoardMemberAdmin(admin.ModelAdmin):
    def member_image(self, obj):
        return format_html(f'<img src="{obj.image.url}" width="100">')

    member_image.allow_tags = True

    list_display = [
        "member_image",
        "name",
        "role",
        "join_date",
        "is_active",
    ]

    list_filter = [
        "is_active",
        "role",
    ]

    readonly_fields = [
        "member_image",
        "created_at",
        "updated_at",
    ]

    ordering = ["name"]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "role",
                    "join_date",
                    "departure_date",
                    "description",
                    "linkedin",
                    "image",
                    "member_image",
                    "is_active",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )
