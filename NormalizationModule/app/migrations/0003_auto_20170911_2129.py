# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-09-12 02:29
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_ontologymatchgroup'),
    ]

    operations = [
        migrations.CreateModel(
            name='OntologyMatch',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('OntologyName', models.CharField(max_length=128)),
                ('OntologyRecordId', models.IntegerField()),
            ],
        ),
        migrations.RemoveField(
            model_name='ontologymatchgroup',
            name='OntologyName',
        ),
        migrations.RemoveField(
            model_name='ontologymatchgroup',
            name='OntologyRecordId',
        ),
        migrations.AddField(
            model_name='ontologymatchgroup',
            name='MatchAlgorithmVersion',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='ontologymatch',
            name='MatchGroup',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.OntologyMatchGroup'),
        ),
    ]