from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .base import WasteOperation
from balances.services import BalanceService, BalanceType


class Utilization(WasteOperation):
    """Операція утилізації відходів"""

    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        verbose_name="Кількість (т)"
    )

    class Meta:
        verbose_name = "Утилізація"
        verbose_name_plural = "Операції утилізації"

    def __str__(self):
        return f"{self.date_time:%d.%m.%Y %H:%M} | Утилізація {self.culture.name} {self.quantity} т з {self.place_from.name}"

    @property
    def action(self):
        return "utilization"
    
    def revert_balance(self):
        """Відкат змін балансу - повертаємо відняту кількість"""
        original_quantity = self.get_original_value('quantity')
        if original_quantity:
            BalanceService.adjust_balance(
                place=self.place_from,
                culture=self.culture,
                delta=original_quantity,  # Додаємо назад
                balance_type=BalanceType.WASTE
            )

    def update_balance(self):
        """Оновлення балансу - віднімаємо кількість"""
        delta = -self.quantity

        BalanceService.adjust_balance(
            place=self.place_from,
            culture=self.culture,
            delta=delta,
            balance_type=BalanceType.WASTE
        )
        
    def save(self, *args, **kwargs):
        """Збереження з коректним оновленням балансу"""     
        is_new = self._state.adding
        
        if not is_new:
            # Для існуючого запису - спочатку відкатуємо старі зміни
            self.revert_balance()
        
        super().save(*args, **kwargs)
        
        # Застосовуємо нові зміни балансу
        self.update_balance()
        
        # Оновлюємо початкові значення
        self._original_values = self._get_operation_values()

    def delete(self, *args, **kwargs):
        """Видалення з поверненням балансу"""
        self.revert_balance()
        super().delete(*args, **kwargs)