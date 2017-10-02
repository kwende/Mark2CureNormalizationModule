from os import listdir
from os.path import isfile, join
import random
from NormalizationModule.settings import BASE_DIR
import lxml.etree
from NormalizationModule.mark2cure.nlp import DiseaseRecord
from app.models import MatchStrengthRecord, MeshRecord, DODRecord, Mark2CureAnnotation, \
    Mark2CurePassage, OntologyMatchGroup, OntologyMatch, OntologyMatchQualitySubmission, OntologyMatchQuality, \
    OntologyMatchQualityConsensus
from enum import Enum
from django.db import models
from django.db.models import Q
from django.conf import settings
from operator import itemgetter, attrgetter, methodcaller

class MatchStrength(Enum):
    NoMatch = -1
    PoorMatch = 0
    PartialMatch = 1
    PerfectMatch = 2

class PartialMatchReasons(Enum):
    AIsMoreSpecificThanB = 0
    AIsLessSpecificThanB = 1
    AIsACompoundTerm = 2

class PoorMatchReasons(Enum):
    AAndBAreUnrelated = 0
    AIsACompoundTerm = 1

class NonPerfectMatch:
    def __init__(self, matchQualityId, annotationText, passageText, matchStrength, ontologyText):
        self.MatchQualityId = matchQualityId
        self.AnnotationText = annotationText
        self.PassageText = passageText
        self.MatchStrength = matchStrength
        self.OntologyText = ontologyText

def DetermineWhetherConsensusForMatchQualityMet(matchGroupId, minAmountForConsensus):
    ontologyMatchGroup = OntologyMatchGroup.objects.get(id = matchGroupId)
    ontologyMatches = OntologyMatch.objects.filter(MatchGroup = ontologyMatchGroup)

    consensusForAllMet = True
    consensus = {}
    for ontologyMatch in ontologyMatches:
        ontologyMatchQualityResponses = OntologyMatchQuality.objects.filter(Match = ontologyMatch)

        numberOfPoor = len([o for o in ontologyMatchQualityResponses if o.MatchStrength == MatchStrength.PoorMatch.value])
        numberOfPartial = len([o for o in ontologyMatchQualityResponses if o.MatchStrength == MatchStrength.PartialMatch.value])
        numberOfPerfect = len([o for o in ontologyMatchQualityResponses if o.MatchStrength == MatchStrength.PerfectMatch.value])

        values = [numberOfPoor, numberOfPartial, numberOfPerfect]
        maxIndex, maxValue = max(enumerate(values), key=itemgetter(1))

        if maxValue < minAmountForConsensus:
            consensusForAllMet = False
            break
        else:
            # 0 for poor, 1 for partial, 2 for perfect
            consensus[ontologyMatch] = maxIndex

    if consensusForAllMet:
        annotation = Mark2CureAnnotation.objects.get(id = ontologyMatchGroup.Annotation.id)
        annotation.Stage = 1
        annotation.save()

        for key,value in consensus.items():
            consensus = OntologyMatchQualityConsensus(Match = key, MatchStrength = value)
            consensus.save()

def CreateOntologyMatchQualityForSubmission(submission, matchId, matchStrength):
    match = OntologyMatch.objects.get(id = matchId)

    ontologyMatchQuality = OntologyMatchQuality(Submission = submission, Match = match, MatchStrength = matchStrength)
    ontologyMatchQuality.save()

def CreateOntologyMatchSubmission(userName, matchGroupId):
    matchGroup = OntologyMatchGroup.objects.get(id = matchGroupId)
    matchGroupSubmission = OntologyMatchQualitySubmission(SubmittedBy = userName, MatchGroup = matchGroup)
    matchGroupSubmission.save()

    return matchGroupSubmission

def RandomlySelectFile(directoryPath):
    fullFiles = [join(directoryPath, f) for f in listdir(directoryPath) if isfile(join(directoryPath, f))]
    randInt = random.randint(0, len(fullFiles) - 1)

    return fullFiles[randInt]

def GetSortedMatchesForMatchGroup(matchGroup, maxToDisplay):
    sortedList = OntologyMatch.objects.filter(MatchGroup__id = matchGroup.id).order_by('-NLPDotProduct')
    return list(sortedList)

