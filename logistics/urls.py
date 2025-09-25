from django.urls import path
from .views import autocomplete_views as a_views
from .views import weigher_views, arrival_views, shipment_views
from .views import weight_views

urlpatterns = [
    # Weight Reader URL
    path("api/current-weight/", weight_views.get_current_weight, name="api_current_weight"),
    
    # Weigher Journal URLs
    path("weigher-journal/", weigher_views.weigher_journal_list, name="weigher_journal_list"),
    path("weigher-journal/add/", weigher_views.weigher_journal_create, name="weigher_journal_add"),
    path("weigher-journal/<int:pk>/edit/", weigher_views.weigher_journal_update, name="weigher_journal_update"),
    path("weigher-journal/<int:pk>/delete/", weigher_views.weigher_journal_delete, name="weigher_journal_delete"),
    
    # Arrival Journal URLs
    path("arrival-journal/", arrival_views.arrival_journal_list, name="arrival_journal_list"),
    path("arrival-journal/add/", arrival_views.arrival_journal_create, name="arrival_journal_add"),
    path("arrival-journal/<int:pk>/edit/", arrival_views.arrival_journal_update, name="arrival_journal_update"),
    path("arrival-journal/<int:pk>/delete/", arrival_views.arrival_journal_delete, name="arrival_journal_delete"),
    
    # Shipment Journal URLs
    path("shipment-journal/", shipment_views.shipment_journal_list, name="shipment_journal_list"),
    path("shipment-journal/add/", shipment_views.shipment_journal_create, name="shipment_journal_add"),
    path("shipment-journal/<int:pk>/edit/", shipment_views.shipment_journal_update, name="shipment_journal_update"),
    path("shipment-journal/<int:pk>/delete/", shipment_views.shipment_journal_delete, name="shipment_journal_delete"),
    
    # Autocomplete URLs
    path('autocomplete/sender/', a_views.SenderAutocomplete.as_view(), name='sender-autocomplete'),
    path('autocomplete/receiver/', a_views.ReceiverAutocomplete.as_view(), name='receiver-autocomplete'),
    path('autocomplete/partner/', a_views.PartnerAutocomplete.as_view(), name='partner-autocomplete'), 
    path('autocomplete/car/', a_views.CarAutocomplete.as_view(), name='car-autocomplete'),
    path('autocomplete/driver/', a_views.DriverAutocomplete.as_view(), name='driver-autocomplete'),
    path('autocomplete/trailer/', a_views.TrailerAutocomplete.as_view(), name='trailer-autocomplete'),
    path('autocomplete/culture/', a_views.CultureAutocomplete.as_view(), name='culture-autocomplete'),
    path('autocomplete/unloading/', a_views.UnloadingPlaceAutocomplete.as_view(), name='unloading-autocomplete'),
]
