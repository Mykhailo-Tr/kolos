from django.db import models
from django.conf import settings
from django.utils import timezone
import json


class ReportTemplate(models.Model):
    """Шаблон звіту"""
    
    REPORT_TYPES = [
        ('balance', 'Залишки'),
        ('waste', 'Відходи'),
        ('weigher', 'Внутрішні переміщення'),
        ('shipment', 'Відвантаження'),
        ('fields', 'Надходження з полів'),
        ('income_date', 'Прихід зерна за дату'),
        ('balance_snapshot', 'Залишки за дату'),
        ('balance_period', 'Залишки за період'),
        ('income_period', 'Прихід зерна за період (старий)'),
        ('shipment_summary', 'Ввезення/вивезення за період'),
        ('total_income_period', 'Прихід зерна (Загальний за період)'), # <-- НОВИЙ ЗВІТ
        ('custom', 'Власний звіт'),
    ]
    
    CHART_TYPES = [
        ('bar', 'Стовпчаста діаграма'),
        ('line', 'Лінійний графік'),
        ('pie', 'Кругова діаграма'),
        ('area', 'Площинний графік'),
        ('table', 'Тільки таблиця'),
    ]
    
    OUTPUT_FORMATS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="Назва звіту")
    description = models.TextField(blank=True, verbose_name="Опис")
    report_type = models.CharField(
        max_length=20, 
        choices=REPORT_TYPES,
        verbose_name="Тип звіту"
    )
    chart_type = models.CharField(
        max_length=20,
        choices=CHART_TYPES,
        default='table',
        verbose_name="Тип візуалізації"
    )
    output_format = models.CharField(
        max_length=10,
        choices=OUTPUT_FORMATS,
        default='pdf',
        verbose_name="Формат виводу"
    )
    
    # JSON конфігурація для власних звітів
    config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Конфігурація",
        help_text="JSON з налаштуваннями фільтрів, полів та формату"
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='report_templates',
        verbose_name="Створено"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата оновлення")
    is_public = models.BooleanField(default=False, verbose_name="Публічний")
    
    class Meta:
        verbose_name = "Шаблон звіту"
        verbose_name_plural = "Шаблони звітів"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class ReportExecution(models.Model):
    """Історія виконання звітів"""
    
    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.CASCADE,
        related_name='executions',
        verbose_name="Шаблон",
        null=True,
        blank=True
    )
    executed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Виконано"
    )
    executed_at = models.DateTimeField(default=timezone.now, verbose_name="Час виконання")
    
    # Параметри виконання

    date_from = models.DateField(null=True, blank=True, verbose_name="Дата з")
    date_to = models.DateField(null=True, blank=True, verbose_name="Дата до")
    filters = models.JSONField(default=dict, blank=True, verbose_name="Фільтри")
    
    # Результати
    result_data = models.JSONField(default=dict, blank=True, verbose_name="Дані результату")
    row_count = models.IntegerField(default=0, verbose_name="Кількість рядків")
    report_type = models.CharField(max_length=20, verbose_name="Тип звіту")
    # Збережений файл
    file_path = models.FileField(
        upload_to='reports/%Y/%m/',
        null=True,
        blank=True,
        verbose_name="Файл звіту"
    )
    file_format = models.CharField(
        max_length=10,
        default='pdf',
        verbose_name="Формат файлу"
    )
    
    class Meta:
        verbose_name = "Виконання звіту"
        verbose_name_plural = "Історія виконань звітів"
        ordering = ['-executed_at']
    
    def __str__(self):
        template_name = self.template.name if self.template else self.report_type
        return f"{template_name} - {self.executed_at:%d.%m.%Y %H:%M}"


class SavedReport(models.Model):
    """Збережені звіти користувача"""
    
    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.CASCADE,
        related_name='saved_reports',
        verbose_name="Шаблон"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_reports',
        verbose_name="Користувач"
    )
    name = models.CharField(max_length=200, verbose_name="Назва")
    filters = models.JSONField(default=dict, verbose_name="Збережені фільтри")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено")
    
    # Посилання на останнє виконання
    last_execution = models.ForeignKey(
        ReportExecution,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Останнє виконання"
    )
    
    class Meta:
        verbose_name = "Збережений звіт"
        verbose_name_plural = "Збережені звіти"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"