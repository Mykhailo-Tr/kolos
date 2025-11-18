from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView, DeleteView
from balances.models import Balance, BalanceType
from .models import Utilization, Recycling
from .forms import UtilizationForm, RecyclingForm


class WasteJournalListView(ListView):
    template_name = "waste/wastes.html"
    context_object_name = "journals"

    def get_queryset(self):
        util = Utilization.objects.all()
        rec = Recycling.objects.all()
        return sorted(
            list(util) + list(rec),
            key=lambda x: x.date_time,
            reverse=True
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            "model_name": "Журнал відходів",
            "waste_balances": Balance.objects.filter(balance_type=BalanceType.WASTE),
            })
        return ctx

    
class UtilizationCreateView(CreateView):
    model = Utilization
    form_class = UtilizationForm
    template_name = "waste/form.html"
    success_url = reverse_lazy("waste_list")

    def dispatch(self, request, *args, **kwargs):
        self.balance = Balance.objects.get(pk=kwargs["balance_id"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.place_from = self.balance.place
        form.instance.culture = self.balance.culture
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Нова утилізація"
        ctx["balance"] = self.balance
        ctx["action_type"] = "utilization"
        return ctx
    
class UtilizationUpdateView(UpdateView):
    model = Utilization
    form_class = UtilizationForm
    template_name = "waste/form.html"
    success_url = reverse_lazy("waste_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Редагувати утилізацію"
        return ctx
    
class UtilizationDeleteView(DeleteView):
    model = Utilization
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("waste_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Видалити утилізацію"
        return ctx


class RecyclingCreateView(CreateView):
    model = Recycling
    form_class = RecyclingForm
    template_name = "waste/form.html"
    success_url = reverse_lazy("waste_list")

    def dispatch(self, request, *args, **kwargs):
        self.balance = Balance.objects.get(pk=kwargs["balance_id"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.place_from = self.balance.place
        form.instance.culture = self.balance.culture
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Нова переробка"
        ctx["balance"] = self.balance
        ctx["action_type"] = "recycling"
        return ctx
    
class RecyclingUpdateView(UpdateView):
    model = Recycling
    form_class = RecyclingForm
    template_name = "waste/form.html"
    success_url = reverse_lazy("waste_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Редагувати переробку"
        return ctx
    
class RecyclingDeleteView(DeleteView):
    model = Recycling
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("waste_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Видалити переробку"
        return ctx
