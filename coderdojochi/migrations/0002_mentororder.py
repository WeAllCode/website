# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coderdojochi', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MentorOrder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=True)),
                ('ip', models.CharField(max_length=255, null=True, blank=True)),
                ('check_in', models.DateTimeField(null=True, blank=True)),
                ('alternate_guardian', models.CharField(max_length=255, null=True, blank=True)),
                ('affiliate', models.CharField(max_length=255, null=True, blank=True)),
                ('order_number', models.CharField(max_length=255, null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('week_reminder_sent', models.BooleanField(default=False)),
                ('day_reminder_sent', models.BooleanField(default=False)),
                ('guardian', models.ForeignKey(to='coderdojochi.Guardian')),
                ('session', models.ForeignKey(to='coderdojochi.Session')),
                ('student', models.ForeignKey(to='coderdojochi.Student')),
            ],
            options={
                'verbose_name': 'mentor order',
                'verbose_name_plural': 'mentor orders',
            },
            bases=(models.Model,),
        ),
    ]
