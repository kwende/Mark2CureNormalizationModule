from os import listdir
from os.path import isfile, join
import random
from NormalizationModule.settings import BASE_DIR
import lxml.etree

def RandomlySelectFile(directoryPath):
    fullFiles = [join(directoryPath, f) for f in listdir(directoryPath) if isfile(join(directoryPath, f))]
    randInt = random.randint(0, len(fullFiles)-1)

    return fullFiles[randInt]

def GetRandomAnnotation():
    randFile = RandomlySelectFile(join(BASE_DIR, 'annotationFiles'))
    tree = lxml.etree.parse(randFile)
    annotations = tree.xpath(".//document/passage/annotation/infon[@key='type' and text() = 'disease']/../text/text()")
    randInt = random.randint(0, len(annotations)-1)

    return annotations[randInt]