def GetRandomOntologyMatchGroup():
    annotations = Mark2CureAnnotation.objects.filter(id = 33443)
    randInt = random.randint(0, len(annotations) - 1)
    annotationToUse = annotations[randInt]

    matchGroupToUse = OntologyMatchGroup.objects.get(Annotation = annotationToUse)

    passageId = annotationToUse.Passage_id
    passageToUse = Mark2CurePassage.objects.get(id = passageId)
    documentId = passageToUse.DocumentId

    return matchGroupToUse, passageToUse.PassageText, annotationToUse.AnnotationText, documentId, annotationToUse.id

def GetRandomAnnotation():

    allAnnotations = Mark2CureAnnotation.objects.filter(Stage = 0)

    randInt = random.randint(0, len(allAnnotations) - 1)

    annotationToUse = allAnnotations[randInt]

    annotationId = annotationToUse.AnnotationId
    annotationText = annotationToUse.AnnotationText
    passageId = annotationToUse.Passage_id

    passageToUse = Mark2CurePassage.objects.filter(id = passageId)[0]

    passageText = passageToUse.PassageText
    documentId = passageToUse.DocumentId

    return passageText, annotationText, documentId, annotationId

def SaveMatchStrengthRecordForNoMatches(documentId, annotationId):
    matchStrengthRecord = MatchStrengthRecord(AnnotationDocumentId = documentId, AnnotationId = annotationId, 
                              MatchStrength = MatchStrength.NoMatch.value)
    matchStrengthRecord.save()

    annotationWithNoMatches = Mark2CureAnnotation.objects.get(id = annotationId)
    annotationWithNoMatches.Stage = -1
    annotationWithNoMatches.save()

def TrimUsingOntologyDatabases(recommendationTuples):

    #duplicate the list to be trimmed
    finalList = []
    meshToIgnore = []
    dodToIgnore = []

    for recommendation, weight in recommendationTuples.items():
        
        bestMeshFamilyMemberText = ""
        bestMeshScore = 0
        bestMeshId = ""
        bestDODFamilyMemberText = ""
        bestDODScore = 0
        bestDODId = ""

        if not recommendation in meshToIgnore:

            # is there a matching mesh record?
            meshRecords = MeshRecord.objects.filter(Name = recommendation)
            for meshRecord in meshRecords:

                # prepare for finding the best of any family.
                bestMeshScore = weight
                bestMeshFamilyMemberText = recommendation

                if not meshRecord.ParentMeshId == None:
                    bestMeshId = meshRecord.ParentMeshId
                else:
                    bestMeshId = meshRecord.MeshId

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

                        if not member.ParentMeshId == None:
                            bestMeshId = member.ParentMeshId
                        else:
                            bestMeshId = member.MeshId
                    else:
                        # otherwise, ignore this one when it comes up
                        meshToIgnore.append(member.Name)

        if not recommendation in dodToIgnore:
            
            dodRecords = DODRecord.objects.filter(Name = recommendation)
            for dodRecord in dodRecords:
                family = DODRecord.objects.filter(DODId = dodRecord.DODId)
                for member in family:
                    if member.Name in recommendationTuples and recommendationTuples[member.Name] > bestDODScore:
                        bestDODScore = recommendationTuples[member.Name]
                        bestDODFamilyMemberText = member.Name
                        bestDODId = member.DODId
                    else:
                        dodToIgnore.append(member.Name)

        justTextList = [f[0] for f in finalList]
        if bestMeshFamilyMemberText == bestDODFamilyMemberText and bestMeshFamilyMemberText is not "" and not bestMeshFamilyMemberText in justTextList:
            # the same phrase is in both ontologies.
            finalList.append((bestMeshFamilyMemberText, "DOD,MESH", bestMeshScore if bestMeshScore > bestDODScore else bestDODScore, bestMeshId))
        else:
            # separate names in separate ontologies
            if bestMeshFamilyMemberText is not "" and not bestMeshFamilyMemberText in justTextList:
                finalList.append((bestMeshFamilyMemberText, "MESH", bestMeshScore, bestMeshId))
            if bestDODFamilyMemberText is not "" and not bestDODFamilyMemberText in justTextList:
                finalList.append((bestDODFamilyMemberText, "DOD", bestDODScore, bestDODId))

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

