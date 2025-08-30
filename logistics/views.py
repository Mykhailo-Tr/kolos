from django.shortcuts import render, redirect, get_object_or_404
from .models import Trip, Car
from .forms import TripForm


def trip_list(request):
    trips = Trip.objects.all().order_by("-date_time")
    return render(request, "logistics/trip_list.html", {"trips": trips, "page": "trips"})



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