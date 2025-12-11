"""
Views for PDF report generation and management.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, ListView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, FileResponse
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.files.base import ContentFile
from typing import Dict, Any, Optional, Union

from .models import ReportTemplate, ReportExecution
from .forms_pdf import (
    BalanceDateReportForm, BalancePeriodReportForm,
    IncomeDateReportForm, IncomePeriodReportForm,
    ShipmentSummaryReportForm, ReportTemplateForm,
    TotalIncomePeriodReportForm
)
from .services.services import ReportService
from .services.pdf_generator import ReportPDFBuilder
from balances.models import BalanceSnapshot


class PDFReportGeneratorMixin:
    """Mixin for generating PDF reports with common functionality."""
    
    TEMPLATE_NAME = 'reports/pdf/report_form_base.html'
    
    def generate_pdf_response(self, pdf_buffer, filename: str) -> HttpResponse:
        """Create HTTP response with PDF file."""
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    def _prepare_filters(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and prepare filters from form data."""
        filters = {
            'orientation': form_data.get('orientation', 'portrait'),
            'include_charts': form_data.get('include_charts', False),
        }
        
        # Add optional filter fields
        optional_fields = ['place', 'culture', 'field', 'place_to']
        for field in optional_fields:
            if field_value := form_data.get(field):
                filters[f'{field}_id'] = field_value.id
        
        # Add enum type fields
        if balance_type := form_data.get('balance_type'):
            filters['balance_type'] = balance_type
        
        if action_type := form_data.get('action_type'):
            filters['action_type'] = action_type
            
        return filters
    
    def save_report_execution(
        self, 
        template: Optional[ReportTemplate],
        report_type: str, 
        filters: Dict[str, Any], 
        data: Union[Dict[str, Any], list],
        pdf_buffer,
        file_format: str = 'pdf'
    ) -> ReportExecution:
        """Save report execution record."""
        # Determine row count based on data structure
        if isinstance(data, dict) and 'total_rows' in data:
            row_count = data['total_rows']
        elif isinstance(data, list):
            row_count = len(data)
        elif isinstance(data, dict) and 'comparison' in data:
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
        
        # Save file
        filename = f"report_{execution.id}.{file_format}"
        execution.file_path.save(
            filename,
            ContentFile(pdf_buffer.getvalue()),
            save=True
        )
        
        return execution
    
    def _get_context(self, form, report_title: str) -> Dict[str, Any]:
        """Get common context for report views."""
        return {
            'form': form,
            'page': 'reports',
            'report_title': report_title
        }


