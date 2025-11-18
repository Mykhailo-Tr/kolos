from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from balances.models import Balance


class BalanceMixin:
    """Mixin для роботи з балансом"""
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        if hasattr(self, 'balance_id_kwarg'):
            self.balance = get_object_or_404(Balance, pk=kwargs[self.balance_id_kwarg])


class WasteOperationMixin:
    """Базовий mixin для операцій з відходами"""
    
    template_name = "waste/form.html"
    success_url = reverse_lazy("waste_list")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_operation_context())
        return context
    
    def get_operation_context(self):
        """Метод для перевизначення в дочірніх класах"""
        return {}


class WasteFormHandlerMixin:
    """Mixin для обробки форм відходів"""
    
    def form_valid(self, form):
        form.instance.place_from = self.balance.place
        form.instance.culture = self.balance.culture
        return super().form_valid(form)
