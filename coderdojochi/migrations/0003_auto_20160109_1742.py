# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coderdojochi', '0002_auto_20160109_1738'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='raceethnicity',
            options={'verbose_name': 'race ethnicity', 'verbose_name_plural': 'race ethnicities'},
        ),
    ]
