from django.urls import path
from . import views

urlpatterns = [
    # Waste Journal URLs
    path('', views.WasteJournalListView.as_view(), name='wastejournal_list'),
    path('create/', views.WasteJournalCreateView.as_view(), name='waste_journal_create'),
    path('<int:pk>/edit/', views.WasteJournalUpdateView.as_view(), name='waste_journal_update'),
    path('<int:pk>/delete/', views.WasteJournalDeleteView.as_view(), name='waste_journal_delete'),
]