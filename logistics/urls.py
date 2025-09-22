from django.urls import path
from . import autocomplete_views as a_views
from . import views

urlpatterns = [
    path("entrys/", views.weigher_journal_list, name="weigher_journal_list"),
    path("entrys/add/", views.weigher_journal_create, name="weigher_journal_add"),
    path("entrys/<int:pk>/edit/", views.weigher_journal_update, name="weigher_journal_update"),
    path("entrys/<int:pk>/delete/", views.weigher_journal_delete, name="weigher_journal_delete"),
    
    # Autocomplete URLs
    path('autocomplete/sender/', a_views.SenderAutocomplete.as_view(), name='sender-autocomplete'),
    path('autocomplete/receiver/', a_views.ReceiverAutocomplete.as_view(), name='receiver-autocomplete'),
    path('autocomplete/car/', a_views.CarAutocomplete.as_view(), name='car-autocomplete'),
    path('autocomplete/driver/', a_views.DriverAutocomplete.as_view(), name='driver-autocomplete'),
    path('autocomplete/trailer/', a_views.TrailerAutocomplete.as_view(), name='trailer-autocomplete'),
    path('autocomplete/culture/', a_views.CultureAutocomplete.as_view(), name='culture-autocomplete'),
    path('autocomplete/unloading/', a_views.UnloadingPlaceAutocomplete.as_view(), name='unloading-autocomplete'),
]
