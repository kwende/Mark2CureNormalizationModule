"""
Definition of views.
"""

from django.shortcuts import render
from django.http import HttpRequest
from django.template import RequestContext
from datetime import datetime
import os
import app.mark2cure.dataaccess
import app.mark2cure.matcher

def home(request):
    """Renders the home page."""
    assert isinstance(request, HttpRequest)
    cwd = os.getcwd()
    annotation = app.mark2cure.dataaccess.GetRandomAnnotation()

    app.mark2cure.matcher.FindRecommendations()

    return render(
        request,
        'app/index.html',
        {
            'title':annotation,
            'message':annotation
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
