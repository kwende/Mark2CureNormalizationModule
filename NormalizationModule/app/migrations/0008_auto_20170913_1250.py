# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-09-13 17:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0007_ontologymatch_conveniencematchstring'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ontologymatch',
            name='OntologyRecordId',
            field=models.CharField(max_length=128),
        ),
    ]
