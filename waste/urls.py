from django.urls import path
from . import views

urlpatterns = [
    # Waste Journal URLs
    path('', views.WasteJournalListView.as_view(), name='waste_list'),
    
    # --- УТИЛІЗАЦІЯ ---
    path("utilization/add/<int:balance_id>/", views.UtilizationCreateView.as_view(), name="utilization_add"),
    path("utilization/<int:pk>/edit/", views.UtilizationUpdateView.as_view(), name="utilization_edit"),
    path("utilization/<int:pk>/delete/", views.UtilizationDeleteView.as_view(), name="utilization_delete"),

    # --- ПЕРЕРОБКА ---
    path("recycling/add/<int:balance_id>/", views.RecyclingCreateView.as_view(), name="recycling_add"),
    path("recycling/<int:pk>/edit/", views.RecyclingUpdateView.as_view(), name="recycling_edit"),
    path("recycling/<int:pk>/delete/", views.RecyclingDeleteView.as_view(), name="recycling_delete"),
]