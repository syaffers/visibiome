# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2017-02-20 14:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0007_auto_20170215_1526'),
    ]

    operations = [
        migrations.AlterField(
            model_name='biomsearchjob',
            name='status',
            field=models.IntegerField(choices=[(-1, b'Stopped'), (1, b'Queued'), (0, b'Validating'), (2, b'Processing'), (3, b'Re-running'), (10, b'Completed')], default=0),
        ),
    ]
