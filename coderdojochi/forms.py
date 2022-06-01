from email.policy import default
import re

from django import forms
from django.contrib.auth import get_user_model
from django.core.files.images import get_image_dimensions
from django.forms import FileField, Form, ModelForm, ValidationError
from django.urls import reverse, reverse_lazy
from django.utils import dateformat, timezone
from django.utils.functional import lazy
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.text import format_lazy

import html5.forms.widgets as html5_widgets
from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV3
from dateutil.relativedelta import relativedelta

from coderdojochi.models import CDCUser, Donation, Guardian, Mentor, RaceEthnicity, Session, Student


class CDCForm(Form):
    # strip leading or trailing whitespace
    def _clean_fields(self):
        for name, field in list(self.fields.items()):
            # value_from_datadict() gets the data from the data dictionaries.
            # Each widget type knows how to retrieve its own data, because some
            # widgets split data over several HTML fields.
            value = field.widget.value_from_datadict(self.data, self.files, self.add_prefix(name))

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
            value = field.widget.value_from_datadict(self.data, self.files, self.add_prefix(name))

            try:
                if isinstance(field, FileField):
                    initial = self.initial.get(name, field.initial)
                    value = field.clean(value, initial)
                else:
                    if isinstance(value, str):
                        # regex normalizes carriage return
                        # and cuts them to two at most
                        value = re.sub(r"\r\n", "\n", value)
                        value = re.sub(r"\n{3,}", "\n\n", value)
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
        fields = (
            "first_name",
            "last_name",
        )


class SignupForm(forms.Form):
    first_name = forms.CharField(
        max_length=30,
    )

    last_name = forms.CharField(
        max_length=30,
    )

    captcha = ReCaptchaField(
        label="",
        widget=ReCaptchaV3,
    )

    field_order = [
        "first_name",
        "last_name",
        "email",
        "password1",
        "password2",
    ]

    class Meta:
        model = get_user_model()

    def signup(self, request, user):
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.save()


class MentorForm(CDCModelForm):
    bio = forms.CharField(
        required=False,
        label="Short Bio",
        widget=forms.Textarea(
            attrs={
                "placeholder": "Short Bio",
                "class": "form-control",
                "rows": 4,
            },
        ),
    )

    gender = forms.CharField(
        required=True,
        label="Gender",
        widget=forms.TextInput(
            attrs={
                "placeholder": "",
                "class": "form-control",
            },
        ),
    )

    race_ethnicity = forms.ModelMultipleChoiceField(
        required=True,
        widget=forms.CheckboxSelectMultiple,
        queryset=RaceEthnicity.objects.filter(is_visible=True),
    )

    birthday = forms.CharField(
        required=True,
        widget=html5_widgets.DateInput(
            attrs={
                "class": "form-control",
            },
        ),
    )

    work_place = forms.CharField(
        required=False,
        label="Work Place",
        widget=forms.TextInput(
            attrs={
                "placeholder": "",
                "class": "form-control",
            },
        ),
    )

    phone = forms.CharField(
        required=False,
        label="Phone",
        widget=forms.TextInput(
            attrs={
                "placeholder": "",
                "class": "form-control",
            },
        ),
    )

    home_address = forms.CharField(
        required=False,
        label="Home Address",
        widget=forms.TextInput(
            attrs={
                "placeholder": "",
                "class": "form-control",
            },
        ),
    )

    class Meta:
        model = Mentor
        fields = (
            "bio",
            "avatar",
            "gender",
            "race_ethnicity",
            "birthday",
            "phone",
            "home_address",
            "work_place",
        )

    def clean_avatar(self):
        avatar = self.cleaned_data["avatar"]

        max_width = max_height = 1000
        min_width = min_height = 500
        valid_image_types = (
            "jpeg",
            "pjpeg",
            "gif",
            "png",
        )
        max_file_size = 2000 * 1024  # 2MB

        if avatar is None:
            return avatar

        try:
            w, h = get_image_dimensions(avatar)

            if w is None or h is None:
                raise forms.ValidationError("Could not determine image dimensions.")

            # validate dimensions

            if w > max_width or h > max_height:
                raise forms.ValidationError(f"Please use an image that is {max_width} 𐄂 {max_height}px or smaller.")

            if w < min_width or h < min_height:
                raise forms.ValidationError(f"Please use an image that is {min_width} 𐄂 {min_height}px or larger.")

            # validate content type
            main, sub = avatar.content_type.split("/")
            if not (main == "image" and sub in valid_image_types):
                raise forms.ValidationError("Please use a JPEG, GIF or PNG image.")

            # validate file size
            if len(avatar) > max_file_size:
                raise forms.ValidationError("Avatar file size may not exceed 2MB.")

        except AttributeError:
            """
            Handles case when we are updating the user profile
            and do not supply a new avatar
            """

        return avatar


