from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("trips/", views.trip_report, name="trip_report"),
]
