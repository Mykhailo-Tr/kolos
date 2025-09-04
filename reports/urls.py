from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("", views.ReportsIndexView.as_view(), name="report_list"),
    path("culture/", views.CultureReportView.as_view(), name="culture_report"),
    path("warehouses/", views.WarehouseReportView.as_view(), name="warehouse_report"),
    path("drivers/", views.DriverReportView.as_view(), name="driver_report"),
    path("balance/", views.BalanceReportView.as_view(), name="balance_report"),
]
