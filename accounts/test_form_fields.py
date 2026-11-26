from django import forms
from django.template.loader import render_to_string
from django.test import SimpleTestCase


class FieldForm(forms.Form):
    name = forms.CharField(help_text="Your <b>full</b> name")
    phone = forms.CharField(
        widget=forms.TextInput(attrs={"placeholder": "Phone Number", "class": "own"})
    )
    agree = forms.BooleanField(label='I agree to the <a href="/terms/">terms</a>')

    def clean(self):
        raise forms.ValidationError("Whole form is wrong")


class FormPartialTest(SimpleTestCase):
    """account/_form.html and _field.html replace django-bootstrap3's tags."""

    def render(self, form, **ctx):
        return render_to_string("account/_form.html", {"form": form, **ctx})

    def test_label_becomes_placeholder_unless_the_widget_sets_one(self):
        html = self.render(FieldForm())
        assert 'placeholder="Name"' in html
        assert 'placeholder="Phone Number"' in html
        assert 'placeholder="Phone"' not in html

    def test_help_text_is_shown_and_becomes_a_plain_title(self):
        html = self.render(FieldForm())
        assert 'title="Your full name"' in html
        assert "<div>Your <b>full</b> name</div>" in html

    def test_plain_mode_has_no_bootstrap_classes(self):
        html = self.render(FieldForm({}))
        for name in (
            "form-group",
            "control-label",
            "form-control",
            "help-block",
            "has-error",
            "alert",
        ):
            assert name not in html
        assert '<label for="id_name">Name</label>' in html
        assert "<div>This field is required.</div>" in html
        assert "Whole form is wrong" in html
        assert 'class="own"' in html

    def test_bootstrap_mode_keeps_bootstrap_classes(self):
        html = self.render(FieldForm({}), bootstrap=True)
        assert (
            '<div class="form-group has-error"><label class="control-label" for="id_name">'
            in html
        )
        assert 'class="form-control"' in html
        assert 'class="form-control own"' in html
        assert '<div class="help-block">This field is required.</div>' in html
        assert 'class="alert alert-danger alert-dismissable alert-link"' in html

    def test_checkbox_label_wraps_the_input_and_keeps_its_link(self):
        html = self.render(FieldForm())
        assert '<label for="id_agree"><input type="checkbox"' in html
        assert 'I agree to the <a href="/terms/">terms</a></label>' in html

    def test_single_field(self):
        html = render_to_string("account/_field.html", {"field": FieldForm()["name"]})
        assert html.startswith(
            '<div><label for="id_name">Name</label><input type="text" name="name"'
        )
