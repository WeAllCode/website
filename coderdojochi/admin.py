from datetime import datetime

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import Case, Count, When
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

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
from import_export import resources
from import_export.admin import ImportExportActionModelAdmin, ImportExportMixin
from import_export.fields import Field

User = get_user_model()


@admin.register(User)
class UserAdmin(ImportExportActionModelAdmin):
    list_display = (
        'email',
        'first_name',
        'last_name',
        'role_link',
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

    def role_link(self, obj):
        if obj.role == 'mentor':
            return format_html(
                '<a href="{url}?q={query}">{role}</a>',
                url=reverse('admin:coderdojochi_mentor_changelist'),
                query=obj.email,
                role=obj.role,
            )
        elif obj.role == 'guardian':
            return format_html(
                '<a href="{url}?q={query}">{role}</a>',
                url=reverse('admin:coderdojochi_guardian_changelist'),
                query=obj.email,
                role=obj.role,
            )

        return obj.role
    role_link.short_description = 'Role'


@admin.register(Mentor)
class MentorAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    list_per_page = 50

    list_display = (
        'first_name',
        'last_name',
        'user_link',
        'mentor_count_link',
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

    list_select_related = (
        'user',
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
        'mentor_count_link',
    )

    def view_on_site(self, obj):
        return obj.get_absolute_url()

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

    def mentor_count_link(self, obj):
        return format_html(
            '<a href="{url}?mentor={query}">{count}</a>',
            url=reverse('admin:coderdojochi_mentororder_changelist'),
            query=obj.id,
            count=obj.mentororder__count,
        )
    mentor_count_link.short_description = 'Orders'
    mentor_count_link.admin_order_field = 'mentororder__count'

    def user_link(self, obj):
        return format_html(
            '<a href="{url}">{user}</a>',
            url=reverse('admin:coderdojochi_cdcuser_change', args=(obj.user.id,)),
            user=obj.user,
        )
    user_link.short_description = 'User'


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
        fields = ('phone', 'zip',)


@admin.register(Guardian)
class GuardianAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    list_per_page = 10

    list_display = (
        'first_name',
        'last_name',
        'student_count_link',
        'user_link',
        'created_at',
        'updated_at',
    )

    list_filter = (
        'zip',
    )

    list_select_related = (
        'user',
    )

    search_fields = (
        'user__first_name',
        'user__last_name',
        'user__username',
        'user__email',
        'phone',
    )

    readonly_fields = (
        'student_count_link',
    )

    date_hierarchy = 'created_at'

    view_on_site = False

    # Import settings
    resource_class = GuardianImportResource

    def get_queryset(self, request):
        qs = super(GuardianAdmin, self).get_queryset(request)
        qs = qs.select_related()
        qs = qs.annotate(
            student_count=Count('student')
        ).order_by('-student_count')
        return qs

    def user_link(self, obj):
        return format_html(
            '<a href="{url}">{name}</a>',
            url=reverse('admin:coderdojochi_cdcuser_change', args=(obj.user.id,)),
            name=obj.user,
        )
    user_link.short_description = 'User'

    def student_count_link(self, obj):
        return format_html(
            '<a href="{url}?guardian={query}">{count}</a>',
            url=reverse('admin:coderdojochi_student_changelist'),
            query=obj.id,
            count=obj.student_count,
        )
    student_count_link.short_description = 'Students'
    student_count_link.admin_order_field = 'student_count'


class StudentResource(resources.ModelResource):
    first_name = Field(
        attribute='first_name',
        column_name='first_name',
    )
    last_name = Field(
        attribute='last_name',
        column_name='last_name',
    )
    guardian_email = Field(
        attribute='guardian_email',
        column_name='guardian_email',
    )
    birthday = Field(
        attribute='birthday',
        column_name='birthday',
    )
    gender = Field(
        attribute='gender',
        column_name='gender',
    )
    school_name = Field(
        attribute='school_name',
        column_name='school_name',
    )
    school_type = Field(
        attribute='school_type',
        column_name='school_type',
    )
    photo_release = Field(
        attribute='photo_release',
        column_name='photo_release',
    )
    consent = Field(
        attribute='consent',
        column_name='consent',
    )

    def import_obj(self, obj, data, dry_run):
        guardian_email = data.get('guardian_email')

        obj.first_name = data.get('first_name')
        obj.last_name = data.get('last_name')
        obj.birthday = datetime.strptime(
            data.get('birthday', ''),
            '%m/%d/%Y'
        )
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
                f'guardian with email {guardian_email} not found'
            )

        if not dry_run:
            obj.save()

    class Meta:
        model = Student
        import_id_fields = ('first_name', 'last_name',)
        fields = ('first_name', 'last_name',)


@admin.register(Student)
class StudentAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    list_per_page = 10

    list_display = (
        'first_name',
        'last_name',
        'gender',
        'get_clean_gender',
        'guardian_link',
        'order_count_link',
        'get_age',
        'is_active',
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
        'order_count_link',
    )

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

    def guardian_link(self, obj):
        return format_html(
            '<a href="{url}">{first} {last}</a>',
            url=reverse("admin:coderdojochi_guardian_change", args=(obj.guardian.id,)),
            # query=obj.guardian.user.email,
            first=obj.guardian.user.first_name,
            last=obj.guardian.user.last_name,
        )
    guardian_link.short_description = 'Guardian'

    def order_count_link(self, obj):
        return format_html(
            '<a href="{url}?student={student}">{count}</a>',
            url=reverse('admin:coderdojochi_order_changelist'),
            student=obj.id,
            count=obj.order__count,
        )
    order_count_link.short_description = 'Orders'
    order_count_link.admin_order_field = 'order__count'


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
        '_course',
        'start_date',
        'end_date',
        'location',
        'capacity',
        'student_count_link',
        'mentor_count_link',
        'is_active',
        'is_public',
        'is_guardian_announced',
    )

    list_filter = (
        'is_active',
        'is_public',
        'course__code',
        'course__title',
        'location',
    )

    list_select_related = (
        'course',
        'location',
        'teacher',
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

    def _course(self, obj):
        return obj.course.code
    _course.short_description = 'Course'
    _course.admin_order_field = 'course__code'

    def mentor_count_link(self, obj):
        return format_html(
            '<a href="{url}?session__id__exact={query}">{count}</a>',
            url=reverse("admin:coderdojochi_mentororder_changelist"),
            query=obj.id,
            count=MentorOrder.objects.filter(session__id=obj.id, is_active=True).count(),
        )
    mentor_count_link.short_description = "Mentors"
    mentor_count_link.admin_order_field = "mentor__count"

    def student_count_link(self, obj):
        return format_html(
            '<a href="{url}?session__id__exact={query}">{count}</a>',
            url=reverse("admin:coderdojochi_order_changelist"),
            query=obj.id,
            count=obj.get_current_orders().count(),
        )
    student_count_link.short_description = "Students"
    student_count_link.admin_order_field = "student__count"


def student_check_in(modeladmin, request, queryset):
    queryset.update(check_in=timezone.now())


student_check_in.short_description = "Check in"


def student_check_out(modeladmin, request, queryset):
    queryset.update(check_in=None)


student_check_out.short_description = "Check out"


@admin.register(Order)
class OrderAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    list_per_page = 50

    list_display = (
        'id',
        'get_student_link',
        'get_student_gender',
        'get_student_age',
        'get_guardian_link',
        # 'alternate_guardian',
        'get_session_link',
        # 'ip',
        '_created_at',
        'is_checked_in',
        # 'updated_at',
        'is_active',
        # 'week_reminder_sent',
        # 'day_reminder_sent',
    )

    list_filter = (
        'is_active',
        'check_in',
        # 'guardian',
        # 'student',
        'session',
    )

    list_select_related = (
        'guardian',
        'session',
        'student',
    )

    search_fields = (
        'student__first_name',
        'student__last_name',
    )

    ordering = (
        'created_at',
    )

    date_hierarchy = 'created_at'

    view_on_site = False

    actions = [
        student_check_in,
        student_check_out,
    ]

    def get_student_link(self, obj):
        return format_html(
            '<a href="{url}">{student}</a>',
            url=reverse('admin:coderdojochi_student_change', args=(obj.student.id,)),
            student=obj.student,
        )
    get_student_link.short_description = 'Student'

    def get_guardian_link(self, obj):
        return format_html(
            '<a href="{url}">{guardian}</a>',
            url=reverse('admin:coderdojochi_guardian_change', args=(obj.guardian.id,)),
            guardian=obj.guardian,
        )
    get_guardian_link.short_description = 'Guardian'

    def get_session_link(self, obj):
        return format_html(
            '<a href="{url}">{course_code}</a>',
            url=reverse("admin:coderdojochi_session_change", args=(obj.session.course.id,)),
            course_code=obj.session.course.code,
        )
    get_session_link.short_description = 'Session'

    def _created_at(self, obj):
        return obj.created_at.strftime("%m/%d/%y %H:%M")
    _created_at.short_description = 'Created At'


def mentor_check_in(modeladmin, request, queryset):
    queryset.update(check_in=timezone.now())


mentor_check_in.short_description = "Check in"


def mentor_check_out(modeladmin, request, queryset):
    queryset.update(check_in=None)


mentor_check_out.short_description = "Check out"


@admin.register(MentorOrder)
class MentorOrderAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    list_per_page = 50

    list_display = (
        'mentor',
        'session',
        'ip',
        'is_checked_in',
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

    list_select_related = (
        'mentor',
        'session',
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

    actions = [
        mentor_check_in,
        mentor_check_out,
    ]

    date_hierarchy = 'created_at'
    view_on_site = False


def meeting_order_check_in(modeladmin, request, queryset):
    queryset.update(check_in=timezone.now())


meeting_order_check_in.short_description = "Check in"


def meeting_order_check_out(modeladmin, request, queryset):
    queryset.update(check_in=None)


meeting_order_check_out.short_description = "Check out"


@admin.register(MeetingOrder)
class MeetingOrderAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    list_per_page = 50

    list_display = (
        'mentor',
        'meeting',
        'ip',
        'is_checked_in',
        'is_active',
        'week_reminder_sent',
        'day_reminder_sent',
        'created_at',
        'updated_at',
    )

    list_filter = (
        'is_active',
        'meeting',
        'check_in',
        'meeting__meeting_type',
    )

    list_select_related = (
        'mentor',
        'meeting',
    )

    ordering = (
        'created_at',
    )

    search_fields = (
        'mentor__user__first_name',
        'mentor__user__last_name',
    )

    actions = [
        meeting_order_check_in,
        meeting_order_check_out,
    ]

    date_hierarchy = 'created_at'

    view_on_site = False

    show_full_result_count = False


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
        'created_at',
    )

    list_filter = (
        'is_active',
        'is_public',
        'location',
        'meeting_type__title',
    )

    list_select_related = (
        'meeting_type',
        'location',
    )

    ordering = (
        '-start_date',
    )

    date_hierarchy = 'start_date'
    view_on_site = False

    def view_on_site(self, obj):
        return obj.get_absolute_url()


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

    list_select_related = (
        'equipment_type',
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
        'created_at',
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


@admin.register(Location)
class LocationAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    view_on_site = False


@admin.register(RaceEthnicity)
class RaceEthnicityAdmin(ImportExportMixin, ImportExportActionModelAdmin):
    pass
