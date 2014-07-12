from django import forms
from django.forms import Form, ModelForm
from coderdojochi.models import Mentor, Guardian, Student

import html5.forms.widgets as html5_widgets

class MentorForm(ModelForm):

    first_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'First Name','class': 'form-control'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Last Name','class': 'form-control'}))
    bio = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Short Bio','class': 'form-control', 'rows': 5}))

    class Meta:
        model = Mentor
        fields = ('first_name', 'last_name', 'bio')


class GuardianForm(ModelForm):

    first_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'First Name','class': 'form-control'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Last Name','class': 'form-control'}))
    phone = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Phone Number','class': 'form-control'}))

    class Meta:
        model = Guardian
        fields = ('first_name', 'last_name', 'phone')

class StudentForm(ModelForm):

    birthday = forms.CharField(widget=html5_widgets.DateInput(attrs={'placeholder': 'Gender','class': 'form-control'}))
    photo_release = forms.BooleanField(widget=forms.CheckboxInput(attrs={'required': 'required'}), label="Photo Consent", help_text="I hereby give permission to CoderDojoChi to use the student's image and/or likeness in promotional materials.")
    consent = forms.BooleanField(widget=forms.CheckboxInput(attrs={'required': 'required'}), label="General Consent", help_text="I hereby give consent for the student signed up above to participate in CoderDojoChi.")

    class Meta:
        model = Student
        exclude = ('guardian', 'created_at', 'updated_at', 'active')
