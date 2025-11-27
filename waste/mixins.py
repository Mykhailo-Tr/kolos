# waste/mixins.py
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from balances.models import Balance, BalanceType


class PageContextMixin:
    """Mixin для додавання контексту сторінки"""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "page": "wastejournal"
        })
        print(context)
        return context

class BalanceContextMixin:
    """Mixin для отримання балансу в контексті"""
    
    def get_balance(self):
        """Отримання балансу для поточного View"""
        # Для створення - баланс передається через URL
        if hasattr(self, 'balance'):
            return self.balance
        
        # Для редагування - отримуємо баланс з об'єкта
        elif hasattr(self, 'object') and self.object:
            return Balance.objects.filter(
                place=self.object.place_from,
                culture=self.object.culture,
                balance_type=BalanceType.WASTE
            ).first()
        
        return None
    
    def get_context_data(self, **kwargs):
        """Додаємо баланс до контексту"""
        context = super().get_context_data(**kwargs)
        context['balance'] = self.get_balance()
        return context


class BalanceMixin(BalanceContextMixin):
    """Mixin для роботи з балансом при створенні"""
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        if hasattr(self, 'balance_id_kwarg') and self.balance_id_kwarg in kwargs:
            self.balance = get_object_or_404(
                Balance, 
                pk=kwargs[self.balance_id_kwarg]
            )


class WasteOperationMixin(BalanceContextMixin):
    """Базовий mixin для операцій з відходами"""
    
    template_name = "waste/form.html"
    success_url = reverse_lazy("waste_list")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = "wastejournal"
        context.update(self.get_operation_context())
        return context
    
    def get_operation_context(self):
        """Метод для перевизначення в дочірніх класах"""
        return {}


class WasteFormHandlerMixin:
    """Mixin для обробки форм відходів"""
    
    def form_valid(self, form):
        # Для створення використовуємо баланс з URL
        if hasattr(self, 'balance'):
            form.instance.place_from = self.balance.place
            form.instance.culture = self.balance.culture
        # Для редагування - дані вже є в об'єкті
        return super().form_valid(form)