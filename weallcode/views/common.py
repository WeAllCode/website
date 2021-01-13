from collections import defaultdict
from datetime import datetime
from itertools import chain

from django.conf import settings
from django.contrib import messages, sitemaps
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import FormView, TemplateView

from meta.views import MetadataMixin
from sentry_sdk import capture_message

from coderdojochi.models import Course, Mentor, Session

from ..forms import ContactForm
from ..models import AssociateBoardMember, BoardMember, StaffMember

User = get_user_model()


def page_not_found_view(*args, **kwargs):
    print("page_not_found_view")
    capture_message("Page not found!", level="error")

    return render(
        request,
        "404.html",
        {
            "sentry_event_id": last_event_id(),
            "SENTRY_DSN": settings.SENTRY_DSN,
        },
        status=404,
    )


class DefaultMetaTags(MetadataMixin):
    title = None
    description = (
        "We All Code is volunteer run nonprofit organization that teaches web, game, and app development to "
        "youth ages 7 to 17 free of charge."
    )
    image = "weallcode/images/photos/real-coding-skills.jpg"
    twitter_card = "summary_large_image"
    twitter_creator = "@weallcode"
    twitter_site = "@weallcode"
