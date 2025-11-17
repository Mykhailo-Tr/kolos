from django.db import models
from django.utils import timezone
from balances.services import BalanceService, BalanceType

class WasteJournal(models.Model):
    """Журнал управління відходами"""

    ACTION_CHOICES = [
        ("utilization", "Утилізація"),
        ("recycling", "Переробка"),
    ]

    date_time = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата та час"
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name="Дія"
    )
    culture = models.ForeignKey(
        "directory.Culture",
        on_delete=models.CASCADE,
        verbose_name="Культура"
    )
    place_from = models.ForeignKey(
        "directory.Place",
        on_delete=models.CASCADE,
        related_name="waste_from",
        verbose_name="Місце відправлення"
    )
    place_to = models.ForeignKey(
        "directory.Place",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="waste_to",
        verbose_name="Місце призначення (для переробки)"
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        verbose_name="Кількість (т)"
    )

    class Meta:
        verbose_name = "Журнал управління відходами"
        verbose_name_plural = "Журнали управління відходами"
        ordering = ["-date_time"]

    def __str__(self):
        if self.action == "recycling" and self.place_to:
            return (
                f"{self.date_time:%d.%m.%Y %H:%M} | Переробка {self.culture.name} "
                f"{self.quantity} т → {self.place_to.name}"
            )
        return (
            f"{self.date_time:%d.%m.%Y %H:%M} | {self.get_action_display()} "
            f"{self.culture.name} {self.quantity} т у {self.place_from.name}"
        )
        
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.action == "utilization":
            # Зменшуємо відходи на місці відправлення
            BalanceService.adjust_balance(
                place=self.place_from,
                culture=self.culture,
                balance_type=BalanceType.WASTE,
                delta=-self.quantity
            )
        elif self.action == "recycling" and self.place_to:
            # Зменшуємо відходи на місці відправлення
            BalanceService.adjust_balance(
                place=self.place_from,
                culture=self.culture,
                balance_type=BalanceType.WASTE,
                delta=-self.quantity
            )
            # Збільшуємо залишок на місці призначення
            BalanceService.adjust_balance(
                place=self.place_to,
                culture=self.culture,
                balance_type=BalanceType.STOCK,
                delta=self.quantity
            )
        

