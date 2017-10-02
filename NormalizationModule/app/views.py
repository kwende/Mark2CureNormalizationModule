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

def home(request):
    return render(request,
                  'app/index.html')

def matchquality(request):
    """Renders the home page."""
    assert isinstance(request, HttpRequest)

    if request.method == "POST":

        matchGroupId = request.POST["matchGroupId"]
        matchGroupSubmission = NormalizationModule.mark2cure.dataaccess.CreateOntologyMatchSubmission("NOWHEREMAN", \
            matchGroupId)

        for variable in request.POST:
            if variable.startswith('match_'):

                unquoted = urllib.parse.unquote(variable).replace('match_','')
                matchId = int(unquoted)
                matchStrength = int(request.POST[variable])

                NormalizationModule.mark2cure.dataaccess.CreateOntologyMatchQualityForSubmission(matchGroupSubmission, \
                    matchId, matchStrength)

        NormalizationModule.mark2cure.dataaccess.DetermineWhetherConsensusForMatchQualityMet(matchGroupId, 3)

        return HttpResponseRedirect('/thanks/')
    else:
        groupToUse, passageText, annotationText, documentId, annotationId = \
            NormalizationModule.mark2cure.dataaccess.GetRandomOntologyMatchGroup()

        sortedList = NormalizationModule.mark2cure.dataaccess.GetSortedMatchesForMatchGroup(groupToUse, 3)

        matches = []
        for r in sortedList:
            key = urllib.parse.quote('match_' + str(r.id))
            matchString = r.ConvenienceMatchString
            matches.append((key, matchString, r.OntologyName))

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
            endIndex = len(passageText) - 1

        return render(request,
            'app/matchquality.html',
            {
                'annotationText':annotationText,
                'matches': matches,
                'dropDownOptions' : dropDownOptions.items(),
                'matchCount' : len(matches),
                'passageText' : "[...]" + passageText[startIndex:endIndex] + "[...]",
                'documentId' : documentId,
                'matchGroupId' : groupToUse.id
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
        matchQualityToExplain = NormalizationModule.mark2cure.dataaccess.GetRandomMatchQualityConsensus()

        if matchQualityToExplain != None:
            annotationText = matchQualityToExplain.AnnotationText
            ontologyText = matchQualityToExplain.OntologyText

            matchStrength = NormalizationModule.mark2cure.dataaccess.MatchStrength(matchQualityToExplain.MatchStrength)
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
                              "matchStrength" : matchQualityToExplain.MatchStrength,
                              "matchStregthText" : matchStrengthText,
                              "annotationText" : annotationText,
                              "passageText" : matchQualityToExplain.PassageText,
                              "ontologyText" : matchQualityToExplain.OntologyText,
                              "OntologyMatchQualityConsensusId" : matchQualityToExplain.MatchQualityId,
                              "form" : form
                      })
        else:
            return render(request, 'app/nothingToExplain.html')

def thanks(request):
    return render(request, 'app/thanks.html', {})