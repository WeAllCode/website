from django import forms
from django.forms import Form, ModelForm
from coderdojochi.models import Mentor

class MentorForm(ModelForm):
    class Meta:
        model = Mentor
        fields = ('first_name', 'last_name', 'bio')
