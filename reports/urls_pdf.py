"""
URL маршрути для PDF звітів
Додайте ці URL до reports/urls.py
"""
from django.urls import path
from .views_pdf import (
    PDFReportsDashboardView,
    BalanceDateReportView, BalancePeriodReportView,
    IncomeDateReportView, IncomePeriodReportView,
    ShipmentSummaryReportView,
    ReportTemplateListView, ReportTemplateUpdateView, ReportTemplateDeleteView,
    ReportExecutionListView, ReportExecutionDownloadView, TotalIncomePeriodReportView, # <-- ІМПОРТ НОВОГО ПРЕДСТАВЛЕННЯ
)

# Додайте ці URL до існуючого списку urlpatterns
pdf_urlpatterns = [
    # Dashboard
    path('pdf/', PDFReportsDashboardView.as_view(), name='pdf_reports_dashboard'),
    
    # Генерація звітів
    path('pdf/balance-date/', BalanceDateReportView.as_view(), name='pdf_balance_date'),
    path('pdf/balance-period/', BalancePeriodReportView.as_view(), name='pdf_balance_period'),
    path('pdf/income-date/', IncomeDateReportView.as_view(), name='pdf_income_date'),
    path('pdf/income-period/', IncomePeriodReportView.as_view(), name='pdf_income_period'),
    path('pdf/shipment-summary/', ShipmentSummaryReportView.as_view(), name='pdf_shipment_summary'),
    path('pdf/total-income-period/', TotalIncomePeriodReportView.as_view(), name='pdf_total_income_period'), # <-- НОВИЙ МАРШРУТ
    
    # Шаблони
    path('templates/', ReportTemplateListView.as_view(), name='report_template_list'),
    path('templates/<int:pk>/edit/', ReportTemplateUpdateView.as_view(), name='report_template_update'),
    path('templates/<int:pk>/delete/', ReportTemplateDeleteView.as_view(), name='report_template_delete'),
    
    # Виконання звітів
    path('executions/', ReportExecutionListView.as_view(), name='report_execution_list'),
    path('executions/<int:pk>/download/', ReportExecutionDownloadView.as_view(), name='report_execution_download'),
]