from django.contrib import admin
from .models import Driver, Car, Culture, Trailer, UnloadingPlace, Partner


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "company")
    search_fields = ("full_name", "phone", "company")


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ("number", "comment")
    search_fields = ("number", "comment")


@admin.register(Culture)
class CultureAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Trailer)
class TrailerAdmin(admin.ModelAdmin):
    list_display = ("number", "comment")
    search_fields = ("number", "comment")


@admin.register(UnloadingPlace)
class UnloadingPlaceAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "place_type")
    search_fields = ("name", "address", "place_type")


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email")
    search_fields = ("name", "phone", "email")