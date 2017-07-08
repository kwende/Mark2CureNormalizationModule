"""
Definition of views.
"""

from django.shortcuts import render
from django.http import HttpRequest
from django.template import RequestContext
from datetime import datetime
from os import path, getcwd
import NormalizationModule.mark2cure.dataaccess
from NormalizationModule.mark2cure.matcher import MeshRecord, FindRecommendations, Mark2CureQuery, ReadMeshRecordsFromDisk, TFIDF
#import app.mark2cure.matcher

def home(request):
    """Renders the home page."""
    assert isinstance(request, HttpRequest)
    annotationText, passageText = NormalizationModule.mark2cure.dataaccess.GetRandomAnnotation()

    desciptorPath = path.join(getcwd(), 'descriptors.pickle')

    query = Mark2CureQuery(annotationText, passageText)
    meshRecords = ReadMeshRecordsFromDisk(desciptorPath)
    tfidf = TFIDF()
    tfidf.TrainModel(meshRecords)
    recommendations = FindRecommendations(query, meshRecords, tfidf, 4)

    return render(
        request,
        'app/index.html',
        {
            'title':annotationText,
            'message':recommendations[0]
        }
    )

def contact(request):
    """Renders the contact page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/contact.html',
        {
            'title':'Contact',
            'message':'Your contact page.',
            'year':datetime.now().year,
        }
    )

def about(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/about.html',
        {
            'title':'About',
            'message':'Your application description page.',
            'year':datetime.now().year,
        }
    )
