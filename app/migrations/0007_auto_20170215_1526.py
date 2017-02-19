# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2017-02-15 11:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0006_biomsample'),
    ]

    operations = [
        migrations.AddField(
            model_name='biomsearchjob',
            name='analysis_type',
            field=models.IntegerField(choices=[(1, b'Bray Curtis'), (2, b'GNAT/UniFrac'), (3, b'Hierarchical Representatives/UniFrac')], default=2),
        ),
        migrations.AlterField(
            model_name='biomsearchjob',
            name='error_code',
            field=models.IntegerField(choices=[(0, b'No errors.'), (1, b'File/text content has errors. Check JSON/TSV content.'), (2, b'Too many samples, only up to 10 samples allowed.'), (3, b'Duplicate observation IDs.'), (-1, b'Error opening uploaded file. Contact site admin.'), (4, b'Some OTUs do not exist in the database. Check that the OTU IDs are generated by GreenGenes using closed reference.'), (5, b'Non-GreenGenes IDs detected. Please ensure your OTU IDs are formatted as GreenGenes integers (i.e. 1991307) and not prepended or appended by other strings (i.e. OTU_1991307, 1991307OTU).'), (6, b'An error occurred. This may be a problem with the system. Try again or contact site admin.')], default=0),
        ),
    ]