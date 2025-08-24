from django.urls import path
from . import views

urlpatterns = [
    path("trips/", views.trip_list, name="trip_list"),
    path("trips/add/", views.trip_create, name="trip_add"),
    path("trips/<int:pk>/edit/", views.trip_update, name="trip_edit"),
    path("trips/<int:pk>/delete/", views.trip_delete, name="trip_delete"),
]
