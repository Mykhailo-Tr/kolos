from django import forms
from .models import Balance, BalanceSnapshot, BalanceHistory


UNIT_CHOICES = (
    ('t', 'Тонни (т)'),
    ('kg', 'Кілограми (кг)'),
)

# Базовий клас для форм з полем quantity, який має логіку перетворення
class BaseQuantityForm(forms.ModelForm):
    # Додаємо нове поле для вибору одиниці виміру. Воно не пов'язане з моделлю.
    unit = forms.ChoiceField(
        choices=UNIT_CHOICES,
        label="", 
        initial='t',  
        widget=forms.Select(attrs={'class': 'form-select unit-switcher'}) 
    )

    def clean_quantity(self):
        q = self.cleaned_data.get('quantity')
        
        # ОТРИМУЄМО ОДИНИЦЮ З СИРИХ ДАНИХ (self.data) ДЛЯ НАДІЙНОСТІ
        # Якщо форма була відправлена (тобто self.data існує)
        unit = self.data.get('unit') if hasattr(self, 'data') else 't'
        
        # 1. Валідація на від'ємне значення
        if q is not None and q < 0:
            raise forms.ValidationError("Кількість не може бути від'ємною.")
            
        # 2. Логіка перетворення: Всі значення зберігаємо у ТОННАХ (t)
        if q is not None and unit == 'kg':
            # q тут вже має бути числом завдяки NumberInput та Django
            q = q / 1000 # <--- ТУТ ВІДБУВАЄТЬСЯ ДІЛЕННЯ
        
        # Повертаємо стандартизоване значення (вже в тоннах)
        return q

class BalanceForm(BaseQuantityForm):
    class Meta:
        model = Balance
        fields = ['place', 'culture', 'balance_type', 'quantity']
        widgets = {
            'place': forms.Select(attrs={'class': 'form-select'}),
            'culture': forms.Select(attrs={'class': 'form-select'}),
            'balance_type': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control quantity-input', 'step': '0.001'}),
        }

class BalanceSnapshotForm(forms.ModelForm):
    class Meta:
        model = BalanceSnapshot
        fields = ['description', 'created_by', 'snapshot_date']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'created_by': forms.TextInput(attrs={'class': 'form-control'}),
            'snapshot_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}, format='%Y-%m-%dT%H:%M')
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.initial['snapshot_date'] = self.instance.snapshot_date.strftime('%Y-%m-%dT%H:%M')


class BalanceHistoryForm(BaseQuantityForm):
    class Meta:
        model = BalanceHistory
        fields = ['place', 'culture', 'balance_type', 'quantity']
        widgets = {
            'place': forms.Select(attrs={'class': 'form-select'}),
            'culture': forms.Select(attrs={'class': 'form-select'}),
            'balance_type': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control quantity-input', 'step': '0.001'}),
        }
    

class EmptySnapshotForm(forms.ModelForm):
    """Форма для створення порожнього зліпка"""
    class Meta:
        model = BalanceSnapshot
        fields = ['snapshot_date', 'description', 'created_by']
        widgets = {
            'snapshot_date': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local', 
                    'class': 'form-control'
                }, 
                format='%Y-%m-%dT%H:%M'
            ),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Опис зліпка'}),
            'created_by': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ваше ім\'я'}),
        }
        labels = {
            'snapshot_date': 'Дата та час зліпка',
            'description': 'Опис',
            'created_by': 'Створено ким',
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user and not self.instance.pk:
            self.fields['created_by'].initial = self.user.get_full_name() or self.user.username
    
    def clean_created_by(self):
        created_by = self.cleaned_data.get('created_by')
        if not created_by and self.user:
            return self.user.get_full_name() or self.user.username
        return created_by