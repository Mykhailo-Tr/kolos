from django import forms
from .models import Culture

class CultureForm(forms.ModelForm):
    class Meta:
        model = Culture
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Назва культури"})
        }
