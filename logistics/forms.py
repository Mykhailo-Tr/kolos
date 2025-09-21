from django import forms
from dal import autocomplete
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
            # For each autocomplete field, set placeholder and min input length.
            # Removed data-tags since inline creation is handled via the "+" buttons.
            "sender": autocomplete.ModelSelect2(
                url='sender-autocomplete',
                attrs={
                    "data-placeholder": "Оберіть відправника",
                    "data-minimum-input-length": 0,
                    "data-allow-clear": "true"
                }
            ),
            "receiver": autocomplete.ModelSelect2(
                url='receiver-autocomplete',
                attrs={
                    "data-placeholder": "Оберіть отримувача",
                    "data-minimum-input-length": 0,
                    "data-allow-clear": "true"
                }
            ),
            "car": autocomplete.ModelSelect2(
                url='car-autocomplete',
                attrs={
                    "data-placeholder": "Оберіть автомобіль",
                    "data-minimum-input-length": 0,
                    "data-allow-clear": "true"
                }
            ),
            "driver": autocomplete.ModelSelect2(
                url='driver-autocomplete',
                attrs={
                    "data-placeholder": "Оберіть водія",
                    "data-minimum-input-length": 0,
                    "data-allow-clear": "true"
                }
            ),
            "trailer": autocomplete.ModelSelect2(
                url='trailer-autocomplete',
                attrs={
                    "data-placeholder": "Оберіть причіп",
                    "data-minimum-input-length": 0,
                    "data-allow-clear": "true"
                }
            ),
            "culture": autocomplete.ModelSelect2(
                url='culture-autocomplete',
                attrs={
                    "data-placeholder": "Оберіть культуру",
                    "data-minimum-input-length": 0,
                    "data-allow-clear": "true"
                }
            ),
            "weight_gross": forms.NumberInput(attrs={"class": "form-control", "step": "1"}),
            "weight_tare": forms.NumberInput(attrs={"class": "form-control", "step": "1"}),
            "unloading_place": autocomplete.ModelSelect2(
                url='unloading-autocomplete',
                attrs={
                    "data-placeholder": "Оберіть місце розвантаження",
                    "data-minimum-input-length": 0,
                    "data-allow-clear": "true"
                }
            ),
            "driver_signature": forms.TextInput(attrs={"class": "form-control"}),
            "note": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # default date_time only for new instances
        if not self.instance.pk:
            self.fields["date_time"].initial = now().strftime("%Y-%m-%dT%H:%M")
