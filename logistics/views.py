from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView, DeleteView
from .models import WeigherJournal, ShipmentJournal, FieldsIncome
from .forms import WeigherJournalForm, ShipmentJournalForm, FieldsIncomeForm


# --- Базовий клас для всіх журналів ---
class BaseJournalViewMixin:
    """Загальна логіка для всіх журналів (створення, оновлення, список)."""
    model = None
    form_class = None
    success_url = None
    template_name = None

    def get_context_data(self, **kwargs):
        """Додає назву моделі у контекст (для універсальних шаблонів)."""
        context = super().get_context_data(**kwargs)
        model = self.model._meta
        context['url_name'] = self.model._meta.model_name
        context["model_name"] = model.verbose_name
        context["model_verbose"] = model.verbose_name_plural
        context["page"] = self.model._meta.model_name
        print(context)
        return context


# --- Базовий ListView для журналів ---
class BaseJournalListView(BaseJournalViewMixin, ListView):
    template_name = "journal/list.html"
    context_object_name = "journals"
    ordering = ["-date_time"]
    paginate_by = 25  # опціонально


# --- Базові Create / Update для журналів ---
class BaseJournalCreateView(BaseJournalViewMixin, CreateView):
    template_name = "journal/form.html"

    def get_success_url(self):
        return self.success_url or reverse_lazy(f"{self.model._meta.model_name}_list")


class BaseJournalUpdateView(BaseJournalViewMixin, UpdateView):
    template_name = "journal/form.html"

    def get_success_url(self):
        return self.success_url or reverse_lazy(f"{self.model._meta.model_name}_list")


class WeigherJournalListView(BaseJournalListView):
    model = WeigherJournal
    template_name = "logistics/weigher_journal/list.html"


class WeigherJournalCreateView(BaseJournalCreateView):
    model = WeigherJournal
    form_class = WeigherJournalForm
    template_name = "logistics/journal/form.html"


class WeigherJournalUpdateView(BaseJournalUpdateView):
    model = WeigherJournal
    form_class = WeigherJournalForm
    template_name = "logistics/journal/form.html"
    

class WeigherJournalDeleteView(DeleteView):
    model = WeigherJournal
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("weigherjournal_list")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_name"] = self.model._meta.model_name
        context["cancel_url"] = reverse_lazy("weigherjournal_list")
        return context


class ShipmentJournalListView(BaseJournalListView):
    model = ShipmentJournal
    template_name = "logistics/shipment_journal/list.html"


class ShipmentJournalCreateView(BaseJournalCreateView):
    model = ShipmentJournal
    form_class = ShipmentJournalForm
    template_name = "logistics/journal/form.html"


class ShipmentJournalUpdateView(BaseJournalUpdateView):
    model = ShipmentJournal
    form_class = ShipmentJournalForm
    template_name = "logistics/journal/form.html"
    

class ShipmentJournalDeleteView(DeleteView):
    model = ShipmentJournal
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("shipmentjournal_list")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_name"] = self.model._meta.model_name
        context["cancel_url"] = reverse_lazy("shipmentjournal_list")
        return context
    
    
class FieldsIncomeListView(BaseJournalListView):
    model = FieldsIncome
    template_name = "logistics/fields_income/list.html"
    

class FieldsIncomeCreateView(BaseJournalCreateView):
    model = FieldsIncome
    form_class = FieldsIncomeForm
    template_name = "logistics/journal/form.html"
    

class FieldsIncomeUpdateView(BaseJournalUpdateView):
    model = FieldsIncome
    form_class = FieldsIncomeForm
    template_name = "logistics/journal/form.html"
    

class FieldsIncomeDeleteView(DeleteView):
    model = FieldsIncome
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("fieldsincome_list")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_name"] = self.model._meta.model_name
        context["cancel_url"] = reverse_lazy("fieldsincome_list")
        return context
