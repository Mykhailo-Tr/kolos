from django.urls import path
from .views import w_autocomplete_views as w_a_views
from .views import weigher_views

urlpatterns = [
    path("entrys/", weigher_views.weigher_journal_list, name="weigher_journal_list"),
    path("entrys/add/", weigher_views.weigher_journal_create, name="weigher_journal_add"),
    path("entrys/<int:pk>/edit/", weigher_views.weigher_journal_update, name="weigher_journal_update"),
    path("entrys/<int:pk>/delete/", weigher_views.weigher_journal_delete, name="weigher_journal_delete"),
    
    # Autocomplete URLs
    path('autocomplete/sender/', w_a_views.SenderAutocomplete.as_view(), name='sender-autocomplete'),
    path('autocomplete/receiver/', w_a_views.ReceiverAutocomplete.as_view(), name='receiver-autocomplete'),
    path('autocomplete/car/', w_a_views.CarAutocomplete.as_view(), name='car-autocomplete'),
    path('autocomplete/driver/', w_a_views.DriverAutocomplete.as_view(), name='driver-autocomplete'),
    path('autocomplete/trailer/', w_a_views.TrailerAutocomplete.as_view(), name='trailer-autocomplete'),
    path('autocomplete/culture/', w_a_views.CultureAutocomplete.as_view(), name='culture-autocomplete'),
    path('autocomplete/unloading/', w_a_views.UnloadingPlaceAutocomplete.as_view(), name='unloading-autocomplete'),
]
