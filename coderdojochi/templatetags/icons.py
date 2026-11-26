"""`{% icon "<name>" %}`: inline a vendored Font Awesome 7 SVG.

Only names in ICONS are accepted; a template never supplies a path.
"""

import re
from functools import lru_cache
from pathlib import Path

from django import template
from django.conf import settings
from django.contrib.staticfiles import finders
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

ICONS = {
    "bars": "vendor/fa-svgs/solid/bars.svg",
    "chevron-right": "vendor/fa-svgs/solid/chevron-right.svg",
    "calendar": "vendor/fa-svgs/solid/calendar.svg",
    "calendar-check": "vendor/fa-svgs/regular/calendar-check.svg",
    "google": "vendor/fa-svgs/brands/google.svg",
    "check": "vendor/fa-svgs/solid/check.svg",
    "graduation-cap": "vendor/fa-svgs/solid/graduation-cap.svg",
    "handshake-angle": "vendor/fa-svgs/solid/handshake-angle.svg",
    "square-check": "vendor/fa-svgs/regular/square-check.svg",
    "circle-exclamation": "vendor/fa-svgs/solid/circle-exclamation.svg",
}

_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_SVG_OPEN_RE = re.compile(r"<svg\b")


@lru_cache(maxsize=len(ICONS))
def _svg(name):
    """Return the SVG markup for an allowlisted name, without its licence comment."""
    if name not in ICONS:
        raise template.TemplateSyntaxError(f"Unknown icon {name!r}")
    path = finders.find(ICONS[name])
    if not path:
        raise template.TemplateSyntaxError(f"icon {name!r}: {ICONS[name]} not found")
    text = _COMMENT_RE.sub("", Path(path).read_text(encoding="utf-8"), count=1)
    text = text.strip()
    if not _SVG_OPEN_RE.match(text):
        raise template.TemplateSyntaxError(f"icon {name!r}: not an <svg> file")
    return text


@register.simple_tag
def icon(name, label=""):
    try:
        svg = _svg(name)
    except template.TemplateSyntaxError:
        if settings.DEBUG:
            raise
        return ""
    if label:
        attrs = format_html(' class="icon" role="img" aria-label="{}"', label)
    else:
        attrs = ' class="icon" aria-hidden="true"'
    return mark_safe(_SVG_OPEN_RE.sub(lambda _: "<svg" + attrs, svg, count=1))  # noqa: S308
