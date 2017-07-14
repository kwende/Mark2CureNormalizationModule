"""
Definition of forms.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext_lazy as _

class RecommendationSelectForm(forms.Form):
    recommendations = forms.ChoiceField(required=False,label="Matches we found:", choices =[], widget=forms.RadioSelect())
    annotation = forms.CharField(required=True, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices', None)

        super(RecommendationSelectForm, self).__init__(*args, **kwargs)

        if choices is not None:
            self.fields['recommendations'].choices = choices

class WhyPoorMatchForm(forms.Form):
    reasons = forms.ChoiceField(label="Choices:", choices=[], widget=forms.RadioSelect())

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices', None)

        super(WhyPoorMatchForm, self).__init__(*args, **kwargs)

        if choices is not None:
            self.fields['reasons'].choices = choices

class WhyOnlyPartialMatchForm(forms.Form):
    reasons = forms.ChoiceField(label="Choices:", choices=[], widget=forms.RadioSelect())

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices', None)

        super(WhyOnlyPartialMatchForm, self).__init__(*args, **kwargs)

        if choices is not None:
            self.fields['reasons'].choices = choices

class PartsForm(forms.Form):
    part1 = forms.CharField(required=True, widget=forms.TextInput())
    part2 = forms.CharField(required=True, widget=forms.TextInput())
    part3 = forms.CharField(required=False, widget=forms.TextInput())
    part4 = forms.CharField(required=False, widget=forms.TextInput())
    part5 = forms.CharField(required=False, widget=forms.TextInput())