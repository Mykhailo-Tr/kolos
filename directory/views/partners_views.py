from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from ..models import Partner    
from ..forms import PartnerForm


@login_required
def partner_list(request):
    partners = Partner.objects.all()
    form = PartnerForm()
    context = {"partners": partners, "form": form, "page": "partners"}
    return render(request, "directory/partner_list.html", context)


@login_required
def partner_create(request):
    next_url = request.GET.get("next") or request.POST.get("next")
    if request.method == "POST":
        form = PartnerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Партнера успішно додано ✅")
            return redirect(next_url or "partner_list")
    else:
        form = PartnerForm()
        
    context = {"form": form, 
               "title": "Додати партнера",
               "page": "partners", 
               "back_url": next_url or reverse("partner_list")}
    return render(request, "directory/form.html", context)


@login_required
def partner_update(request, pk):
    next_url = request.GET.get("next") or request.POST.get("next")
    partner = get_object_or_404(Partner, pk=pk)
    if request.method == "POST":
        form = PartnerForm(request.POST, instance=partner)
        if form.is_valid():
            form.save()
            messages.success(request, "Партнера оновлено ✅")
            return redirect(next_url or "partner_list")
    else:
        form = PartnerForm(instance=partner)
        
    context = {"form": form, 
               "title": "Редагувати партнера", 
               "page": "partners", 
               "back_url": next_url or reverse("partner_list")}
    return render(request, "directory/form.html", context)


@login_required
def partner_delete(request, pk):
    partner = get_object_or_404(Partner, pk=pk)
    if request.method == "POST":
        partner.delete()
        messages.success(request, "Партнера видалено ✅")
    return redirect("partner_list")