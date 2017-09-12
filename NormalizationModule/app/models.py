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
    OntologyRecordId = models.IntegerField()
    MatchGroup = models.ForeignKey(OntologyMatchGroup, on_delete=models.CASCADE)
    QualityConsensus = models.IntegerField(null=True)
    ReasonConsensus = models.IntegerField(null=True)

class OntologyMatchQualitySubmission(models.Model):
    SubmittedOn = models.DateTimeField()
    SubmittedBy = models.CharField(max_length=128)
    MatchGroup = models.ForeignKey(OntologyMatchGroup, on_delete=models.CASCADE)

class OntologyMatchQuality(models.Model):
    Submission = models.ForeignKey(OntologyMatchQualitySubmission, on_delete=models.CASCADE)
    Match = models.ForeignKey(OntologyMatch, on_delete=models.CASCADE)
    MatchStrength = models.IntegerField()

class OntologyMatchQualityReason(models.Model):
    QualityConsensus = models.ForeignKey(OntologyMatch, on_delete=models.CASCADE)