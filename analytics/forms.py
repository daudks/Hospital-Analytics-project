from django import forms
from .models import Dataset


class DatasetForm(forms.ModelForm):
    class Meta:
        model = Dataset
        fields = ['name', 'file']
        widgets = {
            'file': forms.ClearableFileInput(attrs={'accept': '.csv,.xlsx,.json'})
        }
