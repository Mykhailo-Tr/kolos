from django import forms
from .models import WasteJournal


class WasteJournalForm(forms.ModelForm):
    """Форма для журналу управління відходами"""

    class Meta:
        model = WasteJournal
        fields = [
            "date_time",
            "action",
            "culture",
            "place_from",
            "place_to",
            "quantity",
        ]
        widgets = {
            "date_time": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "action": forms.Select(attrs={"class": "form-select"}),
            "culture": forms.Select(attrs={"class": "form-select"}),
            "place_from": forms.Select(attrs={"class": "form-select"}),
            "place_to": forms.Select(attrs={"class": "form-select"}),
            "quantity": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.001",
                    "min": "0",
                    "placeholder": "Вкажіть кількість (т)"
                }
            ),
        }

    def clean(self):
        """Валідація залежності між дією та місцями"""
        cleaned_data = super().clean()
        action = cleaned_data.get("action")
        place_to = cleaned_data.get("place_to")

        if action == "recycling" and not place_to:
            self.add_error("place_to", "Для переробки потрібно вказати місце призначення.")
        if action == "utilization" and place_to:
            self.add_error("place_to", "Для утилізації не потрібно місце призначення.")

        return cleaned_data
