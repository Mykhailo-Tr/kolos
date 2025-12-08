from django.urls import path
from . import views

urlpatterns = [
    # Головна сторінка звітів
    path('', views.ReportsDashboardView.as_view(), name='reports_dashboard'),
    
    # Конкретні звіти
    path('balance/', views.BalanceReportView.as_view(), name='report_balance'),
    path('waste/', views.WasteReportView.as_view(), name='report_waste'),
    path('weigher/', views.WeigherReportView.as_view(), name='report_weigher'),
    path('shipment/', views.ShipmentReportView.as_view(), name='report_shipment'),
    path('fields/', views.FieldsReportView.as_view(), name='report_fields'),
    
    # Денний звіт
    path('daily/', views.DailyReportView.as_view(), name='report_daily'),
    
    # Експорт
    path('export/', views.ExportReportView.as_view(), name='export_report'),
    
    # Конструктор звітів
    path('builder/', views.CustomReportBuilderView.as_view(), name='custom_report_builder'),
    
    # Збережені звіти
    path('saved/', views.SavedReportsListView.as_view(), name='saved_reports'),
    
    # Історія
    path('history/', views.ReportHistoryView.as_view(), name='report_history'),
]