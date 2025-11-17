from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView, DeleteView
from balances.models import Balance, BalanceType
from .models import WasteJournal
from .forms import WasteJournalForm

# --- Базовий клас для журналу відходів ---
class WasteJournalViewMixin:
    """Загальна логіка для журналу відходів."""
    model = WasteJournal
    form_class = WasteJournalForm
    success_url = reverse_lazy("wastejournal_list")
    template_name = None

    def get_context_data(self, **kwargs):
        """Додає назву моделі у контекст (для універсальних шаблонів)."""
        context = super().get_context_data(**kwargs)
        model = self.model._meta
        context['url_name'] = self.model._meta.model_name
        context["model_name"] = model.verbose_name
        context["model_verbose"] = model.verbose_name_plural
        context["cancel_url"] = self.success_url
        return context
    

# --- ListView для журналу відходів ---
class WasteJournalListView(WasteJournalViewMixin, ListView):
    template_name = "waste/wastes.html"
    context_object_name = "journals"
    ordering = ["-date_time"]
    paginate_by = 25  # опціонально
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["waste_balances"] = Balance.objects.filter(balance_type=BalanceType.WASTE)
        return context
    
    
# --- Create / Update для журналу відходів ---
class WasteJournalCreateView(WasteJournalViewMixin, CreateView):
    template_name = "waste/form.html"
    
class WasteJournalUpdateView(WasteJournalViewMixin, UpdateView):
    template_name = "waste/form.html"
    
# -- Delete для журналу відходів ---
class WasteJournalDeleteView(DeleteView):
    model = WasteJournal
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("wastejournal_list")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_name"] = self.model._meta.model_name
        context["cancel_url"] = reverse_lazy("wastejournal_list")
        return context
    