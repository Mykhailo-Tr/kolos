from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("weigher-journal/", views.weigher_journal_report, name="weigher_journal_report"),
    path("shipment-journal/", views.shipment_journal_report, name="shipment_journal_report"),
]
