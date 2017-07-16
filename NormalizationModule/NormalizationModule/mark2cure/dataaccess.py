from os import listdir
from os.path import isfile, join
import random
from NormalizationModule.settings import BASE_DIR
import lxml.etree
from NormalizationModule.mark2cure.nlp import DiseaseRecord


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
    annotationText = annotation.xpath("text()")

    return passageText, annotationText

