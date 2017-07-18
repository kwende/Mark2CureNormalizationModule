import lxml.etree
from nltk.stem import *
import nltk
from nltk import word_tokenize
import time
import pickle
import re
import string
import datetime as dt
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.stem.porter import PorterStemmer
import numpy as np
import os.path
from nltk.metrics import *
from app.models import DODRecord, MeshRecord
from django.db.models import Q

class DiseaseRecord:

    def __init__(self, line):

        self.Line = self.CleanText(line)

        return

    def CleanText(self, text):

        toReturn = text
        toReturn = toReturn.replace(" 's","'s")

        return toReturn

class Mark2CureQuery:

    def __init__(self, tag, sourceText):
        self.Tag = tag
        self.SourceText = sourceText

        return

    def FindAbbreviationMeaningInSource(self, abbreviation):
        sourceText = self.SourceText
        ret = None
        match = re.search(r"\( ?" + abbreviation.upper() + " ?\)", sourceText)
        if match:
            str = match.group(0).replace(")","").replace("(","").strip()
            strAsCharsReversed = list(reversed(list(str.lower())))
            strIndex = sourceText.index(match.group(0))
            curIndex = strIndex - 1
            failureCount = 0
            indices = []
            stillGood = True

            for char in strAsCharsReversed:

                for i in reversed(range(curIndex)):
                    if sourceText[i].lower() == char and i > 0 and sourceText[i - 1] == ' ':
                        failureCount = 0
                        indices.append(i)
                        curIndex = i
                        break
                    elif i == 0 and sourceText[i].lower() == char:
                        failureCount = 0
                        indices.append(i)
                        break
                    elif sourceText[i] == ' ':
                        failureCount = failureCount + 1

                    if failureCount >= 3:
                        stillGood = False
                        break

                if not stillGood:
                    break

            if stillGood:
                ret = sourceText[indices[len(indices) - 1]:strIndex - 1].strip()

            return ret

class TFIDF:

    def __init__(self):
        self.Model = None
        self.Lines = []
        self.Vectorizer = TfidfVectorizer(stop_words="english")
        self.Corpus = []
        self.RecordMap = []

    def TrainModel(self, diseaseRecords):
        translator = str.maketrans('', '', string.punctuation)

        # we may have multiple ontologies.  this prevents
        # overrepresentation of the same text
        linesAlreadyAdded = []
        rawLinesAdded = []

        for diseaseRecord in diseaseRecords:
            lineToAdd = diseaseRecord.Line.lower().translate(translator)
            if not lineToAdd in linesAlreadyAdded:
                self.Corpus.append(lineToAdd)
                rawLinesAdded.append(diseaseRecord.Line)
                linesAlreadyAdded.append(lineToAdd)

                if diseaseRecord.Line == "Ischemia":
                    print("found Ischemia as " + lineToAdd)
                elif diseaseRecord.Line == "ischemia":
                    print("found ischemia as " + lineToAdd)

        self.Model = self.Vectorizer.fit_transform(self.Corpus)
        self.Lines = rawLinesAdded

        return

    def FindClosestMatches(self, queryText, numberToReturn, minimumGoodnessScore):
        translator = str.maketrans('', '', string.punctuation)
        matchMatrix = self.Vectorizer.transform([queryText.lower().translate(translator)])
        resultMatrix = ((matchMatrix * self.Model.T).A[0])

        #exists1 = "ischemia" in self.Lines
        #exists2 = "Ischemia" in self.Lines

        matchedLines = {}
        if np.any(resultMatrix):
            if len(resultMatrix) < numberToReturn:
                numberToReturn = len(resultMatrix)

            bestChoicesIndices = np.argsort(resultMatrix)[-30:]

            for bestChoiceIndex in bestChoicesIndices:
                grade = resultMatrix[bestChoiceIndex]
                if grade > minimumGoodnessScore:
                    line = self.Lines[bestChoiceIndex]
                    if not line in matchedLines:
                        matchedLines[line] = grade

        return matchedLines

def TrimUsingOntologyDatabases(recommendationTuples):

    #duplicate the list to be trimmed
    finalList = []
    meshToIgnore = []
    dodToIgnore = []

    for recommendation, weight in recommendationTuples.items():
        
        bestMeshFamilyMember = ""
        bestDODFamilyMember = ""

        if not recommendation in meshToIgnore:
            bestMeshScore = 0

            # is there a matching mesh record? 
            meshRecords = MeshRecord.objects.filter(Name = recommendation)
            for meshRecord in meshRecords:

                # prepare for finding the best of any family. 
                bestMeshScore = weight
                bestMeshFamilyMember = recommendation

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
                        bestMeshFamilyMember = member.Name
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
                        bestDODFamilyMember = member.Name
                    else:
                        dodToIgnore.append(member.Name)

        if bestMeshFamilyMember == bestDODFamilyMember and bestMeshFamilyMember is not "" and not bestMeshFamilyMember in finalList:
            # the same phrase is in both ontologies. 
            finalList.append(bestMeshFamilyMember)
        else:
            # separate names in separate ontologies
            if bestMeshFamilyMember is not "" and not bestMeshFamilyMember in finalList:
                finalList.append(bestMeshFamilyMember)
            if bestDODFamilyMember is not "" and not bestDODFamilyMember in finalList:
                finalList.append(bestDODFamilyMember)

    return finalList

def FindRecommendations(query, tfidf, numberOfRecommendations, minimumGoodnessScore):
    
    diseaseRecordsToReturn = {}

    # use if-idf to find best we can
    if len(diseaseRecordsToReturn) == 0:
        diseaseRecordsToReturn.update(tfidf.FindClosestMatches(query.Tag, numberOfRecommendations, minimumGoodnessScore))

    # nothing?  is this an abbreviation?  Can we pull out its meaning
    # from the source text?
    if len(diseaseRecordsToReturn) == 0:
        matches = re.fullmatch(r"[A-Z0-9]*(-[A-Z0-9a-z]*)?", query.Tag)
        if matches:
            possibleMeaning = query.FindAbbreviationMeaningInSource(query.Tag)
            if possibleMeaning:
                diseaseRecordsToReturn.update(tfidf.FindClosestMatches(possibleMeaning, numberOfRecommendations, minimumGoodnessScore))
            if len(diseaseRecordsToReturn) == 0: # still nothing!?
                #is this dash-separated?
                if "-" in query.Tag:
                    parts = query.Tag.split('-')
                    for part in parts:
                        possibleMeaning = query.FindAbbreviationMeaningInSource(part)
                        if possibleMeaning:
                            diseaseRecordsToReturn.update(tfidf.FindClosestMatches(possibleMeaning, numberOfRecommendations, minimumGoodnessScore))

                    # STILL nothing!?!  Just try straight-up looking at the
                    # text.
                    for part in parts: 
                        diseaseRecordsToReturn.update(tfidf.FindClosestMatches(part, numberOfRecommendations, minimumGoodnessScore))

    return diseaseRecordsToReturn

def TrainAndPickle(outputPath):
    diseaseRecords = []

    records = MeshRecord.objects.all()
    for record in records:
        diseaseRecords.append(DiseaseRecord(record.Name))

    records = DODRecord.objects.all()
    for record in records:
        diseaseRecords.append(DiseaseRecord(record.Name))

    tfidf = TFIDF()
    tfidf.TrainModel(diseaseRecords)

    with open(outputPath, 'wb') as fout:
        pickle.dump(tfidf, fout)


