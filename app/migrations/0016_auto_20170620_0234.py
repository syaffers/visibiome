# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2017-06-19 22:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0015_auto_20170610_2341'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaxonomyRankChoice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('taxon_rank', models.CharField(max_length=60, verbose_name=b'Taxonomy Chart Rank')),
                ('taxon_rank_proper_name', models.CharField(max_length=60)),
            ],
        ),
        migrations.RemoveField(
            model_name='biomsearchjob',
            name='taxonomy_levels',
        ),
        migrations.DeleteModel(
            name='TaxonomyLevelChoice',
        ),
        migrations.AddField(
            model_name='biomsearchjob',
            name='taxonomy_ranks',
            field=models.ManyToManyField(default=[b'phylum', b'class', b'genus'], max_length=3, to='app.TaxonomyRankChoice'),
        ),
    ]