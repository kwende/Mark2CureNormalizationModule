# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-10-02 21:50
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0014_auto_20171002_1630'),
    ]

    operations = [
        migrations.CreateModel(
            name='OntologyMatchQualityConsensusReasonConsensus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Reason', models.IntegerField()),
                ('MatchQualityConsensus', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='app.OntologyMatchQualityConsensus')),
            ],
        ),
    ]