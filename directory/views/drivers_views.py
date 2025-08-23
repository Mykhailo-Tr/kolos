from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from ..models import Driver
from ..forms import DriverForm


def driver_list(request):
    drivers = Driver.objects.all()
    return render(request, "directory/driver_list.html", {"drivers": drivers})


def driver_create(request):
    if request.method == "POST":
        form = DriverForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("driver_list")
    else:
        form = DriverForm()
    return render(request, "directory/form.html", {"form": form, "title": "Додати водія", "back_url": reverse("driver_list")})


def driver_update(request, pk):
    driver = get_object_or_404(Driver, pk=pk)
    if request.method == "POST":
        form = DriverForm(request.POST, instance=driver)
        if form.is_valid():
            form.save()
            return redirect("driver_list")
        else:
            print(form.errors)
    else:
        form = DriverForm(instance=driver)
    return render(request, "directory/form.html", {"form": form, "title": "Редагувати водія", "back_url": reverse("driver_list")})


def driver_delete(request, pk):
    driver = get_object_or_404(Driver, pk=pk)
    if request.method == "POST":
        driver.delete()
        return redirect("driver_list")
    return redirect("driver_list")
