"""
Definition of models.
"""

from django.db import models
from datetime import datetime

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

class MatchStrengthRecord(models.Model):
    AnnotationDocumentId = models.IntegerField()
    AnnotationId = models.IntegerField()
    OntologyName = models.CharField(max_length=128, null=True)
    OntologyRecordId = models.IntegerField(null=True)
    MatchStrength = models.IntegerField()

class MatchExplanationRecord(models.Model):
    AnnotationDocumentId = models.IntegerField()
    AnnotationId = models.IntegerField()
    OntologyName = models.CharField(max_length=128, null=True)
    OntologyRecordId = models.IntegerField(null=True)
    MatchExplanation = models.IntegerField()

class Mark2CurePassage(models.Model):
    DocumentId = models.IntegerField()
    PassageId = models.IntegerField()
    PassageText = models.TextField()

class Mark2CureAnnotation(models.Model):
    DocumentId = models.IntegerField()
    AnnotationId = models.IntegerField()
    AnnotationText = models.CharField(max_length = 512)
    Passage = models.ForeignKey(Mark2CurePassage, on_delete=models.CASCADE)
    Stage = models.IntegerField(default= 0)

class OntologyMatchGroup(models.Model):
    GeneratedOn = models.DateField()
    Annotation = models.ForeignKey(Mark2CureAnnotation, on_delete=models.CASCADE)
    MatchAlgorithmVersion = models.IntegerField(default=0)

class OntologyMatch(models.Model):
    OntologyName = models.CharField(max_length=128)
    OntologyRecordId = models.CharField(max_length=128)
    MatchGroup = models.ForeignKey(OntologyMatchGroup, on_delete=models.CASCADE)
    QualityConsensus = models.IntegerField(null=True)
    ReasonConsensus = models.IntegerField(null=True)
    NLPDotProduct = models.DecimalField(decimal_places = 4, max_digits = 10, default=0)
    ConvenienceMatchString = models.CharField(max_length=256, default="")

class OntologyMatchQualitySubmission(models.Model):
    SubmittedOn = models.DateTimeField(default=datetime.now, blank=True)
    SubmittedBy = models.CharField(max_length=128)
    MatchGroup = models.ForeignKey(OntologyMatchGroup, on_delete=models.CASCADE)

class OntologyMatchQuality(models.Model):
    Submission = models.ForeignKey(OntologyMatchQualitySubmission, on_delete=models.CASCADE)
    Match = models.ForeignKey(OntologyMatch, on_delete=models.CASCADE)
    MatchStrength = models.IntegerField()

class OntologyMatchQualityConsensus(models.Model):
    Match = models.ForeignKey(OntologyMatch, on_delete=models.CASCADE)
    MatchStrength = models.IntegerField()
    ReasonConfirmed = models.BooleanField(default=False)

class OntologyMatchQualityConsensusReason(models.Model):
    SubmittedOn = models.DateTimeField(default=datetime.now, blank=True)
    SubmittedBy = models.CharField(max_length=128, default="NOWHEREMAN")
    MatchQualityConsensus = models.ForeignKey(OntologyMatchQualityConsensus, on_delete=models.CASCADE, null=True)
    Reason = models.IntegerField(default=-1)

class OntologyMatchQualityConsensusReasonConsensus(models.Model):
    MatchQualityConsensus = models.ForeignKey(OntologyMatchQualityConsensus, on_delete=models.CASCADE, null=True)
    Reason = models.IntegerField()