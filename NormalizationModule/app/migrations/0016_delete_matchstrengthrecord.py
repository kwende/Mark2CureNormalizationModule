# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-10-03 19:40
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0015_ontologymatchqualityconsensusreasonconsensus'),
    ]

    operations = [
        migrations.DeleteModel(
            name='MatchStrengthRecord',
        ),
    ]
