from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, View, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.urls import reverse_lazy
from datetime import datetime, timedelta
import json
from .services import ReportService
from .forms import (
    BalanceReportFilterForm, WasteReportFilterForm,
    WeigherReportFilterForm, ShipmentReportFilterForm,
    FieldsReportFilterForm, ReportTemplateForm,
    SaveReportForm, CustomReportForm
)
from .models import ReportTemplate, ReportExecution, SavedReport


class ReportsDashboardView(LoginRequiredMixin, View):
    """Головна сторінка звітів"""
    
    def get(self, request):
        # Отримуємо денний звіт
        daily_summary = ReportService.get_daily_summary()
        
        # Останні виконані звіти
        recent_reports = ReportExecution.objects.filter(
            executed_by=request.user
        ).select_related('template')[:5]
        
        # Збережені звіти користувача
        saved_reports = SavedReport.objects.filter(
            user=request.user
        ).select_related('template')[:5]
        
        context = {
            'page': 'reports',
            'daily_summary': daily_summary,
            'recent_reports': recent_reports,
            'saved_reports': saved_reports,
        }
        
        return render(request, 'reports/dashboard.html', context)


class BaseReportView(LoginRequiredMixin, View):
    """Базовий клас для звітів"""
    
    template_name = 'reports/report.html'
    form_class = None
    report_method = None
    report_title = ''
    report_type = ''
    
    def get(self, request):
        form = self.form_class()
        
        # Встановлюємо дефолтні значення дат
        today = datetime.now().date()
        default_from = today - timedelta(days=30)
        
        # Оновлюємо форму з дефолтними значеннями
        form = self.form_class(initial={
            'date_from': default_from,
            'date_to': today,
        })
        
        context = {
            'page': 'reports',
            'form': form,
            'report_title': self.report_title,
            'report_type': self.report_type,
            'report_data': None,
            'filters_applied': False,
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request):
        form = self.form_class(request.POST)
        report_data = None
        filters_applied = False
        
        if form.is_valid():
            filters_applied = True
            
            # Отримуємо параметри фільтрації
            date_from = form.cleaned_data.get('date_from')
            date_to = form.cleaned_data.get('date_to')
            
            # Збираємо інші фільтри
            filters = {}
            for field_name, value in form.cleaned_data.items():
                if field_name not in ['date_from', 'date_to'] and value is not None:
                    if hasattr(value, 'id'):
                        filters[f'{field_name}_id'] = value.id
                    elif hasattr(value, 'pk'):
                        filters[f'{field_name}_id'] = value.pk
                    else:
                        filters[field_name] = value
            
            print(f"DEBUG: Calling {self.report_method.__name__} with:")
            print(f"  date_from: {date_from}")
            print(f"  date_to: {date_to}")
            print(f"  filters: {filters}")
            
            # Викликаємо метод сервісу з правильними аргументами
            try:
                # Викликаємо метод як статичний метод класу з явним передаванням аргументів
                report_data = self.report_method.__func__(
                    date_from=date_from,
                    date_to=date_to,
                    filters=filters
                )
            except TypeError as e:
                # Якщо виникає помилка через неправильні аргументи, спробуємо інший підхід
                print(f"TypeError: {e}")
                print(f"Trying alternative approach...")
                
                # Спробуємо викликати метод напряму
                try:
                    if date_from and date_to:
                        report_data = self.report_method(
                            date_from=date_from,
                            date_to=date_to,
                            filters=filters
                        )
                    else:
                        report_data = self.report_method(
                            date_from=date_from,
                            date_to=date_to,
                            filters=filters
                        )
                except Exception as e2:
                    print(f"Alternative approach failed: {e2}")
                    # Якщо все ще помилка, спробуємо передати все як keyword arguments
                    try:
                        report_data = self.report_method(
                            date_from=date_from,
                            date_to=date_to,
                            filters=filters
                        )
                    except Exception as e3:
                        print(f"All approaches failed: {e3}")
                        form.add_error(None, f"Помилка при генерації звіту: {e3}")
                        report_data = None
            except Exception as e:
                print(f"Error generating report: {e}")
                form.add_error(None, f"Помилка при генерації звіту: {str(e)}")
        
        context = {
            'page': 'reports',
            'form': form,
            'report_title': self.report_title,
            'report_type': self.report_type,
            'report_data': report_data,
            'filters_applied': filters_applied,
        }
        
        return render(request, self.template_name, context)


