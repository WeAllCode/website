from django.views.generic import View, TemplateView, FormView, UpdateView
from coderdojochi.models import (Student, Guardian)
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from coderdojochi.forms import StudentForm
from django.core.urlresolvers import reverse_lazy

class StudentDetailView(UpdateView):
    form_class = StudentForm
    template_name = "student-detail.html"
    model = Student
    pk_url_kwarg = 'student_id'
    success_url = reverse_lazy('dojo')

    
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
      return super(StudentDetailView, self).dispatch(*args, **kwargs)

