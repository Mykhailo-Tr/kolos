from django.contrib import admin
from .models import Balance, BalanceType, BalanceHistory

@admin.register(Balance)
class BalanceAdmin(admin.ModelAdmin):
    list_display = ('place', 'culture', 'balance_type', 'quantity')
    list_filter = ('place', 'culture', 'balance_type', )
    search_fields = ('place__name', 'culture__name')
    ordering = ('place', 'culture', 'balance_type',)
    
    
# @admin.register(BalanceHistory)
# class BalanceHistoryAdmin(admin.ModelAdmin):
#     list_display = ('snapshot_date', 'place_name', 'culture_name', 'balance_type', 'quantity')
#     list_filter = ('snapshot_date', 'place_name', 'culture_name', 'balance_type', )
#     search_fields = ('place_name', 'culture_name')
#     ordering = ('-snapshot_date',)

    
