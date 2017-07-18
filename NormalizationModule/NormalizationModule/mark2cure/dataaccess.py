from os import listdir
from os.path import isfile, join
import random
from NormalizationModule.settings import BASE_DIR
import lxml.etree
from NormalizationModule.mark2cure.nlp import DiseaseRecord
from app.models import MatchRecord
from enum import Enum

class MatchStrength(Enum):
    NoMatch = -1
    PoorMatch = 0
    PartialMatch = 1
    PerfectMatch = 2


def RandomlySelectFile(directoryPath):
    fullFiles = [join(directoryPath, f) for f in listdir(directoryPath) if isfile(join(directoryPath, f))]
    randInt = random.randint(0, len(fullFiles)-1)

    return fullFiles[randInt]

def GetRandomAnnotation():
    randFile = RandomlySelectFile(join(BASE_DIR, 'annotationFiles'))
    tree = lxml.etree.parse(randFile)
    annotations = tree.xpath(".//document/passage/annotation/infon[@key='type' and text() = 'disease']/../text")
    randInt = random.randint(0, len(annotations)-1)
    annotation = annotations[randInt]

    passageText = annotation.xpath("../../text/text()")
    documentId = int(tree.xpath(".//document/id/text()")[0])
    annotationText = annotation.xpath("text()")
    annotationId = int(annotation.xpath("../@id")[0])

    return passageText, annotationText, documentId, annotationId

def SaveMatchRecordForNoMatches(documentId, annotationId):
    matchRecord = MatchRecord(AnnotationDocumentId = documentId, AnnotationId = annotationId, MatchStrength = MatchStrength.NoMatch.value)
    matchRecord.save()

def SaveMatchRecord(annotationId, documentId, ontologyType, databaseId, matchQuality):
    return
