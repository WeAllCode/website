# Generated by Django 2.2.9 on 2020-01-02 04:30

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coderdojochi', '0034_auto_20200101_2225'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='maximum_age',
            field=models.IntegerField(default=17, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)]),
        ),
        migrations.AddField(
            model_name='course',
            name='minimum_age',
            field=models.IntegerField(default=7, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)]),
        ),
    ]
