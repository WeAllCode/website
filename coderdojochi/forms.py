import re

from django import forms
from django.contrib.auth import get_user_model
from django.core.files.images import get_image_dimensions
from django.forms import FileField, Form, ModelForm, ValidationError
from django.utils.html import format_html
from django.utils.safestring import mark_safe

import html5.forms.widgets as html5_widgets
from accounts.forms import CDCModelForm

from coderdojochi.models import CDCUser, Donation, Guardian, Mentor, RaceEthnicity, Session, Student

SCHOOL_TYPE_CHOICES = (
    ("Public", "Public"),
    ("Charter", "Charter"),
    ("Private", "Private"),
    ("Homeschool", "Homeschool")
)


class CDCForm(Form):
    # strip leading or trailing whitespace
    def _clean_fields(self):
        for name, field in list(self.fields.items()):
            # value_from_datadict() gets the data from the data dictionaries.
            # Each widget type knows how to retrieve its own data, because some
            # widgets split data over several HTML fields.
            value = field.widget.value_from_datadict(
                self.data,
                self.files,
                self.add_prefix(name)
            )

            try:
                if isinstance(field, FileField):
                    initial = self.initial.get(name, field.initial)
                    value = field.clean(value, initial)
                else:
                    if isinstance(value, str):
                        value = field.clean(value.strip())
                    else:
                        value = field.clean(value)

                self.cleaned_data[name] = value

                if hasattr(self, f"clean_{name}"):
                    value = getattr(self, f"clean_{name}")()
                    self.cleaned_data[name] = value

            except ValidationError as e:
                self.add_error(name, e)


class SignupForm(forms.Form):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)

    class Meta:
        model = get_user_model()

    def save(self, user):
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()


class StudentForm(CDCModelForm):
    first_name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Jane',
                'class': 'form-control'
            }
        ),
        label='First Name'
    )

    last_name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Doe',
                'class': 'form-control'
            }
        ),
        label='Last Name'
    )

    gender = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'placeholder': '',
                'class': 'form-control'
            }
        ),
        label='Gender'
    )

    school_name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'class': 'form-control'
            }
        ),
        label='School Name',
        required=False
    )

    school_type = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=SCHOOL_TYPE_CHOICES,
        required=False
    )

    race_ethnicity = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        queryset=RaceEthnicity.objects.filter(is_visible=True),
        required=False
    )

    birthday = forms.CharField(
        widget=html5_widgets.DateInput(
            attrs={
                'class': 'form-control'
            }
        )
    )

    medications = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'placeholder': 'List any medications currently being taken.',
                'class': 'form-control hidden',
                'rows': 5
            }
        ),
        label=format_html(
            "{0} {1}",
            "Medications",
            mark_safe(
                '<span class="btn btn-xs btn-link js-expand-student-form">expand</span>'
            )
        ),
        required=False
    )

    medical_conditions = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'placeholder': 'List any medical conditions.',
                'class': 'form-control hidden',
                'rows': 5
            }
        ),
        label=format_html(
            "{0} {1}",
            "Medical Conditions",
            mark_safe(
                '<span class="btn btn-xs btn-link js-expand-student-form">expand</span>'
            )
        ),
        required=False
    )

    photo_release = forms.BooleanField(
        widget=forms.CheckboxInput(
            attrs={
                'required': 'required'
            }
        ),
        label=(
            'I hereby give permission to CoderDojoChi to use the '
            'student\'s image and/or likeness in promotional materials.'
        ),
    )

    consent = forms.BooleanField(
        widget=forms.CheckboxInput(
            attrs={
                'required': 'required'
            }
        ),
        label=(
            'I hereby give consent for the student signed up above to participate in CoderDojoChi as per the '
            f"<a href=\"{{ reverse('privacy') }}\">terms</a>."
        ),
    )

    class Meta:
        model = Student
        exclude = ('guardian', 'created_at', 'updated_at', 'is_active')


class ContactForm(CDCForm):
    name = forms.CharField(max_length=100, label='Your name')
    email = forms.EmailField(max_length=200, label='Your email address')
    message = forms.CharField(widget=forms.Textarea, label='Your message')
    human = forms.CharField(max_length=100, label=False, required=False)


class DonationForm(ModelForm):
    session = forms.ModelChoiceField(
        queryset=Session.objects.all(),
        widget=forms.HiddenInput(),
        required=True
    )
    user = forms.ModelChoiceField(
        queryset=CDCUser.objects.all(),
        required=True
    )
    amount = forms.CharField(label='Amount (dollars)')

    class Meta:
        model = Donation
        fields = ['session', 'user', 'amount']
