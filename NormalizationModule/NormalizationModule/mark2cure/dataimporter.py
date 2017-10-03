import json
import lxml.etree
from django.db import models
from app.models import DODRecord, MeshRecord, Mark2CureAnnotation, Mark2CurePassage, OntologyMatchGroup, OntologyMatch, OntologyMatchQualitySubmission, \
    OntologyMatchQuality, OntologyMatchQualityConsensus, OntologyMatchQualityConsensusReason, OntologyMatchQualityConsensusReasonConsensus
import NormalizationModule.mark2cure.dataaccess
import NormalizationModule.mark2cure.nlp
from NormalizationModule.mark2cure.nlp import DiseaseRecord, FindRecommendations, Mark2CureQuery, TFIDF
from os import path, getcwd
import pickle
import operator
from NormalizationModule.settings import MAXIMUM_NUMBER_OPTIONS_TO_DISPLAY
import datetime
from django.db.models import Q

def ResetMark2CureDatabases():

    allAnnotations = Mark2CureAnnotation.objects.filter(~Q(Stage = -1) and ~Q(Stage = 0))
    print("Found " + str(len(allAnnotations)) + " annotations to blank")

    for annotation in allAnnotations:
        annotation.Stage = 0
        annotation.save()

    OntologyMatchQualitySubmission.objects.all().delete()
    OntologyMatchQuality.objects.all().delete()

    OntologyMatchQualityConsensus.objects.all().delete()
    OntologyMatchQualityConsensusReason.objects.all().delete()

    OntologyMatchQualityConsensusReasonConsensus.objects.all().delete()

    allOntologyMatchesToCorrect = OntologyMatch.objects.filter(~Q(QualityConsensus = None) or ~Q(ReasonConsensus = None))
    print("Found " + str(len(allOntologyMatchesToCorrect)) + " matches to correct.")

    for ontologyMatchToCorrect in allOntologyMatchesToCorrect:
        ontologyMatchToCorrect.QualityConsensus = None
        ontologyMatchToCorrect.ReasonConsensus = None
        ontologyMatchToCorrect.save()

def BuildOutMatchRecords():

    allUninitializedAnnotations = Mark2CureAnnotation.objects.filter(Stage = 0)

    for uninitializedAnnotation in allUninitializedAnnotations:

        annotationId = uninitializedAnnotation.AnnotationId
        annotationText = uninitializedAnnotation.AnnotationText
        passageId = uninitializedAnnotation.Passage_id

        passageToUse = Mark2CurePassage.objects.filter(id = passageId)[0]

        passageText = passageToUse.PassageText
        documentId = passageToUse.DocumentId

        tfidf = None
        trainedPickle = path.join(getcwd(), 'trained.pickle')
        with open(trainedPickle, 'rb') as fin:
            tfidf = pickle.load(fin)

        query = Mark2CureQuery(annotationText, passageText)
        recommendationsWithWeights = FindRecommendations(query, tfidf, 30, .5)

        recommendationsWithWeights = NormalizationModule.mark2cure.dataaccess.TrimUsingOntologyDatabases(recommendationsWithWeights)
            
        sortedList = sorted(recommendationsWithWeights, key=operator.itemgetter(2), reverse = True)
        if len(sortedList) > MAXIMUM_NUMBER_OPTIONS_TO_DISPLAY:
            sortedList = sortedList[0:MAXIMUM_NUMBER_OPTIONS_TO_DISPLAY]

        if len(recommendationsWithWeights) == 0:
            NormalizationModule.mark2cure.dataaccess.SaveMatchStrengthRecordForNoMatches(documentId, annotationId)

        ontologyMatchGroup = OntologyMatchGroup(GeneratedOn = datetime.datetime.now(), \
            Annotation = uninitializedAnnotation, MatchAlgorithmVersion = 1)
        ontologyMatchGroup.save()

        for match in sortedList:
            ontologyMatch = OntologyMatch(OntologyName = match[1], OntologyRecordId = match[3], MatchGroup = ontologyMatchGroup, \
                NLPDotProduct = match[2], ConvenienceMatchString = match[0])
            ontologyMatch.save()


