from django.shortcuts import render, redirect, get_object_or_404
from .models import Driver, Culture, Partner
from .models import Trip, Car
from .forms import TripForm


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


def trip_create(request):
    car_driver_map = {str(car.id): car.default_driver_id for car in Car.objects.filter(default_driver__isnull=False)}
    
    if request.method == "POST":
        form = TripForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("trip_list")
    else:
        form = TripForm()
    return render(request, "logistics/trip_form.html", {
        "form": form,
        "page": "trips",
        "car_driver_map": car_driver_map
    })


def trip_update(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    if request.method == "POST":
        form = TripForm(request.POST, instance=trip)
        if form.is_valid():
            form.save()
            return redirect("trip_list")
    else:
        form = TripForm(instance=trip)
    return render(request, "logistics/trip_form.html", {"form": form, "page": "trips"})


def trip_delete(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    if request.method == "POST":
        trip.delete()
    return redirect("trip_list")