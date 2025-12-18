"""
Форми для налаштування та генерації PDF звітів
"""
from django import forms
from django.utils import timezone
from datetime import datetime, timedelta

from .models import ReportTemplate, SavedReport
from directory.models import Culture, Place, Field
from balances.models import BalanceType


class BasePDFReportForm(forms.Form):
    """Базова форма для PDF звітів"""
    
    OUTPUT_FORMATS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]
    
    output_format = forms.ChoiceField(
        choices=OUTPUT_FORMATS,
        initial='pdf',
        label="Формат виводу",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    orientation = forms.ChoiceField(
        choices=[
            ('portrait', 'Портретна'),
            ('landscape', 'Альбомна'),
        ],
        initial='portrait',
        label="Орієнтація сторінки",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    include_charts = forms.BooleanField(
        required=False,
        initial=False,
        label="Включити графіки",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    save_template = forms.BooleanField(
        required=False,
        initial=False,
        label="Зберегти як шаблон",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    template_name = forms.CharField(
        required=False,
        max_length=200,
        label="Назва шаблону",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введіть назву для збереження'
        })
    )
    
    send_to_report_server = forms.BooleanField(
        required=False,
        initial=False,
        label="Відправити на Report Server",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )



class BalanceDateReportForm(BasePDFReportForm):
    """Форма для звіту залишків за дату"""
    
    report_date = forms.DateField(
        required=True,
        label="Дата звіту",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        }),
        initial=timezone.now().date
    )
    
    place = forms.ModelChoiceField(
        queryset=Place.objects.all(),
        required=False,
        label="Місце (необов'язково)",
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Всі місця"
    )
    
    culture = forms.ModelChoiceField(
        queryset=Culture.objects.all(),
        required=False,
        label="Культура (необов'язково)",
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Всі культури"
    )
    
    balance_type = forms.ChoiceField(
        choices=[('', 'Всі'), ('stock', 'Зерно'), ('waste', 'Відходи')],
        required=False,
        label="Тип",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    group_by = forms.ChoiceField(
        choices=[
            ('none', 'Не групувати'),
            ('place', 'По місцях'),
            ('culture', 'По культурах'),
        ],
        initial='none',
        label="Групування",
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class BalancePeriodReportForm(BasePDFReportForm):
    """Форма для звіту залишків за період"""
    
    date_from = forms.DateField(
        required=True,
        label="Дата початку",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        })
    )
    
    date_to = forms.DateField(
        required=True,
        label="Дата кінця",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        }),
        initial=timezone.now().date
    )
    
    place = forms.ModelChoiceField(
        queryset=Place.objects.all(),
        required=False,
        label="Місце",
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Всі місця"
    )
    
    culture = forms.ModelChoiceField(
        queryset=Culture.objects.all(),
        required=False,
        label="Культура",
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Всі культури"
    )
    
    show_difference = forms.BooleanField(
        required=False,
        initial=True,
        label="Показати різницю",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            today = timezone.now().date()
            self.fields['date_from'].initial = today - timedelta(days=30)
            self.fields['date_to'].initial = today


class IncomeDateReportForm(BasePDFReportForm):
    """Форма для звіту приходу за дату"""
    
    report_date = forms.DateField(
        required=True,
        label="Дата звіту",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        }),
        initial=timezone.now().date
    )
    
    field = forms.ModelChoiceField(
        queryset=Field.objects.all(),
        required=False,
        label="Поле",
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Всі поля"
    )
    
    culture = forms.ModelChoiceField(
        queryset=Culture.objects.all(),
        required=False,
        label="Культура",
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Всі культури"
    )
    
    place_to = forms.ModelChoiceField(
        queryset=Place.objects.all(),
        required=False,
        label="Місце прийому",
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Всі місця"
    )


class IncomePeriodReportForm(BasePDFReportForm):
    """Форма для звіту приходу за період"""
    
    date_from = forms.DateField(
        required=True,
        label="Дата початку",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        })
    )
    
    date_to = forms.DateField(
        required=True,
        label="Дата кінця",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        }),
        initial=timezone.now().date
    )
    
    field = forms.ModelChoiceField(
        queryset=Field.objects.all(),
        required=False,
        label="Поле",
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Всі поля"
    )
    
    culture = forms.ModelChoiceField(
        queryset=Culture.objects.all(),
        required=False,
        label="Культура",
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Всі культури"
    )
    
    group_by = forms.ChoiceField(
        choices=[
            ('none', 'Не групувати'),
            ('date', 'По датах'),
            ('field', 'По полях'),
            ('culture', 'По культурах'),
        ],
        initial='date',
        label="Групування",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            today = timezone.now().date()
            self.fields['date_from'].initial = today - timedelta(days=30)


class ShipmentSummaryReportForm(BasePDFReportForm):
    """Форма для звіту ввезення/вивезення"""
    
    date_from = forms.DateField(
        required=True,
        label="Дата початку",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        })
    )
    
    date_to = forms.DateField(
        required=True,
        label="Дата кінця",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        }),
        initial=timezone.now().date
    )
    
    action_type = forms.ChoiceField(
        choices=[
            ('', 'Всі операції'),
            ('import', 'Тільки ввезення'),
            ('export', 'Тільки вивезення'),
        ],
        required=False,
        label="Тип операції",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    culture = forms.ModelChoiceField(
        queryset=Culture.objects.all(),
        required=False,
        label="Культура",
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Всі культури"
    )
    
    group_by = forms.ChoiceField(
        choices=[
            ('none', 'Не групувати'),
            ('date', 'По датах'),
            ('action', 'По типах операцій'),
            ('culture', 'По культурах'),
        ],
        initial='action',
        label="Групування",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    show_summary = forms.BooleanField(
        required=False,
        initial=True,
        label="Показати підсумки",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            today = timezone.now().date()
            self.fields['date_from'].initial = today - timedelta(days=30)


class ReportTemplateForm(forms.ModelForm):
    """Форма для створення/редагування шаблону звіту"""
    
    class Meta:
        model = ReportTemplate
        fields = [
            'name', 'description', 'report_type', 
            'output_format', 'chart_type', 'is_public'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Назва шаблону'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Опис шаблону'
            }),
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'output_format': forms.Select(attrs={'class': 'form-select'}),
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
        

class TotalIncomePeriodReportForm(BasePDFReportForm):
    """Форма для звіту 'Прихід зерна (Загальний за період)'."""
    
    date_from = forms.DateField(
        label="Дата початку",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        label="Дата кінця",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    # Можна додати інші фільтри (culture, place, field тощо)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            today = timezone.now().date()
            # Ініціалізація дат за замовчуванням
            self.fields['date_from'].initial = today - timedelta(days=7) 
            self.fields['date_to'].initial = today