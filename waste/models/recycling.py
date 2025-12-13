from django.db import models
from django.core.exceptions import ValidationError
from .base import WasteOperation
from balances.services import BalanceService, BalanceType


class Recycling(WasteOperation):
    """Операція переробки відходів"""

    place_to = models.ForeignKey(
        "directory.Place",
        on_delete=models.CASCADE,
        related_name="recycling_in",
        verbose_name="Місце призначення"
    )
    input_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        verbose_name="Кількість"
    )
    output_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        verbose_name="Кількість на виході"
    )

    class Meta:
        verbose_name = "Переробка"
        verbose_name_plural = "Операції переробки"

    def __str__(self):
        return f"{self.date_time:%d.%m.%Y %H:%M} | Переробка {self.culture.name} {self.input_quantity} т → {self.output_quantity} т у {self.place_from.name} -> {self.place_to.name}"
    
    @property
    def action(self):
        return "recycling"

    def revert_balance(self):
        """Відкат змін балансу - повертаємо вхід та віднімаємо вихід"""
        original_input = self.get_original_value('input_quantity')
        original_output = self.get_original_value('output_quantity')
        
        if original_input and original_output:
            # Повертаємо відходи на склад відправлення
            BalanceService.adjust_balance(
                place=self.place_from,
                culture=self.culture,
                delta=original_input,
                balance_type=BalanceType.WASTE
            )
            try:
                # Віднімаємо продукцію зі складу призначення
                BalanceService.adjust_balance(
                    place=self.place_to,
                    culture=self.culture,
                    delta=-original_output,
                    balance_type=BalanceType.STOCK
                )
            except ValueError:
                BalanceService.set_balance(
                    place=self.place_to,
                    culture=self.culture,
                    balance_type=BalanceType.STOCK,
                    quantity=0
                )

    def update_balance(self):
        """Оновлення балансу - віднімаємо вхід та додаємо вихід"""
        input_delta = -self.input_quantity
        output_delta = self.output_quantity
        
        # Якщо це редагування, враховуємо різницю з початковими значеннями
        original_input = self.get_original_value('input_quantity')
        original_output = self.get_original_value('output_quantity')
        
        input_delta = -(self.input_quantity)
        output_delta = self.output_quantity
        
        BalanceService.adjust_balance(
            place=self.place_from,
            culture=self.culture,
            delta=input_delta,
            balance_type=BalanceType.WASTE
        )
        BalanceService.adjust_balance(
            place=self.place_to,
            culture=self.culture,
            delta=output_delta,
            balance_type=BalanceType.STOCK
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