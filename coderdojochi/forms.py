import re

from django import forms
from django.contrib.auth import get_user_model
from django.core.files.images import get_image_dimensions
from django.forms import FileField, Form, ModelForm, ValidationError
from django.utils.html import format_html
from django.utils.safestring import mark_safe

import html5.forms.widgets as html5_widgets

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


class CDCModelForm(ModelForm):
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
                        # regex normalizes carriage return
                        # and cuts them to two at most
                        value = re.sub(r'\r\n', '\n', value)
                        value = re.sub(r'\n{3,}', '\n\n', value)
                        value = field.clean(value.strip())
                    else:
                        value = field.clean(value)

                self.cleaned_data[name] = value

                if hasattr(self, f"clean_{name}"):
                    value = getattr(self, f"clean_{name}")()
                    self.cleaned_data[name] = value

            except ValidationError as e:
                self.add_error(name, e)

    class Meta:
        model = CDCUser
        fields = ('first_name', 'last_name')


class SignupForm(forms.Form):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)

    class Meta:
        model = get_user_model()

    def save(self, user):
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()


class MentorForm(CDCModelForm):
    bio = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'placeholder': 'Short Bio',
                'class': 'form-control',
                'rows': 4
            }
        ),
        label='Short Bio',
        required=False
    )

    gender = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'placeholder': '',
                'class': 'form-control'
            }
        ),
        label='Gender',
        required=True
    )

    race_ethnicity = forms.ModelMultipleChoiceField(
        widget=forms.SelectMultiple,
        queryset=RaceEthnicity.objects.filter(is_visible=True),
        required=True
    )

    birthday = forms.CharField(
        widget=html5_widgets.DateInput(
            attrs={
                'class': 'form-control'
            }
        ),
        required=True
    )

    work_place = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'placeholder': '',
                'class': 'form-control'
            }
        ),
        label='Work Place',
        required=False
    )

    phone = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'placeholder': '',
                'class': 'form-control'
            }
        ),
        label='Phone',
        required=False
    )

    home_address = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'placeholder': '',
                'class': 'form-control'
            }
        ),
        label='Home Address',
        required=False
    )

    class Meta:
        model = Mentor
        fields = ('bio', 'avatar', 'gender', 'race_ethnicity', 'birthday', 'phone', 'home_address', 'work_place')

    def clean_avatar(self):
        avatar = self.cleaned_data['avatar']

        if avatar is None:
            return avatar

        try:
            w, h = get_image_dimensions(avatar)

            # validate dimensions
            max_width = max_height = 1000
            if w > max_width or h > max_height:
                raise forms.ValidationError(
                    f'Please use an image that is {max_width} x {max_height}px or smaller.'
                )

            min_width = min_height = 500
            if w < min_width or h < min_height:
                raise forms.ValidationError(
                    f'Please use an image that is {min_width} x {min_height}px or larger.'
                )

            # validate content type
            main, sub = avatar.content_type.split('/')
            if (
                not (
                    main == 'image' and
                    sub in ['jpeg', 'pjpeg', 'gif', 'png']
                )
            ):
                raise forms.ValidationError(
                    'Please use a JPEG, GIF or PNG image.'
                )

            # validate file size
            if len(avatar) > (2000 * 1024):
                raise forms.ValidationError(
                    'Avatar file size may not exceed 2MB.'
                )

        except AttributeError:
            """
            Handles case when we are updating the user profile
            and do not supply a new avatar
            """
            pass

        return avatar


class GuardianForm(CDCModelForm):
    phone = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Phone Number',
                'class': 'form-control'
            }
        ),
        label='Phone Number'
    )

    zip = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Zip Code',
                'class': 'form-control'
            }
        ),
        label='Zip Code'
    )

    gender = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'placeholder': '',
                'class': 'form-control'
            }
        ),
        label='Gender',
        required=True
    )

    race_ethnicity = forms.ModelMultipleChoiceField(
        widget=forms.SelectMultiple,
        queryset=RaceEthnicity.objects.filter(is_visible=True),
        required=True
    )

    birthday = forms.CharField(
        widget=html5_widgets.DateInput(
            attrs={
                'class': 'form-control'
            }
        ),
        required=True
    )

    class Meta:
        model = Guardian
        fields = ('phone', 'zip', 'gender', 'race_ethnicity', 'birthday')


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
