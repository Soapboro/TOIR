from rest_framework import serializers

from equipment.serializers import EquipmentListSerializer
from users.serializers import UserSerializer
from .models import RepairRequest


class RepairRequestSerializer(serializers.ModelSerializer):
    equipment_detail = EquipmentListSerializer(source='equipment', read_only=True)
    created_by_detail = UserSerializer(source='created_by', read_only=True)
    assigned_to_detail = UserSerializer(source='assigned_to', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = RepairRequest
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', 'completed_at']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
