from django.contrib import admin
from .models import StockLog, InventoryAlert


@admin.register(StockLog)
class StockLogAdmin(admin.ModelAdmin):
    list_display = ('product', 'change_type', 'quantity', 'reason', 'created_at')
    list_filter = ('change_type',)


@admin.register(InventoryAlert)
class InventoryAlertAdmin(admin.ModelAdmin):
    list_display = ('product', 'threshold', 'is_resolved', 'created_at')
    list_filter = ('is_resolved',)