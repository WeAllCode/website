from django.contrib.auth import get_user_model
from django.contrib import admin
from coderdojochi.models import Mentor, Guardian, Student, Course, Session, Order

User = get_user_model()

admin.site.register(User)
admin.site.register(Mentor)
admin.site.register(Guardian)
admin.site.register(Student)
admin.site.register(Course)
admin.site.register(Session)
admin.site.register(Order)
