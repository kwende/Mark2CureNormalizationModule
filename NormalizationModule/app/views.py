"""
Definition of views.
"""

from django.shortcuts import render
from django.http import HttpRequest, HttpResponseRedirect, HttpResponse, QueryDict
from django.template import RequestContext
from datetime import datetime
from os import path, getcwd
import NormalizationModule.mark2cure.dataaccess
import NormalizationModule.mark2cure.matcher
from NormalizationModule.mark2cure.matcher import MeshRecord, FindRecommendations, Mark2CureQuery, ReadMeshRecordsFromDisk, TFIDF
import app.forms

def home(request):
    """Renders the home page."""
    assert isinstance(request, HttpRequest)

    if request.method == "POST":
        if 'perfect_match' in request.POST:
            return HttpResponseRedirect('/thanks/')
        if 'partial_match' in request.POST:
            dict = QueryDict("", mutable =True)
            dict['annotationText'] = request.POST['annotationText']
            dict['recommendation'] = request.POST['recommendations']
            queryString = dict.urlencode()
            return HttpResponseRedirect('/why/?' + queryString)
        if 'no_match' in request.POST:
            return HttpResponseRedirect('/thanks/')

        return HttpResponseRedirect('/thanks/')
    else:
        passageText, annotationText = NormalizationModule.mark2cure.dataaccess.GetRandomAnnotation()

        desciptorPath = path.join(getcwd(), 'descriptors.pickle')

        query = Mark2CureQuery(annotationText[0], passageText[0])
        meshRecords = ReadMeshRecordsFromDisk(desciptorPath)
        tfidf = TFIDF()
        tfidf.TrainModel(meshRecords)
        recommendations = FindRecommendations(query, meshRecords, tfidf, 4)

        matches = []
        for r in recommendations:
            matches.append((r.MainLine,r.MainLine))

        #form = app.forms.RecommendationSelectForm(choices = choices)

        dropDownOptions = {}
        dropDownOptions["PerfectMatch"] = "Perfect Match"
        dropDownOptions["PartialMatch"] = "Partial Match"
        dropDownOptions["BadMatch"] = "Bad Match"

        return render(request,
            'app/index.html',
            {
                'annotationText':annotationText[0],
                'matches': matches,
                'dropDownOptions' : dropDownOptions.items(),
                'matchCount' : len(matches)
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