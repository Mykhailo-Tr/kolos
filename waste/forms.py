from django import forms
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from .models import Utilization, Recycling # Припускаємо, що моделі Utilization та Recycling імпортовані


UNIT_CHOICES = (
    ('t', 'Тонни (т)'),
    ('kg', 'Кілограми (кг)'),
)


# Базовий клас для форм утилізації/переробки з полями quantity (кількість)
class BaseWasteQuantityForm(forms.ModelForm):
    # Додаємо поле для вибору одиниці виміру для вхідної кількості
    input_unit = forms.ChoiceField(
        choices=UNIT_CHOICES,
        label="", 
        initial='t',
        widget=forms.Select(attrs={'class': 'form-select input-unit-switcher'})
    )

    # Додаємо поле для вибору одиниці виміру для вихідної кількості (для RecyclingForm)
    output_unit = forms.ChoiceField(
        choices=UNIT_CHOICES,
        label="",
        initial='t',
        widget=forms.Select(attrs={'class': 'form-select output-unit-switcher'})
    )

    def clean_quantity_field(self, field_name, unit_field_name):
        """
        Загальна логіка очищення та перетворення для полів quantity.
        Всі значення зберігаємо у ТОННАХ (t).
        """
        q = self.cleaned_data.get(field_name)
        
        # Отримуємо одиницю з сирих даних (self.data) для надійності
        unit = self.data.get(unit_field_name) if hasattr(self, 'data') else 't'
        
        if q is not None:
            # Специфічна валідація, що кількість > 0
            if q <= 0:
                raise ValidationError("Кількість повинна бути більшою за 0.")
            
            # Логіка перетворення:
            if unit == 'kg':
                q = q / 1000 # Перетворюємо кілограми в тонни

        return q
    
    pass


# 1. Оновлення UtilizationForm
class UtilizationForm(BaseWasteQuantityForm):
    
    class Meta:
        model = Utilization
        exclude = ("place_from", "culture")
        widgets = {
            "date_time": forms.DateTimeInput(attrs={
                "type": "datetime-local",
                "class": "form-control",
                "value": now().strftime("%Y-%m-%dT%H:%M"),
            }),     
            "quantity": forms.NumberInput(attrs={
                "class": "form-control input-quantity-input", 
                "step": "0.001",
                "min": "0",
                "placeholder": "Кількість утилізованих відходів (тонн)" 
            }),
            "note": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Примітка (необов’язково)",
            }),
        }
        
    def __init__(self, *args, balance=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.balance = balance
        
        # Видаляємо поле output_unit, щоб воно не відображалося у формі утилізації
        if 'output_unit' in self.fields:
            del self.fields['output_unit']

    def clean_quantity(self):
        # 1. Застосовуємо загальне перетворення (використовуємо input_unit)
        qty = self.clean_quantity_field("quantity", "input_unit") 

        # 2. Застосовуємо специфічну для Utilization валідацію (проти балансу)
        if qty is not None and self.balance and qty > self.balance.quantity:
            raise ValidationError(
                f"Неможливо утилізувати {qty} т — на балансі є лише {self.balance.quantity} т."
            )

        return qty

        
# 2. Оновлення RecyclingForm
class RecyclingForm(BaseWasteQuantityForm):
    class Meta:
        model = Recycling
        exclude = ("place_from", "culture")
        widgets = {
            "date_time": forms.DateTimeInput(attrs={
                "type": "datetime-local",
                "class": "form-control",
                "value": now().strftime("%Y-%m-%dT%H:%M"),
            }),     
            "input_quantity": forms.NumberInput(attrs={
                "class": "form-control input-quantity-input",
                "step": "0.001",
                "min": "0",
                "placeholder": "Кількість відходів для переробки (тонн)"
            }),
            "output_quantity": forms.NumberInput(attrs={
                "class": "form-control output-quantity-input",
                "step": "0.001",
                "min": "0",
                "placeholder": "Кількість отриманої продукції (тонн)"
            }),
            "place_to": forms.Select(attrs={"class": "form-select"}),
            "note": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Примітка (необов’язково)",
            }),
        }

    def __init__(self, *args, balance=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.balance = balance
        
    def clean_input_quantity(self):
        # Перетворюємо input_quantity, використовуючи input_unit
        return self.clean_quantity_field("input_quantity", "input_unit")

    def clean_output_quantity(self):
        # Перетворюємо output_quantity, використовуючи output_unit
        return self.clean_quantity_field("output_quantity", "output_unit")

    def clean(self):
        """
        Валідація на рівні форми: перевірка, що вихідна кількість <= вхідна кількість.
        """
        cleaned_data = super().clean()
        input_qty = cleaned_data.get("input_quantity")
        output_qty = cleaned_data.get("output_quantity")
        
        # Перевірка: обидва значення вже в тоннах
        if input_qty is not None and output_qty is not None:
            # Специфічна валідація для RecyclingForm: вихід не може бути більшим за вхід
            if output_qty > input_qty:
                # Додаємо помилку до поля output_quantity
                self.add_error('output_quantity', 
                               ValidationError(
                                   "Кількість на виході ({:.3f} т) не може бути більшою, ніж на вході ({:.3f} т)."
                                   .format(output_qty, input_qty)
                               ))
            
            # Також перевіряємо, чи input_quantity не перевищує баланс (якщо це тут потрібно)
            if self.balance and input_qty > self.balance.quantity:
                 self.add_error('input_quantity', 
                                ValidationError(
                                    f"Неможливо переробити {input_qty} т — на балансі є лише {self.balance.quantity} т."
                                ))
        
        return cleaned_data