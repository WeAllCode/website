from django.contrib.auth import get_user_model
from django.contrib import admin
from coderdojochi.models import Mentor, Guardian, Student, Course, Session, Order, EquipmentType, Equipment, MeetingType, Meeting, Location, Donation

User = get_user_model()

class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_staff', 'is_superuser', 'last_login', 'date_joined',)
    list_filter = ('role', 'is_staff',)
    ordering = ('-date_joined',)
    list_per_page = 100
    date_hierarchy = 'date_joined'
    search_fields = ('first_name','last_name', 'email',)

    change_form_template = 'loginas/change_form.html'

class MentorAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'user', 'active', 'has_attended_intro_meeting', 'public', 'created_at', 'updated_at',)
    ordering = ('-created_at',)
    list_per_page = 100
    date_hierarchy = 'created_at'
    search_fields = ('first_name','last_name', 'user',)

class GuardianAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'user', 'phone', 'zip', 'created_at', 'updated_at',)
    list_filter = ('zip',)
    ordering = ('-created_at',)
    list_per_page = 100
    date_hierarchy = 'created_at'
    search_fields = ('first_name','last_name', 'user',)

class StudentAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'gender', 'guardian', 'created_at', 'updated_at', 'active',)
    ordering = ('guardian',)
    list_per_page = 100
    date_hierarchy = 'created_at'

class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'slug', 'created_at', 'updated_at',)
    ordering = ('created_at',)
    list_per_page = 100

class SessionAdmin(admin.ModelAdmin):
    list_display = ('course', 'start_date', 'end_date', 'location', 'capacity', 'active', 'public', 'announced_date',)
    ordering = ('start_date',)
    list_per_page = 100
    date_hierarchy = 'start_date'

class OrderAdmin(admin.ModelAdmin):
    list_display = ('guardian', 'student', 'session', 'active', 'ip', 'check_in', 'alternate_guardian', 'affiliate', 'order_number', 'created_at', 'updated_at', 'week_reminder_sent', 'day_reminder_sent',)
    list_filter = ('check_in', 'session',)
    ordering = ('created_at',)
    list_per_page = 100
    date_hierarchy = 'created_at'

class MeetingTypeAdmin(admin.ModelAdmin):
    pass

class MeetingAdmin(admin.ModelAdmin):
    list_display = ('meeting_type', 'start_date', 'end_date', 'location', 'public', 'active', 'announced_date', 'created_at',)
    ordering = ('start_date',)
    list_per_page = 100
    date_hierarchy = 'start_date'

class EquipmentTypeAdmin(admin.ModelAdmin):
    pass

class EquipmentAdmin(admin.ModelAdmin):
    pass

class DonationAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'amount', 'verified', 'receipt_sent', 'created_at', 'updated_at',)
    list_filter = ('amount', 'receipt_sent',)
    ordering = ('-created_at',)
    list_per_page = 100
    date_hierarchy = 'created_at'

class LocationAdmin(admin.ModelAdmin):
    pass


admin.site.register(User, UserAdmin)
admin.site.register(Mentor, MentorAdmin)
admin.site.register(Guardian, GuardianAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Session, SessionAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(MeetingType, MeetingTypeAdmin)
admin.site.register(Meeting, MeetingAdmin)
admin.site.register(EquipmentType, EquipmentTypeAdmin)
admin.site.register(Equipment, EquipmentAdmin)
admin.site.register(Donation, DonationAdmin)
admin.site.register(Location, LocationAdmin)
