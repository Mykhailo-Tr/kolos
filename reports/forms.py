from django import forms
from directory.models import Driver, Car, Trailer, Culture, Place
from django.utils.timezone import now
from django.utils.timezone import localdate
from django.utils import timezone

class DailyReportForm(forms.Form):
    date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        initial=localdate
    )

    group_by = forms.ChoiceField(
        required=False,
        choices=[
            ("none", "Зведення по складах (за замовчуванням)"),
            ("culture", "По культурах"),
            ("driver", "По водіях"),
            ("car", "По машинах"),
            ("trailer", "По причепах"),
            ("sender", "По відправниках"),
            ("unloading_place", "По місцях розвантаження"),
        ],
        initial="none",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    # Опційні фільтри
    driver = forms.ModelChoiceField(queryset=Driver.objects.all(), required=False,
                                    widget=forms.Select(attrs={"class": "form-select"}))
    car = forms.ModelChoiceField(queryset=Car.objects.all(), required=False,
                                 widget=forms.Select(attrs={"class": "form-select"}))
    trailer = forms.ModelChoiceField(queryset=Trailer.objects.all(), required=False,
                                     widget=forms.Select(attrs={"class": "form-select"}))
    culture = forms.ModelChoiceField(queryset=Culture.objects.all(), required=False,
                                     widget=forms.Select(attrs={"class": "form-select"}))
    unloading_place = forms.ModelChoiceField(queryset=Place.objects.all(), required=False,
                                             widget=forms.Select(attrs={"class":"form-select"}))

    export = forms.BooleanField(required=False, widget=forms.HiddenInput(), initial=False)
    

class StockBalanceFilterForm(forms.Form):
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    unloading_place = forms.ModelChoiceField(queryset=Place.objects.all(), required=False)
    culture = forms.ModelChoiceField(queryset=Culture.objects.all(), required=False)
    driver = forms.ModelChoiceField(queryset=Driver.objects.all(), required=False)
    car = forms.ModelChoiceField(queryset=Car.objects.all(), required=False)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("date_from") and cleaned.get("date_to"):
            if cleaned["date_from"] > cleaned["date_to"]:
                raise forms.ValidationError("Дата від і до некоректні.")
        # defaults
        if not cleaned.get("date_to"):
            cleaned["date_to"] = timezone.now().date()
        if not cleaned.get("date_from"):
            cleaned["date_from"] = cleaned["date_to"]
        return cleaned


class BaseJournalFilterForm(forms.Form):
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )

    driver = forms.ModelChoiceField(
        queryset=Driver.objects.all(), required=False,
        widget=forms.Select(attrs={"class": "form-select"})
    )
    car = forms.ModelChoiceField(
        queryset=Car.objects.all(), required=False,
        widget=forms.Select(attrs={"class": "form-select"})
    )
    trailer = forms.ModelChoiceField(
        queryset=Trailer.objects.all(), required=False,
        widget=forms.Select(attrs={"class": "form-select"})
    )
    culture = forms.ModelChoiceField(
        queryset=Culture.objects.all(), required=False,
        widget=forms.Select(attrs={"class": "form-select"})
    )

    unloading_place = forms.ModelChoiceField(
        queryset=Place.objects.all(), required=False,
        widget=forms.Select(attrs={"class": "form-select"})
    )


class WeigherJournalFilterForm(BaseJournalFilterForm):
    receiver = None


class ShipmentJournalFilterForm(BaseJournalFilterForm):
    """Спадковує всі спільні фільтри, додаткових не треба"""
    pass


class ArrivalJournalFilterForm(forms.Form):
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )

    driver = forms.ModelChoiceField(
        queryset=Driver.objects.all(), required=False,
        widget=forms.Select(attrs={"class": "form-select"})
    )
    car = forms.ModelChoiceField(
        queryset=Car.objects.all(), required=False,
        widget=forms.Select(attrs={"class": "form-select"})
    )
    trailer = forms.ModelChoiceField(
        queryset=Trailer.objects.all(), required=False,
        widget=forms.Select(attrs={"class": "form-select"})
    )
    culture = forms.ModelChoiceField(
        queryset=Culture.objects.all(), required=False,
        widget=forms.Select(attrs={"class": "form-select"})
    )

    unloading_place = forms.ModelChoiceField(
        queryset=Place.objects.all(), required=False,
        widget=forms.Select(attrs={"class": "form-select"})
    )
