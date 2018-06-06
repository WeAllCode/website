# Generated by Django 1.9.6 on 2016-08-17 23:13


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coderdojochi', '0004_auto_20160718_2044'),
    ]

    operations = [
        migrations.AlterField(
            model_name='equipment',
            name='force_update_on_next_boot',
            field=models.BooleanField(default=False, verbose_name=b'Force Update'),
        ),
        migrations.AlterField(
            model_name='equipment',
            name='last_system_update',
            field=models.DateTimeField(blank=True, null=True, verbose_name=b'Last Update'),
        ),
        migrations.AlterField(
            model_name='equipment',
            name='last_system_update_check_in',
            field=models.DateTimeField(blank=True, null=True, verbose_name=b'Last Check In'),
        ),
    ]
