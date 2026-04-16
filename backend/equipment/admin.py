from django.contrib import admin
from .models import Equipment


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'inventory_number', 'category', 'location', 'status', 'installation_date']
    list_filter = ['status', 'category']
    search_fields = ['name', 'inventory_number', 'serial_number']
    readonly_fields = ['created_at', 'updated_at']
