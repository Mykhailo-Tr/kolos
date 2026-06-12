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

    to_balance_type = models.CharField(
        max_length=10,
        choices=BalanceType.choices,
        default=BalanceType.STOCK,
        verbose_name="Приймається як",
        help_text=(
            "Визначає, як зараховується кількість на місці призначення: "
            "як зерно чи як відходи. З місця відправлення завжди списується "
            "повна вага, що виїхала (брутто - тара), незалежно від втрат у дорозі."
        ),
    )

    class Meta:
        verbose_name = "Журнал внутрішніх переміщень"
        verbose_name_plural = "Журнали внутрішніх переміщень"
        ordering = ['-date_time']

    def __str__(self):
        return f"Внутрішнє переміщення {self.document_number} ({self.culture.name}): {self.weight_net} тонн"

    @property
    def departed_weight(self):
        """
        Повна вага, що фізично виїхала з from_place (брутто - тара),
        БЕЗ урахування втрат у дорозі. Саме цю вагу списуємо з джерела —
        бо склад фізично "втратив" всю завантажену кількість, незалежно
        від того, скільки з неї доїхало.
        """
        gross = self.weight_gross or 0
        tare = self.weight_tare or 0
        return gross - tare

    # ------------------------------------------------------------------
    # Зберігаємо "знімок" значень на момент завантаження з БД.
    # Потрібен, щоб revert_balance() міг коректно відкотити старий запис,
    # навіть якщо форма змінила culture / place / to_balance_type / вагу.
    # ------------------------------------------------------------------
    def _get_operation_values(self):
        values = super()._get_operation_values()
        values.update({
            'from_place_id': self.from_place_id,
            'to_place_id': self.to_place_id,
            'culture_id': self.culture_id,
            'to_balance_type': self.to_balance_type,
            'departed_weight': self.departed_weight,
        })
        return values

    def revert_balance(self):
        """Відкочує баланси за СТАРИМИ (на момент завантаження) значеннями."""
        original_weight_net = self.get_original_value('weight_net')
        if original_weight_net is None:
            return

        original_from_place_id = self.get_original_value('from_place_id')
        original_to_place_id = self.get_original_value('to_place_id')
        original_culture_id = self.get_original_value('culture_id')
        original_to_balance_type = self.get_original_value('to_balance_type', BalanceType.STOCK)
        # Фолбек для старих записів, у яких ще немає 'departed_weight' у знімку
        original_departed = self.get_original_value('departed_weight', original_weight_net)

        original_from_place = Place.objects.filter(pk=original_from_place_id).first() if original_from_place_id else None
        original_to_place = Place.objects.filter(pk=original_to_place_id).first() if original_to_place_id else None
        original_culture = Culture.objects.filter(pk=original_culture_id).first() if original_culture_id else None

        # На відправлення повертаємо ПОВНУ вагу, що виїхала (gross - tare),
        # бо саме її було списано в update_balance() — а не "нетто".
        if original_from_place and original_culture:
            BalanceService.adjust_balance(
                place=original_from_place,
                culture=original_culture,
                balance_type=BalanceType.STOCK,
                delta=original_departed
            )

        # На прийманні відкочуємо саме той тип балансу і ту "нетто"-суму
        # (gross - tare - loss), яку було нараховано.
        if original_to_place and original_culture:
            try:
                BalanceService.adjust_balance(
                    place=original_to_place,
                    culture=original_culture,
                    balance_type=original_to_balance_type,
                    delta=-original_weight_net
                )
            except ValueError:
                BalanceService.set_balance(
                    place=original_to_place,
                    culture=original_culture,
                    balance_type=original_to_balance_type,
                    quantity=0
                )

    def update_balance(self):
        """Нараховує баланси за НОВИМИ (поточними) значеннями."""
        if self.from_place:
            # З місця відправлення списується ПОВНА вага, що виїхала
            # (gross - tare), незалежно від втрат у дорозі.
            BalanceService.adjust_balance(
                place=self.from_place,
                culture=self.culture,
                balance_type=BalanceType.STOCK,
                delta=-self.departed_weight
            )
        if self.to_place:
            # На місце призначення приходить "нетто" (gross - tare - loss)
            # у вигляді зерна або відходів — залежно від перемикача.
            BalanceService.adjust_balance(
                place=self.to_place,
                culture=self.culture,
                balance_type=self.to_balance_type,
                delta=self.weight_net
            )

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if not is_new:
            self.revert_balance()

        super().save(*args, **kwargs)

        self.update_balance()

        # Оновлюємо "знімок" — щоб подальші save() в межах того ж інстансу
        # відкочували вже актуальні значення.
        self._original_values = self._get_operation_values()

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
            try:
                BalanceService.adjust_balance(
                    place=self.place_from,
                    culture=self.culture,
                    balance_type=BalanceType.STOCK,
                    delta=-self.weight_net,
                )
            except ValueError as e:
                BalanceService.set_balance(
                    place=self.place_from,
                    culture=self.culture,
                    balance_type=BalanceType.STOCK,
                    quantity=0
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
            try:
                BalanceService.adjust_balance(
                    place=self.place_to,
                    culture=self.culture,
                    balance_type=BalanceType.STOCK,
                    delta=-original_weight_net,
                )
            except ValueError:
                BalanceService.set_balance(
                    place=self.place_to,
                    culture=self.culture,
                    balance_type=BalanceType.STOCK,
                    quantity=0,
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
        

class OtherIncome(BaseJournal):
    """ Журнал інгорних надходжень (від людей, продавців) """
    
    seller = models.CharField(max_length=255, verbose_name="Продавець")
    
    place_to = models.ForeignKey(
        Place,
        on_delete=models.SET_NULL,
        related_name="other_incomes",
        verbose_name="Місце прийому",
        null=True
    )
        
    class Meta:
        verbose_name = "Журнал інших надходжень"
        verbose_name_plural = "Журнали інших надходжень"
        ordering = ['-date_time']
        
    def __str__(self):
        return f"Надходження {self.document_number} ({self.culture.name}) від {self.seller} до {self.place_to.name}: {self.weight_net} тонн"
    
    def revert_balance(self):
        """Відкат змін балансу (для видалення або редагування)"""
        original_weight_net = self.get_original_value('weight_net')
        if original_weight_net is not None and self.place_to:
            try:
                BalanceService.adjust_balance(
                    place=self.place_to,
                    culture=self.culture,
                    balance_type=BalanceType.STOCK,
                    delta=-original_weight_net,
                )
            except ValueError:
                BalanceService.set_balance(
                    place=self.place_to,
                    culture=self.culture,
                    balance_type=BalanceType.STOCK,
                    quantity=0,
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
        

