from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import Driver
from ..forms import DriverForm


@login_required
def driver_list(request):
    drivers = Driver.objects.all()
    form = DriverForm()
    context = {"drivers": drivers, "form": form, "page": "drivers"}
    return render(request, "directory/driver_list.html", context)



@login_required
def driver_create(request):
    if request.method == "POST":
        form = DriverForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Водій успішно доданий ✅")
            return redirect("driver_list")
        else:
            # Повертаємо список + форму з помилками
            drivers = Driver.objects.all()
            return render(request, "directory/driver_list.html", {"drivers": drivers, "form": form})
    return redirect("driver_list")


@login_required
def driver_update(request, pk):
    driver = get_object_or_404(Driver, pk=pk)
    if request.method == "POST":
        form = DriverForm(request.POST, instance=driver)
        if form.is_valid():
            form.save()
            messages.success(request, "Водій оновлений ✅")
            return redirect("driver_list")
        else:
            drivers = Driver.objects.all()
            return render(request, "directory/driver_list.html", {"drivers": drivers, "form": DriverForm(), "edit_form": form, "edit_id": pk})
    return redirect("driver_list")


@login_required
def driver_delete(request, pk):
    driver = get_object_or_404(Driver, pk=pk)
    if request.method == "POST":
        driver.delete()
    return redirect("driver_list")