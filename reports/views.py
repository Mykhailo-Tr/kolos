from django.shortcuts import render
from .forms import TripReportForm
from logistics.models import Trip
from . import services


def trip_report(request):
    form = TripReportForm(request.GET or None)

    # базовий queryset з select_related для оптимізації
    trips = Trip.objects.select_related(
        "driver", "car", "trailer", "culture",
        "sender", "receiver", "unloading_place"
    )

    # застосування фільтрів
    if form.is_valid():
        cd = form.cleaned_data
        if cd.get("date_from"):
            trips = trips.filter(date_time__gte=cd["date_from"])
        if cd.get("date_to"):
            trips = trips.filter(date_time__lte=cd["date_to"])
        if cd.get("driver"):
            trips = trips.filter(driver=cd["driver"])
        if cd.get("car"):
            trips = trips.filter(car=cd["car"])
        if cd.get("trailer"):
            trips = trips.filter(trailer=cd["trailer"])
        if cd.get("culture"):
            trips = trips.filter(culture=cd["culture"])
        if cd.get("sender"):
            trips = trips.filter(sender=cd["sender"])
        if cd.get("receiver"):
            trips = trips.filter(receiver=cd["receiver"])
        if cd.get("unloading_place"):
            trips = trips.filter(unloading_place=cd["unloading_place"])

    # агреговані дані (через services)
    culture_stats = services.get_culture_stats(trips)
    driver_stats = services.get_driver_stats(trips)
    car_stats = services.get_car_stats(trips)
    unloading_stats = services.get_unloading_stats(trips)
    balance = services.get_balance(trips)

    context = {
        "form": form,
        "trips": trips,

        # дані для графіків і таблиць
        "culture_labels": [c["culture__name"] or "Без культури" for c in culture_stats],
        "culture_values": [float(c["total_net"] or 0) for c in culture_stats],

        "driver_labels": [d["driver__full_name"] or "Без водія" for d in driver_stats],
        "driver_values": [float(d["total_net"] or 0) for d in driver_stats],

        "car_labels": [c["car__number"] or "Без авто" for c in car_stats],
        "car_values": [float(c["total_net"] or 0) for c in car_stats],

        "unloading_labels": [u["unloading_place__name"] or "Без місця" for u in unloading_stats],
        "unloading_values": [float(u["total_net"] or 0) for u in unloading_stats],

        "balance": balance,
    }
    return render(request, "reports/trip_report.html", context)
