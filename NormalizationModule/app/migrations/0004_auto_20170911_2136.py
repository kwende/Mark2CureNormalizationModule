# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-09-12 02:36
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_auto_20170911_2129'),
    ]

    operations = [
        migrations.CreateModel(
            name='OntologyMatchQuality',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('MatchStrength', models.IntegerField()),
                ('Match', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.OntologyMatch')),
            ],
        ),
        migrations.CreateModel(
            name='OntologyMatchQualitySubmission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('SubmittedOn', models.DateTimeField()),
                ('SubmittedBy', models.CharField(max_length=128)),
                ('MatchGroup', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.OntologyMatchGroup')),
            ],
        ),
        migrations.AddField(
            model_name='ontologymatchquality',
            name='Submission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.OntologyMatchQualitySubmission'),
        ),
    ]
