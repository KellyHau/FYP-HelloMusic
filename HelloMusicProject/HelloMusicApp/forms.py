from django import forms
from .models import *

class MusicSheetForm(forms.ModelForm):
    class Meta:
        model = MusicSheet
        fields = ['title']
        