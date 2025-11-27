from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from .models import Balance
from .forms import BalanceForm


class BalanceListView(ListView):
    model = Balance
    template_name = "balances/list.html"
    context_object_name = "balances"
    paginate_by = 10  # Кількість записів на сторінку

    def get_queryset(self):
        qs = super().get_queryset().select_related("place", "culture")
        order = self.request.GET.get("order")
        valid_orders = [
            "id", "-id",
            "place__name", "-place__name",
            "culture__name", "-culture__name",
            "balance_type", "-balance_type",
            "quantity", "-quantity"
        ]
        if order in valid_orders:
            qs = qs.order_by(order)
        else:
            qs = qs.order_by("-id")
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_name"] = "Журнал залишків"
        context["page"] = "balances"
        return context



class BalanceCreateView(CreateView):
    model = Balance
    form_class = BalanceForm
    template_name = "balances/form.html"
    success_url = reverse_lazy("balance_list")

    def form_valid(self, form):
        messages.success(self.request, "✅ Новий запис залишку успішно створено.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "❌ Помилка при створенні запису. Перевірте дані.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_name"] = self.model._meta.verbose_name
        context["url_name"] = "balance"
        context["page"] = "balances"
        return context


class BalanceUpdateView(UpdateView):
    model = Balance
    form_class = BalanceForm
    template_name = "balances/form.html"
    success_url = reverse_lazy("balance_list")

    def form_valid(self, form):
        messages.success(self.request, "✅ Запис залишку оновлено успішно.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "❌ Не вдалося оновити запис.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_name"] = self.model._meta.verbose_name
        context["url_name"] = "balance"
        context["page"] = "balances"
        return context


class BalanceDeleteView(DeleteView):
    model = Balance
    template_name = "confirm_delete.html"
    success_url = reverse_lazy("balance_list")

    def delete(self, request, *args, **kwargs):
        messages.warning(request, "⚠️ Запис залишку успішно видалено.")
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = self.success_url
        context["model_name"] = self.model._meta.verbose_name
        context["page"] = "balances"
        return context
