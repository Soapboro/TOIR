from django.contrib import admin
from .models import RepairRequest


@admin.register(RepairRequest)
class RepairRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'equipment', 'priority', 'status', 'assigned_to', 'created_at']
    list_filter = ['status', 'priority']
    search_fields = ['title', 'description', 'equipment__name']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    autocomplete_fields = ['equipment', 'assigned_to']
