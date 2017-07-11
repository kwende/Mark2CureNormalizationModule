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
            # TODO: create a hidden field for the item that was being matched. 
            # then go through and pass it. 
            return HttpResponseRedirect('/why/?' + queryString)
        if 'no_match' in request.POST:
            return

        return HttpResponseRedirect('/thanks/')
    else:
        passageText, annotationText = NormalizationModule.mark2cure.dataaccess.GetRandomAnnotation()

        desciptorPath = path.join(getcwd(), 'descriptors.pickle')

        query = Mark2CureQuery(annotationText[0], passageText[0])
        meshRecords = ReadMeshRecordsFromDisk(desciptorPath)
        tfidf = TFIDF()
        tfidf.TrainModel(meshRecords)
        recommendations = FindRecommendations(query, meshRecords, tfidf, 4)

        choices = []
        for r in recommendations:
            choices.append((r.MainLine,r.MainLine))

        form = app.forms.RecommendationSelectForm(choices = choices)

        return render(request,
            'app/index.html',
            {
                'annotationText':annotationText[0],
                'form': form
            })

def why(request):

    annotationText = request.GET['annotationText']
    recommendation = request.GET['recommendation']

    option1 = "Because %s is more specific than %s" % (annotationText, recommendation)
    option2 = "Because %s is less specific than %s" % (annotationText, recommendation)

    form = app.forms.WhyOnlyPartialMatchForm(choices = [(0, option1), (1 , option2)])

    return render(request, "app/why.html", 
                  {
                      'annotationText' : request.GET['annotationText'],
                      'recommendation' : request.GET['recommendation'],
                      'form' : form
                  })

def thanks(request):
    return render(request, 'app/thanks.html', {})

def contact(request):
    """Renders the contact page."""
    assert isinstance(request, HttpRequest)
    return render(request,
        'app/contact.html',
        {
            'title':'Contact',
            'message':'Your contact page.',
            'year':datetime.now().year,
        })

def about(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    return render(request,
        'app/about.html',
        {
            'title':'About',
            'message':'Your application description page.',
            'year':datetime.now().year, 
        })
