from django.shortcuts import render, redirect, get_object_or_404
from .models import Driver, Culture, Partner
from .models import Trip, Car, Trailer
from django.db import transaction
from .forms import TripForm

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
            label = raw.strip()
            obj, created = Model.objects.get_or_create(**{lookup_field: label})
            post_data[field] = str(obj.pk)

    return post_data


def trip_create(request):
    car_driver_map = {str(car.id): car.default_driver_id for car in Car.objects.filter(default_driver__isnull=False)}
    if request.method == "POST":
        data = request.POST.copy()  # mutable
        # normalize/create tag fields in a transaction
        with transaction.atomic():
            data = _normalize_fk_fields(data)

            form = TripForm(data)
            if form.is_valid():
                form.save()
                return redirect("trip_list")
            else:
                print(form.errors)
    else:
        form = TripForm()

    return render(request, "logistics/trip_form.html", {
        "form": form,
        "page": "trips",
        "car_driver_map": car_driver_map,
    })


def trip_update(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    if request.method == "POST":
        data = request.POST.copy()
        with transaction.atomic():
            data = _normalize_fk_fields(data)
            form = TripForm(data, instance=trip)
            if form.is_valid():
                form.save()
                return redirect("trip_list")
            else:
                pass
    else:
        form = TripForm(instance=trip)

    return render(request, "logistics/trip_form.html", {"form": form, "page": "trips"})

def trip_list(request):
    trips = Trip.objects.all().order_by("-date_time")

    # фільтрація
    if request.GET.get("car"):
        trips = trips.filter(car_id=request.GET["car"])
    if request.GET.get("driver"):
        trips = trips.filter(driver_id=request.GET["driver"])
    if request.GET.get("culture"):
        trips = trips.filter(culture_id=request.GET["culture"])
    if request.GET.get("sender"):
        trips = trips.filter(sender_id=request.GET["sender"])
    if request.GET.get("receiver"):
        trips = trips.filter(receiver_id=request.GET["receiver"])
    if request.GET.get("q"):
        trips = trips.filter(document_number__icontains=request.GET["q"])

    context = {
        "trips": trips,
        "cars": Car.objects.all(),
        "drivers": Driver.objects.all(),
        "cultures": Culture.objects.all(),
        "senders": Partner.objects.all(),
        "receivers": Partner.objects.all(),
        "page": "trips",
    }
    return render(request, "logistics/trip_list.html", context)


def trip_delete(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    if request.method == "POST":
        trip.delete()
    return redirect("trip_list")