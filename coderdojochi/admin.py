from django.contrib.auth import get_user_model
from django.contrib import admin
from coderdojochi.models import Mentor, Guardian, Student, Course, Session, Order, EquipmentType, Equipment, MeetingType, Meeting, Location, Donation

User = get_user_model()

class UserAdmin(admin.ModelAdmin):
    change_form_template = 'loginas/change_form.html'

admin.site.register(User, UserAdmin)
admin.site.register(Mentor)
admin.site.register(Guardian)
admin.site.register(Student)
admin.site.register(Course)
admin.site.register(Session)
admin.site.register(Order)
admin.site.register(MeetingType)
admin.site.register(Meeting)
admin.site.register(EquipmentType)
admin.site.register(Equipment)
admin.site.register(Donation)
admin.site.register(Location)
