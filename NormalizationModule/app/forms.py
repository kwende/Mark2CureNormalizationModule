"""
Definition of forms.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext_lazy as _

class RecommendationSelectForm(forms.Form):
    recommendations = forms.ChoiceField(choices = [(1, 'Mac'), (2, 'PC')], widget=forms.RadioSelect())
