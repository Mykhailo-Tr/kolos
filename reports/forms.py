from django import forms
from django.utils.timezone import now
from directory.models import Driver, Car, Trailer, Culture, Partner, UnloadingPlace


class TripReportForm(forms.Form):
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
    sender = forms.ModelChoiceField(
        queryset=Partner.objects.filter(partner_type__in=["sender", "both"]),
        required=False, widget=forms.Select(attrs={"class": "form-select"})
    )
    receiver = forms.ModelChoiceField(
        queryset=Partner.objects.filter(partner_type__in=["receiver", "both"]),
        required=False, widget=forms.Select(attrs={"class": "form-select"})
    )
    unloading_place = forms.ModelChoiceField(
        queryset=UnloadingPlace.objects.all(), required=False,
        widget=forms.Select(attrs={"class": "form-select"})
    )
