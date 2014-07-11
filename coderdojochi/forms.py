from django import forms
from django.forms import Form, ModelForm
from coderdojochi.models import Mentor, Guardian, Student

class MentorForm(ModelForm):

    first_name = forms.CharField(label='', widget=forms.TextInput(attrs={'placeholder': 'First Name','class': 'form-control'}))
    last_name = forms.CharField(label='', widget=forms.TextInput(attrs={'placeholder': 'Last Name','class': 'form-control'}))
    bio = forms.CharField(label='', widget=forms.Textarea(attrs={'placeholder': 'Short Bio','class': 'form-control', 'rows': 5}))

    class Meta:
        model = Mentor
        fields = ('first_name', 'last_name', 'bio')


class GuardianForm(ModelForm):

    first_name = forms.CharField(label='', widget=forms.TextInput(attrs={'placeholder': 'First Name','class': 'form-control'}))
    last_name = forms.CharField(label='', widget=forms.TextInput(attrs={'placeholder': 'Last Name','class': 'form-control'}))
    phone = forms.CharField(label='', widget=forms.TextInput(attrs={'placeholder': 'Phone Number','class': 'form-control'}))

    class Meta:
        model = Guardian
        fields = ('first_name', 'last_name', 'phone')

class StudentForm(ModelForm):

    first_name = forms.CharField(label='', widget=forms.TextInput(attrs={'placeholder': 'First Name','class': 'form-control'}))
    last_name = forms.CharField(label='', widget=forms.TextInput(attrs={'placeholder': 'Last Name','class': 'form-control'}))
    gender = forms.CharField(label='', widget=forms.TextInput(attrs={'placeholder': 'Gender','class': 'form-control'}))

    class Meta:
        model = Student
        fields = ('first_name', 'last_name', 'gender')
