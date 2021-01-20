import re

from django import template
from django.urls import reverse

register = template.Library()


@register.simple_tag(takes_context=True)
def active(context, pattern_or_urlname, css_class="active"):
    try:
        pattern = "^" + reverse(pattern_or_urlname)
    except NoReverseMatch:
        pattern = pattern_or_urlname

    if re.search(pattern, context["request"].path):
        return css_class
    else:
        return ""
