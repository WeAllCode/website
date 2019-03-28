from django import forms

import html5.forms.widgets as html5_widgets

from coderdojochi.models import CDCUser, Guardian, Mentor, RaceEthnicity


class CDCModelForm(forms.ModelForm):
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
                if isinstance(field, forms.FileField):
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

            except forms.ValidationError as e:
                self.add_error(name, e)

    class Meta:
        model = CDCUser
        fields = ('first_name', 'last_name')


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
        widget=forms.DateInput(
            attrs={
                'class': 'form-control'
            }
        ),
        required=True
    )

    class Meta:
        model = Guardian
        fields = ('phone', 'zip', 'gender', 'race_ethnicity', 'birthday')


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
