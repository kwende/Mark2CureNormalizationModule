# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-10-02 03:57
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0011_ontologymatchqualityconsensus'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='OntologyMatchQualityReason',
            new_name='OntologyMatchQualityConsensusReason',
        ),
    ]
