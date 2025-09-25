from django.contrib import admin
from .models import WeigherJournal, ArrivalJournal, ShipmentJournal, StockBalance

@admin.register(WeigherJournal)
class WeigherJournalAdmin(admin.ModelAdmin):
    list_display = ("document_number", "date_time", "sender", "receiver", "car", "driver", "culture", "weight_gross", "weight_tare", "weight_net", "unloading_place")
    list_filter = ("date_time", "sender", "receiver", "car", "driver", "culture", "unloading_place")
    search_fields = ("document_number", "sender__name", "receiver__name", "car__number", "driver__full_name", "culture__name", "unloading_place__name")
    readonly_fields = ("weight_net",)
    ordering = ("-date_time",)
    
@admin.register(ArrivalJournal)
class ArrivalJournalAdmin(admin.ModelAdmin):
    list_display = ("document_number", "date_time", "sender_or_receiver", "car", "driver", "culture", "weight_gross", "weight_tare", "weight_net", "unloading_place")
    list_filter = ("date_time", "sender_or_receiver", "car", "driver", "culture", "unloading_place")
    search_fields = ("document_number", "sender_or_receiver__name", "car__number", "driver__full_name", "culture__name", "unloading_place__name")
    readonly_fields = ("weight_net",)
    ordering = ("-date_time",)

@admin.register(ShipmentJournal)
class ShipmentJournalAdmin(admin.ModelAdmin):
    list_display = ("document_number", "date_time", "sender", "car", "driver", "culture", "weight_gross", "weight_tare", "weight_net", "unloading_place")
    list_filter = ("date_time", "sender", "car", "driver", "culture", "unloading_place")
    search_fields = ("document_number", "sender_or_receiver__name", "car__number", "driver__full_name", "culture__name", "unloading_place__name")
    readonly_fields = ("weight_net",)
    ordering = ("-date_time",)
    

@admin.register(StockBalance)
class StockBalanceAdmin(admin.ModelAdmin):
    list_display = ("unloading_place", "culture", "quantity")
    list_filter = ("unloading_place", "culture")
    search_fields = ("unloading_place__name", "culture__name")
    ordering = ("unloading_place", "culture")
    readonly_fields = ("quantity",)
    
