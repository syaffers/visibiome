# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-03-19 08:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0009_auto_20160315_1829'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='biomsearchjob',
            name='input_file',
        ),
        migrations.AddField(
            model_name='biomsearchjob',
            name='otu_text',
            field=models.TextField(default=None),
        ),
        migrations.AlterField(
            model_name='biomsearchjob',
            name='criteria',
            field=models.CharField(choices=[('all', 'All Ecosystem'), ('animal', 'Animal/Human'), ('anthropogenic', 'Anthropogenic'), ('freshwater', 'Freshwater'), ('marine', 'Marine'), ('soil', 'Soil'), ('plant', 'Plant'), ('geothermal', 'Geothermal'), ('biofilm', 'Biofilm')], default='all', max_length=200),
        ),
    ]
