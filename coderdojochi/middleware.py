from django.conf import settings
from django.shortcuts import render
import logging
import traceback
from urllib3.exceptions import HTTPError


logger = logging.getLogger(__name__)


class HandleExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        logger.exception(traceback.format_exc(limit=3))
        return render(request, '500.html')
