# forms.py
from django import forms
from dal import autocomplete
from django.utils.timezone import now
from .models import WeigherJournal, ShipmentJournal, ArrivalJournal

class WeigherJournalForm(forms.ModelForm):
    class Meta:
        model = WeigherJournal
        fields = [
            "document_number", "date_time", "sender", "receiver",
            "car", "driver", "trailer", "culture",
            "weight_gross", "weight_tare", "unloading_place", "note"
        ]

        widgets = {
            "document_number": forms.TextInput(attrs={"class": "form-control"}),
            "date_time": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M"
            ),

            # sender / receiver: searchable, but NO inline creation
            "sender": autocomplete.ModelSelect2(
                url='sender-autocomplete',
                attrs={
                    "data-placeholder": "Введіть або оберіть відправника",
                    "data-minimum-input-length": 0,
                    "class": "form-control ajax-no-tags"
                }
            ),
            "receiver": autocomplete.ModelSelect2(
                url='receiver-autocomplete',
                attrs={
                    "data-placeholder": "Введіть або оберіть отримувача",
                    "data-minimum-input-length": 0,
                    "class": "form-control ajax-no-tags"
                }
            ),

            # car, driver, trailer, culture: searchable + allow typing new values (tags)
            # We will init these selects on client side with select2(tags: true)
            "car": autocomplete.ModelSelect2(
                url='car-autocomplete',
                attrs={
                    "data-placeholder": "Введіть або оберіть авто",
                    "data-minimum-input-length": 0,
                    "class": "form-control ajax-tags"
                }
            ),
            "driver": autocomplete.ModelSelect2(
                url='driver-autocomplete',
                attrs={
                    "data-placeholder": "Введіть або оберіть водія",
                    "data-minimum-input-length": 0,
                    "class": "form-control ajax-tags"
                }
            ),
            "trailer": autocomplete.ModelSelect2(
                url='trailer-autocomplete',
                attrs={
                    "data-placeholder": "Введіть або оберіть причіп",
                    "data-minimum-input-length": 0,
                    "class": "form-control ajax-tags"
                }
            ),
            "culture": autocomplete.ModelSelect2(
                url='culture-autocomplete',
                attrs={
                    "data-placeholder": "Введіть або оберіть культуру",
                    "data-minimum-input-length": 0,
                    "class": "form-control ajax-tags"
                }
            ),

            "weight_gross": forms.NumberInput(attrs={"class": "form-control", "step": "1", "id": "id_weight_gross"}),
            "weight_tare": forms.NumberInput(attrs={"class": "form-control", "step": "1", "id": "id_weight_tare"}),

            "unloading_place": autocomplete.ModelSelect2(
                url='unloading-autocomplete',
                attrs={
                    "data-placeholder": "Введіть або оберіть місце розвантаження",
                    "data-minimum-input-length": 0,
                    "class": "form-control ajax-no-tags"
                }
            ),

            "note": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # default date_time only for new instances
        if not self.instance.pk:
            self.fields["date_time"].initial = now().strftime("%Y-%m-%dT%H:%M")


class ShipmentJournalForm(forms.ModelForm):
    class Meta:
        model = ShipmentJournal
        fields = [
            "document_number", "date_time", "sender",
            "car", "driver", "trailer", "culture",
            "weight_gross", "weight_tare", "unloading_place", "note"
        ]
        # Similar widget definitions as in WeigherJournalForm
        widgets = WeigherJournalForm.Meta.widgets.copy()
        del widgets["receiver"]  # ShipmentJournal does not have receiver

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields["date_time"].initial = now().strftime("%Y-%m-%dT%H:%M")
            

class ArrivalJournalForm(forms.ModelForm):
    class Meta:
        model = ArrivalJournal
        fields = [
            "document_number", "date_time", "sender_or_receiver",
            "car", "driver", "trailer", "culture",
            "weight_gross", "weight_tare", "unloading_place", "note"
        ]
        # Similar widget definitions as in WeigherJournalForm
        widgets = WeigherJournalForm.Meta.widgets.copy()
        del widgets["sender"]
        del widgets["receiver"]
        widgets["sender_or_receiver"] = autocomplete.ModelSelect2(
            url='partner-autocomplete',  
            attrs={
                "data-placeholder": "Введіть або оберіть відправника / отримувача",
                "data-minimum-input-length": 0,
                "class": "form-control ajax-no-tags"
            }
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields["date_time"].initial = now().strftime("%Y-%m-%dT%H:%M")