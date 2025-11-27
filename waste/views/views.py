from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView, DeleteView
from django.views import View
from balances.models import Balance, BalanceType
from ..models import Utilization, Recycling
from ..forms import UtilizationForm, RecyclingForm
from ..mixins import BalanceMixin, WasteOperationMixin, WasteFormHandlerMixin, PageContextMixin


class WasteJournalListView(ListView):
    """View для відображення журналу відходів"""
    
    template_name = "waste/wastes.html"
    context_object_name = "journals"
    paginate_by = 20

    def get_queryset(self):
        """Отримання об'єднаного та відсортованого queryset"""
        utilizations = Utilization.objects.select_related('culture', 'place_from')
        recyclings = Recycling.objects.select_related('culture', 'place_from', 'place_to')
        
        combined = list(utilizations) + list(recyclings)
        return sorted(combined, key=lambda x: x.date_time, reverse=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "model_name": "Журнал відходів",
            "waste_balances": Balance.objects.filter(
                balance_type=BalanceType.WASTE,
                quantity__gt=0
                ),
            "page": "wastejournal"
        })
        
        return context
