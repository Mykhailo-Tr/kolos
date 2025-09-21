from django.urls import path
from . import autocomplete_views as a_views
from . import views

urlpatterns = [
    path("trips/", views.trip_list, name="trip_list"),
    path("trips/add/", views.trip_create, name="trip_add"),
    path("trips/<int:pk>/edit/", views.trip_update, name="trip_edit"),
    path("trips/<int:pk>/delete/", views.trip_delete, name="trip_delete"),
    
    # Autocomplete URLs
    path('autocomplete/sender/', a_views.SenderAutocomplete.as_view(), name='sender-autocomplete'),
    path('autocomplete/receiver/', a_views.ReceiverAutocomplete.as_view(), name='receiver-autocomplete'),
    path('autocomplete/car/', a_views.CarAutocomplete.as_view(), name='car-autocomplete'),
    path('autocomplete/driver/', a_views.DriverAutocomplete.as_view(), name='driver-autocomplete'),
    path('autocomplete/trailer/', a_views.TrailerAutocomplete.as_view(), name='trailer-autocomplete'),
    path('autocomplete/culture/', a_views.CultureAutocomplete.as_view(), name='culture-autocomplete'),
    path('autocomplete/unloading/', a_views.UnloadingPlaceAutocomplete.as_view(), name='unloading-autocomplete'),
]
