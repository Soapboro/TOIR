from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from .models import MaintenanceHistory, MaintenancePlan, MaintenanceSchedule, PlanStatus


@admin.register(MaintenancePlan)
class MaintenancePlanAdmin(admin.ModelAdmin):
    list_display = ['equipment', 'maintenance_type', 'scheduled_date', 'status', 'assigned_to']
    list_filter = ['status', 'maintenance_type']
    search_fields = ['equipment__name']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['equipment', 'assigned_to', 'regulation']
    date_hierarchy = 'scheduled_date'


@admin.register(MaintenanceHistory)
class MaintenanceHistoryAdmin(admin.ModelAdmin):
    list_display = ['equipment', 'maintenance_type', 'performed_at', 'performed_by', 'next_due_date']
    list_filter = ['maintenance_type']
    search_fields = ['equipment__name', 'work_performed']
    readonly_fields = ['created_at']
    autocomplete_fields = ['equipment', 'performed_by']
    date_hierarchy = 'performed_at'


@admin.register(MaintenanceSchedule)
class MaintenanceScheduleAdmin(admin.ModelAdmin):
    list_display = ['equipment', 'regulation_type', 'scheduled_date_colored', 'status']
    list_filter = ['status', 'regulation__maintenance_type']
    search_fields = ['equipment__name']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['equipment', 'regulation']
    date_hierarchy = 'scheduled_date'

    @admin.display(description='Вид ТО')
    def regulation_type(self, obj):
        return obj.regulation.get_maintenance_type_display()

    @admin.display(description='Плановая дата', ordering='scheduled_date')
    def scheduled_date_colored(self, obj):
        today = timezone.now().date()
        is_overdue = (
            obj.scheduled_date < today
            and obj.status not in (PlanStatus.COMPLETED, PlanStatus.CANCELLED)
        )
        if is_overdue:
            return format_html(
                '<span style="color:#e74c3c; font-weight:bold;">⚠ {}</span>',
                obj.scheduled_date,
            )
        return obj.scheduled_date
