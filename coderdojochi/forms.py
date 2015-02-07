from django import forms
from django.forms import Form, ModelForm
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from coderdojochi.models import Mentor, Guardian, Student

import html5.forms.widgets as html5_widgets

class MentorForm(ModelForm):

    bio = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Short Bio','class': 'form-control', 'rows': 5}), label='Short Bio')

    class Meta:
        model = Mentor
        fields = ('bio',)

class GuardianForm(ModelForm):

    phone = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Phone Number','class': 'form-control'}), label='Phone Number')
    zip = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Zip Code','class': 'form-control'}), label='Zip Code')

    class Meta:
        model = Guardian
        fields = ('phone','zip',)

class StudentForm(ModelForm):

    first_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Jane','class': 'form-control'}), label='First Name')
    last_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Doe','class': 'form-control'}), label='Last Name')
    gender = forms.CharField(widget=forms.TextInput(attrs={'placeholder': '','class': 'form-control'}), label='Gender')
    birthday = forms.CharField(widget=html5_widgets.DateInput(attrs={'class': 'form-control', 'min': '1995-01-01', 'max': '2010-01-01'}))
    medications = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'List any medications currently being taken.','class': 'form-control hidden', 'rows': 5}), label=format_html(u"{0} {1}", "Medications", mark_safe('<span class="btn btn-xs btn-link js-expand-student-form">expand</span>')), required=False)
    medical_conditions = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'List any medical conditions.','class': 'form-control hidden', 'rows': 5}), label=format_html(u"{0} {1}", "Medical Conditions", mark_safe('<span class="btn btn-xs btn-link js-expand-student-form">expand</span>')), required=False)
    photo_release = forms.BooleanField(widget=forms.CheckboxInput(attrs={'required': 'required'}), label="I hereby give permission to CoderDojoChi to use the student's image and/or likeness in promotional materials.")
    consent = forms.BooleanField(widget=forms.CheckboxInput(attrs={'required': 'required'}), label="I hereby give consent for the student signed up above to participate in CoderDojoChi.")

    class Meta:
        model = Student
        exclude = ('guardian', 'created_at', 'updated_at', 'active')

class ContactForm(forms.Form):

    name = forms.CharField(max_length=100, label='Your name')
    email = forms.EmailField(max_length=200, label='Your email address')
    body = forms.CharField(widget=forms.Textarea, label='Your message')
    human = forms.CharField(max_length=100, label=False, required=False)

