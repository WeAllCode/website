from coderdojochi.models import Member, Student, Class
from django.contrib.auth import get_user_model
from django.contrib import admin

User = get_user_model()

admin.site.register(User)
admin.site.register(Member)
admin.site.register(Student)
admin.site.register(Class)
