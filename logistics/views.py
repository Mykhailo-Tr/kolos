from django.shortcuts import render, redirect, get_object_or_404
from .models import Trip
from .forms import TripForm


def trip_list(request):
    trips = Trip.objects.all().order_by("-date_time")
    return render(request, "logistics/trip_list.html", {"trips": trips, "page": "trips"})


def trip_create(request):
    if request.method == "POST":
        form = TripForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("trip_list")
    else:
        form = TripForm()
    return render(request, "logistics/trip_form.html", {"form": form, "page": "trips"})


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