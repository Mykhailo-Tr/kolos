from django.views.generic import CreateView, UpdateView, DeleteView
from ..models import Utilization
from ..forms import UtilizationForm
from ..mixins import BalanceMixin, WasteOperationMixin, WasteFormHandlerMixin

class UtilizationCreateView(BalanceMixin, WasteFormHandlerMixin, WasteOperationMixin, CreateView):
    """View для створення утилізації"""
    
    model = Utilization
    form_class = UtilizationForm
    balance_id_kwarg = 'balance_id'

    def get_operation_context(self):
        return {
            "title": "Нова утилізація",
            "balance": self.balance,
            "action_type": "utilization",
        }


class UtilizationUpdateView(WasteOperationMixin, UpdateView):
    """View для оновлення утилізації"""
    
    model = Utilization
    form_class = UtilizationForm
    queryset = Utilization.objects.select_related('culture', 'place_from')

    def get_operation_context(self):
        return {
            "title": "Редагувати утилізацію",
            "action_type": "utilization",
        }


class UtilizationDeleteView(WasteOperationMixin, DeleteView):
    """View для видалення утилізації"""
    
    model = Utilization
    template_name = "confirm_delete.html"
    queryset = Utilization.objects.select_related('culture', 'place_from')

    def get_operation_context(self):
        return {
            "title": "Видалити утилізацію",
        }