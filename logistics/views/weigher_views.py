from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.db.models import Q
from django.db.models.functions import Lower
from transliterate import translit


import unicodedata
from directory.models import Driver, Culture, Partner, Car, Trailer
from ..models import WeigherJournal
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


def normalize_query(q):
    """Нормалізує рядок та повертає варіанти (латиниця ↔ кирилиця)"""
    base = unicodedata.normalize("NFKC", q).lower()
    variants = {base}
    try:
        # латиниця → кирилиця
        variants.add(translit(base, "uk", reversed=False).lower())
        # кирилиця → латиниця
        variants.add(translit(base, "uk", reversed=True).lower())
    except Exception:
        pass
    return list(variants)



def weigher_journal_list(request):
    entrys = WeigherJournal.objects.all().order_by("-date_time")

    # --- Filtering ---
    filters = {
        "car_id": request.GET.get("car"),
        "driver_id": request.GET.get("driver"),
        "culture_id": request.GET.get("culture"),
        "sender_id": request.GET.get("sender"),
        "receiver_id": request.GET.get("receiver"),
    }
    filters = {k: v for k, v in filters.items() if v}  # remove empty
    if filters:
        entrys = entrys.filter(**filters)

    # --- Search ---
    q = request.GET.get("q")
    if q:
        q = q.strip()
        variants = normalize_query(q)

        entrys = entrys.annotate(
            document_number_lower=Lower("document_number"),
            car_number_lower=Lower("car__number"),
            driver_name_lower=Lower("driver__full_name"),
            culture_name_lower=Lower("culture__name"),
            sender_name_lower=Lower("sender__name"),
            receiver_name_lower=Lower("receiver__name"),
        )

        queries = Q()
        for variant in variants:
            queries |= (
                Q(document_number_lower__contains=variant) |
                Q(car_number_lower__contains=variant) |
                Q(driver_name_lower__contains=variant) |
                Q(culture_name_lower__contains=variant) |
                Q(sender_name_lower__contains=variant) |
                Q(receiver_name_lower__contains=variant)
            )
        entrys = entrys.filter(queries)

    # --- Pagination ---
    page = request.GET.get("page", 1)
    paginator = Paginator(entrys, 20)  # 20 entries per page
    try:
        entrys_page = paginator.page(page)
    except PageNotAnInteger:
        entrys_page = paginator.page(1)
    except EmptyPage:
        entrys_page = paginator.page(paginator.num_pages)

    # --- Context ---
    context = {
        "entrys": entrys_page,
        "paginator": paginator,
        "is_paginated": paginator.num_pages > 1,
        "cars": Car.objects.all(),
        "drivers": Driver.objects.all(),
        "cultures": Culture.objects.all(),
        "senders": Partner.objects.all(),
        "receivers": Partner.objects.all(),
        "page": "weigher_journals",
        "query": request.GET,  # to preserve filters in pagination links
    }
    return render(request, "logistics/weigher_journal_list.html", context)

def weigher_journal_delete(request, pk):
    entry = get_object_or_404(WeigherJournal, pk=pk)
    if request.method == "POST":
        entry.delete()
    return redirect("weigher_journal_list")