from django import forms
from django.conf import settings
from django.contrib import messages
from django.forms import Form

from coderdojochi.util import email


class GridForm(Form):
    def as_grid(self):
        return ''.join([self.field_html(f[0], f[1]) for f in self.widths])

    def field_html(self, field_name, field_classes):
        field = self[field_name]
        return f"<div class='cell {field_classes}'>{field.label_tag()}{field}{field.errors}</div>"


class ContactForm(GridForm):
    widths = (
        ('name', 'small-6'),
        ('email', 'small-6'),
        ('interest', 'small-6'),
        ('phone', 'small-6'),
        ('message', 'small-12'),
        ('human', 'edih'),
    )

    human = forms.CharField(
        max_length=100,
        label=False,
        required=False
    )

    name = forms.CharField(
        max_length=100,
        label='Full Name',
    )

    email = forms.EmailField(
        max_length=200,
        label='Email Address',
        widget=forms.TextInput(attrs={'placeholder': 'email@example.com'})
    )

    interest = forms.ChoiceField(
        choices=[
            ('volunteer', 'Volunteer'),
            ('donate', 'Donate'),
            ('sponsor', 'Sponsor'),
            ('collaborate', 'Collaborate'),
            ('other', 'Other'),
        ],
        label='Topic of Interest'
    )

    phone = forms.CharField(
        max_length=20,
        label='Phone Number',
        widget=forms.TextInput(attrs={'type': 'tel', 'placeholder': '+1 555 555-5555'})
    )

    message = forms.CharField(
        label='Message',
        widget=forms.Textarea(attrs={'placeholder': 'Enter your message'})
    )

    def send_email(self):
        # send email using the self.cleaned_data dictionary
        data = self.cleaned_data
        email(
            subject=f"{data['name']} | We All Code Contact Form",
            recipients=[settings.CONTACT_EMAIL],
            reply_to=[f"{data['name']}<{data['email']}>"],
            template_name='contact-email',
            merge_global_data={
                'interest': data['interest'],
                'message': data['message']
            },
        )
