# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-07-11 07:48
from __future__ import unicode_literals

import app.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0014_auto_20160630_1526'),
    ]

    operations = [
        migrations.AlterField(
            model_name='biomsearchjob',
            name='biom_file',
            field=models.FileField(blank=True, null=True, upload_to=app.models.upload_path_handler),
        ),
    ]
