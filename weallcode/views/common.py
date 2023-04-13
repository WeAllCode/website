from django.conf import settings
from django.contrib.auth import get_user_model

from meta.views import MetadataMixin
from sentry_sdk import capture_message

User = get_user_model()


def page_not_found_view(*args, **kwargs):
    print("page_not_found_view")

    options = {}

    if settings.SENTRY_DSN:
        capture_message("Page not found!", level="error")
        options["sentry_event_id"] = last_event_id()
        options["SENTRY_DSN"] = settings.SENTRY_DSN

    return render(
        request,
        "404.html",
        options,
        status=404,
    )


class DefaultMetaTags(MetadataMixin):
    title = None
    description = (
        "We All Code is volunteer run nonprofit organization that teaches web,"
        " game, and app development to youth ages 7 to 17 free of charge."
    )
    image = "weallcode/images/photos/real-coding-skills.jpg"
    twitter_card = "summary_large_image"
    twitter_creator = "@weallcode"
    twitter_site = "@weallcode"
