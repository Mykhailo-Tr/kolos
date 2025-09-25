from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.timezone import now
from datetime import timedelta
from .forms import WeigherJournalFilterForm, ShipmentJournalFilterForm, ArrivalJournalFilterForm
from logistics.models import WeigherJournal, ShipmentJournal, ArrivalJournal
from . import services


def reports_home(request):
    today = now().date()
    start = now().replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)

    qs = WeigherJournal.objects.filter(date_time__gte=start, date_time__lt=end)
    context = {
        "culture_stats": services.get_culture_stats(qs),
        "car_stats": services.get_car_stats(qs),
        "driver_stats": services.get_driver_stats(qs),
    }
    return render(request, "reports/reports.html", context)


def daily_report(request):
    """Формування зведеного денного звіту (PDF або HTML попередній перегляд)"""
    today = now().date()
    start = now().replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)

    # дані по кожному журналу
    weigher_qs = WeigherJournal.objects.filter(date_time__gte=start, date_time__lt=end)
    shipment_qs = ShipmentJournal.objects.filter(date_time__gte=start, date_time__lt=end)
    arrival_qs = ArrivalJournal.objects.filter(date_time__gte=start, date_time__lt=end)

    context = {
        "today": today.strftime("%d.%m.%Y"),
        "weigher": {
            "culture_stats": services.get_culture_stats(weigher_qs),
            "car_stats": services.get_car_stats(weigher_qs),
            "driver_stats": services.get_driver_stats(weigher_qs),
            "balance": services.get_balance(weigher_qs, receiver_field="receiver"),
        },
        "shipment": {
            "culture_stats": services.get_culture_stats(shipment_qs),
            "car_stats": services.get_car_stats(shipment_qs),
            "driver_stats": services.get_driver_stats(shipment_qs),
            "balance": services.get_balance(shipment_qs, receiver_field="unloading_place"),
        },
        "arrival": {
            "culture_stats": services.get_culture_stats(arrival_qs),
            "car_stats": services.get_car_stats(arrival_qs),
            "driver_stats": services.get_driver_stats(arrival_qs),
            "balance": services.get_balance(arrival_qs, receiver_field="sender_or_receiver", use_single_field=True),
        }
    }

    # 👉 краща практика: формувати PDF для бухгалтерії
    # Якщо треба HTML-перегляд → рендеримо шаблон
    html = render_to_string("reports/daily_report.html", context)
    return HttpResponse(html)  # можна підмінити на PDF рендерер (weasyprint / xhtml2pdf)


def weigher_journal_report(request):
    form = WeigherJournalFilterForm(request.GET or None)

    # базовий queryset з select_related для оптимізації
    entrys = WeigherJournal.objects.select_related(
        "driver", "car", "trailer", "culture",
        "sender", "receiver", "unloading_place"
    ).order_by("-date_time")

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
    balance = services.get_balance(entrys, receiver_field="receiver")


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
    return render(request, "reports/weigher_journal_report.html", context)

def shipment_journal_report(request):
    form = ShipmentJournalFilterForm(request.GET or None)

    entrys = ShipmentJournal.objects.select_related(
        "driver", "car", "trailer", "culture", "sender", "unloading_place"
    ).order_by("-date_time")

    if form.is_valid():
        cd = form.cleaned_data
        if cd.get("start_date"):
            entrys = entrys.filter(date_time__gte=cd["start_date"])
        if cd.get("end_date"):
            entrys = entrys.filter(date_time__lte=cd["end_date"])
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
        if cd.get("unloading_place"):
            entrys = entrys.filter(unloading_place=cd["unloading_place"])

    culture_stats = services.get_culture_stats(entrys)
    driver_stats = services.get_driver_stats(entrys)
    car_stats = services.get_car_stats(entrys)
    unloading_stats = services.get_unloading_stats(entrys)
    balance = services.get_balance(entrys, receiver_field="unloading_place")


    context = {
        "form": form,
        "entrys": entrys,

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
    return render(request, "reports/shipment_journal_report.html", context)


def arrival_journal_report(request):
    form = ArrivalJournalFilterForm(request.GET or None)

    entrys = ArrivalJournal.objects.select_related(
        "driver", "car", "trailer", "culture", "sender_or_receiver", "unloading_place"
    ).order_by("-date_time")

    if form.is_valid():
        cd = form.cleaned_data
        if cd.get("start_date"):
            entrys = entrys.filter(date_time__gte=cd["start_date"])
        if cd.get("end_date"):
            entrys = entrys.filter(date_time__lte=cd["end_date"])
        if cd.get("driver"):
            entrys = entrys.filter(driver=cd["driver"])
        if cd.get("car"):
            entrys = entrys.filter(car=cd["car"])
        if cd.get("trailer"):
            entrys = entrys.filter(trailer=cd["trailer"])
        if cd.get("culture"):
            entrys = entrys.filter(culture=cd["culture"])
        if cd.get("sender_or_receiver"):
            entrys = entrys.filter(sender_or_receiver=cd["sender_or_receiver"])
        if cd.get("unloading_place"):
            entrys = entrys.filter(unloading_place=cd["unloading_place"])

    # агреговані дані
    culture_stats = services.get_culture_stats(entrys)
    driver_stats = services.get_driver_stats(entrys)
    car_stats = services.get_car_stats(entrys)
    unloading_stats = services.get_unloading_stats(entrys)

    balance = services.get_balance(entrys, receiver_field="sender_or_receiver", use_single_field=True)


    context = {
        "form": form,
        "entrys": entrys,
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
    return render(request, "reports/arrival_journal_report.html", context)