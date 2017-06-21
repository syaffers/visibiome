# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2017-06-10 19:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0014_auto_20170610_2315'),
    ]

    operations = [
        migrations.AlterField(
            model_name='biomsearchjob',
            name='taxonomy_levels',
            field=models.ManyToManyField(default=[b'phylum', b'class', b'genus'], max_length=3, to='app.TaxonomyLevelChoice'),
        ),
    ]