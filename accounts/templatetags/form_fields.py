"""Widget attrs that django-bootstrap3 used to add; the markup is in account/_field.html."""

from django import forms
from django import template
from django.utils.html import strip_tags

register = template.Library()

# Widgets that get the label as their placeholder (bootstrap3's is_widget_with_placeholder).
PLACEHOLDER_WIDGETS = (
    forms.TextInput,
    forms.Textarea,
    forms.NumberInput,
    forms.EmailInput,
    forms.URLInput,
    forms.PasswordInput,
)
# Widgets that never get the form-control class in bootstrap mode.
NO_FORM_CONTROL = (
    forms.CheckboxInput,
    forms.RadioSelect,
    forms.CheckboxSelectMultiple,
    forms.FileInput,
)


@register.filter
def render_widget(field, bootstrap=False):  # noqa: FBT002 (template filters take one positional arg)
    """Render a bound field's widget with a label placeholder and a help-text title.

    With bootstrap=True (dashboard pages that still load Bootstrap CSS) the
    widget also gets the form-control class.
    """
    widget = field.field.widget
    attrs = {}
    if bootstrap and not isinstance(widget, NO_FORM_CONTROL):
        classes = [
            c for c in widget.attrs.get("class", "").split() if c != "form-control"
        ]
        attrs["class"] = " ".join(["form-control", *classes])
    if (
        field.label
        and isinstance(widget, PLACEHOLDER_WIDGETS)
        and "placeholder" not in widget.attrs
    ):
        attrs["placeholder"] = field.label
    help_text = strip_tags(field.help_text)
    if (
        help_text
        and not isinstance(widget, forms.CheckboxInput)
        and "title" not in widget.attrs
    ):
        attrs["title"] = help_text
    return field.as_widget(attrs=attrs)
