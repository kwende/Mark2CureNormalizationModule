"""
Definition of views.
"""

from django.shortcuts import render
from django.http import HttpRequest
from django.template import RequestContext
from datetime import datetime
from mark2cure import dataaccess

def home(request):
    """Renders the home page."""
    assert isinstance(request, HttpRequest)

    randomAnnotation = mark2cure.dataaccess.GetRandomAnnotation()

    return render(
        request,
        'app/index.html',
        {
            'title':'Home Page',
            'message':'test'
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
