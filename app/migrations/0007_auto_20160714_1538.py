# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-07-14 11:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0006_auto_20160714_1536'),
    ]

    operations = [
        migrations.AlterField(
            model_name='biomsearchjob',
            name='error_code',
            field=models.IntegerField(choices=[(0, b'No errors.'), (1, b'File/text content has errors. Only JSON or TSV content allowed.'), (2, b'Too many samples, only 1 sample allowed.')], default=0),
        ),
    ]