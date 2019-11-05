from django.conf import settings


def main_config_processor(request):
    return {
        'DEBUG': settings.DEBUG,
        'SITE_URL': settings.SITE_URL,
        'STATIC_URL': settings.STATIC_URL,
        'CONTACT_EMAIL': settings.CONTACT_EMAIL,
        'SITE_PROTOCOL': settings.META_SITE_PROTOCOL,
        'SITE_DOMAIN': settings.META_SITE_DOMAIN,
        'SITE_NAME': settings.META_SITE_NAME,
    }
