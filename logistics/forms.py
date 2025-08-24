from django import forms
from .models import Trip


class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = [
            "document_number", "sender", "receiver", "car", "driver", "trailer",
            "culture", "weight_gross", "weight_tare", "unloading_place",
            "driver_signature", "note"
        ]
        widgets = {
            "date_time": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "note": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }
