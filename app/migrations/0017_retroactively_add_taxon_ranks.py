# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2017-06-19 22:35
from __future__ import unicode_literals

from django.db import migrations

def add_taxonomy_ranks(apps, schema_editor):
    BiomSearchJob = apps.get_model('app', 'BiomSearchJob')
    TaxonomyRankChoice = apps.get_model('app', 'TaxonomyRankChoice')
    for job in BiomSearchJob.objects.all():
        for choice in TaxonomyRankChoice.objects.filter(taxon_rank_proper_name__in=["phylum", "family", "genus"]):
            job.taxonomy_ranks.add(choice)

class Migration(migrations.Migration):

    dependencies = [
        ('app', '0016_auto_20170620_0234'),
    ]

    operations = [
        migrations.RunPython(add_taxonomy_ranks, reverse_code=migrations.RunPython.noop)
    ]
