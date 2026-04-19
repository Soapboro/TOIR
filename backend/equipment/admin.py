from django.contrib import admin

from .models import Equipment, MaintenanceRegulation


class MaintenanceRegulationInline(admin.TabularInline):
    model = MaintenanceRegulation
    extra = 0
    fields = ['maintenance_type', 'interval_days', 'description']


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'model', 'status', 'location', 'category', 'inventory_number']
    list_filter = ['status', 'category', 'manufacturer']
    search_fields = ['name', 'inventory_number', 'serial_number', 'manufacturer', 'model', 'location']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [MaintenanceRegulationInline]
    date_hierarchy = 'installation_date'


@admin.register(MaintenanceRegulation)
class MaintenanceRegulationAdmin(admin.ModelAdmin):
    list_display = ['equipment', 'maintenance_type', 'interval_days']
    list_filter = ['maintenance_type']
    search_fields = ['equipment__name', 'description']
    autocomplete_fields = ['equipment']
