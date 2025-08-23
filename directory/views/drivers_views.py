from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from ..models import Driver
from ..forms import DriverForm


def driver_list(request):
    drivers = Driver.objects.all()
    context = {"drivers": drivers, "page": "drivers"}
    return render(request, "directory/driver_list.html", context)


def driver_create(request):
    if request.method == "POST":
        form = DriverForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Водія успішно додано ✅")
            return redirect("driver_list")
    else:
        form = DriverForm()
    
    context = {"form": form, "title": "Додати водія", "back_url": reverse("driver_list")}
    return render(request, "directory/form.html", context)


def driver_update(request, pk):
    driver = get_object_or_404(Driver, pk=pk)
    if request.method == "POST":
        form = DriverForm(request.POST, instance=driver)
        if form.is_valid():
            form.save()
            messages.success(request, "Водія оновлено ✅")
            return redirect("driver_list")
    else:
        form = DriverForm(instance=driver)
        
    context = {"form": form, "title": "Редагувати водія", "back_url": reverse("driver_list")}
    return render(request, "directory/form.html", context)


def driver_delete(request, pk):
    driver = get_object_or_404(Driver, pk=pk)
    if request.method == "POST":
        driver.delete()
        messages.success(request, "Водія видалено ✅")
    return redirect("driver_list")
