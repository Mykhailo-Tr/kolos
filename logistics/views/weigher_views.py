from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from ..models import Driver, Culture, Partner
from ..models import WeigherJournal, Car, Trailer
from ..forms import WeigherJournalForm
from ..utils import _normalize_fk_fields


def weigher_journal_create(request):
    car_driver_map = {str(car.id): car.default_driver_id for car in Car.objects.filter(default_driver__isnull=False)}
    if request.method == "POST":
        data = request.POST.copy()  # mutable
        # normalize/create tag fields in a transaction
        with transaction.atomic():
            data = _normalize_fk_fields(data)

            form = WeigherJournalForm(data)
            if form.is_valid():
                form.save()
                return redirect("weigher_journal_list")
            else:
                print(form.errors)
    else:
        form = WeigherJournalForm()

    return render(request, "logistics/weigher_journal_form.html", {
        "form": form,
        "page": "weigher_journals",
        "car_driver_map": car_driver_map,
    })


def weigher_journal_update(request, pk):
    entry = get_object_or_404(WeigherJournal, pk=pk)
    if request.method == "POST":
        data = request.POST.copy()
        with transaction.atomic():
            data = _normalize_fk_fields(data)
            form = WeigherJournalForm(data, instance=entry)
            if form.is_valid():
                form.save()
                return redirect("weigher_journal_list")
            else:
                pass
    else:
        form = WeigherJournalForm(instance=entry)

    return render(request, "logistics/weigher_journal_form.html", {
        "form": form, 
        "page":"weigher_journals"
    })


def weigher_journal_list(request):
    entrys = WeigherJournal.objects.all().order_by("-date_time")

    # фільтрація
    if request.GET.get("car"):
        entrys = entrys.filter(car_id=request.GET["car"])
    if request.GET.get("driver"):
        entrys = entrys.filter(driver_id=request.GET["driver"])
    if request.GET.get("culture"):
        entrys = entrys.filter(culture_id=request.GET["culture"])
    if request.GET.get("sender"):
        entrys = entrys.filter(sender_id=request.GET["sender"])
    if request.GET.get("receiver"):
        entrys = entrys.filter(receiver_id=request.GET["receiver"])
    if request.GET.get("q"):
        entrys = entrys.filter(document_number__icontains=request.GET["q"])

    context = {
        "entrys": entrys,
        "cars": Car.objects.all(),
        "drivers": Driver.objects.all(),
        "cultures": Culture.objects.all(),
        "senders": Partner.objects.all(),
        "receivers": Partner.objects.all(),
        "page": "weigher_journals",
    }
    return render(request, "logistics/weigher_journal_list.html", context)


def weigher_journal_delete(request, pk):
    entry = get_object_or_404(WeigherJournal, pk=pk)
    if request.method == "POST":
        entry.delete()
    return redirect("weigher_journal_list")