class BasePDFReportView(LoginRequiredMixin, PDFReportGeneratorMixin, View):
    """Base view for PDF report generation."""
    
    form_class = None
    report_title = ''
    
    def get(self, request):
        form = self.form_class()
        return render(request, self.TEMPLATE_NAME, self._get_context(form, self.report_title))
    
    def post(self, request):
        form = self.form_class(request.POST)
        
        if not form.is_valid():
            return render(request, self.TEMPLATE_NAME, self._get_context(form, self.report_title))
        
        try:
            return self._process_valid_form(form)
        except Exception as e:
            messages.error(request, f'Помилка при генерації звіту: {str(e)}')
            return render(request, self.TEMPLATE_NAME, self._get_context(form, self.report_title))
    
    def _process_valid_form(self, form):
        """Process valid form data - to be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement this method")


class BalanceDateReportView(BasePDFReportView):
    """Report of balances for a specific date."""
    
    form_class = BalanceDateReportForm
    report_title = 'Звіт залишків за дату'
    
    def _process_valid_form(self, form):
        report_date = form.cleaned_data['report_date']
        filters = self._prepare_filters(form.cleaned_data)
        
        # Get snapshot data
        snapshot = BalanceSnapshot.objects.filter(
            snapshot_date__date__lte=report_date
        ).order_by('-snapshot_date').first()
        
        if snapshot:
            data = ReportService.get_balance_snapshot_data(snapshot, filters)
        else:
            # Use current balances if no snapshot exists
            data = ReportService.get_balance_report(filters=filters)
        
        # Generate PDF
        pdf_buffer = ReportPDFBuilder.build_balance_report(
            data, 
            date=report_date,
            filters=filters
        )
        
        # Save execution
        self.save_report_execution(
            template=None,
            report_type='balance_snapshot',
            filters={'date': report_date.isoformat(), **filters},
            data=data,
            pdf_buffer=pdf_buffer
        )
        
        # Return PDF
        filename = f"balance_report_{report_date.strftime('%Y%m%d')}.pdf"
        return self.generate_pdf_response(pdf_buffer, filename)


class BalancePeriodReportView(BasePDFReportView):
    """Balance report for a period (comparison)."""
    
    form_class = BalancePeriodReportForm
    report_title = 'Звіт залишків за період'
    
    def _process_valid_form(self, form):
        date_from = form.cleaned_data['date_from']
        date_to = form.cleaned_data['date_to']
        filters = self._prepare_filters(form.cleaned_data)
        
        # Get snapshots for start and end of period
        start_snapshot = BalanceSnapshot.objects.filter(
            snapshot_date__date__lte=date_from
        ).order_by('-snapshot_date').first()
        
        end_snapshot = BalanceSnapshot.objects.filter(
            snapshot_date__date__lte=date_to
        ).order_by('-snapshot_date').first()
        
        if not start_snapshot or not end_snapshot:
            messages.error(
                self.request,
                'Недостатньо даних для побудови звіту за вказаний період'
            )
            context = self._get_context(form, self.report_title)
            return render(self.request, self.TEMPLATE_NAME, context)
        
        # Compare data
        comparison_data = ReportService.compare_balance_snapshots(
            start_snapshot, end_snapshot, filters
        )
        
        # Generate PDF
        pdf_buffer = ReportPDFBuilder.build_balance_period_report(
            comparison_data,
            date_from,
            date_to,
            filters=filters
        )
        
        # Save execution
        self.save_report_execution(
            template=None,
            report_type='balance_period',
            filters={
                'date_from': date_from.isoformat(),
                'date_to': date_to.isoformat(),
                **filters
            },
            data={'comparison': comparison_data},
            pdf_buffer=pdf_buffer
        )
        
        # Return PDF
        filename = f"balance_period_{date_from.strftime('%Y%m%d')}_{date_to.strftime('%Y%m%d')}.pdf"
        return self.generate_pdf_response(pdf_buffer, filename)


class IncomeDateReportView(BasePDFReportView):
    """Grain income report for a specific date."""
    
    form_class = IncomeDateReportForm
    report_title = 'Звіт приходу зерна за дату'
    
    def _process_valid_form(self, form):
        report_date = form.cleaned_data['report_date']
        filters = self._prepare_filters(form.cleaned_data)
        
        # Get data for the date
        data = ReportService.get_fields_report(
            date_from=report_date,
            date_to=report_date,
            filters=filters
        )
        
        # Generate PDF
        pdf_buffer = ReportPDFBuilder.build_income_report(
            data,
            report_date,
            report_date,
            filters
        )
        
        # Save execution
        self.save_report_execution(
            template=None,
            report_type='income_date',
            filters={'date': report_date.isoformat(), **filters},
            data=data,
            pdf_buffer=pdf_buffer
        )
        
        # Return PDF
        filename = f"income_report_{report_date.strftime('%Y%m%d')}.pdf"
        return self.generate_pdf_response(pdf_buffer, filename)


class IncomePeriodReportView(BasePDFReportView):
    """Grain income report for a period."""
    
    form_class = IncomePeriodReportForm
    report_title = 'Звіт приходу зерна за період'
    
    def _process_valid_form(self, form):
        date_from = form.cleaned_data['date_from']
        date_to = form.cleaned_data['date_to']
        filters = self._prepare_filters(form.cleaned_data)
        
        # Get data for the period
        data = ReportService.get_fields_report(
            date_from=date_from,
            date_to=date_to,
            filters=filters
        )
        
        # Generate PDF
        pdf_buffer = ReportPDFBuilder.build_income_report(
            data,
            date_from,
            date_to,
            filters
        )
        
        # Save execution
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
        
        # Return PDF
        filename = f"income_period_{date_from.strftime('%Y%m%d')}_{date_to.strftime('%Y%m%d')}.pdf"
        return self.generate_pdf_response(pdf_buffer, filename)


class ShipmentSummaryReportView(BasePDFReportView):
    """Import/export report for a period."""
    
    form_class = ShipmentSummaryReportForm
    report_title = 'Звіт ввезення/вивезення'
    
    def _process_valid_form(self, form):
        date_from = form.cleaned_data['date_from']
        date_to = form.cleaned_data['date_to']
        filters = self._prepare_filters(form.cleaned_data)
        
        # Get data for the period
        data = ReportService.get_shipment_report(
            date_from=date_from,
            date_to=date_to,
            filters=filters
        )
        
        # Generate PDF
        pdf_buffer = ReportPDFBuilder.build_shipment_summary(
            data,
            date_from,
            date_to,
            filters
        )
        
        # Save execution
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
        
        # Return PDF
        filename = f"shipment_summary_{date_from.strftime('%Y%m%d')}_{date_to.strftime('%Y%m%d')}.pdf"
        return self.generate_pdf_response(pdf_buffer, filename)


class TotalIncomePeriodReportView(LoginRequiredMixin, PDFReportGeneratorMixin, View):
    """Total grain income report for a period."""
    
    template_name = 'reports/pdf/report_form_base.html'
    
    def get(self, request):
        form = TotalIncomePeriodReportForm()
        context = {
            'form': form,
            'page': 'reports',
            'report_title': 'Прихід зерна (Загальний за період)'
        }
        return render(request, self.template_name, context)

    def post(self, request):
        form = TotalIncomePeriodReportForm(request.POST)
        
        if not form.is_valid():
            context = {
                'form': form,
                'page': 'reports',
                'report_title': 'Прихід зерна (Загальний за період)'
            }
            return render(request, self.template_name, context)
        
        filters = form.cleaned_data
        date_from = filters['date_from']
        date_to = filters['date_to']
        output_format = filters['output_format']
        
        # 1. Get data
        try:
            data = ReportService.get_total_income_period_data(date_from, date_to, filters)
        except Exception as e:
            messages.error(request, f"Помилка при отриманні даних: {e}")
            context = {
                'form': form,
                'page': 'reports',
                'report_title': 'Прихід зерна (Загальний за період)'
            }
            return render(request, self.template_name, context)
        
        # 2. Generate
        if output_format == 'pdf':
            pdf_buffer = ReportPDFBuilder.build_total_income_period_report(
                data, date_from, date_to, filters
            )
            filename = f"Прихід_зерна_загальний_{date_from:%d%m%Y}_{date_to:%d%m%Y}.pdf"
            
            # 3. Save execution
            self.save_report_execution(
                template=None,
                report_type='total_income_period',
                filters=filters,
                data=data,
                pdf_buffer=pdf_buffer
            )
            
            return self.generate_pdf_response(pdf_buffer, filename)
        
        messages.warning(request, f"Формат {output_format.upper()} не підтримується для цього звіту.")
        context = {
            'form': form,
            'page': 'reports',
            'report_title': 'Прихід зерна (Загальний за період)'
        }
        return render(request, self.template_name, context)


class ReportTemplateListView(LoginRequiredMixin, ListView):
    """List of report templates."""
    
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
    """Update report template."""
    
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
    """Delete report template."""
    
    model = ReportTemplate
    template_name = 'confirm_delete.html'
    success_url = reverse_lazy('report_template_list')
    
    def get_queryset(self):
        return ReportTemplate.objects.filter(created_by=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.warning(request, 'Шаблон видалено')
        return super().delete(request, *args, **kwargs)


class ReportExecutionListView(LoginRequiredMixin, ListView):
    """List of executed reports."""
    
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
    """Download saved report."""
    
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
    """Main dashboard for PDF reports."""
    
    template_name = 'reports/pdf/dashboard.html'
    
    def get(self, request):
        # Recent executions
        recent_executions = ReportExecution.objects.filter(
            executed_by=request.user
        ).select_related('template')[:5]
        
        # User templates
        templates = ReportTemplate.objects.filter(
            created_by=request.user
        )[:5]
        
        context = {
            'page': 'reports',
            'recent_executions': recent_executions,
            'templates': templates,
        }
        
        return render(request, self.template_name, context)