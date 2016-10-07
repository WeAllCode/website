# -*- coding: utf-8 -*-
from datetime import datetime

from django.contrib import admin
from django.contrib.auth import get_user_model
# from django.core.urlresolvers import reverse
from django.db.models import Count
# from django.template.defaultfilters import pluralize
# from django.utils.safestring import mark_safe

from import_export.admin import ImportMixin
from import_export.formats.base_formats import CSV
from import_export.resources import ModelResource
from import_export.fields import Field

from coderdojochi.models import (
    Course,
    Donation,
    Equipment,
    EquipmentType,
    Guardian,
    Location,
    Meeting,
    MeetingOrder,
    MeetingType,
    Mentor,
    MentorOrder,
    Order,
    RaceEthnicity,
    Session,
    Student,
    PartnerPasswordAccess,
)

from coderdojochi.util import str_to_bool

User = get_user_model()


class UserAdmin(admin.ModelAdmin):
    list_display = (
        'email',
        'first_name',
        'last_name',
        'role',
        'date_joined',
        'last_login',
        'is_active',
        'is_staff',
        'is_superuser',
    )

    list_filter = (
        'role',
        'is_active',
        'is_staff',
        'date_joined',
    )

    ordering = (
        '-date_joined',
    )

    date_hierarchy = 'date_joined'

    search_fields = (
        'first_name',
        'last_name',
        'email',
    )

    view_on_site = False

    filter_horizontal = (
        'groups',
        'user_permissions',
    )

    readonly_fields = (
        'password',
        'last_login',
    )

    change_form_template = 'loginas/change_form.html'


class MentorAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'get_first_name',
        'get_last_name',
        'created_at',
        'updated_at',
        'active',
        'public',
        'background_check',
        'avatar_approved',
    )

    list_filter = (
        'active',
        'public',
        'background_check',
        'avatar_approved',
    )

    ordering = (
        '-created_at',
    )

    date_hierarchy = 'created_at'

    search_fields = (
        'user__first_name',
        'user__last_name',
        'user__username',
        'user__email'
    )

    def view_on_site(self, obj):
        return obj.get_absolute_url()

    def get_first_name(self, obj):
        return obj.user.first_name
    get_first_name.short_description = 'First Name'
    get_first_name.admin_order_field = 'user__first_name'

    def get_last_name(self, obj):
        return obj.user.last_name
    get_last_name.short_description = 'First Name'
    get_last_name.admin_order_field = 'user__last_name'


class GuardianImportResource(ModelResource):
    first_name = Field(attribute='first_name', column_name='first_name')
    last_name = Field(attribute='last_name', column_name='last_name')
    email = Field(attribute='email', column_name='email')
    phone = Field(attribute='phone', column_name='phone')
    zip = Field(attribute='zip', column_name='zip')

    def get_or_init_instance(self, instance_loader, row):
        """
        Either fetches an already existing instance or initializes a new one.
        """
        try:
            instance = User.objects.get(email=row['email'])
        except User.DoesNotExist as e:
            return Guardian(user=User()), True
        else:
            return (Guardian.objects.get(user=instance), False)

    def import_obj(self, obj, data, dry_run):
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email')
        zip = data.get('zip')
        phone = data.get('phone')
        if obj.pk:
            user = obj.user
        else:
            user = User(first_name=first_name, last_name=last_name, email=email,
                        role='guardian', username=email)

        obj.user = user
        obj.active = False
        obj.zip = zip
        obj.phone = phone
        if not dry_run:
            user.save()
            obj.user = user
            obj.save()

    class Meta:
        model = Guardian
        import_id_fields = ('phone',)
        fields = ('phone', 'zip')


class GuardianAdmin(ImportMixin, admin.ModelAdmin):
    list_display = (
        # 'user',
        'get_first_name',
        'get_last_name',
        # 'phone',
        # 'zip',
        'get_student_count',
        'created_at',
        'updated_at',
    )

    list_filter = (
        'zip',
    )

    ordering = (
        '-created_at',
    )

    search_fields = (
        'user__first_name',
        'user__last_name',
        'user__username',
    )

    date_hierarchy = 'created_at'

    view_on_site = False

    # Import settings
    formats = (CSV,)
    resource_class = GuardianImportResource

    def get_queryset(self, request):
        qs = super(GuardianAdmin, self).get_queryset(request)
        qs = qs.annotate(Count('student'))
        return qs

    def get_first_name(self, obj):
        return obj.user.first_name
    get_first_name.short_description = 'First Name'
    get_first_name.admin_order_field = 'user__first_name'

    def get_last_name(self, obj):
        return obj.user.last_name
    get_last_name.short_description = 'Last Name'
    get_last_name.admin_order_field = 'user__last_name'

    def get_student_count(self, obj):
        return obj.student__count
    get_student_count.short_description = '# of Students'
    get_student_count.admin_order_field = 'student__count'


class StudentAdmin(admin.ModelAdmin):
    list_display = (
        'first_name',
        'last_name',
        'gender',
        'guardian',
        'created_at',
        'updated_at',
        'active'
    )

    list_filter = (
        'gender',
    )

    filter_horizontal = (
        'race_ethnicity',
    )

    ordering = (
        'guardian',
    )

    search_fields = (
        'first_name',
        'last_name',
        'guardian__user__first_name',
        'guardian__user__last_name',
    )

    date_hierarchy = 'created_at'

    view_on_site = False

    # Import settings
    formats = (CSV,)
    resource_class = StudentImportResource


class CourseAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'title',
        'slug',
        'created_at',
        'updated_at',
    )

    list_filter = (
        'code',
    )

    ordering = (
        'created_at',
    )

    view_on_site = False


