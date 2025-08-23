from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from ..models import UnloadingPlace
from ..forms import UnloadingPlaceForm


@login_required
def place_list(request):
    places = UnloadingPlace.objects.all().order_by("name")
    form = UnloadingPlaceForm()
    context = {"places": places, "form": form, "page": "places"}
    return render(request, "directory/place_list.html", context)


@login_required
def place_create(request):
    if request.method == "POST":
        form = UnloadingPlaceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Місце розвантаження успішно додане ✅")
            return redirect("place_list")
    else:
        form = UnloadingPlaceForm()
    context = {"form": form, "title": "Додати місце розвантаження", "page": "places", "back_url": reverse("place_list")}
    return render(request, "directory/form.html", context)


@login_required
def place_update(request, pk):
    place = get_object_or_404(UnloadingPlace, pk=pk)
    if request.method == "POST":
        form = UnloadingPlaceForm(request.POST, instance=place)
        if form.is_valid():
            form.save()
            messages.success(request, "Місце розвантаження оновлене ✅")
            return redirect("place_list")
    else:
        form = UnloadingPlaceForm(instance=place)
        
    context = {"form": form, "title": "Редагувати місце розвантаження", "page": "places", "back_url": reverse("place_list")}
    return render(request, "directory/form.html", context)


@login_required
def place_delete(request, pk):
    place = get_object_or_404(UnloadingPlace, pk=pk)
    if request.method == "POST":
        place.delete()
        messages.success(request, "Місце розвантаження видалене ✅")
    return redirect("place_list")