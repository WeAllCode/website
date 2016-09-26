# -*- coding: utf-8 -*-

from django.apps import AppConfig


class CoderDojoChiConfig(AppConfig):
    name = 'coderdojochi'
    verbose_name = "CoderDojoChi"

    def ready(self):
        import coderdojochi.signals_handlers

