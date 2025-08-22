from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Culture
from .forms import CultureForm


@login_required
def culture_list(request):
    cultures = Culture.objects.all()
    form = CultureForm()
    context = {"cultures": cultures, "form": form, "page": "cultures"}
    return render(request, "directory/culture_list.html", context)


@login_required
def culture_create(request):
    if request.method == "POST":
        form = CultureForm(request.POST)
        if form.is_valid():
            form.save()
    return redirect("culture_list")


@login_required
def culture_update(request, pk):
    culture = get_object_or_404(Culture, pk=pk)
    if request.method == "POST":
        form = CultureForm(request.POST, instance=culture)
        if form.is_valid():
            form.save()
    return redirect("culture_list")


@login_required
def culture_delete(request, pk):
    culture = get_object_or_404(Culture, pk=pk)
    if request.method == "POST":
        culture.delete()
    return redirect("culture_list")
