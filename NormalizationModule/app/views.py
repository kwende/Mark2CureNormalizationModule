"""
Definition of views.
"""

from django.shortcuts import render
from django.http import HttpRequest, HttpResponseRedirect, HttpResponse, QueryDict
from django.template import RequestContext
from datetime import datetime
from os import path, getcwd
import NormalizationModule.mark2cure.dataaccess
import NormalizationModule.mark2cure.nlp
from NormalizationModule.mark2cure.nlp import DiseaseRecord, FindRecommendations, Mark2CureQuery, TFIDF
import app.forms
import pickle
import urllib.parse
from enum import Enum
import operator

MaximumNumberOfOptionsToDisplay = 3

def home(request):
    return render(request,
                  'app/index.html')

def matchquality(request):
    """Renders the home page."""
    assert isinstance(request, HttpRequest)

    if request.method == "POST":

        for variable in request.POST:
            if variable.startswith('match_'):
                unquoted = urllib.parse.unquote(variable).replace('match_', '')
                underScoreIndex = unquoted.index('_')
                ontologyType = unquoted[:underScoreIndex]

                key = unquoted[underScoreIndex+1:]
                value = int(request.POST[variable])

                dbRecordId = NormalizationModule.mark2cure.dataaccess.GetIdForOntologyRecord(ontologyType, key)

                annotationId = int(request.POST["annotationId"])
                documentId = int(request.POST["documentId"])
                NormalizationModule.mark2cure.dataaccess.SaveMatchStrengthRecord(annotationId, documentId, ontologyType, dbRecordId, value)

        return HttpResponseRedirect('/thanks/')
    else:
        # continue looping until we find something for which matches are identified. 
        while True:
            passageText, annotationText, documentId, annotationId = NormalizationModule.mark2cure.dataaccess.GetRandomAnnotation()

            tfidf = None
            trainedPickle = path.join(getcwd(), 'trained.pickle')
            with open(trainedPickle, 'rb') as fin:
                tfidf = pickle.load(fin)

            query = Mark2CureQuery(annotationText, passageText)
            recommendationsWithWeights = FindRecommendations(query, tfidf, 30, .5)

            recommendationsWithWeights = NormalizationModule.mark2cure.dataaccess.TrimUsingOntologyDatabases(recommendationsWithWeights)
            
            sortedList = sorted(recommendationsWithWeights, key=operator.itemgetter(2), reverse = True)
            if len(sortedList) > MaximumNumberOfOptionsToDisplay:
                sortedList = sortedList[0:MaximumNumberOfOptionsToDisplay]

            if len(recommendationsWithWeights) == 0:
                NormalizationModule.mark2cure.dataaccess.SaveMatchStrengthRecordForNoMatches(documentId, annotationId)
            else:
                break

        matches = []
        for r in sortedList:
            key = urllib.parse.quote('match_' + r[1] + '_' + r[0])
            value = r[0]
            matches.append((key, value, r[1], r[3]))

        dropDownOptions = {}
        dropDownOptions["2"] = "Perfect Match"
        dropDownOptions["1"] = "Partial Match"
        dropDownOptions["0"] = "Bad Match"

        index = passageText.lower().index(annotationText.lower())
        startIndex = index - 50
        if startIndex < 0:
            startIndex = 0
        endIndex = index + 50
        if endIndex >= len(passageText):
            endIndex = len(passageText)-1

        return render(request,
            'app/matchquality.html',
            {
                'annotationText':annotationText,
                'matches': matches,
                'dropDownOptions' : dropDownOptions.items(),
                'matchCount' : len(matches),
                'passageText' : "[...]" + passageText[startIndex:endIndex] + "[...]",
                'documentId' : documentId,
                'annotationId' : annotationId
            })

def explain_match(request):

    if request.method == "POST":
        MatchStrengthRecordId = int(request.POST['MatchStrengthRecordId'])
        matchStrength = NormalizationModule.mark2cure.dataaccess.MatchStrength(int(request.POST["MatchStrength"]))
        reasonAsInt = int(request.POST["reasons"])

        if matchStrength == NormalizationModule.mark2cure.dataaccess.MatchStrength.PartialMatch:
            reason = NormalizationModule.mark2cure.dataaccess.PartialMatchReasons(reasonAsInt)
            NormalizationModule.mark2cure.dataaccess.UpdateMatchStrengthRecordWithReason(MatchStrengthRecordId, reason)
        elif matchStrength == NormalizationModule.mark2cure.dataaccess.MatchStrength.PoorMatch:
            reason = NormalizationModule.mark2cure.dataaccess.PoorMatchReasons(reasonAsInt)
            NormalizationModule.mark2cure.dataaccess.UpdateMatchStrengthRecordWithReason(MatchStrengthRecordId, reason)

        return HttpResponseRedirect('/thanks/')
    else:
        unexplainedMatch = NormalizationModule.mark2cure.dataaccess.GetRandomAnnotationInExplanationPhase()

        annotationText = unexplainedMatch.AnnotationText
        ontologyText = unexplainedMatch.OntologyText

        matchStrength = NormalizationModule.mark2cure.dataaccess.MatchStrength(unexplainedMatch.MatchStrength)
        matchStrengthText = ""

        form = None
        if matchStrength == NormalizationModule.mark2cure.dataaccess.MatchStrength.PartialMatch:
            matchStrengthText = "partial match"
            choiceList = [(NormalizationModule.mark2cure.dataaccess.PartialMatchReasons.AIsMoreSpecificThanB.value, annotationText + " is more specific than " + ontologyText), 
                       (NormalizationModule.mark2cure.dataaccess.PartialMatchReasons.AIsLessSpecificThanB.value, annotationText + " is less specific than " + ontologyText),
                       (NormalizationModule.mark2cure.dataaccess.PartialMatchReasons.AIsACompoundTerm.value, annotationText + " is a compound term")]
            form = app.forms.ExplainWhyPartialForm(choices = choiceList)
        elif matchStrength == NormalizationModule.mark2cure.dataaccess.MatchStrength.PoorMatch:
            matchStrengthText = "poor match"
            choiceList = [(NormalizationModule.mark2cure.dataaccess.PoorMatchReasons.AIsACompoundTerm.value, annotationText + " is a compound term."), 
                       (NormalizationModule.mark2cure.dataaccess.PoorMatchReasons.AAndBAreUnrelated.value, annotationText + " and " + ontologyText + " are completely unrelated")]
            form = app.forms.ExplainWhyPoorForm(choices = choiceList)

        return render(request, 'app/explain.html',
                      {
                          "matchStrength" : unexplainedMatch.MatchStrength,
                          "matchStregthText" : matchStrengthText,
                          "annotationText" : annotationText,
                          "passageText" : unexplainedMatch.PassageText,
                          "ontologyText" : unexplainedMatch.OntologyText,
                          "MatchStrengthRecordId" : unexplainedMatch.NonPerfectMatchId,
                          "form" : form
                      })

def thanks(request):
    return render(request, 'app/thanks.html', {})