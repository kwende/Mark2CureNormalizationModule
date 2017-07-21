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
                NormalizationModule.mark2cure.dataaccess.SaveMatchRecord(annotationId, documentId, ontologyType, dbRecordId, value)

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
            recommendationsWithWeights = FindRecommendations(query, tfidf, 30, .45)

            recommendations = NormalizationModule.mark2cure.dataaccess.TrimUsingOntologyDatabases(recommendationsWithWeights)

            if len(recommendations) == 0:
                NormalizationModule.mark2cure.dataaccess.SaveMatchRecordForNoMatches(documentId, annotationId)
            else:
                break

        matches = []
        for r in recommendations:
            key = urllib.parse.quote('match_' + r[1] + '_' + r[0])
            value = r[0]
            matches.append((key, value))

        dropDownOptions = {}
        dropDownOptions["2"] = "Perfect Match"
        dropDownOptions["1"] = "Partial Match"
        dropDownOptions["0"] = "Bad Match"

        return render(request,
            'app/matchquality.html',
            {
                'annotationText':annotationText,
                'matches': matches,
                'dropDownOptions' : dropDownOptions.items(),
                'matchCount' : len(matches),
                'passageText' : passageText,
                'documentId' : documentId,
                'annotationId' : annotationId
            })

def explain_match(request):
    unexplainedMatch = NormalizationModule.mark2cure.dataaccess.GetRandomNonPerfectMatch()

    annotationText = unexplainedMatch.AnnotationText
    ontologyText = unexplainedMatch.OntologyText

    matchStrength = NormalizationModule.mark2cure.dataaccess.MatchStrength(unexplainedMatch.MatchStrength)
    matchStrengthText = ""

    form = None
    if matchStrength == NormalizationModule.mark2cure.dataaccess.MatchStrength.PartialMatch:
        matchStrengthText = "partial match"
        choiceList = [(0, annotationText + " is more specific than " + ontologyText), 
                   (1, annotationText + " is less specific than " + ontologyText),
                   (2, annotationText + " is a compound term")]
        form = app.forms.ExplainWhyPartialForm(choices = choiceList)
    elif matchStrength == NormalizationModule.mark2cure.dataaccess.MatchStrength.PoorMatch:
        matchStrengthText = "poor match"
        choiceList = [(0, annotationText + " is a compound term."), 
                   (1, annotationText + " and " + ontologyText + " are completely unrelated")]
        form = app.forms.ExplainWhyPoorForm(choices = choiceList)

    return render(request, 'app/explain.html',
                  {
                      "matchStregthText" : matchStrengthText,
                      "annotationText" : annotationText,
                      "passageText" : unexplainedMatch.PassageText,
                      "ontologyText" : unexplainedMatch.OntologyText,
                      "matchRecordId" : unexplainedMatch.NonPerfectMatchId,
                      "form" : form
                  })

def thanks(request):
    return render(request, 'app/thanks.html', {})