from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from ..models import Car
from ..forms import CarForm


@login_required
def car_list(request):
    cars = Car.objects.all()
    form = CarForm()
    context = {"cars": cars, "form": form, "page": "cars"}
    return render(request, "directory/car_list.html", context)


@login_required
def car_create(request):
    if request.method == "POST":
        form = CarForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Авто успішно додане ✅")
            return redirect("car_list")
    else:
        form = CarForm()
    context = {"form": form, "title": "Додати авто", "back_url": reverse("car_list")}
    return render(request, "directory/form.html", context)


@login_required
def car_update(request, pk):
    car = get_object_or_404(Car, pk=pk)
    if request.method == "POST":
        form = CarForm(request.POST, instance=car)
        if form.is_valid():
            form.save()
            messages.success(request, "Авто оновлене ✅")
            return redirect("car_list")
    else:
        form = CarForm(instance=car)
        
    context = {"form": form, "title": "Редагувати авто", "back_url": reverse("car_list")}
    return render(request, "directory/form.html", context)


@login_required
def car_delete(request, pk):
    car = get_object_or_404(Car, pk=pk)
    if request.method == "POST":
        car.delete()
        messages.success(request, "Авто видалене ✅")
    return redirect("car_list")