from django.contrib import admin
from .models import Balance, BalanceSnapshot, BalanceHistory


@admin.register(Balance)
class BalanceAdmin(admin.ModelAdmin):
    list_display = ('place', 'culture', 'balance_type', 'quantity')
    search_fields = ('place__name', 'culture__name')
    list_filter = ('balance_type', 'place', 'culture')
    ordering = ('place__name', 'culture__name')


@admin.register(BalanceSnapshot)
class BalanceSnapshotAdmin(admin.ModelAdmin):
    list_display = ('snapshot_date', 'created_by', 'description', 'total_records')
    readonly_fields = ('total_records', 'total_quantity')


@admin.register(BalanceHistory)
class BalanceHistoryAdmin(admin.ModelAdmin):
    list_display = ('snapshot', 'place', 'culture', 'balance_type', 'quantity')
    list_filter = ('balance_type',)
    search_fields = ('place__name', 'culture__name')