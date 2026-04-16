from django.contrib import admin
from .models import MaintenancePlan, MaintenanceHistory


@admin.register(MaintenancePlan)
class MaintenancePlanAdmin(admin.ModelAdmin):
    list_display = ['equipment', 'maintenance_type', 'scheduled_date', 'status', 'assigned_to']
    list_filter = ['status', 'maintenance_type']
    search_fields = ['equipment__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(MaintenanceHistory)
class MaintenanceHistoryAdmin(admin.ModelAdmin):
    list_display = ['equipment', 'maintenance_type', 'performed_at', 'performed_by', 'next_due_date']
    list_filter = ['maintenance_type']
    search_fields = ['equipment__name', 'work_performed']
    readonly_fields = ['created_at']
