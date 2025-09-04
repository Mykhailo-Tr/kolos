from django.shortcuts import render
from django.db.models import Sum, F
from django.utils.timezone import now
from .forms import TripReportForm
from logistics.models import Trip


def trip_report(request):
    form = TripReportForm(request.GET or None)
    trips = Trip.objects.all()

    if form.is_valid():
        if form.cleaned_data.get("date_from"):
            trips = trips.filter(date_time__gte=form.cleaned_data["date_from"])
        if form.cleaned_data.get("date_to"):
            trips = trips.filter(date_time__lte=form.cleaned_data["date_to"])
        if form.cleaned_data.get("driver"):
            trips = trips.filter(driver=form.cleaned_data["driver"])
        if form.cleaned_data.get("car"):
            trips = trips.filter(car=form.cleaned_data["car"])
        if form.cleaned_data.get("trailer"):
            trips = trips.filter(trailer=form.cleaned_data["trailer"])
        if form.cleaned_data.get("culture"):
            trips = trips.filter(culture=form.cleaned_data["culture"])

    # агрегації для графіків
    by_driver = list(trips.values("driver__full_name").annotate(
        total_net=Sum(F("weight_gross") - F("weight_tare"))
    ))

    by_culture = list(trips.values("culture__name").annotate(
        total_net=Sum(F("weight_gross") - F("weight_tare"))
    ))

    context = {
        "form": form,
        "trips": trips,
        "driver_labels": [d["driver__full_name"] or "Без водія" for d in by_driver],
        "driver_values": [d["total_net"] or 0 for d in by_driver],
        "culture_labels": [c["culture__name"] or "Без культури" for c in by_culture],
        "culture_values": [c["total_net"] or 0 for c in by_culture],
    }
    return render(request, "reports/trip_report.html", context)
