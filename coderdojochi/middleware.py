import logging
import traceback

from django.conf import settings
from django.shortcuts import render

from sentry_sdk import last_event_id

logger = logging.getLogger(__name__)


class HandleExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        logger.exception(traceback.format_exc(limit=3))

        if settings.DEBUG:
            raise exception

        return render(
            request, "500.html", {"sentry_event_id": last_event_id(), "SENTRY_DSN": settings.SENTRY_DSN,}, status=500
        )
