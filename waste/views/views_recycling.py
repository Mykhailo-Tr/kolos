from django.views.generic import CreateView, UpdateView, DeleteView
from ..models import Recycling
from ..forms import RecyclingForm
from ..mixins import BalanceMixin, WasteOperationMixin, WasteFormHandlerMixin


class RecyclingCreateView(BalanceMixin, WasteFormHandlerMixin, WasteOperationMixin, CreateView):
    """View для створення переробки"""
    
    model = Recycling
    form_class = RecyclingForm
    balance_id_kwarg = 'balance_id'

    def get_operation_context(self):
        return {
            "title": "Нова переробка",
            "balance": self.balance,
            "action_type": "recycling",
        }


class RecyclingUpdateView(WasteOperationMixin, UpdateView):
    """View для оновлення переробки"""
    
    model = Recycling
    form_class = RecyclingForm
    queryset = Recycling.objects.select_related('culture', 'place_from', 'place_to')

    def get_operation_context(self):
        return {
            "title": "Редагувати переробку",
            "action_type": "recycling",
        }


class RecyclingDeleteView(WasteOperationMixin, DeleteView):
    """View для видалення переробки"""
    
    model = Recycling
    template_name = "confirm_delete.html"
    queryset = Recycling.objects.select_related('culture', 'place_from', 'place_to')

    def get_operation_context(self):
        return {
            "title": "Видалити переробку",
        }