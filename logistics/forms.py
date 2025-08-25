from django import forms
from django.utils.timezone import now
from .models import Trip


class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = [
            "document_number", "date_time", "sender", "receiver",
            "car", "driver", "trailer", "culture",
            "weight_gross", "weight_tare", "unloading_place",
            "driver_signature", "note"
        ]
        widgets = {
            "document_number": forms.TextInput(attrs={"class": "form-control"}),
            "date_time": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M"
            ),
            "sender": forms.Select(attrs={"class": "form-select"}),
            "receiver": forms.Select(attrs={"class": "form-select"}),
            "car": forms.Select(attrs={"class": "form-select"}),
            "driver": forms.Select(attrs={"class": "form-select"}),
            "trailer": forms.Select(attrs={"class": "form-select"}),
            "culture": forms.Select(attrs={"class": "form-select"}),
            "weight_gross": forms.NumberInput(attrs={"class": "form-control", "step": "1"}),
            "weight_tare": forms.NumberInput(attrs={"class": "form-control", "step": "1"}),
            "unloading_place": forms.Select(attrs={"class": "form-select"}),
            "driver_signature": forms.TextInput(attrs={"class": "form-control"}),
            "note": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # якщо створюється новий Trip, ставимо поточний час
        if not self.instance.pk:
            self.fields["date_time"].initial = now().strftime("%Y-%m-%dT%H:%M")
