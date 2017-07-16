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

        for diseaseRecord in diseaseRecords:
            lineToAdd = diseaseRecord.Line.lower().translate(translator)
            if not lineToAdd in linesAlreadyAdded:
                self.Corpus.append(lineToAdd)
                linesAlreadyAdded.append(lineToAdd)

        self.Model = self.Vectorizer.fit_transform(self.Corpus)
        self.Lines = linesAlreadyAdded

        return

    def FindClosestMatches(self, queryText, numberToReturn):
        translator = str.maketrans('', '', string.punctuation)
        matchMatrix = self.Vectorizer.transform([queryText.lower().translate(translator)])
        resultMatrix = ((matchMatrix * self.Model.T).A[0])

        matchedLines = []
        if np.any(resultMatrix):
            bestChoicesIndices = np.argpartition(resultMatrix, -numberToReturn)[-numberToReturn:]

            for bestChoiceIndex in bestChoicesIndices:
                line = self.Lines[bestChoiceIndex]
                if not line in matchedLines:
                    matchedLines.append(line)

        return matchedRecords

def FindRecommendations(query, tfidf, numberOfRecommendations):
    
    diseaseRecordsToReturn = []

    # use if-idf to find best we can
    if len(diseaseRecordsToReturn) == 0:
        diseaseRecordsToReturn = diseaseRecordsToReturn + tfidf.FindClosestMatches(query.Tag, numberOfRecommendations)

    # nothing?  is this an abbreviation?  Can we pull out its meaning
    # from the source text?
    if len(diseaseRecordsToReturn) == 0:
        matches = re.fullmatch(r"[A-Z0-9]*(-[A-Z0-9a-z]*)?", query.Tag)
        if matches:
            possibleMeaning = query.FindAbbreviationMeaningInSource(query.Tag)
            if possibleMeaning:
                diseaseRecordsToReturn = diseaseRecordsToReturn + tfidf.FindClosestMatches(possibleMeaning, numberOfRecommendations)
            if len(diseaseRecordsToReturn) == 0: # still nothing!?
                #is this dash-separated?
                if "-" in query.Tag:
                    parts = query.Tag.split('-')
                    for part in parts:
                        possibleMeaning = query.FindAbbreviationMeaningInSource(part)
                        if possibleMeaning:
                            diseaseRecordsToReturn = diseaseRecordsToReturn + tfidf.FindClosestMatches(possibleMeaning, numberOfRecommendations)

                    # STILL nothing!?!  Just try straight-up looking at the
                    # text.
                    for part in parts: 
                        diseaseRecordsToReturn = diseaseRecordsToReturn + tfidf.FindClosestMatches(part, numberOfRecommendations)

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
