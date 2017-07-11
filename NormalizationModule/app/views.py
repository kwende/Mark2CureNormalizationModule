"""
Definition of views.
"""

from django.shortcuts import render
from django.http import HttpRequest
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
