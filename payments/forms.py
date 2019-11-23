from django import forms


class DonateForm(forms.Form):
    name = forms.CharField()
    email = forms.EmailField()
    amount = forms.DecimalField(
        widget=forms.TextInput(
            attrs={
                'class': 'input-group-field',
                'inputmode': 'decimal',
                'pattern': '[0-9.]+'
                }
            )
        )


class PaymentForm(forms.Form):
    name = forms.CharField()
    email = forms.EmailField()
    amount = forms.DecimalField()
