from django.urls import path
from . import views
from . import send_views

urlpatterns = [
    path("", views.reports_home, name="reports"),
    path("weigher-journal/", views.weigher_journal_report, name="weigher_journal_report"),
    path("shipment-journal/", views.shipment_journal_report, name="shipment_journal_report"),
    path("arrival-journal/", views.arrival_journal_report, name="arrival_journal_report"),
    path("daily/", views.daily_report, name="daily_report"),  
    path("stock-balance/", views.StockBalanceReportView.as_view(), name="stock_balance_report"),

    path("send/", send_views.send_report, name="reports_send"),  
]
