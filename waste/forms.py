from django import forms
from django.utils.timezone import now
from .models import Utilization, Recycling

class UtilizationForm(forms.ModelForm):
    class Meta:
        model = Utilization
        exclude = ("place_from", "culture")  # ❗ автоматичні поля
        widgets = {
            "date_time": forms.DateTimeInput(attrs={
                "type": "datetime-local",
                "class": "form-control",
                "value": now().strftime("%Y-%m-%dT%H:%M"),
            }),     
            "quantity": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.001",
                "min": "0",
                "placeholder": "Кількість утилізованих відходів (тонн)"
            }),
            "note": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Примітка (необов’язково)",
            }),
        }


class RecyclingForm(forms.ModelForm):
    class Meta:
        model = Recycling
        exclude = ("place_from", "culture")   # ❗ автоматичні поля
        widgets = {
            "date_time": forms.DateTimeInput(attrs={
                "type": "datetime-local",
                "class": "form-control",
                "value": now().strftime("%Y-%m-%dT%H:%M"),
            }),     
            "input_quantity": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.001",
                "min": "0",
                "placeholder": "Кількість відходів для переробки (тонн)"
            }),
            "output_quantity": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.001",
                "min": "0",
                "placeholder": "Кількість отриманої продукції (тонн)"
            }),
            "place_to": forms.Select(attrs={"class": "form-select"}),
            "note": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Примітка (необов’язково)",
            }),
        }