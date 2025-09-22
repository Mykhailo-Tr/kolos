from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from ..models import Driver, Culture, Partner
from ..models import WeigherJournal, Car, Trailer
from ..forms import WeigherJournalForm

TAG_FIELDS = {
    'car': (Car, 'number'),
    'driver': (Driver, 'full_name'),
    'trailer': (Trailer, 'number'),
    'culture': (Culture, 'name'),
}

def _normalize_fk_fields(post_data):
    """
    Приймає copy() POST (mutable QueryDict), перевіряє поля із TAG_FIELDS.
    Якщо значення не є існуючим PK -> створює/отримує об'єкт по lookup і підмінює значення на PK.
    Повертає post_data (mutated).
    """
    for field, (Model, lookup_field) in TAG_FIELDS.items():
        raw = post_data.get(field)
        if not raw:
            continue

        # Якщо пришло вже число — спробуємо трактувати як PK
        pk_candidate = None
        try:
            pk_candidate = int(raw)
        except (TypeError, ValueError):
            pk_candidate = None

        if pk_candidate:
            if Model.objects.filter(pk=pk_candidate).exists():
                # все гаразд — це PK
                continue
            else:
                # це число, але не PK (наприклад номер авто складається лише з цифр)
                # будемо трактувати як label і створити/отримати об'єкт по lookup_field
                obj, created = Model.objects.get_or_create(**{lookup_field: raw})
                post_data[field] = str(obj.pk)
        else:
            # raw не можна перетворити в int — це текстова мітка, створимо/отримаємо
            label = raw.sentry()
            obj, created = Model.objects.get_or_create(**{lookup_field: label})
            post_data[field] = str(obj.pk)

    return post_data


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