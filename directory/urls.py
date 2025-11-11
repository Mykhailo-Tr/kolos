from django.urls import path
from .views import driver, car, trailer, culture, place, field

urlpatterns = [
    # Driver
    path("drivers/", driver.DriverListView.as_view(), name="driver_list"),
    path("drivers/add/", driver.DriverCreateView.as_view(), name="driver_create"),
    path("drivers/<int:pk>/edit/", driver.DriverUpdateView.as_view(), name="driver_update"),
    path("drivers/<int:pk>/delete/", driver.DriverDeleteView.as_view(), name="driver_delete"),

    # Car
    path("cars/", car.CarListView.as_view(), name="car_list"),
    path("cars/add/", car.CarCreateView.as_view(), name="car_create"),
    path("cars/<int:pk>/edit/", car.CarUpdateView.as_view(), name="car_update"),
    path("cars/<int:pk>/delete/", car.CarDeleteView.as_view(), name="car_delete"),

    # Trailer
    path("trailers/", trailer.TrailerListView.as_view(), name="trailer_list"),
    path("trailers/add/", trailer.TrailerCreateView.as_view(), name="trailer_create"),
    path("trailers/<int:pk>/edit/", trailer.TrailerUpdateView.as_view(), name="trailer_update"),
    path("trailers/<int:pk>/delete/", trailer.TrailerDeleteView.as_view(), name="trailer_delete"),

    # Culture
    path("cultures/", culture.CultureListView.as_view(), name="culture_list"),
    path("cultures/add/", culture.CultureCreateView.as_view(), name="culture_create"),
    path("cultures/<int:pk>/edit/", culture.CultureUpdateView.as_view(), name="culture_update"),
    path("cultures/<int:pk>/delete/", culture.CultureDeleteView.as_view(), name="culture_delete"),

    # Place
    path("places/", place.PlaceListView.as_view(), name="place_list"),
    path("places/add/", place.PlaceCreateView.as_view(), name="place_create"),
    path("places/<int:pk>/edit/", place.PlaceUpdateView.as_view(), name="place_update"),
    path("places/<int:pk>/delete/", place.PlaceDeleteView.as_view(), name="place_delete"),

    # Field
    path("fields/", field.FieldListView.as_view(), name="field_list"),
    path("fields/add/", field.FieldCreateView.as_view(), name="field_create"),
    path("fields/<int:pk>/edit/", field.FieldUpdateView.as_view(), name="field_update"),
    path("fields/<int:pk>/delete/", field.FieldDeleteView.as_view(), name="field_delete"),
]
