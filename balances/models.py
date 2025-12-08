from django.db import models
from django.utils import timezone


class BalanceType(models.TextChoices):
    STOCK = "stock", "Зерно"
    WASTE = "waste", "Відходи"


class Balance(models.Model):
    """Поточні залишки — унікальна комбінація (place, culture, balance_type)."""

    place = models.ForeignKey(
        'directory.Place',
        on_delete=models.CASCADE,
        related_name='balances',
        verbose_name='Місце зберігання',
    )
    culture = models.ForeignKey(
        'directory.Culture',
        on_delete=models.CASCADE,
        related_name='balances',
        verbose_name='Культура',
    )
    balance_type = models.CharField(
        max_length=10,
        choices=BalanceType.choices,
        default=BalanceType.STOCK,
        verbose_name='Тип балансу',
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0,
        verbose_name='Кількість (тонн)'
    )

    class Meta:
        verbose_name = 'Залишок'
        verbose_name_plural = 'Залишки'
        ordering = ['place__name', 'culture__name', 'balance_type']
        unique_together = ('place', 'culture', 'balance_type')

    def __str__(self):
        return f"{self.place} - {self.culture} ({self.balance_type}): {self.quantity} т"


class BalanceSnapshot(models.Model):
    """Група записів — зліпок на певну дату/час."""

    snapshot_date = models.DateTimeField(default=timezone.now, verbose_name='Дата зліпку')
    description = models.CharField(max_length=255, blank=True, default='', verbose_name='Опис')
    created_by = models.CharField(max_length=100, blank=True, default='система', verbose_name='Створено')

    class Meta:
        verbose_name = 'Зліпок залишків'
        verbose_name_plural = 'Зліпки залишків'
        ordering = ['-snapshot_date']

    def __str__(self):
        return f"Зліпок від {self.snapshot_date.strftime('%d.%m.%Y %H:%M')}"

    def total_records(self):
        return self.history_records.count()

    def total_quantity(self):
        from django.db.models import Sum
        agg = self.history_records.aggregate(total=Sum('quantity'))
        return agg['total'] or 0


class BalanceHistory(models.Model):
    """Окремий запис в контексті зліпку. Зберігає FK на place/culture для простоти доступу."""

    snapshot = models.ForeignKey(
        BalanceSnapshot,
        on_delete=models.CASCADE,
        related_name='history_records',
        verbose_name='Зліпок',
    )

    place = models.ForeignKey(
        'directory.Place',
        on_delete=models.PROTECT,
        related_name='balance_history',
        verbose_name='Місце зберігання',
    )
    culture = models.ForeignKey(
        'directory.Culture',
        on_delete=models.PROTECT,
        related_name='balance_history',
        verbose_name='Культура',
    )

    balance_type = models.CharField(
        max_length=10,
        choices=BalanceType.choices,
        default=BalanceType.STOCK,
        verbose_name='Тип балансу',
    )

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0,
        verbose_name='Кількість (тонн)'
    )

    class Meta:
        verbose_name = 'Історія залишків'
        verbose_name_plural = 'Історія залишків'
        ordering = ['place__name', 'culture__name']

    def __str__(self):
        return f"{self.place} — {self.culture}: {self.quantity} т"
