"""Mark the header link for the current section with aria-current="page"."""

from django import template
from django.urls import NoReverseMatch
from django.urls import reverse
from django.utils.encoding import escape_uri_path
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def nav_current(context, viewname):
    """Return ' aria-current="page"' when the request is in this view's section.

    A link is current when the request path is the view's path or below it, so
    /programs/summer-camps/ marks Programs. Unlike django-active-link 0.3.0, a
    request for "/" doesn't mark every link (it also matched path.startswith("/")).
    """
    request = context.get("request")
    if request is None:
        return ""
    try:
        path = reverse(viewname)
    except NoReverseMatch:
        return ""
    if path != "/" and escape_uri_path(request.path).startswith(path):
        return mark_safe(' aria-current="page"')
    return ""
