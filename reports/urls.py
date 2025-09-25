from django.urls import path
from . import views

urlpatterns = [
    path("", views.reports_home, name="reports"),
    path("weigher-journal/", views.weigher_journal_report, name="weigher_journal_report"),
    path("shipment-journal/", views.shipment_journal_report, name="shipment_journal_report"),
    path("arrival-journal/", views.arrival_journal_report, name="arrival_journal_report"),
    path("daily/", views.daily_report, name="daily_report"),  

]
