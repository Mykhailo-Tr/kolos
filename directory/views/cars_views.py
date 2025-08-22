from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import Car
from ..forms import CarForm


@login_required
def car_list(request):
    cars = Car.objects.all()
    form = CarForm()
    context = {"cars": cars, "form": form, "page": "cars"}
    return render(request, "directory/cars_list.html", context)


@login_required
def car_create(request):
    if request.method == "POST":
        form = CarForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Авто успішно додане ✅")
            return redirect("car_list")
        else:
            cars = Car.objects.all()
            return render(request, "directory/cars_list.html", {"cars": cars, "form": form})
    return redirect("car_list")


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
            cars = Car.objects.all()
            return render(request, "directory/cars_list.html", {"cars": cars, "form": CarForm(), "edit_form": form, "edit_id": pk})
    return redirect("car_list")


@login_required
def car_delete(request, pk):
    car = get_object_or_404(Car, pk=pk)
    if request.method == "POST":
        car.delete()
    return redirect("car_list")