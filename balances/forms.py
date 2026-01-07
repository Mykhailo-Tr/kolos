from django import forms
from .models import Balance, BalanceSnapshot, BalanceHistory
from datetime import timedelta


UNIT_CHOICES = (
    ('t', 'т'),
    ('kg', 'кг'),
)

# Базовий клас для форм з полем quantity, який має логіку перетворення
class BaseQuantityForm(forms.ModelForm):
    # Додаємо нове поле для вибору одиниці виміру. Воно не пов'язане з моделлю.
    unit = forms.ChoiceField(
        choices=UNIT_CHOICES,
        label="", 
        initial='t',  
        # КЛАС ДЛЯ СТИЛІЗАЦІЇ 'select-in-table' ВСТАНОВЛЕНО ТУТ
        widget=forms.Select(attrs={'class': 'select-in-table unit-switcher'}) 
    )
    
    # ... (решта BaseQuantityForm без змін) ...
    def clean_quantity(self):
        q = self.cleaned_data.get('quantity')
        unit = self.data.get(f'{self.prefix}-unit') if self.prefix else self.data.get('unit')
        if not unit:
             unit = 't' 
        
        if q is not None and q < 0:
            raise forms.ValidationError("Кількість не може бути від'ємною.")
            
        if q is not None and unit == 'kg':
            q = q / 1000 
        
        return q

class BalanceForm(BaseQuantityForm):
    class Meta:
        model = Balance
        fields = ['place', 'culture', 'balance_type', 'quantity']
        # Тут можна залишити form-select/form-control або змінити на input-in-table/select-in-table
        widgets = {
            'place': forms.Select(attrs={'class': 'form-select'}),
            'culture': forms.Select(attrs={'class': 'form-select'}),
            'balance_type': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control quantity-input', 'step': '0.001'}),
        }

# ... (BalanceSnapshotForm без змін) ...
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
            self.initial['snapshot_date'] = (self.instance.snapshot_date + timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M')


class BalanceHistoryForm(BaseQuantityForm):
    """
    ФОРМА ДЛЯ ФОРМСЕТА. ТУТ ВСТАНОВЛЮЄМО ВАШІ КЛАСИ.
    """
    class Meta:
        model = BalanceHistory
        fields = ['place', 'culture', 'balance_type', 'quantity']
        widgets = {
            # ВСТАНОВЛЕННЯ КЛАСІВ ДЛЯ SELECTS
            'place': forms.Select(attrs={'class': 'select-in-table'}),
            'culture': forms.Select(attrs={'class': 'select-in-table'}),
            'balance_type': forms.Select(attrs={'class': 'select-in-table'}),
            # ВСТАНОВЛЕННЯ КЛАСУ ДЛЯ INPUT
            'quantity': forms.NumberInput(
                attrs={
                    'class': 'input-in-table quantity-input', 
                    'step': '0.001',
                    'style': 'text-align:right;' # Це для чистого HTML-вирівнювання
                }
            ),
        }
    

# ... (EmptySnapshotForm без змін) ...
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