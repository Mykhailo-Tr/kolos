from django.urls import path
from . import views

urlpatterns = [
    # Weigher Journal URLs
    path('weigher_journals/', views.WeigherJournalListView.as_view(), name='weigherjournal_list'),
    path('weigher_journals/create/', views.WeigherJournalCreateView.as_view(), name='weigher_journal_create'),
    path('weigher_journals/<int:pk>/edit/', views.WeigherJournalUpdateView.as_view(), name='weigher_journal_update'),
    path('weigher_journals/<int:pk>/delete/', views.WeigherJournalDeleteView.as_view(), name='weigher_journal_delete'),
    
    # Shipment Journal URLs
    path('shipment_journals/', views.ShipmentJournalListView.as_view(), name='shipmentjournal_list'),
    path('shipment_journals/create/', views.ShipmentJournalCreateView.as_view(), name='shipment_journal_create'),
    path('shipment_journals/<int:pk>/edit/', views.ShipmentJournalUpdateView.as_view(), name='shipment_journal_update'),
    path('shipment_journals/<int:pk>/delete/', views.ShipmentJournalDeleteView.as_view(), name='shipment_journal_delete'),
    
    # Fields Income URLs
    path('fields_income/', views.FieldsIncomeListView.as_view(), name='fieldsincome_list'),
    path('fields_income/create/', views.FieldsIncomeCreateView.as_view(), name='fields_income_create'),
    path('fields_income/<int:pk>/edit/', views.FieldsIncomeUpdateView.as_view(), name='fields_income_update'),
    path('fields_income/<int:pk>/delete/', views.FieldsIncomeDeleteView.as_view(), name='fields_income_delete'),
    
    # Other Income URLs
    path('other_income/', views.OtherIncomeListView.as_view(), name='otherincome_list'),
    path('other_income/create/', views.OtherIncomeCreateView.as_view(), name='other_income_create'),
    path('other_income/<int:pk>/edit/', views.OtherIncomeUpdateView.as_view(), name='other_income_update'),
    path('other_income/<int:pk>/delete/', views.OtherIncomeDeleteView.as_view(), name='other_income_delete'),
]
