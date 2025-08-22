from django.urls import path
from . import views

urlpatterns = [
    path("cultures/", views.culture_list, name="culture_list"),
    path("cultures/add/", views.culture_create, name="culture_add"),
    path("cultures/<int:pk>/edit/", views.culture_update, name="culture_edit"),
    path("cultures/<int:pk>/delete/", views.culture_delete, name="culture_delete"),
]
