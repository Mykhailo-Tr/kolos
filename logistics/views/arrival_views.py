from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.db.models import Q
from directory.models import Driver, Culture, Partner, Car, Trailer
from django.core.paginator import Paginator

from activity.utils import log_activity
from ..models import ArrivalJournal
from ..forms import ArrivalJournalForm
from ..utils import _normalize_fk_fields


def arrival_journal_list(request):
    entrys = ArrivalJournal.objects.all().order_by("-date_time")

    # фільтрація з нечутливістю до регістру
    if request.GET.get("car"):
        entrys = entrys.filter(car_id__iexact=request.GET["car"])
    if request.GET.get("driver"):
        entrys = entrys.filter(driver_id__iexact=request.GET["driver"])
    if request.GET.get("culture"):
        entrys = entrys.filter(culture_id__iexact=request.GET["culture"])
    if request.GET.get("sender"):
        entrys = entrys.filter(sender_id__iexact=request.GET["sender"])
    if request.GET.get("receiver"):
        entrys = entrys.filter(receiver_id__iexact=request.GET["receiver"])

    # пошук
    if request.GET.get("q"):
        q = request.GET["q"].strip()
        entrys = entrys.filter(
            Q(car__number__icontains=q) |
            Q(driver__full_name__icontains=q) |
            Q(culture__name__icontains=q) |
            Q(sender__name__icontains=q) |
            Q(receiver__name__icontains=q)
        )

    # ✅ Пагінація (20 записів на сторінці)
    paginator = Paginator(entrys, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "logistics/arrival_journal_list.html", {
        "entrys": page_obj,  # замість entrys передаємо page_obj
        "page_obj": page_obj,
        "page": "arrival_journals",
        "cars": Car.objects.all().order_by("number"),
        "drivers": Driver.objects.all().order_by("full_name"),
        "cultures": Culture.objects.all().order_by("name"),
        "partners": Partner.objects.all().order_by("name"),
        "senders": Partner.objects.filter(partner_type__in=["sender", "both"]).order_by("name"),
        "receivers": Partner.objects.filter(partner_type__in=["receiver", "both"]).order_by("name"),
    })

def arrival_journal_create(request):
    car_driver_map = {str(car.id): car.default_driver_id for car in Car.objects.filter(default_driver__isnull=False)}
    if request.method == "POST":
        data = request.POST.copy()  # mutable
        # normalize/create tag fields in a transaction
        with transaction.atomic():
            data = _normalize_fk_fields(data)

            form = ArrivalJournalForm(data)
            if form.is_valid():
                form.save()
                log_activity(request.user, "create", f"Додав прибуття №{form.instance.document_number}")
                return redirect("arrival_journal_list")
            else:
                print(form.errors)
    else:
        form = ArrivalJournalForm()

    return render(request, "logistics/arrival_journal_form.html", {
        "form": form,
        "page": "arrival_journals",
        "car_driver_map": car_driver_map,
    })
    
    
def arrival_journal_update(request, pk):
    entry = get_object_or_404(ArrivalJournal, pk=pk)
    if request.method == "POST":
        data = request.POST.copy()
        with transaction.atomic():
            data = _normalize_fk_fields(data)
            form = ArrivalJournalForm(data, instance=entry)
            if form.is_valid():
                form.save()
                log_activity(request.user, "update", f"Редагував прибуття №{entry.document_number}")
                return redirect("arrival_journal_list")
            else:
                pass
    else:
        form = ArrivalJournalForm(instance=entry)

    return render(request, "logistics/arrival_journal_form.html", {
        "form": form, 
        "page":"arrival_journals"
    })
    

def arrival_journal_delete(request, pk):
    entry = get_object_or_404(ArrivalJournal, pk=pk)
    if request.method == "POST":
        entry.delete()
        log_activity(request.user, "delete", f"Видалив прибуття №{entry.document_number}")
    return redirect("arrival_journal_list")