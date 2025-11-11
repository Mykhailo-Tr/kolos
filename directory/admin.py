from django.contrib import admin
from .models import Driver, Car, Culture, Trailer, Place, Field


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone")
    search_fields = ("full_name", "phone")


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ("number", "name", "default_driver")
    search_fields = ("number", "name", "default_driver__full_name")
    
@admin.register(Trailer)
class TrailerAdmin(admin.ModelAdmin):
    list_display = ("number", "comment")
    search_fields = ("number", "comment")


@admin.register(Culture)
class CultureAdmin(admin.ModelAdmin):
    list_display = ("name", "parent")
    search_fields = ("name", "parent__name")
    

@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ("name", "place_type")
    search_fields = ("name", "place_type")
    
    
@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ("name", )
    search_fields = ("name", )


