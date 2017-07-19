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

            query = Mark2CureQuery(annotationText[0], passageText[0])
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
                'annotationText':annotationText[0],
                'matches': matches,
                'dropDownOptions' : dropDownOptions.items(),
                'matchCount' : len(matches),
                'passageText' : passageText[0],
                'documentId' : documentId,
                'annotationId' : annotationId
            })

def nomatch(request):
    annotationText = request.GET['annotationText']
    recommendation = request.GET['recommendation']

    option1 = "Because '%s' and '%s' are completely unrelated" % (annotationText, recommendation)
    option2 = "Because '%s' is a compound term and must be broken up further." % (recommendation)

    form = app.forms.WhyPoorMatchForm(choices = [(1,option1),(2,option2)])
    return render(request, "app/nomatch.html", 
    {
       'form' : form
    })
     
def breakup(request):
    if request.method == "POST":
        return HttpResponseRedirect('/thanks/')
    else:
        form = app.forms.PartsForm()
        return render(request, "app/breakup.html", 
                      {
                          "form" : form,
                          "recommendation": request.GET['recommendation']
                      })

def why(request):

    if request.method == "POST":
        
        reason = int(request.POST['reasons'])
        if reason == 0:
            return HttpResponseRedirect('/thanks/')
        elif reason == 1:
            return HttpResponseRedirect('/thanks/')
        elif reason == 2:
            recommendation = request.GET['recommendation']
            dict = QueryDict("", mutable =True)
            dict['recommendation'] = recommendation
            queryString = dict.urlencode()
            return HttpResponseRedirect('/breakup/?' + queryString)
        else:
            return
    else:
        annotationText = request.GET['annotationText']
        recommendation = request.GET['recommendation']

        option1 = "Because '%s' is more specific than '%s'" % (annotationText, recommendation)
        option2 = "Because '%s' is less specific than '%s'" % (annotationText, recommendation)
        option3 = "Because '%s' is a compound term and must be broken up further." % (recommendation)

        form = app.forms.WhyOnlyPartialMatchForm(choices = [(0, option1), (1 , option2), (2, option3)])
        
        return render(request, "app/why.html", 
                      {
                          'annotationText' : request.GET['annotationText'],
                          'recommendation' : request.GET['recommendation'],
                          'form' : form
                      })

def thanks(request):
    return render(request, 'app/thanks.html', {})