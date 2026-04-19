from django.contrib import admin

from .models import RepairRequest


@admin.register(RepairRequest)
class RepairRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'equipment', 'status', 'priority', 'assigned_to', 'created_by', 'created_at']
    list_filter = ['status', 'priority', 'created_at']
    search_fields = ['title', 'description', 'equipment__name', 'assigned_to__full_name']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    autocomplete_fields = ['equipment', 'assigned_to', 'created_by']
    date_hierarchy = 'created_at'
