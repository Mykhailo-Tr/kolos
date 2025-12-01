from django.db import models
from django.utils import timezone


class BalanceType(models.TextChoices):
    STOCK = "stock", "Зерно"
    WASTE = "waste", "Відходи"
    
class Balance(models.Model):
    """ Модель для збереження залишків зерна / відходів на складах. """

    place = models.ForeignKey(
        'directory.Place',
        on_delete=models.CASCADE,
        related_name='balances_records',
        verbose_name="Місце зберігання",
    )
    culture = models.ForeignKey(
        'directory.Culture',
        on_delete=models.CASCADE,
        related_name='balances_records',
        verbose_name="Культура",
    )
    balance_type = models.CharField(
        max_length=10,
        choices=BalanceType.choices,
        default=BalanceType.STOCK,
        verbose_name="Тип балансу",
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0,
        verbose_name="Кількість (тонн)",
    )
    
    class Meta:
        verbose_name = "Залишок"
        verbose_name_plural = "Залишки"
        ordering = ['place', 'culture', 'balance_type']
        unique_together = ('place', 'culture', 'balance_type')

    def __str__(self):
        return f"{self.place} - {self.culture} ({self.balance_type}): {self.quantity} тонн"
    
    @classmethod
    def create_snapshot(cls, description=""):
        """Створює зліпок всіх поточних залишків."""
        snapshot = BalanceSnapshot.objects.create(
            snapshot_date=timezone.now(),
            description=description
        )
        
        balances = cls.objects.select_related('place', 'culture').all()
        
        for balance in balances:
            BalanceHistory.objects.create(
                snapshot=snapshot,
                place_name=balance.place.name,
                culture_name=balance.culture.name,
                balance_type=balance.balance_type,
                quantity=balance.quantity,
            )
        
        return snapshot


class BalanceSnapshot(models.Model):
    """ Зліпок залишків (група записів історії). """
    
    snapshot_date = models.DateTimeField(default=timezone.now, verbose_name="Дата зліпку")
    description = models.CharField(
        max_length=255, 
        blank=True, 
        default="",
        verbose_name="Опис"
    )
    created_by = models.CharField(
        max_length=100,
        blank=True,
        default="система",
        verbose_name="Створено"
    )

    class Meta:
        verbose_name = "Зліпок залишків"
        verbose_name_plural = "Зліпки залишків"
        ordering = ['-snapshot_date']

    def __str__(self):
        return f"Зліпок від {self.snapshot_date.strftime('%d.%m.%Y %H:%M')}"
    
    def total_records(self):
        """Повертає кількість записів в зліпку."""
        return self.history_records.count()
    
    def total_quantity(self):
        """Повертає загальну кількість по зліпку."""
        from django.db.models import Sum
        result = self.history_records.aggregate(total=Sum('quantity'))
        return result['total'] or 0


class BalanceHistory(models.Model):
    """ Історичні записи залишків. """

    snapshot = models.ForeignKey(
        BalanceSnapshot,
        on_delete=models.CASCADE,
        related_name='history_records',
        verbose_name="Зліпок",
        null=True,  # Тимчасово для міграції
        blank=True
    )
    place_name = models.CharField(max_length=255, default="", verbose_name="Місце зберігання")
    culture_name = models.CharField(max_length=255, default="", verbose_name="Культура")
    balance_type = models.CharField(
        max_length=10,
        choices=BalanceType.choices,
        default=BalanceType.STOCK,
        verbose_name="Тип балансу",
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0,
        verbose_name="Кількість (тонн)"
    )

    class Meta:
        verbose_name = "Історія залишків"
        verbose_name_plural = "Історія залишків"
        ordering = ['place_name', 'culture_name']

    def __str__(self):
        return f"{self.place_name} — {self.culture_name}: {self.quantity} т"