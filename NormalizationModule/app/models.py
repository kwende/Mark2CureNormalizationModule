"""
Definition of models.
"""

from django.db import models

# Create your models here.
class MeshRecord(models.Model):
    MeshId = models.CharField(max_length=10)
    Name = models.TextField()
    IsSynonym = models.BooleanField()
    ParentMeshId = models.CharField(max_length=10, null=True)

class DODRecord(models.Model):
    DODId = models.CharField(max_length=128)
    Name = models.TextField()
    IsSynonym = models.BooleanField()

class MatchRecord(models.Model):
    AnnotationDocumentId = models.IntegerField()
    AnnotationId = models.IntegerField()
    OntologyName = models.CharField(max_length=128, null=True)
    OntologyRecordId = models.IntegerField(null=True)
    MatchStrength = models.IntegerField()
