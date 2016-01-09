# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coderdojochi', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RaceEthnicity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('race_ethnicity', models.CharField(max_length=255)),
                ('visible', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='student',
            name='race_ethnicity',
            field=models.ManyToManyField(to='coderdojochi.RaceEthnicity', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='student',
            name='school_name',
            field=models.CharField(max_length=255, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='student',
            name='school_type',
            field=models.CharField(max_length=255, null=True),
            preserve_default=True,
        ),
    ]
