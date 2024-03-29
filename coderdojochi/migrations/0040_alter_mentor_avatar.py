# Generated by Django 4.1.7 on 2023-04-02 14:56

import coderdojochi.models.mentor
from django.db import migrations
import stdimage.models


class Migration(migrations.Migration):

    dependencies = [
        ('coderdojochi', '0039_auto_20210611_1044'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mentor',
            name='avatar',
            field=stdimage.models.StdImageField(blank=True, force_min_size=False, upload_to=coderdojochi.models.mentor.generate_filename, variations={'thumbnail': {'crop': True, 'height': 500, 'width': 500}}),
        ),
    ]
