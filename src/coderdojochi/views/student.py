from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.core.urlresolvers import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import (
    UpdateView,
)
from coderdojochi.forms import StudentForm
from coderdojochi.models import (
    Student,
    Guardian,
)


class StudentDetailView(SuccessMessageMixin, UpdateView):
    form_class = StudentForm
    template_name = "student-detail.html"
    model = Student
    pk_url_kwarg = 'student_id'
    success_url = reverse_lazy('dojo')
    success_message = "%(first_name)s's information was updated"


    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
      return super(StudentDetailView, self).dispatch(*args, **kwargs)