class GuardianForm(CDCModelForm):
    phone = forms.CharField(
        required=True,
        label="Parent's Phone Number",
        # help_text="Please enter the parent's phone number.",
        widget=forms.TextInput(
            attrs={
                "placeholder": "000-000-0000",
                "class": "form-control",
                "inputmode": "tel",
            }
        ),
    )

    zip = forms.CharField(
        required=True,
        label="Parent's Zip Code",
        widget=forms.TextInput(
            attrs={
                "placeholder": "60606",
                "class": "form-control",
                "inputmode": "numeric",
            }
        ),
    )

    gender = forms.CharField(
        required=True,
        label="Parent's Gender",
        widget=forms.TextInput(
            attrs={
                "placeholder": "",
                "class": "form-control",
            }
        ),
    )

    race_ethnicity = forms.ModelMultipleChoiceField(
        required=True,
        label="Parent's Gender",
        # widget=forms.SelectMultiple,
        widget=forms.CheckboxSelectMultiple,
        queryset=RaceEthnicity.objects.filter(is_visible=True),
    )

    birthday = forms.CharField(
        required=True,
        label="Parent's Date of Birth",
        widget=html5_widgets.DateInput(
            attrs={
                "class": "form-control",
            }
        ),
    )

    class Meta:
        model = Guardian
        fields = (
            "phone",
            "zip",
            "gender",
            "birthday",
            "race_ethnicity",
        )


class StudentForm(CDCModelForm):

    PUBLIC = "PU"
    CHARTER = "CH"
    PRIVATE = "PR"
    HOMESCHOOL = "HM"

    SCHOOL_TYPE_CHOICES = [
        (PUBLIC, "Public"),
        (CHARTER, "Charter"),
        (PRIVATE, "Private"),
        (HOMESCHOOL, "Homeschool"),
    ]

    first_name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Jane",
                "class": "form-control",
            },
        ),
        label="First Name",
    )

    last_name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Doe",
                "class": "form-control",
            },
        ),
        label="Last Name",
    )

    gender = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "",
                "class": "form-control",
            },
        ),
        label="Gender",
    )

    school_name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
            },
        ),
        label="School Name",
        required=False,
    )

    school_type = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=SCHOOL_TYPE_CHOICES,
        required=False,
    )

    race_ethnicity = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        queryset=RaceEthnicity.objects.filter(is_visible=True),
        required=False,
    )

    birthday = forms.CharField(
        widget=html5_widgets.DateInput(
            attrs={
                "class": "form-control",
                "min": dateformat.format(timezone.now() - relativedelta(years=19), "Y-m-d"),
                "max": dateformat.format(timezone.now() - relativedelta(years=5), "Y-m-d"),
            }
        ),
    )

    medications = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "placeholder": "List any medications currently being taken.",
                "class": "form-control hidden",
                "rows": 5,
            }
        ),
        label="Medications",
        required=False,
    )

    medical_conditions = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "placeholder": "List any medical conditions.",
                "class": "form-control hidden",
                "rows": 5,
            },
        ),
        label="Medical Conditions",
        required=False,
    )

    photo_release = forms.BooleanField(
        
        widget=forms.CheckboxInput(
            attrs={
                "required": "required",
                "checked": "checked",
            },
        ),
        label=(
            "I hereby give permission to We All Code to use the "
            "student's image and/or likeness in promotional materials."
        ),
    )

    consent = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(
            attrs={
                "required": "required",
                "checked": "checked",
            },
        ),
        label=format_lazy(
            "I hereby give consent for the student signed up above to participate in We All Code as per the "
            '<a href="{0}">terms</a>.',
            reverse_lazy("weallcode-privacy"),
        ),
    )

    class Meta:
        model = Student
        exclude = (
            "guardian",
            "created_at",
            "updated_at",
            "is_active",
        )


class ContactForm(CDCForm):
    name = forms.CharField(
        max_length=100,
        label="Your name",
    )
    email = forms.EmailField(
        max_length=200,
        label="Your email address",
    )
    message = forms.CharField(
        widget=forms.Textarea,
        label="Your message",
    )
    human = forms.CharField(
        max_length=100,
        label=None,
        required=False,
    )


class DonationForm(ModelForm):
    session = forms.ModelChoiceField(
        queryset=Session.objects.all(),
        widget=forms.HiddenInput(),
        required=True,
    )
    user = forms.ModelChoiceField(
        queryset=CDCUser.objects.all(),
        required=True,
    )
    amount = forms.CharField(
        label="Amount (dollars)",
    )

    class Meta:
        model = Donation
        fields = (
            "session",
            "user",
            "amount",
        )
