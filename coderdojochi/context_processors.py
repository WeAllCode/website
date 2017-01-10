# -*- coding: utf-8 -*-

from django.conf import settings


def main_config_processor(request):
    return {
        'SITE_URL': settings.SITE_URL,
        'DEBUG': settings.DEBUG,
        'STATIC_URL': settings.STATIC_URL,
        'CONTACT_EMAIL': settings.CONTACT_EMAIL,
    }
