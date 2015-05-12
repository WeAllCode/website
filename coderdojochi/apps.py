from django.apps import AppConfig

class CoderDojoChiConfig(AppConfig):
    name = 'coderdojochi'
    verbose_name = "CoderDojoChi"

    def ready(self):
        import coderdojochi.signals_handlers
        from .models import CDCUser

        CDCUser._meta.get_field_by_name('email')[0]._unique = True
        CDCUser.REQUIRED_FIELDS.remove('email')