class SessionAdmin(admin.ModelAdmin):
    list_display = (
        'course',
        'start_date',
        'end_date',
        'location',
        'capacity',
        'get_current_orders_count',
        'get_mentor_count',
        'active',
        'public',
        'announced_date'
    )

    list_filter = (
        'active',
        'public',
        'course__title',
        'location',
    )

    ordering = (
        '-start_date',
    )

    filter_horizontal = (
        'waitlist_mentors',
        'waitlist_students',
    )

    date_hierarchy = 'start_date'

    view_on_site = False

    def view_on_site(self, obj):
        return obj.get_absolute_url()

    def get_mentor_count(self, obj):
        return MentorOrder.objects.filter(session__id=obj.id).count()
    get_mentor_count.short_description = 'Mentors'

    def get_current_orders_count(self, obj):
        return obj.get_current_orders().count()
    get_current_orders_count.short_description = "Students"


class OrderAdmin(admin.ModelAdmin):
    list_display = (
        # 'id',
        'student',
        'guardian',
        'alternate_guardian',
        'session',
        # 'ip',
        'check_in',
        'created_at',
        'updated_at',
        'active',
        'week_reminder_sent',
        'day_reminder_sent',
    )

    list_filter = (
        'active',
        'check_in',
        # 'guardian',
        'student',
        'session',
    )

    ordering = (
        'created_at',
    )

    date_hierarchy = 'created_at'

    view_on_site = False


class MentorOrderAdmin(admin.ModelAdmin):
    # def session(obj):
    #     url = reverse(
    #         'admin:coderdojochi_session_change',
    #         args=(obj.session.id,)
    #     )
    #     return mark_safe('<a href="{0}">{1}</a>'.format(url, obj.session))

    # session.short_description = 'Session'
    # raw_id_fields = ('session',)
    # readonly_fields = (session, 'session',)

    list_display = (
        'mentor',
        'session',
        'ip',
        'check_in',
        'active',
        'week_reminder_sent',
        'day_reminder_sent',
        'created_at',
        'updated_at',
    )

    list_display_links = (
        'mentor',
    )

    list_filter = (
        'active',
        'check_in',
        'session',
        # 'mentor',
    )

    ordering = (
        'created_at',
    )

    search_fields = (
        'mentor__user__first_name',
        'mentor__user__last_name',
    )

    readonly_fields = (
        # 'mentor',
        # 'session',
        'ip',
        # 'check_in',
    )

    date_hierarchy = 'created_at'
    view_on_site = False


class MeetingOrderAdmin(admin.ModelAdmin):
    list_display = (
        'mentor',
        'meeting',
        'ip',
        'check_in',
        'active',
        'week_reminder_sent',
        'day_reminder_sent',
        'created_at',
        'updated_at'
    )

    list_filter = (
        'active',
        'meeting',
        'check_in',
        'meeting__meeting_type',
    )

    ordering = (
        'created_at',
    )

    search_fields = (
        'mentor__user__first_name',
        'mentor__user__last_name',
    )

    date_hierarchy = 'created_at'

    view_on_site = False


class MeetingTypeAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'title',
        'slug',
    )
    list_display_links = (
        'title',
    )
    view_on_site = False


class MeetingAdmin(admin.ModelAdmin):
    list_display = (
        'meeting_type',
        'start_date',
        'end_date',
        'location',
        'get_mentor_count',
        'public',
        'announced_date',
        'created_at'
    )

    list_filter = (
        'active',
        'public',
        'location',
        'meeting_type__title',
    )

    ordering = (
        '-start_date',
    )

    date_hierarchy = 'start_date'
    view_on_site = False

    def view_on_site(self, obj):
        return obj.get_absolute_url()

    def get_mentor_count(self, obj):
        return MeetingOrder.objects.filter(meeting__id=obj.id).count()
    get_mentor_count.short_description = 'Mentors'


class EquipmentTypeAdmin(admin.ModelAdmin):
    view_on_site = False


class EquipmentAdmin(admin.ModelAdmin):
    list_display = (
        'uuid',
        'asset_tag',
        'equipment_type',
        'make',
        'model',
        'condition',
        'last_system_update_check_in',
        'last_system_update',
        'force_update_on_next_boot',
    )

    list_filter = (
        'condition',
        'equipment_type',
        'make',
        'model',
    )

    ordering = (
        'uuid',
    )

    search_fields = (
        'uuid',
        'make',
        'model',
        'asset_tag',
    )

    readonly_fields = (
        'last_system_update_check_in',
        'last_system_update',
    )

    view_on_site = False


class DonationAdmin(admin.ModelAdmin):
    list_display = (
        'first_name',
        'last_name',
        'email',
        'amount',
        'verified',
        'receipt_sent',
        'created_at',
        'updated_at',
    )

    list_filter = (
        'verified',
        'receipt_sent',
        'amount',
        'created_at',
    )

    ordering = (
        '-created_at',
    )

    search_fields = (
        'first_name',
        'last_name',
        'email',
    )

    date_hierarchy = 'created_at'

    view_on_site = False


class LocationAdmin(admin.ModelAdmin):
    view_on_site = False


admin.site.register(User, UserAdmin)
admin.site.register(Mentor, MentorAdmin)
admin.site.register(Guardian, GuardianAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Session, SessionAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(MentorOrder, MentorOrderAdmin)
admin.site.register(MeetingOrder, MeetingOrderAdmin)
admin.site.register(MeetingType, MeetingTypeAdmin)
admin.site.register(Meeting, MeetingAdmin)
admin.site.register(EquipmentType, EquipmentTypeAdmin)
admin.site.register(Equipment, EquipmentAdmin)
admin.site.register(Donation, DonationAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(RaceEthnicity)
