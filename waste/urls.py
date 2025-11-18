from django.urls import path
from .views import (
    WasteJournalListView,
    UtilizationCreateView, UtilizationUpdateView, UtilizationDeleteView,
    RecyclingCreateView, RecyclingUpdateView, RecyclingDeleteView,
)


urlpatterns = [
    # Waste Journal URLs
    path('', WasteJournalListView.as_view(), name='waste_list'),
    
    # --- УТИЛІЗАЦІЯ ---
    path("utilization/add/<int:balance_id>/", UtilizationCreateView.as_view(), name="utilization_add"),
    path("utilization/<int:pk>/edit/", UtilizationUpdateView.as_view(), name="utilization_edit"),
    path("utilization/<int:pk>/delete/", UtilizationDeleteView.as_view(), name="utilization_delete"),

    # --- ПЕРЕРОБКА ---
    path("recycling/add/<int:balance_id>/", RecyclingCreateView.as_view(), name="recycling_add"),
    path("recycling/<int:pk>/edit/", RecyclingUpdateView.as_view(), name="recycling_edit"),
    path("recycling/<int:pk>/delete/", RecyclingDeleteView.as_view(), name="recycling_delete"),
]