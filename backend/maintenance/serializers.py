from rest_framework import serializers
from .models import MaintenancePlan, MaintenanceHistory


class MaintenancePlanSerializer(serializers.ModelSerializer):
    maintenance_type_display = serializers.CharField(source='get_maintenance_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = MaintenancePlan
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class MaintenanceHistorySerializer(serializers.ModelSerializer):
    maintenance_type_display = serializers.CharField(source='get_maintenance_type_display', read_only=True)

    class Meta:
        model = MaintenanceHistory
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        instance = super().create(validated_data)
        # Mark linked plan as completed
        if instance.plan:
            instance.plan.status = 'completed'
            instance.plan.save(update_fields=['status'])
        return instance
