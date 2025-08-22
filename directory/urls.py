from django.urls import path
from .views import cultures_views, drivers_views

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
]
