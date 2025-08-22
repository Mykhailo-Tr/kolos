from django.contrib import admin
from .models import Driver, Car, Culture


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
