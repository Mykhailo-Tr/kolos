from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from balances.services import BalanceService, BalanceType


class WasteOperation(models.Model):
    """Абстрактна базова модель для операцій з відходами"""
    
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
    note = models.TextField(
        blank=True,
        null=True,
        verbose_name="Примітка"
    )
    
    # Поля для відстеження початкових значень
    _original_values = None

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Зберігаємо початкові значення при завантаженні об'єкта
        if self.pk:
            self._original_values = self._get_operation_values()

    def _get_operation_values(self):
        """Отримує значення операції для відстеження змін"""
        values = {}
        if hasattr(self, 'quantity'):
            values['quantity'] = self.quantity
        if hasattr(self, 'input_quantity'):
            values['input_quantity'] = self.input_quantity
        if hasattr(self, 'output_quantity'):
            values['output_quantity'] = self.output_quantity
        return values

    def revert_balance(self):
        """Відкат змін балансу (для видалення або редагування)"""
        raise NotImplementedError("Підкласи повинні реалізувати цей метод")

    def update_balance(self):
        """Оновлення балансу (для створення або редагування)"""
        raise NotImplementedError("Підкласи повинні реалізувати цей метод")

    def get_original_value(self, field_name, default=None):
        """Безпечне отримання початкового значення"""
        if self._original_values and field_name in self._original_values:
            return self._original_values[field_name]
        return default
    
 