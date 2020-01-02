# Generated by Django 2.2.9 on 2020-01-03 21:25

import datetime
import django.core.validators
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    replaces = [('coderdojochi', '0029_course_duration'), ('coderdojochi', '0030_auto_20200101_2217'), ('coderdojochi', '0031_auto_20200101_2218'), ('coderdojochi', '0032_auto_20200101_2221'), ('coderdojochi', '0033_auto_20200101_2222'), ('coderdojochi', '0034_auto_20200101_2225'), ('coderdojochi', '0035_auto_20200101_2230'), ('coderdojochi', '0036_auto_20200101_2238'), ('coderdojochi', '0037_auto_20200101_2239'), ('coderdojochi', '0038_auto_20200102_1332'), ('coderdojochi', '0039_auto_20200102_1655'), ('coderdojochi', '0040_auto_20200102_1801')]

    dependencies = [
        ('coderdojochi', '0028_rename_race_ethnicity'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='duration',
            field=models.DurationField(default=datetime.timedelta(seconds=10800), help_text='HH:MM:ss'),
        ),
        migrations.RenameField(
            model_name='session',
            old_name='end_date',
            new_name='old_end_date',
        ),
        migrations.RenameField(
            model_name='session',
            old_name='mentor_end_date',
            new_name='old_mentor_end_date',
        ),
        migrations.RenameField(
            model_name='session',
            old_name='mentor_start_date',
            new_name='old_mentor_start_date',
        ),
        migrations.AlterField(
            model_name='session',
            name='old_end_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='session',
            name='old_mentor_end_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='session',
            name='old_mentor_start_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
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
        migrations.AlterField(
            model_name='session',
            name='cost',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
        migrations.RenameField(
            model_name='equipment',
            old_name='aquisition_date',
            new_name='acquisition_date',
        ),
        migrations.AddField(
            model_name='equipmenttype',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='equipmenttype',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='location',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='location',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='partnerpasswordaccess',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='raceethnicity',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='raceethnicity',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.RenameField(
            model_name='session',
            old_name='max_cost',
            new_name='maximum_cost',
        ),
        migrations.RenameField(
            model_name='session',
            old_name='min_cost',
            new_name='minimum_cost',
        ),
        migrations.RenameField(
            model_name='session',
            old_name='max_age_limitation',
            new_name='override_maximum_age_limitation',
        ),
        migrations.AlterField(
            model_name='session',
            name='override_maximum_age_limitation',
            field=models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)]),
        ),
        migrations.AlterField(
            model_name='session',
            name='override_maximum_age_limitation',
            field=models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name='Max Age'),
        ),
        migrations.RenameField(
            model_name='session',
            old_name='min_age_limitation',
            new_name='override_minimum_age_limitation',
        ),
        migrations.AlterField(
            model_name='session',
            name='override_minimum_age_limitation',
            field=models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)]),
        ),
        migrations.AlterField(
            model_name='session',
            name='override_minimum_age_limitation',
            field=models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name='Min Age'),
        ),
        migrations.AlterField(
            model_name='session',
            name='gender_limitation',
            field=models.CharField(blank=True, choices=[('male', 'Male'), ('female', 'Female')], help_text='Limits the class to be only one gender.', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='session',
            name='override_maximum_age_limitation',
            field=models.IntegerField(blank=True, help_text='Only update this if different from the default.', null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name='Max Age'),
        ),
        migrations.AlterField(
            model_name='session',
            name='override_minimum_age_limitation',
            field=models.IntegerField(blank=True, help_text='Only update this if different from the default.', null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name='Min Age'),
        ),
    ]
