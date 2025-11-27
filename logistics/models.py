from django.db import models
from django.utils import timezone
from directory.models import Car, Trailer, Driver, Culture, Place, Field
from balances.services import BalanceService, BalanceType



class BaseJournal(models.Model):
    """ Базова модель для операцій зважування """

    document_number = models.CharField(max_length=50, verbose_name="№ документа / накладної")
    date_time = models.DateTimeField(default=timezone.now, verbose_name="Дата і час")

    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, verbose_name="Водій", null=True)
    car = models.ForeignKey(Car, on_delete=models.SET_NULL, verbose_name="Автомобіль", null=True)
    trailer = models.ForeignKey(Trailer, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Причеп")
    culture = models.ForeignKey(Culture, on_delete=models.SET_NULL, verbose_name="Культура", null=True)

    weight_gross = models.DecimalField(max_digits=12, decimal_places=3, verbose_name="Вага брутто (тонн)")
    weight_tare = models.DecimalField(max_digits=12, decimal_places=3, verbose_name="Вага тара (тонн)")
    weight_loss = models.DecimalField(max_digits=12, decimal_places=3,  verbose_name="Вага втрат (тонн)",
                                      null=True, blank=True)
    weight_net = models.DecimalField(max_digits=12, decimal_places=3, editable=False, verbose_name="Вага нетто (тонн)")
    note = models.TextField(blank=True, null=True, verbose_name="Примітка")

    _original_values = None
    
    class Meta:
        abstract = True  # це важливо — Django не створюватиме таблицю для базового класу

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.pk:
            self._original_values = self._get_operation_values()
            
    def _get_operation_values(self):
        return {
            'weight_net': self.weight_net,
        }
    
    def get_original_value(self, field_name, default=None):
        if self._original_values and field_name in self._original_values:
            return self._original_values[field_name]
        return default
    
    def save(self, *args, **kwargs):
        if self.weight_loss:
            self.weight_net = self.weight_gross - self.weight_tare - self.weight_loss
        else:
            self.weight_net = self.weight_gross - self.weight_tare
        super().save(*args, **kwargs)


class WeigherJournal(BaseJournal):
    """ Внутрішні переміщення """
    
    from_place = models.ForeignKey(
        Place,
        on_delete=models.SET_NULL,
        related_name="weighings_from",
        verbose_name="З місця",
        null=True
    )
    to_place = models.ForeignKey(
        Place,
        on_delete=models.SET_NULL,
        related_name="weighings_to",
        verbose_name="До місця",
        null=True
    )
    
    class Meta:
        verbose_name = "Журнал внутрішніх переміщень"
        verbose_name_plural = "Журнали внутрішніх переміщень"
        ordering = ['-date_time']
        
    def __str__(self):
        return f"Внутрішнє переміщення {self.document_number} ({self.culture.name}): {self.weight_net} тонн"

    def revert_balance(self):
        original_weight_net = self.get_original_value('weight_net')
        if original_weight_net is not None:
            if self.from_place:
                BalanceService.adjust_balance(
                    place=self.from_place,
                    culture=self.culture,
                    balance_type=BalanceType.STOCK,
                    delta=original_weight_net
                )
            if self.to_place:
                try:
                    BalanceService.adjust_balance(
                        place=self.to_place,
                        culture=self.culture,
                        balance_type=BalanceType.STOCK,
                        delta=-original_weight_net
                    )
                except ValueError:
                    BalanceService.set_balance(
                        place=self.to_place,
                        culture=self.culture,
                        balance_type=BalanceType.STOCK,
                        quantity=0
                    )
                
    def update_balance(self):
        if self.from_place:
            BalanceService.adjust_balance(
                place=self.from_place,
                culture=self.culture,
                balance_type=BalanceType.STOCK,
                delta=-self.weight_net
            )
        if self.to_place:
            BalanceService.adjust_balance(
                place=self.to_place,
                culture=self.culture,
                balance_type=BalanceType.STOCK,
                delta=self.weight_net
            )
                
    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if not is_new:
            self.revert_balance()
            
        super().save(*args, **kwargs)
        
        self.update_balance()
            
    def delete(self, *args, **kwargs):
        self.revert_balance()
        super().delete(*args, **kwargs)


class ShipmentAction(models.TextChoices):
    IMPORT = "import", "Ввезення"
    EXPORT = "export", "Вивезення"

class ShipmentJournal(BaseJournal):
    """ Зовнішні операції - відвантаження """
    
    action_type = models.CharField(
        max_length=10,
        choices=ShipmentAction.choices,
        verbose_name="Тип операції",
        null=True
    )
    place_from = models.ForeignKey(
        Place,
        on_delete=models.SET_NULL,
        related_name="shipments",
        verbose_name="Місце з",
        null=True,
        blank=True
    )
    place_from_text = models.CharField(max_length=255, blank=True, null=True, verbose_name="Місце з (текст)")
    
    place_to = models.ForeignKey(
        Place,
        on_delete=models.SET_NULL,
        related_name="receipts",
        verbose_name="Місце до",
        null=True,
        blank=True
    )
    place_to_text = models.CharField(max_length=255, blank=True, null=True, verbose_name="Місце до (текст)")
    
    class Meta:
        verbose_name = "Журнал відвантажень"
        verbose_name_plural = "Журнали відвантажень"
        ordering = ['-date_time']
    
    @property
    def display_place_from(self):
        if self.action_type == ShipmentAction.EXPORT:
            return self.place_from.name if self.place_from else self.place_from_text or "Невідомо"
        return self.place_from.name if self.place_from else "—"

    @property
    def display_place_to(self):
        if self.action_type == ShipmentAction.IMPORT:
            return self.place_to.name if self.place_to else self.place_to_text or "Невідомо"
        return self.place_to.name if self.place_to else "—"
        
    def __str__(self):
        return (
            f"Відвантаження {self.document_number} ({self.culture.name}) "
            f"з {self.display_place_from} до {self.display_place_to}: "
            f"{self.weight_net} тонн"
        )
        
    
    def revert_balance(self):
        original_weight_net = self.get_original_value('weight_net')
        print(f"{original_weight_net = }")
        print(f"{self.weight_net = }")
        print(f"{self.action_type = }")
        print(f"{self.place_from = }")
        print(f"{self.place_to = }")
        if self.action_type == ShipmentAction.IMPORT and self.place_to:
            try:
                BalanceService.adjust_balance(
                    place=self.place_to,
                    culture=self.culture,
                    balance_type=BalanceType.STOCK,
                    delta=-original_weight_net,
                )
            except ValueError as e:
                BalanceService.set_balance(
                    place=self.place_to,
                    culture=self.culture,
                    balance_type=BalanceType.STOCK,
                    quantity=0
                )
        elif self.action_type == ShipmentAction.EXPORT and self.place_from:
            BalanceService.adjust_balance(
                place=self.place_from,
                culture=self.culture,
                balance_type=BalanceType.STOCK,
                delta=original_weight_net,
            )

        
    def update_balance(self):
        """Делегує бізнес-логіку в BalanceService."""
        if not self.culture or not self.weight_net:
            return

        if self.action_type == ShipmentAction.IMPORT and self.place_to:
            BalanceService.adjust_balance(
                place=self.place_to,
                culture=self.culture,
                balance_type=BalanceType.STOCK,
                delta=self.weight_net,
            )
        elif self.action_type == ShipmentAction.EXPORT and self.place_from:
            BalanceService.adjust_balance(
                place=self.place_from,
                culture=self.culture,
                balance_type=BalanceType.STOCK,
                delta=-self.weight_net,
            )
            
    def clean(self):
        """Валідація залежно від типу дії."""
        from django.core.exceptions import ValidationError

        if self.action_type == ShipmentAction.IMPORT:
            if not self.place_to:
                raise ValidationError("Для ввезення потрібно вказати 'Місце до'.")
        elif self.action_type == ShipmentAction.EXPORT:
            if not self.place_from :
                raise ValidationError("Для вивезення потрібно вказати 'Місце з'.")
            
        
    def save(self, *args, **kwargs):
        """Збереження з коректним оновленням балансу"""
        self.full_clean()
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
        

class FieldsIncome(BaseJournal):
    """ Журнал надходжень з полів """
    
    field = models.ForeignKey(
        Field,
        on_delete=models.SET_NULL,
        related_name="field_outcomes",
        verbose_name="Поле",
        null=True
    )
    
    place_to = models.ForeignKey(
        Place,
        on_delete=models.SET_NULL,
        related_name="field_incomes",
        verbose_name="Місце прийому",
        null=True
    )
        
    class Meta:
        verbose_name = "Журнал надходжень з полів"
        verbose_name_plural = "Журнали надходжень з полів"
        ordering = ['-date_time']
        
    def __str__(self):
        return f"Надходження {self.document_number} ({self.culture.name}) з поля {self.field.name} до {self.place_to.name}: {self.weight_net} тонн"
    
    def revert_balance(self):
        """Відкат змін балансу (для видалення або редагування)"""
        original_weight_net = self.get_original_value('weight_net')
        if original_weight_net is not None and self.place_to:
            BalanceService.adjust_balance(
                place=self.place_to,
                culture=self.culture,
                balance_type=BalanceType.STOCK,
                delta=-original_weight_net,
            )
            
    def update_balance(self):
        weight_net = self.weight_net
        if self.place_to:
            BalanceService.adjust_balance(
                place=self.place_to,
                culture=self.culture,
                balance_type=BalanceType.STOCK,
                delta=weight_net,
            )
    
    def save(self, *args, **kwargs):
        is_new = self._state.adding

        if not is_new:
            self.revert_balance()

        super().save(*args, **kwargs)

        self.update_balance()
        
    def delete(self, *args, **kwargs):
        self.revert_balance()
        super().delete(*args, **kwargs)
        

