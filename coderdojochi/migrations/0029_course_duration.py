# Generated by Django 2.2.9 on 2020-01-02 04:16

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coderdojochi', '0028_rename_race_ethnicity'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='duration',
            field=models.DurationField(default=datetime.timedelta(0, 10800), help_text='HH:MM:ss'),
        ),
    ]