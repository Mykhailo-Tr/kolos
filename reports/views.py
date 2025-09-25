from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic import TemplateView
from django.utils.timezone import now
from datetime import timedelta
from django.utils.timezone import make_aware
from datetime import datetime
import csv
from .forms import WeigherJournalFilterForm, ShipmentJournalFilterForm, ArrivalJournalFilterForm, DailyReportForm
from logistics.models import WeigherJournal, ShipmentJournal, ArrivalJournal
from . import services
from .services import unify_rows_from_querysets, aggregate_rows
from datetime import time


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


def _day_range_for_date(date):
    # date is a date object
    start = datetime.combine(date, time.min)
    end = datetime.combine(date, time.max)
    # If your DB fields are timezone-aware, ensure aware datetimes:
    try:
        start = make_aware(start)
        end = make_aware(end)
    except Exception:
        pass
    return start, end

def daily_report(request):
    form = DailyReportForm(request.GET or None)
    date = form.initial.get("date")
    if form.is_bound and form.is_valid():
        date = form.cleaned_data.get("date") or date

    start_dt, end_dt = _day_range_for_date(date)

    # base querysets (for the day)
    w_qs = WeigherJournal.objects.select_related("car", "driver", "trailer", "culture", "unloading_place", "sender", "receiver").filter(date_time__gte=start_dt, date_time__lte=end_dt)
    s_qs = ShipmentJournal.objects.select_related("car", "driver", "trailer", "culture", "unloading_place", "sender").filter(date_time__gte=start_dt, date_time__lte=end_dt)
    a_qs = ArrivalJournal.objects.select_related("car", "driver", "trailer", "culture", "unloading_place", "sender_or_receiver").filter(date_time__gte=start_dt, date_time__lte=end_dt)

    # apply optional filters from form
    if form.is_bound and form.is_valid():
        cd = form.cleaned_data
        if cd.get("car"):
            w_qs = w_qs.filter(car=cd["car"]); s_qs = s_qs.filter(car=cd["car"]); a_qs = a_qs.filter(car=cd["car"])
        if cd.get("driver"):
            w_qs = w_qs.filter(driver=cd["driver"]); s_qs = s_qs.filter(driver=cd["driver"]); a_qs = a_qs.filter(driver=cd["driver"])
        if cd.get("culture"):
            w_qs = w_qs.filter(culture=cd["culture"]); s_qs = s_qs.filter(culture=cd["culture"]); a_qs = a_qs.filter(culture=cd["culture"])
        if cd.get("sender"):
            w_qs = w_qs.filter(sender=cd["sender"]); s_qs = s_qs.filter(sender=cd["sender"]); # arrival uses sender_or_receiver
        if cd.get("unloading_place"):
            w_qs = w_qs.filter(unloading_place=cd["unloading_place"]); s_qs = s_qs.filter(unloading_place=cd["unloading_place"]); a_qs = a_qs.filter(unloading_place=cd["unloading_place"])

    # unify
    rows = unify_rows_from_querysets(w_qs, s_qs, a_qs)

    group_by = (form.cleaned_data["group_by"] if form.is_bound and form.is_valid() else form.fields["group_by"].initial) or "none"

    report = aggregate_rows(rows, group_by=group_by)

    # export CSV
    if request.GET.get("export") == "csv":
        # build CSV from report["table_rows"]
        response = HttpResponse(content_type="text/csv")
        fname = f"daily_report_{date.isoformat()}.csv"
        response["Content-Disposition"] = f'attachment; filename="{fname}"'
        writer = csv.writer(response)
        # header
        writer.writerow(["Group", "Culture", "Gross (kg)", "Tare (kg)", "Net (kg)"])
        for r in report["table_rows"]:
            writer.writerow([r["group"], r["culture"], r["gross"], r["tare"], r["net"]])
        # totals block
        writer.writerow([])
        writer.writerow(["Totals", "", "Gross in", report["totals"]["gross_in"]])
        writer.writerow(["Totals", "", "Net in", report["totals"]["net_in"]])
        writer.writerow(["Totals", "", "Gross out", report["totals"]["gross_out"]])
        writer.writerow(["Totals", "", "Net out", report["totals"]["net_out"]])
        writer.writerow(["Totals", "", "Balance", report["totals"]["balance"]])
        return response

    # prepare minimal chart data (optional)
    chart_labels = [r["group"] + " — " + r["culture"] for r in report["table_rows"][:30]]  # limit
    chart_values = [r["net"] for r in report["table_rows"][:30]]

    context = {
        "form": form,
        "report": report,
        "table_rows": report["table_rows"],
        "groups_summary": report["groups_summary"],
        "totals": report["totals"],
        "chart_labels": chart_labels,
        "chart_values": chart_values,
        "selected_date": date,
        "group_by": group_by,
    }
    return render(request, "reports/daily_report.html", context)