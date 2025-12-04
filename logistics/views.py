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
        # print(context)
        return context


# --- Базовий ListView для журналів ---
class BaseJournalListView(BaseJournalViewMixin, ListView):
    template_name = "journal/list.html"
    context_object_name = "journals"
    # ordering = ["-date_time"]
    paginate_by = 10  # опціонально

    base_valid_orders = [
        "id", "-id",
        "document_number", "-document_number",
        "date_time", "-date_time",
        "weight_gross", "-weight_gross",
        "weight_tare", "-weight_tare",
        "weight_net", "-weight_net",
        "weight_loss", "-weight_loss",
        "note", "-note",
        "car__name", "-car__name",
        "culture__name", "-culture__name",
        "driver__name", "-driver__name",
        "trailer__name", "-trailer__name",
    ]

    journal_valid_orders = []

    base_select_related = ["car", "culture", "driver", "trailer"]

    journal_select_related = []

    def get_valid_orders(self):
        return self.base_valid_orders + self.journal_valid_orders
    
    def get_queryset(self):
        qs = super().get_queryset().select_related(
            *(self.base_select_related + self.journal_select_related)
        )
    
        order = self.request.GET.get("order")
        valid_orders = self.get_valid_orders()

        if order in valid_orders:
            qs = qs.order_by(order)
        else:
            qs = qs.order_by("-id")
        return qs


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

    journal_valid_orders = [
        "to_place__name", "-to_place__name",
        "from_place__name", "-from_place__name",
    ]

    journal_select_related = ["to_place", "from_place"]


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

    journal_valid_orders = [
        "place_to__name", "-place_to__name",
        "place_from__name", "-place_from__name",
        "action_type", "-action_type",
        "place_from_text", "-place_from_text",
        "place_to_text", "-place_to_text",
    ]

    journal_select_related = ["place_to", "place_from"]


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

    journal_valid_orders = [
        "place_to__name", "-place_to__name",
        "field__name", "-field__name",
    ]

    journal_select_related = ["place_to","field"]
    

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
