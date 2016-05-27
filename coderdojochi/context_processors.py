# -*- coding: utf-8 -*-

from django.conf import settings


def main_config_processor(request):
    return {
        'SITE_URL': settings.SITE_URL,
        'IS_PRODUCTION': settings.IS_PRODUCTION
    }