def EnterMark2CureAnnotationFile(filePath, minimumReoccurenceCount):
    tree = lxml.etree.parse(filePath)

    documentId = int(tree.xpath(".//document/id/text()")[0])
    passages = tree.xpath(".//document/passage")

    for passage in passages:

        passageText = passage.xpath(".//text/text()")[0]
        passageId = int(passage.xpath(".//infon[@key='id']/text()")[0])

        passageRecord = Mark2CurePassage(DocumentId = documentId, PassageId = passageId, PassageText = passageText)
        passageRecord.save()

        annotations = passage.xpath(".//annotation/infon[@key='type' and text() = 'disease']/..")

        annotationCountDictionary = {}
        annotationDictionary = {}
        for annotation in annotations:
            annotationText = annotation.xpath(".//text/text()")[0]
            if not annotationText in annotationDictionary:
                annotationDictionary[annotationText] = annotation
            if not annotationText in annotationCountDictionary:
                annotationCountDictionary[annotationText] = 1
            else:
                annotationCountDictionary[annotationText] = annotationCountDictionary[annotationText] + 1

        for k,v in annotationDictionary.items():
            if annotationCountDictionary[k] >= minimumReoccurenceCount:
                annotationText = k
                annotationId = int(v.xpath(".//@id")[0])
                annotationRecord = Mark2CureAnnotation(DocumentId = documentId, AnnotationId = annotationId, 
                                                       AnnotationText = annotationText, Passage = passageRecord)
                annotationRecord.save()

def BuildDODRecordsFromDisk(jsonDodFilePath):
    with open(jsonDodFilePath) as jsonFile:
        jsonData = json.load(jsonFile)

        dodRecords = []
        for d in jsonData['graphs'][0]['nodes']:
            if 'meta' in d and 'definition' in d['meta']:
                dodRecords.append(DODRecord(DODId = d['id'], Name = d['lbl'], IsSynonym = False))
                if 'synonyms' in d['meta']:
                    for s in d['meta']['synonyms']:
                        dodRecords.append(DODRecord(DODId = d['id'], Name = s['val'], IsSynonym = True))

        DODRecord.objects.bulk_create(dodRecords)

def BuildMeshRecordsFromDisk(xmlFilePath, suppXmlFilePath):
    diseaseRecords = []
    descriptorUIs = []
    descTree = lxml.etree.parse(xmlFilePath)
    
    num = 0

    diseases = descTree.xpath(".//DescriptorRecord/TreeNumberList/TreeNumber[starts-with(text(), 'C')]/../../DescriptorName/String/text()")
    for disease in diseases:
        descriptorRecord = descTree.xpath('.//DescriptorRecord/DescriptorName/String[text()="' + disease + '"]/../..')[0]
        synonyms = descriptorRecord.xpath(".//ConceptList/Concept/TermList/Term")
        print("found " + str(len(synonyms)) + " synonyms")
        #synonymNames =
        #descriptorRecord.xpath(".//ConceptList/Concept/TermList/Term/String/text()")
        descriptorUI = descriptorRecord.xpath(".//DescriptorUI/text()")[0]
        descriptorUIs.append(descriptorUI)

        diseaseRecords.append(diseaseRecord(MeshId = descriptorUI, Name = disease, IsSynonym = False, ParentMeshId = None))

        for synonym in synonyms:
            synonymName = synonym.xpath(".//String/text()")[0]
            synonymId = synonym.xpath(".//TermUI/text()")[0]
            if not synonymName == disease:
                diseaseRecords.append(diseaseRecord(MeshId = synonymId, Name = synonymName, IsSynonym = True, ParentMeshId = descriptorUI))

        print("Finished " + str(num) + " of " + str(len(diseases)))
        num = num + 1

    print("Working on supplemental records...")

    num = 0
    existingSupplementalRecords = []
    descTree = lxml.etree.parse(suppXmlFilePath)
    for descriptorUI in descriptorUIs:
        xpath = ".//SupplementalRecord/HeadingMappedToList/HeadingMappedTo/DescriptorReferredTo/DescriptorUI[text()='*" + descriptorUI + "']/../../../.."
        supplementalRecords = descTree.xpath(xpath)
        for supplementalRecord in supplementalRecords:
            supplementalRecordUI = supplementalRecord.xpath(".//SupplementalRecordUI/text()")[0]
            if not supplementalRecordUI in existingSupplementalRecords:
                existingSupplementalRecords.append(supplementalRecordUI)

                disease = supplementalRecord.xpath(".//SupplementalRecordName/String/text()")[0]
                synonyms = supplementalRecord.xpath(".//ConceptList/Concept/TermList/Term")
                
                diseaseRecords.append(MeshRecord(MeshId = supplementalRecordUI, Name = disease, IsSynonym = False, ParentMeshId = None))

                for synonym in synonyms:
                    synonymName = synonym.xpath(".//String/text()")[0]
                    synonymId = synonym.xpath(".//TermUI/text()")[0]
                    if not synonymName == disease:
                        diseaseRecords.append(MeshRecord(MeshId = synonymId, Name = synonymName, IsSynonym = True, ParentMeshId = supplementalRecordUI))
        
        print("Finished " + str(num) + " of " + str(len(descriptorUIs)))
        num = num + 1

    print("Bulk saving...")
    MeshRecord.objects.bulk_create(diseaseRecords)