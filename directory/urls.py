from django.urls import path
from .views import cultures_views, drivers_views, cars_views, trailers_views

urlpatterns = [
    # ========== Cultures URLs ==========
    path("cultures/", cultures_views.culture_list, name="culture_list"),
    path("cultures/add/", cultures_views.culture_create, name="culture_add"),
    path("cultures/<int:pk>/edit/", cultures_views.culture_update, name="culture_edit"),
    path("cultures/<int:pk>/delete/", cultures_views.culture_delete, name="culture_delete"),
    
    # ========== Drivers URLs ==========
    path("drivers/", drivers_views.driver_list, name="driver_list"),
    path("drivers/add/", drivers_views.driver_create, name="driver_add"),
    path("drivers/<int:pk>/edit/", drivers_views.driver_update, name="driver_edit"),
    path("drivers/<int:pk>/delete/", drivers_views.driver_delete, name="driver_delete"),

    # ========== Cars URLs ==========
    path("cars/", cars_views.car_list, name="car_list"),
    path("cars/add/", cars_views.car_create, name="car_add"),
    path("cars/<int:pk>/edit/", cars_views.car_update, name="car_edit"),
    path("cars/<int:pk>/delete/", cars_views.car_delete, name="car_delete"),
    
    # ========== Trailers URLs ==========
    path("trailers/", trailers_views.trailer_list, name="trailer_list"),
    path("trailers/add/", trailers_views.trailer_create, name="trailer_add"),
    path("trailers/<int:pk>/edit/", trailers_views.trailer_update, name="trailer_edit"),
    path("trailers/<int:pk>/delete/", trailers_views.trailer_delete, name="trailer_delete"),
]