class BalanceReportView(BaseReportView):
    """Звіт по залишках"""
    form_class = BalanceReportFilterForm
    report_method = ReportService.get_balance_report
    report_title = 'Звіт по залишках'
    report_type = 'balance'


class WasteReportView(BaseReportView):
    """Звіт по відходах"""
    form_class = WasteReportFilterForm
    report_method = ReportService.get_waste_report
    report_title = 'Звіт по відходах'
    report_type = 'waste'


class WeigherReportView(BaseReportView):
    """Звіт по внутрішніх переміщеннях"""
    form_class = WeigherReportFilterForm
    report_method = ReportService.get_weigher_report
    report_title = 'Звіт по внутрішніх переміщеннях'
    report_type = 'weigher'


class ShipmentReportView(BaseReportView):
    """Звіт по відвантаженням"""
    form_class = ShipmentReportFilterForm
    report_method = ReportService.get_shipment_report
    report_title = 'Звіт по відвантаженням'
    report_type = 'shipment'


class FieldsReportView(BaseReportView):
    """Звіт по надходженням з полів"""
    form_class = FieldsReportFilterForm
    report_method = ReportService.get_fields_report
    report_title = 'Звіт по надходженням з полів'
    report_type = 'fields'


class ExportReportView(LoginRequiredMixin, View):
    """Експорт звіту в CSV"""
    
    def post(self, request):
        try:
            # Отримуємо дані зі запиту
            data_json = request.POST.get('data', '[]')
            data = json.loads(data_json)
            columns = request.POST.get('columns', '').split(',')
            report_name = request.POST.get('report_name', 'report')
            
            # Фільтруємо порожні колонки
            columns = [col for col in columns if col]
            
            if not data or not columns:
                return JsonResponse({'error': 'Немає даних для експорту'}, status=400)
            
            # Генеруємо CSV
            csv_content = ReportService.export_to_csv(data, columns)
            
            # Повертаємо файл
            response = HttpResponse(csv_content, content_type='text/csv; charset=utf-8-sig')
            response['Content-Disposition'] = f'attachment; filename="{report_name}_{datetime.now():%Y%m%d_%H%M%S}.csv"'
            
            return response
        except json.JSONDecodeError as e:
            return JsonResponse({'error': f'Помилка формату JSON: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Помилка при експорті: {str(e)}'}, status=500)


class DailyReportView(LoginRequiredMixin, View):
    """Денний звіт"""
    
    def get(self, request):
        date_str = request.GET.get('date')
        
        if date_str:
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                date = datetime.now().date()
        else:
            date = datetime.now().date()
        
        daily_summary = ReportService.get_daily_summary(date)
        
        # Розрахунок дат для навігації
        prev_date = date - timedelta(days=1)
        next_date = date + timedelta(days=1)
        
        context = {
            'page': 'reports',
            'daily_summary': daily_summary,
            'selected_date': date,
            'prev_date': prev_date,
            'next_date': next_date,
        }
        
        return render(request, 'reports/daily_report.html', context)


class CustomReportBuilderView(LoginRequiredMixin, View):
    """Конструктор власних звітів"""
    
    def get(self, request):
        form = CustomReportForm()
        
        context = {
            'page': 'reports',
            'form': form,
        }
        
        return render(request, 'reports/custom_builder.html', context)
    
    def post(self, request):
        form = CustomReportForm(request.POST)
        
        if form.is_valid():
            # Тут буде логіка обробки власного звіту
            # TODO: Реалізувати динамічну генерацію
            
            return JsonResponse({
                'success': True,
                'message': 'Звіт сформовано успішно'
            })
        
        return render(request, 'reports/custom_builder.html', {
            'page': 'reports',
            'form': form,
            'errors': form.errors
        })


class SavedReportsListView(LoginRequiredMixin, ListView):
    """Список збережених звітів"""
    
    model = SavedReport
    template_name = 'reports/saved_list.html'
    context_object_name = 'saved_reports'
    paginate_by = 20
    
    def get_queryset(self):
        return SavedReport.objects.filter(
            user=self.request.user
        ).select_related('template').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page'] = 'reports'
        return context


class ReportHistoryView(LoginRequiredMixin, ListView):
    """Історія виконаних звітів"""
    
    model = ReportExecution
    template_name = 'reports/history.html'
    context_object_name = 'executions'
    paginate_by = 20
    
    def get_queryset(self):
        return ReportExecution.objects.filter(
            executed_by=self.request.user
        ).select_related('template').order_by('-executed_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page'] = 'reports'
        return context