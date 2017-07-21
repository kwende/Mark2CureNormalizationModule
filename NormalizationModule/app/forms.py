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

class ExplainWhyPoorForm(forms.Form):
    reasons = forms.ChoiceField(required = True, label="Reasons:", choices=[], widget=forms.RadioSelect())

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices', None)
        super(ExplainWhyPoorForm, self).__init__(*args, **kwargs)
        if choices is not None:
            self.fields['reasons'].choices = choices

class ExplainWhyPartialForm(forms.Form):
    reasons = forms.ChoiceField(required = True, label="Reasons:", choices=[], widget=forms.RadioSelect())

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices', None)
        super(ExplainWhyPartialForm, self).__init__(*args, **kwargs)
        if choices is not None:
            self.fields['reasons'].choices = choices