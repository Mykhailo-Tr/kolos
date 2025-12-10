from django import forms
from django.utils import timezone
from datetime import datetime, timedelta
from .models import ReportTemplate, SavedReport
from directory.models import Culture, Place, Field
from balances.models import BalanceType


class ReportFilterForm(forms.Form):
    """Базова форма фільтрів для звітів"""
    
    date_from = forms.DateField(
        required=True,
        label="Дата з",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        })
    )
    date_to = forms.DateField(
        required=True,
        label="Дата до",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Встановлюємо дефолтні значення дат
        if not self.is_bound:
            today = datetime.now().date()
            default_from = today - timedelta(days=30)
            
            self.fields['date_from'].initial = default_from
            self.fields['date_to'].initial = today


class BalanceReportFilterForm(ReportFilterForm):
    """Форма фільтрів для звіту по залишках"""
    
    place = forms.ModelChoiceField(
        queryset=Place.objects.all(),
        required=False,
        label="Місце",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    culture = forms.ModelChoiceField(
        queryset=Culture.objects.all(),
        required=False,
        label="Культура",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    balance_type = forms.ChoiceField(
        choices=[('', 'Всі'), ('stock', 'Зерно'), ('waste', 'Відходи')],
        required=False,
        label="Тип",
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class WasteReportFilterForm(ReportFilterForm):
    """Форма фільтрів для звіту по відходах"""
    
    place = forms.ModelChoiceField(
        queryset=Place.objects.all(),
        required=False,
        label="Місце",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    culture = forms.ModelChoiceField(
        queryset=Culture.objects.all(),
        required=False,
        label="Культура",
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class WeigherReportFilterForm(ReportFilterForm):
    """Форма фільтрів для звіту по внутрішніх переміщеннях"""
    
    from_place = forms.ModelChoiceField(
        queryset=Place.objects.all(),
        required=False,
        label="З місця",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    to_place = forms.ModelChoiceField(
        queryset=Place.objects.all(),
        required=False,
        label="До місця",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    culture = forms.ModelChoiceField(
        queryset=Culture.objects.all(),
        required=False,
        label="Культура",
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class ShipmentReportFilterForm(ReportFilterForm):
    """Форма фільтрів для звіту по відвантаженням"""
    
    action_type = forms.ChoiceField(
        choices=[('', 'Всі'), ('import', 'Ввезення'), ('export', 'Вивезення')],
        required=False,
        label="Тип операції",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    culture = forms.ModelChoiceField(
        queryset=Culture.objects.all(),
        required=False,
        label="Культура",
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class FieldsReportFilterForm(ReportFilterForm):
    """Форма фільтрів для звіту по надходженням з полів"""
    
    field = forms.ModelChoiceField(
        queryset=Field.objects.all(),
        required=False,
        label="Поле",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    culture = forms.ModelChoiceField(
        queryset=Culture.objects.all(),
        required=False,
        label="Культура",
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class ReportTemplateForm(forms.ModelForm):
    """Форма для створення шаблону звіту"""
    
    class Meta:
        model = ReportTemplate
        fields = ['name', 'description', 'report_type', 'chart_type', 'is_public']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Назва звіту'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Опис звіту'
            }),
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'chart_type': forms.Select(attrs={'class': 'form-select'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SaveReportForm(forms.ModelForm):
    """Форма для збереження звіту"""
    
    class Meta:
        model = SavedReport
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Назва збереженого звіту'
            })
        }


class CustomReportForm(forms.Form):
    """Форма для створення власного звіту"""
    
    MODELS = [
        ('balance', 'Залишки'),
        ('weigher', 'Внутрішні переміщення'),
        ('shipment', 'Відвантаження'),
        ('fields', 'Надходження з полів'),
    ]
    
    AGGREGATIONS = [
        ('sum', 'Сума'),
        ('avg', 'Середнє'),
        ('count', 'Кількість'),
        ('min', 'Мінімум'),
        ('max', 'Максимум'),
    ]
    
    model = forms.ChoiceField(
        choices=MODELS,
        label="Модель даних",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    fields = forms.MultipleChoiceField(
        choices=[],  # Заповнюється динамічно
        label="Поля для відображення",
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )
    
    group_by = forms.ChoiceField(
        choices=[],  # Заповнюється динамічно
        required=False,
        label="Групувати по",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    aggregation = forms.ChoiceField(
        choices=AGGREGATIONS,
        required=False,
        label="Агрегація",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    aggregation_field = forms.ChoiceField(
        choices=[],  # Заповнюється динамічно
        required=False,
        label="Поле для агрегації",
        widget=forms.Select(attrs={'class': 'form-select'})
    )