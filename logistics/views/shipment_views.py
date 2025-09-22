from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from directory.models import Driver, Culture, Partner, Car, Trailer
from ..models import ShipmentJournal
from ..forms import ShipmentJournalForm
from ..utils import _normalize_fk_fields


def shipment_journal_list(request):
    entrys = ShipmentJournal.objects.all().order_by("-date_time")

    # фільтрація
    if request.GET.get("car"):
        entrys = entrys.filter(car_id=request.GET["car"])
    if request.GET.get("driver"):
        entrys = entrys.filter(driver_id=request.GET["driver"])
    if request.GET.get("culture"):
        entrys = entrys.filter(culture_id=request.GET["culture"])
    if request.GET.get("sender"):
        entrys = entrys.filter(sender_id=request.GET["sender"])


    return render(request, "logistics/shipment_journal_list.html", {
        "entrys": entrys,
        "page": "shipment_journals",
        "cars": Car.objects.all().order_by("number"),
        "drivers": Driver.objects.all().order_by("full_name"),
        "cultures": Culture.objects.all().order_by("name"),
        "partners": Partner.objects.all().order_by("name"),
        "senders": Partner.objects.filter(partner_type__in=["sender", "both"]).order_by("name"),
    })
    
    
def shipment_journal_create(request):
    car_driver_map = {str(car.id): car.default_driver_id for car in Car.objects.filter(default_driver__isnull=False)}
    if request.method == "POST":
        data = request.POST.copy()  # mutable
        # normalize/create tag fields in a transaction
        with transaction.atomic():
            data = _normalize_fk_fields(data)

            form = ShipmentJournalForm(data)
            if form.is_valid():
                form.save()
                return redirect("shipment_journal_list")
            else:
                print(form.errors)
    else:
        form = ShipmentJournalForm()

    return render(request, "logistics/shipment_journal_form.html", {
        "form": form,
        "page": "shipment_journals",
        "car_driver_map": car_driver_map,
    })
    

def shipment_journal_update(request, pk):
    entry = get_object_or_404(ShipmentJournal, pk=pk)
    car_driver_map = {str(car.id): car.default_driver_id for car in Car.objects.filter(default_driver__isnull=False)}
    if request.method == "POST":
        data = request.POST.copy()  # mutable
        # normalize/create tag fields in a transaction
        with transaction.atomic():
            data = _normalize_fk_fields(data)

            form = ShipmentJournalForm(data, instance=entry)
            if form.is_valid():
                form.save()
                return redirect("shipment_journal_list")
            else:
                print(form.errors)
    else:
        form = ShipmentJournalForm(instance=entry)

    return render(request, "logistics/shipment_journal_form.html", {
        "form": form,
        "page": "shipment_journals",
        "car_driver_map": car_driver_map,
        "entry": entry,
    })
    
    
def shipment_journal_delete(request, pk):
    entry = get_object_or_404(ShipmentJournal, pk=pk)
    if request.method == "POST":
        entry.delete()
    return redirect("shipment_journal_list")
