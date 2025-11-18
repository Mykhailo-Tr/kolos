from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from balances.services import BalanceService, BalanceType
from balances.models import Balance

class Utilization(models.Model):
    """Операція утилізації відходів"""

    date_time = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата та час"
    )
    culture = models.ForeignKey(
        "directory.Culture",
        on_delete=models.CASCADE,
        verbose_name="Культура"
    )
    place_from = models.ForeignKey(
        "directory.Place",
        on_delete=models.CASCADE,
        verbose_name="Місце відправлення"
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        verbose_name="Кількість (т)"
    )
    note = models.TextField(
        blank=True,
        null=True,
        verbose_name="Примітка"
    )

    class Meta:
        verbose_name = "Утилізація"
        verbose_name_plural = "Операції утилізації"

    def __str__(self):
        return f"{self.date_time:%d.%m.%Y %H:%M} | Утилізація {self.culture.name} {self.quantity} т у {self.place_from.name}"

    @property
    def action(self):
        return "utilization"
    
    def save(self, *args, **kwargs):
        """Оновлення балансу відходів при збереженні утилізації"""
        super().save(*args, **kwargs)
        BalanceService.adjust_balance(
            place=self.place_from,
            culture=self.culture,
            delta=-self.quantity,
            balance_type=BalanceType.WASTE
        )
        

class Recycling(models.Model):
    """Операція переробки відходів"""

    date_time = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата та час"
    )
    culture = models.ForeignKey(
        "directory.Culture",
        on_delete=models.CASCADE,
        verbose_name="Культура"
    )
    place_from = models.ForeignKey(
        "directory.Place",
        on_delete=models.CASCADE,
        verbose_name="Місце відправлення"
    )
    place_to = models.ForeignKey(
        "directory.Place",
        on_delete=models.CASCADE,
        related_name="recycling_in",
        verbose_name="Місце призначення"
    )
    input_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        verbose_name="Кількість (т)"
    )
    output_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        verbose_name="Кількість на виході (т)"
    )
    note = models.TextField(
        blank=True,
        null=True,
        verbose_name="Примітка"
    )

    class Meta:
        verbose_name = "Переробка"
        verbose_name_plural = "Операції переробки"

    def __str__(self):
        return f"{self.date_time:%d.%m.%Y %H:%M} | Переробка {self.culture.name} {self.input_quantity} т → {self.output_quantity} т у {self.place_from.name} -> {self.place_to.name}"
    
    @property
    def action(self):
        return "recycling"
    
    def clean(self):
        """Перевірка коректності даних перед збереженням"""
        # if self.input_quantity > BalanceService.get_balance(self.place_from, self.culture, BalanceType.WASTE).quantity:
        #     raise ValidationError("Недостатньо відходів для переробки.")
        print(f"Input: {self.input_quantity}, Output: {self.output_quantity}")
        if self.output_quantity > self.input_quantity:
            raise ValidationError("Кількість на виході не може перевищувати вхідну кількість.")
        
    def save(self, *args, **kwargs):
        """Оновлення балансу відходів при збереженні переробки"""
        super().save(*args, **kwargs)
        BalanceService.adjust_balance(
            place=self.place_from,
            culture=self.culture,
            delta=-self.input_quantity,
            balance_type=BalanceType.WASTE
        )
        BalanceService.adjust_balance(
            place=self.place_to,
            culture=self.culture,
            delta=self.output_quantity,
            balance_type=BalanceType.STOCK
        )

