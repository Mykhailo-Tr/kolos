from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from ..models import Culture
from ..forms import CultureForm


@login_required
def culture_list(request):
    cultures = Culture.objects.all()
    form = CultureForm()
    context = {"cultures": cultures, "form": form, "page": "cultures"}
    return render(request, "directory/culture_list.html", context)


@login_required
def culture_create(request):
    next_url = request.GET.get("next") or request.POST.get("next")
    if request.method == "POST":
        form = CultureForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Культуру успішно додано ✅")
            return redirect(next_url or "culture_list")
    else:
        form = CultureForm()
        
    context = {"form": form, 
               "title": "Додати культуру", 
               "page": "cultures", 
               "back_url": next_url or reverse("culture_list")}
    return render(request, "directory/form.html", context)


@login_required
def culture_update(request, pk):
    next_url = request.GET.get("next") or request.POST.get("next")
    culture = get_object_or_404(Culture, pk=pk)
    if request.method == "POST":
        form = CultureForm(request.POST, instance=culture)
        if form.is_valid():
            form.save()
            messages.success(request, "Культуру оновлено ✅")
            return redirect(next_url or "culture_list")
    else:
        form = CultureForm(instance=culture)
        
    context = {"form": form, 
               "title": "Редагувати культуру", 
               "page": "cultures", 
               "back_url": next_url or reverse("culture_list")}
    return render(request, "directory/form.html", context)


@login_required
def culture_delete(request, pk):
    culture = get_object_or_404(Culture, pk=pk)
    if request.method == "POST":
        messages.success(request, "Культуру видалено ✅")
        culture.delete()
    return redirect("culture_list")
