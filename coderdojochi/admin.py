from django.contrib.auth import get_user_model
from django.contrib import admin
from coderdojochi.models import Mentor, Student, Class

User = get_user_model()

admin.site.register(User)
admin.site.register(Mentor)
admin.site.register(Student)
admin.site.register(Class)
