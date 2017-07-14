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

class MeshRecord:

    def __init__(self, mainLine, synonyms):

        self.MainLine = self.CleanText(mainLine)
        self.Synonyms = [self.CleanText(s) for s in synonyms]

        tokens = word_tokenize(self.MainLine)
        self.MainLineAbbreviation = "".join([t[0][0] for t in nltk.pos_tag(tokens) if t[1] != "IN"])

        self.SynonymAbbreviations = []
        for synonym in self.Synonyms:
            tokens = word_tokenize(synonym)
            self.SynonymAbbreviations.append("".join([t[0][0] for t in nltk.pos_tag(tokens) if t[1] != "IN"]))

        return

    def CleanText(self, text):

        toReturn = text
        toReturn = toReturn.replace(" 's","'s")

        return toReturn

    def IsExactMatch(self, mark2CureQuery):
        
        textToMatch = mark2CureQuery.Tag.lower()

        if self.MainLine.lower() == textToMatch:
            quality = 1
        else:
            for synonym in self.Synonyms:
                if synonym.lower() == textToMatch:
                    quality = 1
                    break

    def GetAbbreviationQuality(self, abbreviation):

        smallestDistance = edit_distance(abbreviation, self.MainLineAbbreviation)

        for synonymAbbreviation in self.SynonymAbbreviations:
            curDistance = edit_distance(abbreviation, synonymAbbreviation)
            if curDistance < smallestDistance:
                smallestDistance = curDistance

        return smallestDistance

    def DoesAbbreviationMatch(self, abbreviation):
        matches = False

        if abbreviation.lower() == self.MainLineAbbreviation:
            matches = True
        else:
            for synonymAbbreviation in self.SynonymAbbreviations:
                if synonymAbbreviation.lower() == abbreviation.lower():
                    matches = True
                    break

        return matches; 

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
        self.RecordsTrainedOn = []
        self.Vectorizer = TfidfVectorizer(stop_words="english")
        self.Corpus = []
        self.RecordMap = []

    def TrainModel(self, meshRecords):
        translator = str.maketrans('', '', string.punctuation)

        recordIndex = 0
        for meshRecord in meshRecords:
            self.Corpus.append(meshRecord.MainLine.lower().translate(translator))
            self.RecordMap.append(recordIndex)

            for synonym in meshRecord.Synonyms:
                self.Corpus.append(synonym.lower().translate(str.maketrans(translator)))
                self.RecordMap.append(recordIndex)

            recordIndex = recordIndex + 1

        self.Model = self.Vectorizer.fit_transform(self.Corpus)
        self.RecordsTrainedOn = meshRecords

        return

    def FindClosestMatches(self, queryText, numberToReturn):
        translator = str.maketrans('', '', string.punctuation)
        matchMatrix = self.Vectorizer.transform([queryText.lower().translate(translator)])
        resultMatrix = ((matchMatrix * self.Model.T).A[0])

        matchedRecords = []
        if np.any(resultMatrix):
            bestChoicesIndices = np.argpartition(resultMatrix, -numberToReturn)[-numberToReturn:]

            for bestChoiceIndex in bestChoicesIndices:
                record = self.RecordsTrainedOn[self.RecordMap[bestChoiceIndex]]
                if not record in matchedRecords:
                    matchedRecords.append(record)

        return matchedRecords

def ReadMeshRecordsFromDisk(picklePath):
    meshRecords = []

    with open(picklePath, "rb") as p:
        meshRecords = pickle.load(p)

    return meshRecords

def FindRecommendations(query, meshRecords, tfidf, numberOfRecommendations):
    
    meshRecordsToReturn = []

    # can i find an exact match?
    for meshRecord in meshRecords:
        if meshRecord.IsExactMatch(query):
            meshRecordsToReturn.append(meshRecord)
            break

    # if no perfect matches found, use if-idf to find best we can
    if len(meshRecordsToReturn) == 0:
        meshRecordsToReturn = meshRecordsToReturn + tfidf.FindClosestMatches(query.Tag, numberOfRecommendations)

    # still nothing?  is this an abbreviation?  Can we pull out its meaning
    # from the source text?
    if len(meshRecordsToReturn) == 0:
        matches = re.fullmatch(r"[A-Z0-9]*(-[A-Z0-9a-z]*)?", query.Tag)
        if matches:
            possibleMeaning = query.FindAbbreviationMeaningInSource(query.Tag)
            if possibleMeaning:
                meshRecordsToReturn = meshRecordsToReturn + tfidf.FindClosestMatches(possibleMeaning, numberOfRecommendations)
            if len(meshRecordsToReturn) == 0: # still nothing!?
                #is this dash-separated? 
                if "-" in query.Tag:
                    parts = query.Tag.split('-')
                    for part in parts:
                        possibleMeaning = query.FindAbbreviationMeaningInSource(part)
                        if possibleMeaning:
                            meshRecordsToReturn = meshRecordsToReturn + tfidf.FindClosestMatches(possibleMeaning, numberOfRecommendations)

                    # STILL nothing!?! Just try straight-up looking at the text. 
                    for part in parts: 
                        meshRecordsToReturn = meshRecordsToReturn + tfidf.FindClosestMatches(part, numberOfRecommendations)

    # if we still haven't found anything, 
    #if len(meshRecordsToReturn) == 0:

    return meshRecordsToReturn