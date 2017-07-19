"""
Definition of urls for NormalizationModule.
"""

from datetime import datetime
from django.conf.urls import url
import django.contrib.auth.views

import app.forms
import app.views


urlpatterns = [
    url(r'^$', app.views.home, name='home'),
    url(r'^thanks', app.views.thanks, name='thanks'),
    url(r'^why', app.views.why, name='why'),
    url(r'^breakup', app.views.breakup, name='breakup'),
    url(r'^nomatch', app.views.nomatch, name='nomatch'),
    url(r'^matchquality', app.views.matchquality, name='nomatch'),
]
