from django import forms


class DonateForm(forms.Form):
    # first_name = forms.CharField()
    # last_name = forms.CharField()
    name = forms.CharField()
    email = forms.EmailField()
    amount = forms.DecimalField()
