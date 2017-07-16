"""
Definition of models.
"""
import json
import lxml.etree
from django.db import models

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