def SaveMatchStrengthRecord(annotationId, documentId, ontologyType, databaseId, matchQuality):
    matchStrengthRecord = MatchStrengthRecord(AnnotationDocumentId = documentId, AnnotationId = annotationId, 
                              MatchStrength = matchQuality, OntologyName = ontologyType, 
                              OntologyRecordId = databaseId)
    matchStrengthRecord.save()

    # how many people have looked at this?
    matchStrengthRecords = MatchStrengthRecord.objects.filter(AnnotationDocumentId = documentId, AnnotationId = annotationId, 
                               OntologyName = ontologyType, OntologyRecordId = databaseId)
    
    # determine the match strength consensus (if any yet).
    poorMatchCount = sum(1 for m in matchStrengthRecords if MatchStrength(m.MatchStrength) == MatchStrength.PoorMatch)
    partialMatchCount = sum(1 for m in matchStrengthRecords if MatchStrength(m.MatchStrength) == MatchStrength.PartialMatch)
    perfectMatchCount = sum(1 for m in matchStrengthRecords if MatchStrength(m.MatchStrength) == MatchStrength.PerfectMatch)

    # if there is enough consensus, then pass to the next phase
    if max([poorMatchCount, partialMatchCount, perfectMatchCount]) >= settings.REQUIRED_VIEWS:
        annotationWeMatched = Mark2CureAnnotation.objects.filter(AnnotationId = annotationId)[0]
        annotationWeMatched.Stage = 1
        annotationWeMatched.save()

    return

def UpdateMatchStrengthRecordWithReason(MatchStrengthRecordId, reason):
    matchStrengthRecord = MatchStrengthRecord.objects.filter(id = MatchStrengthRecordId)[0]
    matchStrengthRecord.Reason = reason.value
    matchStrengthRecord.save()

def GetRandomMatchQualityConsensus():

    matchQualitiesToExplain = OntologyMatchQualityConsensus.objects.filter(ReasonConfirmed = False)

    randInt = random.randint(0, len(matchQualitiesToExplain) - 1)
    randomMatchQualityToExplain = matchQualitiesToExplain[randInt]

    match = randomMatchQualityToExplain.Match
    m2cAnnotation = match.MatchGroup.Annotation
    passage = m2cAnnotation.Passage

    unexplainedMatch = NonPerfectMatch(randomMatchQualityToExplain.id, m2cAnnotation.AnnotationText, 
                                        passage.PassageText, randomMatchQualityToExplain.MatchStrength,
                                        match.ConvenienceMatchString)
    return unexplainedMatch

#def GetRandomAnnotationInExplanationPhase():
#    annotationsInExplanationPhase = Mark2CureAnnotation.objects.filter(Stage = 1)

#    if len(annotationsInExplanationPhase) == 0:
#        return None
#    else:
#        randInt = random.randint(0, len(annotationsInExplanationPhase) - 1)
#        annotationInExplanationPhase = annotationsInExplanationPhase[randInt]

#        passageRecord = Mark2CurePassage.objects.filter(id = annotationInExplanationPhase.Passage_id)[0]

#        ontologyName = unexplainedNonPerfectMatch.OntologyName
#        matchedOntologyText = ""
#        ontologyRecordId = unexplainedNonPerfectMatch.OntologyRecordId

#        if ontologyName.lower() == "mesh":
#            matchedRecord = MeshRecord.objects.filter(id = ontologyRecordId)[0]
#            matchedOntologyText = matchedRecord.Name
#        elif ontologyName.lower() == "dod":
#            matchedReocrd = DODRecord.objects.filter(id = ontologyRecordId)[0]
#            matchedOntologyText = matchedRecord.Name
#        #TODO: else throw exception
       
#        unexplainedMatch = NonPerfectMatch(unexplainedNonPerfectMatch.id, annotationRecord.AnnotationText, 
#                                           passageRecord.PassageText, unexplainedNonPerfectMatch.MatchStrength,
#                                           matchedOntologyText)
#        return unexplainedMatch
