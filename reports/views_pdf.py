"""
В'юшки для роботи з PDF звітами
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, ListView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, FileResponse
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.files.base import ContentFile
from datetime import datetime
import json

from .models import ReportTemplate, ReportExecution, SavedReport
from .forms_pdf import (
    BalanceDateReportForm, BalancePeriodReportForm,
    IncomeDateReportForm, IncomePeriodReportForm,
    ShipmentSummaryReportForm, ReportTemplateForm
)
from .services.services import ReportService
from .services.pdf_generator import ReportPDFBuilder
from balances.models import BalanceSnapshot


class PDFReportGeneratorMixin:
    """Mixin для генерації PDF звітів"""
    
    def generate_pdf_response(self, pdf_buffer, filename):
        """Створює HTTP відповідь з PDF файлом"""
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    def save_report_execution(self, template, report_type, filters, data, pdf_buffer, file_format='pdf'):
        """Зберігає виконання звіту"""
        # Визначаємо кількість рядків. Для порівняльних звітів (як BalancePeriod) data це список,
        # для інших - dict з ключем 'total_rows'
        if isinstance(data, dict) and 'total_rows' in data:
            row_count = data['total_rows']
        elif isinstance(data, list):
            row_count = len(data)
        elif isinstance(data, dict) and 'comparison' in data: # Якщо comparison_data
             row_count = len(data['comparison'])
        else:
            row_count = 0
            
        execution = ReportExecution.objects.create(
            template=template,
            executed_by=self.request.user,
            report_type=report_type,
            date_from=filters.get('date_from'),
            date_to=filters.get('date_to'),
            filters=filters,
            result_data=data,
            row_count=row_count, 
            file_format=file_format
        )
        
        # Зберігаємо файл
        filename = f"report_{execution.id}.{file_format}"
        execution.file_path.save(
            filename,
            ContentFile(pdf_buffer.getvalue()),
            save=True
        )
        
        return execution


class BalanceDateReportView(LoginRequiredMixin, PDFReportGeneratorMixin, View):
    """Звіт залишків за конкретну дату"""
    
    template_name = 'reports/pdf/report_form_base.html' # <--- ОНОВЛЕНО
    form_class = BalanceDateReportForm
    
    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {
            'form': form,
            'page': 'reports',
            'report_title': 'Звіт залишків за дату'
        })
    
    def post(self, request):
        form = self.form_class(request.POST)
        
        if form.is_valid():
            report_date = form.cleaned_data['report_date']
            filters = {
                'place_id': form.cleaned_data.get('place').id if form.cleaned_data.get('place') else None,
                'culture_id': form.cleaned_data.get('culture').id if form.cleaned_data.get('culture') else None,
                'balance_type': form.cleaned_data.get('balance_type'),
                'orientation': form.cleaned_data.get('orientation', 'portrait'),
                'include_charts': form.cleaned_data.get('include_charts', False), # <--- ДОДАНО/ОНОВЛЕНО
            }
            
            # Отримуємо дані зі снепшота найближчого до вказаної дати
            snapshot = BalanceSnapshot.objects.filter(
                snapshot_date__date__lte=report_date
            ).order_by('-snapshot_date').first()
            
            if snapshot:
                data = ReportService.get_balance_snapshot_data(snapshot, filters)
            else:
                # Якщо немає снепшотів, беремо поточні залишки
                data = ReportService.get_balance_report(filters=filters)
            
            # Генеруємо PDF
            pdf_buffer = ReportPDFBuilder.build_balance_report(
                data, 
                date=report_date,
                filters=filters
            )
            
            # Зберігаємо виконання
            self.save_report_execution(
                template=None,
                report_type='balance_snapshot',
                filters={'date': report_date.isoformat(), **filters},
                data=data,
                pdf_buffer=pdf_buffer
            )
            
            # Повертаємо PDF
            filename = f"balance_report_{report_date.strftime('%Y%m%d')}.pdf"
            return self.generate_pdf_response(pdf_buffer, filename)
        
        return render(request, self.template_name, {
            'form': form,
            'page': 'reports',
            'report_title': 'Звіт залишків за дату'
        })


class BalancePeriodReportView(LoginRequiredMixin, PDFReportGeneratorMixin, View):
    """Звіт залишків за період (порівняння)"""
    
    template_name = 'reports/pdf/report_form_base.html' # <--- ОНОВЛЕНО
    form_class = BalancePeriodReportForm
    
    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {
            'form': form,
            'page': 'reports',
            'report_title': 'Звіт залишків за період'
        })
    
    def post(self, request):
        form = self.form_class(request.POST)
        
        if form.is_valid():
            date_from = form.cleaned_data['date_from']
            date_to = form.cleaned_data['date_to']
            filters = {
                'place_id': form.cleaned_data.get('place').id if form.cleaned_data.get('place') else None,
                'culture_id': form.cleaned_data.get('culture').id if form.cleaned_data.get('culture') else None,
                'orientation': form.cleaned_data.get('orientation', 'portrait'),
                'include_charts': form.cleaned_data.get('include_charts', False), # <--- ДОДАНО/ОНОВЛЕНО
            }
            
            # Отримуємо снепшоти на початок та кінець періоду
            start_snapshot = BalanceSnapshot.objects.filter(
                snapshot_date__date__lte=date_from
            ).order_by('-snapshot_date').first()
            
            end_snapshot = BalanceSnapshot.objects.filter(
                snapshot_date__date__lte=date_to
            ).order_by('-snapshot_date').first()
            
            if not start_snapshot or not end_snapshot:
                messages.error(request, 'Недостатньо даних для побудови звіту за вказаний період')
                return render(request, self.template_name, {
                    'form': form,
                    'page': 'reports',
                    'report_title': 'Звіт залишків за період'
                })
            
            # Порівнюємо дані
            comparison_data = ReportService.compare_balance_snapshots(start_snapshot, end_snapshot, filters)
            
            # Передаємо filters
            pdf_buffer = ReportPDFBuilder.build_balance_period_report(
                comparison_data,
                date_from,
                date_to,
                filters=filters
            )
            
            # Зберігаємо виконання
            self.save_report_execution(
                template=None,
                report_type='balance_period',
                filters={
                    'date_from': date_from.isoformat(),
                    'date_to': date_to.isoformat(),
                    **filters
                },
                data={'comparison': comparison_data}, # Зберігаємо comparison_data
                pdf_buffer=pdf_buffer
            )
            
            # Повертаємо PDF
            filename = f"balance_period_{date_from.strftime('%Y%m%d')}_{date_to.strftime('%Y%m%d')}.pdf"
            return self.generate_pdf_response(pdf_buffer, filename)
        
        return render(request, self.template_name, {
            'form': form,
            'page': 'reports',
            'report_title': 'Звіт залишків за період'
        })


class IncomeDateReportView(LoginRequiredMixin, PDFReportGeneratorMixin, View):
    """Звіт приходу зерна за дату"""
    
    template_name = 'reports/pdf/report_form_base.html' # <--- ОНОВЛЕНО
    form_class = IncomeDateReportForm
    
    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {
            'form': form,
            'page': 'reports',
            'report_title': 'Звіт приходу зерна за дату'
        })
    
    def post(self, request):
        form = self.form_class(request.POST)
        
        if form.is_valid():
            report_date = form.cleaned_data['report_date']
            filters = {
                'field_id': form.cleaned_data.get('field').id if form.cleaned_data.get('field') else None,
                'culture_id': form.cleaned_data.get('culture').id if form.cleaned_data.get('culture') else None,
                'place_to_id': form.cleaned_data.get('place_to').id if form.cleaned_data.get('place_to') else None,
                'orientation': form.cleaned_data.get('orientation', 'portrait'),
                'include_charts': form.cleaned_data.get('include_charts', False), # <--- ДОДАНО/ОНОВЛЕНО
            }
            
            # Отримуємо дані за дату
            data = ReportService.get_fields_report(
                date_from=report_date,
                date_to=report_date,
                filters=filters
            )
            
            # Генеруємо PDF
            pdf_buffer = ReportPDFBuilder.build_income_report(
                data,
                report_date,
                report_date,
                filters
            )
            
            # Зберігаємо виконання
            self.save_report_execution(
                template=None,
                report_type='income_date',
                filters={'date': report_date.isoformat(), **filters},
                data=data,
                pdf_buffer=pdf_buffer
            )
            
            # Повертаємо PDF
            filename = f"income_report_{report_date.strftime('%Y%m%d')}.pdf"
            return self.generate_pdf_response(pdf_buffer, filename)
        
        return render(request, self.template_name, {
            'form': form,
            'page': 'reports',
            'report_title': 'Звіт приходу зерна за дату'
        })


class IncomePeriodReportView(LoginRequiredMixin, PDFReportGeneratorMixin, View):
    """Звіт приходу зерна за період"""
    
    template_name = 'reports/pdf/report_form_base.html' # <--- ОНОВЛЕНО
    form_class = IncomePeriodReportForm
    
    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {
            'form': form,
            'page': 'reports',
            'report_title': 'Звіт приходу зерна за період'
        })
    
    def post(self, request):
        form = self.form_class(request.POST)
        
        if form.is_valid():
            date_from = form.cleaned_data['date_from']
            date_to = form.cleaned_data['date_to']
            filters = {
                'field_id': form.cleaned_data.get('field').id if form.cleaned_data.get('field') else None,
                'culture_id': form.cleaned_data.get('culture').id if form.cleaned_data.get('culture') else None,
                'orientation': form.cleaned_data.get('orientation', 'portrait'),
                'include_charts': form.cleaned_data.get('include_charts', False), # <--- ДОДАНО/ОНОВЛЕНО
            }
            
            # Отримуємо дані за період
            data = ReportService.get_fields_report(
                date_from=date_from,
                date_to=date_to,
                filters=filters
            )
            
            # Генеруємо PDF
            pdf_buffer = ReportPDFBuilder.build_income_report(
                data,
                date_from,
                date_to,
                filters
            )
            
            # Зберігаємо виконання
            self.save_report_execution(
                template=None,
                report_type='income_period',
                filters={
                    'date_from': date_from.isoformat(),
                    'date_to': date_to.isoformat(),
                    **filters
                },
                data=data,
                pdf_buffer=pdf_buffer
            )
            
            # Повертаємо PDF
            filename = f"income_period_{date_from.strftime('%Y%m%d')}_{date_to.strftime('%Y%m%d')}.pdf"
            return self.generate_pdf_response(pdf_buffer, filename)
        
        return render(request, self.template_name, {
            'form': form,
            'page': 'reports',
            'report_title': 'Звіт приходу зерна за період'
        })


class ShipmentSummaryReportView(LoginRequiredMixin, PDFReportGeneratorMixin, View):
    """Звіт ввезення/вивезення за період"""
    
    template_name = 'reports/pdf/report_form_base.html' # <--- ОНОВЛЕНО
    form_class = ShipmentSummaryReportForm
    
    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {
            'form': form,
            'page': 'reports',
            'report_title': 'Звіт ввезення/вивезення'
        })
    
    def post(self, request):
        form = self.form_class(request.POST)
        
        if form.is_valid():
            date_from = form.cleaned_data['date_from']
            date_to = form.cleaned_data['date_to']
            filters = {
                'action_type': form.cleaned_data.get('action_type'),
                'culture_id': form.cleaned_data.get('culture').id if form.cleaned_data.get('culture') else None,
                'orientation': form.cleaned_data.get('orientation', 'portrait'),
                'include_charts': form.cleaned_data.get('include_charts', False), # <--- ДОДАНО/ОНОВЛЕНО
            }
            
            # Отримуємо дані за період
            data = ReportService.get_shipment_report(
                date_from=date_from,
                date_to=date_to,
                filters=filters
            )
            
            # Генеруємо PDF
            pdf_buffer = ReportPDFBuilder.build_shipment_summary(
                data,
                date_from,
                date_to,
                filters
            )
            
            # Зберігаємо виконання
            self.save_report_execution(
                template=None,
                report_type='shipment_summary',
                filters={
                    'date_from': date_from.isoformat(),
                    'date_to': date_to.isoformat(),
                    **filters
                },
                data=data,
                pdf_buffer=pdf_buffer
            )
            
            # Повертаємо PDF
            filename = f"shipment_summary_{date_from.strftime('%Y%m%d')}_{date_to.strftime('%Y%m%d')}.pdf"
            return self.generate_pdf_response(pdf_buffer, filename)
        
        return render(request, self.template_name, {
            'form': form,
            'page': 'reports',
            'report_title': 'Звіт ввезення/вивезення'
        })


# ... (Усі інші класи, такі як ReportTemplateListView, залишаються без змін) ...

class ReportTemplateListView(LoginRequiredMixin, ListView):
    """Список шаблонів звітів"""
    
    model = ReportTemplate
    template_name = 'reports/pdf/template_list.html'
    context_object_name = 'templates'
    paginate_by = 20
    
    def get_queryset(self):
        return ReportTemplate.objects.filter(
            created_by=self.request.user
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page'] = 'reports'
        return context


class ReportTemplateUpdateView(LoginRequiredMixin, UpdateView):
    """Редагування шаблону звіту"""
    
    model = ReportTemplate
    form_class = ReportTemplateForm
    template_name = 'reports/pdf/template_form.html'
    success_url = reverse_lazy('report_template_list')
    
    def get_queryset(self):
        return ReportTemplate.objects.filter(created_by=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Шаблон оновлено')
        return super().form_valid(form)


class ReportTemplateDeleteView(LoginRequiredMixin, DeleteView):
    """Видалення шаблону звіту"""
    
    model = ReportTemplate
    template_name = 'confirm_delete.html'
    success_url = reverse_lazy('report_template_list')
    
    def get_queryset(self):
        return ReportTemplate.objects.filter(created_by=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.warning(request, 'Шаблон видалено')
        return super().delete(request, *args, **kwargs)


class ReportExecutionListView(LoginRequiredMixin, ListView):
    """Список виконаних звітів"""
    
    model = ReportExecution
    template_name = 'reports/pdf/execution_list.html'
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


class ReportExecutionDownloadView(LoginRequiredMixin, View):
    """Завантаження збереженого звіту"""
    
    def get(self, request, pk):
        execution = get_object_or_404(
            ReportExecution,
            pk=pk,
            executed_by=request.user
        )
        
        if not execution.file_path:
            messages.error(request, 'Файл звіту не знайдено')
            return redirect('report_execution_list')
        
        return FileResponse(
            execution.file_path.open('rb'),
            as_attachment=True,
            filename=execution.file_path.name
        )


class PDFReportsDashboardView(LoginRequiredMixin, View):
    """Головна сторінка PDF звітів"""
    
    template_name = 'reports/pdf/dashboard.html'
    
    def get(self, request):
        # Останні виконані звіти
        recent_executions = ReportExecution.objects.filter(
            executed_by=request.user
        ).select_related('template')[:5]
        
        # Шаблони користувача
        templates = ReportTemplate.objects.filter(
            created_by=request.user
        )[:5]
        
        context = {
            'page': 'reports',
            'recent_executions': recent_executions,
            'templates': templates,
        }
        
        return render(request, self.template_name, context)