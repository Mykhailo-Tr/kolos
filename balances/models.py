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
    
    def snapshot(self):
        """Створює запис в історії (зліпок поточного стану)."""
        BalanceHistory.objects.create(
            place_name=self.place.name,
            culture_name=self.culture.name,
            balance_type=self.balance_type,
            quantity=self.quantity,
            snapshot_date=timezone.now(),
        )
        

class BalanceHistory(models.Model):
    """ Історичні зліпки залишків по складах. """

    snapshot_date = models.DateField(default=timezone.now)
    # place_name = models.CharField(max_length=255)
    # culture_name = models.CharField(max_length=255)
    # balance_type = models.CharField(
    #     max_length=10,
    #     choices=BalanceType.choices,
    #     verbose_name="Тип балансу",
    # )
    # quantity = models.DecimalField(
    #     max_digits=12,
    #     decimal_places=3,
    #     verbose_name="Кількість (тонн)"
    # )

    class Meta:
        verbose_name = "Історія залишків"
        verbose_name_plural = "Історія залишків"
        ordering = ['-snapshot_date']

    def __str__(self):
        return f"[{self.snapshot_date}] {self.place_name} — {self.culture_name}: {self.quantity} т"

