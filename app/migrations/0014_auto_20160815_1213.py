# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-08-15 08:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0013_auto_20160814_1645'),
    ]

    operations = [
        migrations.AlterField(
            model_name='biomsearchjob',
            name='sample_name',
            field=models.CharField(default=b'(no name)', max_length=100),
        ),
    ]
