"""
Definition of models.
"""
import lxml.etree
from django.db import models

def BuildMeshRecordsFromDisk(xmlFilePath, suppXmlFilePath):
    meshRecords = []
    descriptorUIs = []
    descTree = lxml.etree.parse(xmlFilePath)
    
    num = 0

    diseases = descTree.xpath(".//DescriptorRecord/TreeNumberList/TreeNumber[starts-with(text(), 'C')]/../../DescriptorName/String/text()")
    for disease in diseases:
        descriptorRecord = descTree.xpath('.//DescriptorRecord/DescriptorName/String[text()="' + disease + '"]/../..')[0]
        syonyms = descriptorRecord.xpath(".//ConceptList/Concept/TermList/Term")
        #synonymNames = descriptorRecord.xpath(".//ConceptList/Concept/TermList/Term/String/text()")
        descriptorUI = descriptorRecord.xpath(".//DescriptorUI/text()")[0]
        descriptorUIs.append(descriptorUI)

        meshRecords.append(MeshRecord(MeshId = descriptorUI, Name = disease, IsSynonym = False, ParentMeshId = None))

        for synonym in syonyms:
            synonymName = synonym
            if not synonymName == disease:
                meshRecords.append(MeshRecord(MeshId = descriptorUI, Name = synonymName, IsSynonym = True, ParentMeshId = descriptorUI))

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
                synonymsToUse = supplementalRecord.xpath(".//ConceptList/Concept/TermList/Term/String/text()")
                
                meshRecords.append(MeshRecord(MeshId = supplementalRecordUI, Name = disease, IsSynonym = False, ParentMeshId = None))

                for synonymName in synonymsToUse:
                    if not synonymName == disease:
                        meshRecords.append(MeshRecord(MeshId = supplementalRecordUI, Name = synonymName, IsSynonym = True, ParentMeshId = supplementalRecordUI))
        
        print("Finished " + str(num) + " of " + str(len(descriptorUIs)))
        num = num + 1

    print("Bulk saving...")
    MeshRecord.objects.bulk_create(meshRecords)

# Create your models here.
class MeshRecord(models.Model):
    MeshId = models.CharField(max_length=10)
    Name = models.TextField()
    IsSynonym = models.BooleanField()
    ParentMeshId = models.CharField(max_length=10, null=True)
