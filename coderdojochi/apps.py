# -*- coding: utf-8 -*-

from django.apps import AppConfig
from django.conf import settings


class CoderDojoChiConfig(AppConfig):
    name = 'coderdojochi'
    verbose_name = settings.SITE_NAME

    def ready(self):
        import coderdojochi.signals_handlers
