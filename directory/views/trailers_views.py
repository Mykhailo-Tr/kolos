from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages 
from django.urls import reverse
from ..models import Trailer
from ..forms import TrailerForm


@login_required
def trailer_list(request):
    trailers = Trailer.objects.all()
    form = TrailerForm()
    context = {"trailers": trailers, "form": form, "page": "trailers"}
    return render(request, "directory/trailer_list.html", context)


@login_required
def trailer_create(request): 
    next_url = request.GET.get("next") or request.POST.get("next")     
    if request.method == "POST":
        form = TrailerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Причеп успішно додано ✅")
            return redirect(next_url or "trailer_list")
    else:
        form = TrailerForm()
        
    context = {"form": form, 
               "title": "Додати причеп", 
               "page": "trailers", 
               "back_url": next_url or reverse("trailer_list")}
    return render(request, "directory/form.html", context)


@login_required
def trailer_update(request, pk):
    next_url = request.GET.get("next") or request.POST.get("next")
    trailer = get_object_or_404(Trailer, pk=pk)
    if request.method == "POST":
        form = TrailerForm(request.POST, instance=trailer)
        if form.is_valid():
            form.save()
            messages.success(request, "Причеп оновлено ✅")
            return redirect(next_url or "trailer_list")
    else:
        form = TrailerForm(instance=trailer)
        
    context = {"form": form, 
               "title": "Редагувати причеп", 
               "page": "trailers", 
               "back_url": next_url or reverse("trailer_list")}
    return render(request, "directory/form.html", context)


@login_required
def trailer_delete(request, pk):
    trailer = get_object_or_404(Trailer, pk=pk)
    if request.method == "POST":
        trailer.delete()
        messages.success(request, "Причеп видалено ✅")
    return redirect("trailer_list")
