# -*- coding: utf-8 -*-
from datetime import datetime

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.db.models import (
    Case,
    Count,
    When,
)
# from django.template.defaultfilters import pluralize
from django.utils.safestring import mark_safe

from import_export import resources
from import_export.admin import (
    ImportExportActionModelAdmin,
    ImportExportMixin,
)

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
)

from coderdojochi.util import str_to_bool

User = get_user_model()


@admin.register(User)
class UserAdmin(ImportExportActionModelAdmin):
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


@admin.register(Mentor)
class MentorAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    list_per_page = 50

    list_display = (
        'user',
        'get_first_name',
        'get_last_name',
        'get_mentororder_count',
        'created_at',
        'updated_at',
        'is_active',
        'is_public',
        'background_check',
        'avatar_approved',
    )

    list_filter = (
        'is_active',
        'is_public',
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
        'user__email',
    )

    readonly_fields = (
        'get_mentororder_count',
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

    def get_queryset(self, request):
        qs = super(MentorAdmin, self).get_queryset(request)

        # Count all orders that are marked as active
        qs = qs.annotate(
            mentororder__count=Count(
                Case(
                    When(
                        mentororder__is_active=True,
                        then=1,
                    )
                )
            )
        )
        return qs

    def get_mentororder_count(self, obj):
        return mark_safe(
            '<a href="{}?mentor={}">{}</a>'.format(
                reverse("admin:coderdojochi_mentororder_changelist"),
                obj.id,
                obj.mentororder__count,
            )
        )
    get_mentororder_count.short_description = 'Orders'
    get_mentororder_count.admin_order_field = 'mentororder__count'


class GuardianImportResource(resources.ModelResource):
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
        except User.DoesNotExist:
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
            user = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                role='guardian',
                username=email,
            )

        obj.user = user
        obj.is_active = False
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


@admin.register(Guardian)
class GuardianAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    list_per_page = 10

    list_display = (
        # 'user',
        'get_first_name',
        'get_last_name',
        # 'phone',
        # 'zip',
        'get_student_count',
        'user_link',
        'created_at',
        'updated_at',
    )

    list_filter = (
        'zip',
    )

    ordering = (
        '-student__count',
    )

    search_fields = (
        'user__first_name',
        'user__last_name',
        'user__username',
        'user__email',
    )

    date_hierarchy = 'created_at'

    view_on_site = False

    # Import settings
    resource_class = GuardianImportResource

    def user_link(self, obj):
        return mark_safe(
            '<a href="{}?q={}">{}</a>'.format(
                reverse("admin:coderdojochi_cdcuser_changelist"),
                obj.user.email,
                obj.user,
            )
        )
    user_link.short_description = 'User'

    def get_queryset(self, request):
        qs = super(GuardianAdmin, self).get_queryset(request)
        qs = qs.select_related()
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
        return mark_safe(
            '<a href="{}?guardian={}">{}</a>'.format(
                reverse("admin:coderdojochi_student_changelist"),
                obj.id,
                obj.student__count,
            )
        )
    get_student_count.short_description = 'Students'
    get_student_count.admin_order_field = 'student__count'


class StudentResource(resources.ModelResource):
    first_name = Field(attribute='first_name', column_name='first_name')
    last_name = Field(attribute='last_name', column_name='last_name')
    guardian_email = Field(attribute='guardian_email',
                           column_name='guardian_email')
    birthday = Field(attribute='birthday', column_name='birthday')
    gender = Field(attribute='gender', column_name='gender')
    school_name = Field(attribute='school_name', column_name='school_name')
    school_type = Field(attribute='school_type', column_name='school_type')
    photo_release = Field(attribute='photo_release',
                          column_name='photo_release')
    consent = Field(attribute='consent', column_name='consent')

    def import_obj(self, obj, data, dry_run):
        guardian_email = data.get('guardian_email')

        obj.first_name = data.get('first_name')
        obj.last_name = data.get('last_name')
        obj.birthday = datetime.strptime(data.get('birthday', ''), '%m/%d/%Y')
        obj.gender = data.get('gender', '')
        obj.school_name = data.get('school_name', '')
        obj.school_type = data.get('school_type', '')
        obj.photo_release = str_to_bool(data.get('photo_release', ''))
        obj.consent = str_to_bool(data.get('consent', ''))
        obj.is_active = True

        try:
            obj.guardian = Guardian.objects.get(user__email=guardian_email)
        except Guardian.DoesNotExist:
            raise ImportError(
                u'guardian with email {} not found'.format(guardian_email)
            )

        if not dry_run:
            obj.save()

    class Meta:
        model = Student
        import_id_fields = ('first_name', 'last_name')
        fields = ('first_name', 'last_name')
        # fields = ()


