# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-09-30 23:00
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0008_auto_20170913_1250'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ontologymatchqualitysubmission',
            name='SubmittedOn',
            field=models.DateTimeField(blank=True, default=datetime.datetime.now),
        ),
    ]