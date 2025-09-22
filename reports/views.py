from django.shortcuts import render
from .forms import TripReportForm
from logistics.models import WeigherJournal
from . import services


def trip_report(request):
    form = TripReportForm(request.GET or None)

    # базовий queryset з select_related для оптимізації
    entrys = WeigherJournal.objects.select_related(
        "driver", "car", "trailer", "culture",
        "sender", "receiver", "unloading_place"
    )

    # застосування фільтрів
    if form.is_valid():
        cd = form.cleaned_data
        if cd.get("date_from"):
            entrys = entrys.filter(date_time__gte=cd["date_from"])
        if cd.get("date_to"):
            entrys = entrys.filter(date_time__lte=cd["date_to"])
        if cd.get("driver"):
            entrys = entrys.filter(driver=cd["driver"])
        if cd.get("car"):
            entrys = entrys.filter(car=cd["car"])
        if cd.get("trailer"):
            entrys = entrys.filter(trailer=cd["trailer"])
        if cd.get("culture"):
            entrys = entrys.filter(culture=cd["culture"])
        if cd.get("sender"):
            entrys = entrys.filter(sender=cd["sender"])
        if cd.get("receiver"):
            entrys = entrys.filter(receiver=cd["receiver"])
        if cd.get("unloading_place"):
            entrys = entrys.filter(unloading_place=cd["unloading_place"])

    # агреговані дані (через services)
    culture_stats = services.get_culture_stats(entrys)
    driver_stats = services.get_driver_stats(entrys)
    car_stats = services.get_car_stats(entrys)
    unloading_stats = services.get_unloading_stats(entrys)
    balance = services.get_balance(entrys)

    context = {
        "form": form,
        "entrys": entrys,

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
