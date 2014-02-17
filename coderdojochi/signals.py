from registration.signals import user_registered

from coderdojochi.models import Mentor, Student


def afterRegister(sender, user, request, **kwargs):

    print 'ROLE'
    print request.POST.get('role')

    role = request.POST.get('role')

    if role:
        if role == 'mentor':
            mentor = Mentor(user=user)
            mentor.save()

        if role == 'student':
            student = Student(user=user)
            student.save()

        user.role = role
        user.save()

user_registered.connect(afterRegister)
