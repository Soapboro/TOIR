from django.contrib import admin
from .models import EquipmentReliability, FailurePrediction


@admin.register(EquipmentReliability)
class EquipmentReliabilityAdmin(admin.ModelAdmin):
    list_display = ['equipment', 'failure_count', 'mtbf_hours', 'mttr_hours', 'availability_percent', 'calculated_at']
    readonly_fields = ['calculated_at']


@admin.register(FailurePrediction)
class FailurePredictionAdmin(admin.ModelAdmin):
    list_display = ['equipment', 'predicted_failure_date', 'confidence_percent', 'is_acknowledged', 'created_at']
    list_filter = ['is_acknowledged']
