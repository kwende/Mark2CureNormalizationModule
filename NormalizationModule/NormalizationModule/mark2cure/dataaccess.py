from os import listdir
from os.path import isfile, join
import random
from NormalizationModule.settings import BASE_DIR
import lxml.etree
from NormalizationModule.mark2cure.nlp import DiseaseRecord
from app.models import MatchRecord, MeshRecord, DODRecord, Mark2CureAnnotation, Mark2CurePassage
from enum import Enum
from django.db import models
from django.db.models import Q

class MatchStrength(Enum):
    NoMatch = -1
    PoorMatch = 0
    PartialMatch = 1
    PerfectMatch = 2

class NonPerfectMatch:
    def __init__(self, nonPerfectMatchId, annotationText, passageText, matchStrength, ontologyText):
        self.NonPerfectMatchId = nonPerfectMatchId
        self.AnnotationText = annotationText
        self.PassageText = passageText
        self.MatchStrength = matchStrength
        self.OntologyText = ontologyText


def RandomlySelectFile(directoryPath):
    fullFiles = [join(directoryPath, f) for f in listdir(directoryPath) if isfile(join(directoryPath, f))]
    randInt = random.randint(0, len(fullFiles)-1)

    return fullFiles[randInt]

def GetRandomAnnotation():

    allAnnotations = Mark2CureAnnotation.objects.filter(Solved = False)

    randInt = random.randint(0, len(allAnnotations)-1)

    annotationToUse = allAnnotations[randInt]

    annotationId = annotationToUse.AnnotationId
    annotationText = annotationToUse.AnnotationText
    passageId = annotationToUse.Passage_id

    passageToUse = Mark2CurePassage.objects.filter(id = passageId)[0]

    passageText = passageToUse.PassageText
    documentId = passageToUse.DocumentId

    return passageText, annotationText, documentId, annotationId

def SaveMatchRecordForNoMatches(documentId, annotationId):
    matchRecord = MatchRecord(AnnotationDocumentId = documentId, AnnotationId = annotationId, 
                              MatchStrength = MatchStrength.NoMatch.value, Reason = -1)
    matchRecord.save()

def TrimUsingOntologyDatabases(recommendationTuples):

    #duplicate the list to be trimmed
    finalList = []
    meshToIgnore = []
    dodToIgnore = []

    for recommendation, weight in recommendationTuples.items():
        
        bestMeshFamilyMemberText = ""
        bestDODFamilyMemberText = ""

        if not recommendation in meshToIgnore:
            bestMeshScore = 0

            # is there a matching mesh record? 
            meshRecords = MeshRecord.objects.filter(Name = recommendation)
            for meshRecord in meshRecords:

                # prepare for finding the best of any family. 
                bestMeshScore = weight
                bestMeshFamilyMemberText = recommendation

                # get the whole family for this phrase
                if not meshRecord.IsSynonym:
                    parentMeshId = meshRecord.MeshId
                else:
                    parentMeshId = meshRecord.ParentMeshId
                family = MeshRecord.objects.filter(Q(MeshId = parentMeshId) | Q(ParentMeshId = parentMeshId))

                # find the highest weighted family member also in this list.
                for member in family:
                    if member.Name in recommendationTuples and recommendationTuples[member.Name] > bestMeshScore:
                        # if we found one better, keep it. 
                        bestMeshScore = recommendationTuples[member.Name]
                        bestMeshFamilyMemberText = member.Name
                    else:
                        # otherwise, ignore this one when it comes up 
                        meshToIgnore.append(member.Name)

        if not recommendation in dodToIgnore:
            bestDODScore = 0
            
            dodRecords = DODRecord.objects.filter(Name = recommendation)
            for dodRecord in dodRecords:
                family = DODRecord.objects.filter(DODId = dodRecord.DODId)
                for member in family:
                    if member.Name in recommendationTuples and recommendationTuples[member.Name] > bestDODScore:
                        bestDODScore = recommendationTuples[member.Name]
                        bestDODFamilyMemberText = member.Name
                    else:
                        dodToIgnore.append(member.Name)

        justTextList = [f[0] for f in finalList]
        if bestMeshFamilyMemberText == bestDODFamilyMemberText and bestMeshFamilyMemberText is not "" and not bestMeshFamilyMemberText in justTextList:
            # the same phrase is in both ontologies. 
            finalList.append((bestMeshFamilyMemberText, "DOD,MESH"))
        else:
            # separate names in separate ontologies
            if bestMeshFamilyMemberText is not "" and not bestMeshFamilyMemberText in justTextList:
                finalList.append((bestMeshFamilyMemberText, "MESH"))
            if bestDODFamilyMemberText is not "" and not bestDODFamilyMemberText in justTextList:
                finalList.append((bestDODFamilyMemberText, "DOD"))

    return finalList

def GetIdForOntologyRecord(ontologyType, recordText):

    id = -1
    if ontologyType.lower() == "mesh":
        records = MeshRecord.objects.filter(Name = recordText)
        if not records is None and len(records) == 1: 
            id = records[0].id
    elif ontologyType.lower() == "dod":
        records = DODRecord.objects.filter(Name = recordText)
        if not records is None and len(records) == 1:
            id = records[0].id

    return id

def SaveMatchRecord(annotationId, documentId, ontologyType, databaseId, matchQuality):
    matchRecord = MatchRecord(AnnotationDocumentId = documentId, AnnotationId = annotationId, 
                              MatchStrength = matchQuality, OntologyName = ontologyType, OntologyRecordId = databaseId, Reason = -1)
    matchRecord.save()

    annotationWeMatched = Mark2CureAnnotation.objects.filter(AnnotationId = annotationId)[0]
    annotationWeMatched.Solved = True
    annotationWeMatched.save()

    return

def GetRandomNonPerfectMatch():
    unexplainedNonPerfectMatches = MatchRecord.objects.filter((Q(MatchStrength = 0) | Q(MatchStrength = 1)), Reason = -1)

    if len(unexplainedNonPerfectMatches) == 0:
        return None
    else:
        randInt = random.randint(0, len(unexplainedNonPerfectMatches)-1)
        unexplainedNonPerfectMatch = unexplainedNonPerfectMatches[randInt]

        annotationRecord = Mark2CureAnnotation.objects.filter(AnnotationId = unexplainedNonPerfectMatch.AnnotationId)[0]
        passageRecord = Mark2CurePassage.objects.filter(id = annotationRecord.Passage_id)[0]

        ontologyName = unexplainedNonPerfectMatch.OntologyName
        matchedOntologyText = ""
        ontologyRecordId = unexplainedNonPerfectMatch.OntologyRecordId

        if ontologyName.lower() == "mesh":
            matchedRecord = MeshRecord.objects.filter(id = ontologyRecordId)[0]
            matchedOntologyText = matchedRecord.Name
        elif ontologyName.lower() == "dod":
            matchedReocrd = DODRecord.objects.filter(id = ontologyRecordId)[0]
            matchedOntologyText = matchedRecord.Name
        #TODO: else throw exception
       
        unexplainedMatch = NonPerfectMatch(unexplainedNonPerfectMatch.id, annotationRecord.AnnotationText, 
                                           passageRecord.PassageText, unexplainedNonPerfectMatch.MatchStrength,
                                           matchedOntologyText)
        return unexplainedMatch
