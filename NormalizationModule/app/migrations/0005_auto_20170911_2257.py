# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-09-12 03:57
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_auto_20170911_2136'),
    ]

    operations = [
        migrations.CreateModel(
            name='OntologyMatchQualityReason',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.AddField(
            model_name='ontologymatch',
            name='QualityConsensus',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='ontologymatch',
            name='ReasonConsensus',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='ontologymatchqualityreason',
            name='QualityConsensus',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.OntologyMatch'),
        ),
    ]