@admin.register(Student)
class StudentAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    list_per_page = 10

    list_display = (
        'first_name',
        'last_name',
        'gender',
        'guardian_link',
        'get_order_count',
        'created_at',
        'updated_at',
        'is_active'
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
    resource_class = StudentResource

    readonly_fields = (
        'guardian_link',
        'get_order_count',
    )

    def guardian_link(self, obj):
        return mark_safe(
            '<a href="{}?q={}">{} {}</a>'.format(
                reverse("admin:coderdojochi_guardian_changelist"),
                obj.guardian.user.email,
                obj.guardian.user.first_name,
                obj.guardian.user.last_name,
            )
        )
    guardian_link.short_description = 'Guardian'

    def get_queryset(self, request):
        qs = super(StudentAdmin, self).get_queryset(request)

        qs = qs.select_related()

        # Count all orders that are marked as active
        qs = qs.annotate(
            order__count=Count(
                Case(
                    When(
                        order__is_active=True,
                        then=1,
                    )
                )
            )
        )
        return qs

    def get_order_count(self, obj):
        return mark_safe(
            '<a href="{}?mentor={}">{}</a>'.format(
                reverse("admin:coderdojochi_order_changelist"),
                obj.id,
                obj.order__count,
            )
        )
    get_order_count.short_description = 'Orders'
    get_order_count.admin_order_field = 'order__count'


@admin.register(Course)
class CourseAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    list_per_page = 10

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


@admin.register(Session)
class SessionAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    list_per_page = 10

    list_display = (
        'course',
        'start_date',
        'end_date',
        'location',
        'capacity',
        'get_student_count',
        'get_mentor_count',
        'is_active',
        'is_public',
        'announced_date'
    )

    list_filter = (
        'is_active',
        'is_public',
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
        return mark_safe(
            '<a href="{}?session__id__exact={}">{}</a>'.format(
                reverse("admin:coderdojochi_mentororder_changelist"),
                obj.id,
                MentorOrder.objects.filter(session__id=obj.id, is_active=True).count(),
            )
        )
    get_mentor_count.short_description = 'Mentors'
    get_mentor_count.admin_order_field = 'mentor__count'

    def get_student_count(self, obj):
        return mark_safe(
            '<a href="{}?session__id__exact={}">{}</a>'.format(
                reverse("admin:coderdojochi_order_changelist"),
                obj.id,
                obj.get_current_orders().count(),
            )
        )
    get_student_count.short_description = "Students"
    get_student_count.admin_order_field = 'student__count'


@admin.register(Order)
class OrderAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    list_per_page = 50

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
        'is_active',
        'week_reminder_sent',
        'day_reminder_sent',
    )

    list_filter = (
        'is_active',
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


@admin.register(MentorOrder)
class MentorOrderAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    list_per_page = 50

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
        'is_active',
        'week_reminder_sent',
        'day_reminder_sent',
        'created_at',
        'updated_at',
    )

    list_display_links = (
        'mentor',
    )

    list_filter = (
        'is_active',
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


@admin.register(MeetingOrder)
class MeetingOrderAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    list_per_page = 50

    list_display = (
        'mentor',
        'meeting',
        'ip',
        'check_in',
        'is_active',
        'week_reminder_sent',
        'day_reminder_sent',
        'created_at',
        'updated_at'
    )

    list_filter = (
        'is_active',
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


@admin.register(MeetingType)
class MeetingTypeAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    list_display = (
        'code',
        'title',
        'slug',
    )
    list_display_links = (
        'title',
    )
    view_on_site = False


@admin.register(Meeting)
class MeetingAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    list_per_page = 10

    list_display = (
        'meeting_type',
        'start_date',
        'end_date',
        'location',
        'get_mentor_count',
        'is_public',
        'announced_date',
        'created_at'
    )

    list_filter = (
        'is_active',
        'is_public',
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


@admin.register(EquipmentType)
class EquipmentTypeAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    view_on_site = False


@admin.register(Equipment)
class EquipmentAdmin(ImportExportMixin, ImportExportActionModelAdmin):
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


@admin.register(Donation)
class DonationAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    list_display = (
        'session',
        'get_first_name',
        'get_last_name',
        'get_email',
        'amount',
        'is_verified',
        'receipt_sent',
        'created_at'
    )

    list_filter = (
        'session',
        'user',
        'is_verified',
        'receipt_sent',
        'amount',
        'created_at',
    )

    ordering = (
        '-created_at',
    )

    search_fields = (
        'get_first_name',
        'get_last_name',
        'get_email',
        'session',
    )

    date_hierarchy = 'created_at'

    view_on_site = False

    def get_first_name(self, obj):
        if obj.user:
            return obj.user.first_name
        else:
            return obj.first_name
    get_first_name.short_description = 'First Name'

    def get_last_name(self, obj):
        if obj.user:
            return obj.user.last_name
        else:
            return obj.last_name
    get_last_name.short_description = 'Last Name'

    def get_email(self, obj):
        if obj.user:
            return obj.user.email
        else:
            return obj.email
    get_email.short_description = 'Email'


@admin.register(Location)
class LocationAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    view_on_site = False


@admin.register(RaceEthnicity)
class RaceEthnicityAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    pass
