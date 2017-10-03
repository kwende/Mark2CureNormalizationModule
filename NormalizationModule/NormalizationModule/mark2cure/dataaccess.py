from os import listdir
from os.path import isfile, join
import random
from NormalizationModule.settings import BASE_DIR
import lxml.etree
from NormalizationModule.mark2cure.nlp import DiseaseRecord
from app.models import MeshRecord, DODRecord, Mark2CureAnnotation, \
    Mark2CurePassage, OntologyMatchGroup, OntologyMatch, OntologyMatchQualitySubmission, OntologyMatchQuality, \
    OntologyMatchQualityConsensus, OntologyMatchQualityConsensusReason, OntologyMatchQualityConsensusReasonConsensus
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
    MatchAssessmentRejected = 99

class PoorMatchReasons(Enum):
    AAndBAreUnrelated = 0
    AIsACompoundTerm = 1
    MatchAssessmentRejected = 99

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
        existingConsensus = OntologyMatchQualityConsensus.objects.filter(Match = ontologyMatch)

        # is there a consensus for this one? 
        if len(existingConsensus) == 0:
            # nope, so investigate. 
            ontologyMatchQualityResponses = OntologyMatchQuality.objects.filter(Match = ontologyMatch)

            numberOfPoor = len([o for o in ontologyMatchQualityResponses if o.MatchStrength == MatchStrength.PoorMatch.value])
            numberOfPartial = len([o for o in ontologyMatchQualityResponses if o.MatchStrength == MatchStrength.PartialMatch.value])
            numberOfPerfect = len([o for o in ontologyMatchQualityResponses if o.MatchStrength == MatchStrength.PerfectMatch.value])

            values = [numberOfPoor, numberOfPartial, numberOfPerfect]
            maxIndex, maxValue = max(enumerate(values), key=itemgetter(1))

            if maxValue < minAmountForConsensus:
                consensusForAllMet = False
            else:
                # 0 for poor, 1 for partial, 2 for perfect
                consensus[ontologyMatch] = maxIndex

    for key,value in consensus.items():
        consensus = OntologyMatchQualityConsensus(Match = key, MatchStrength = value)
        consensus.save()

        match = consensus.Match
        match.QualityConsensus = value
        match.save()

    if consensusForAllMet:
        annotation = Mark2CureAnnotation.objects.get(id = ontologyMatchGroup.Annotation.id)
        annotation.Stage = 1
        annotation.save()

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
    sortedList = OntologyMatch.objects.filter(MatchGroup__id = matchGroup.id, QualityConsensus = None).order_by('-NLPDotProduct')
    return list(sortedList)

def GetRandomOntologyMatchGroup():
    annotations = Mark2CureAnnotation.objects.filter(Stage = 0)
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

def SaveOntologyMatchQualityConsensusReason(matchQualityConsensusId, reasonAsInt, submittedBy):

    matchQualityConsensus = OntologyMatchQualityConsensus.objects.get(id = matchQualityConsensusId)

    matchQualityConsensusReason = OntologyMatchQualityConsensusReason(SubmittedBy = submittedBy, MatchQualityConsensus = matchQualityConsensus, \
        Reason = reasonAsInt)
    matchQualityConsensusReason.save()

def DetermineWhetherConsensusForMatchQualityConsensusReasonMet(matchQualityConsensusId, minAmountForConsensus):

    matchQualityConensusReasons = OntologyMatchQualityConsensusReason.objects.filter(MatchQualityConsensus__id = matchQualityConsensusId)

    #I don't care what TYPE of match it is, just whether a consensus was made. Depending on the type, 
    # the range of responses is 0-1, or 0-2. Just aggregate them al. 
    reason0 = len([o for o in matchQualityConensusReasons if o.Reason ==0])
    reason1 = len([o for o in matchQualityConensusReasons if o.Reason == 1])
    reason2 = len([o for o in matchQualityConensusReasons if o.Reason == 2])
    rejected = len([o for o in matchQualityConensusReasons if o.Reason == 99])

    values = [reason0, reason1, reason2, rejected]
    maxIndex, maxValue = max(enumerate(values), key=itemgetter(1))

    if maxValue >= minAmountForConsensus:
            
        #consensus has been made
        if maxIndex == 3:
            consensus = matchQualityConensusReasons[0].MatchQualityConsensus
            matchAssociatedWithConsensus = consensus.Match
            responsesContributingToConsensus = OntologyMatchQuality.objects.filter(Match = matchAssociatedWithConsensus)
            responsesToConsensus = OntologyMatchQualityConsensusReason.objects.filter(MatchQualityConsensus = consensus)

            responsesContributingToConsensus.delete()
            responsesToConsensus.delete()
            consensus.delete()

            annotation = consensus.Match.MatchGroup.Annotation

            annotationToReset = Mark2CureAnnotation.objects.get(id = annotation.id)

            # reset. we should just view the rejected ones, not all of the associated options. 
            matchAssociatedWithConsensus.QualityConsensus = None
            matchAssociatedWithConsensus.ReasonConsensus = None
            matchAssociatedWithConsensus.save()

            annotationToReset.Stage = 0
            annotationToReset.save()
        else:
            # get the OntologyMatchQualityConsensus associated with these guys and
            # set ReasonConfirmed = True
            consensus = OntologyMatchQualityConsensus.objects.get(id = matchQualityConensusReasons[0].MatchQualityConsensus.id)
            consensus.ReasonConfirmed = True
            consensus.save()

            match = consensus.Match
            match.ReasonConsensus = maxIndex
            match.save()

            reasonConsensus = OntologyMatchQualityConsensusReasonConsensus(MatchQualityConsensus = consensus, Reason = maxIndex)
            reasonConsensus.save()