# Generated by Django 3.1.2 on 2021-01-15 22:24

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coderdojochi', '0035_auto_20200811_2046'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cdcuser',
            name='first_name',
            field=models.CharField(blank=True, max_length=150, verbose_name='first name'),
        ),
        migrations.AlterField(
            model_name='course',
            name='maximum_age',
            field=models.IntegerField(default=18, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)]),
        ),
        migrations.AlterField(
            model_name='guardian',
            name='birthday',
            field=models.DateField(null=True),
        ),
        migrations.AlterField(
            model_name='mentor',
            name='birthday',
            field=models.DateField(null=True),
        ),
        migrations.AlterField(
            model_name='student',
            name='birthday',
            field=models.DateField(),
        ),
    ]
