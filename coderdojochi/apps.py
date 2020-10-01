from django.apps import AppConfig


class CoderDojoChiConfig(AppConfig):
    name = 'coderdojochi'
    verbose_name = "CoderDojoChi"

    def ready(self):
        import coderdojochi.signals_handlers
pip install django
