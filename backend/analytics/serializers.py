from rest_framework import serializers
from .models import EquipmentReliability, FailurePrediction


class EquipmentReliabilitySerializer(serializers.ModelSerializer):
    equipment_name = serializers.CharField(source='equipment.name', read_only=True)

    class Meta:
        model = EquipmentReliability
        fields = '__all__'
        read_only_fields = ['id', 'calculated_at']


class FailurePredictionSerializer(serializers.ModelSerializer):
    equipment_name = serializers.CharField(source='equipment.name', read_only=True)

    class Meta:
        model = FailurePrediction
        fields = '__all__'
        read_only_fields = ['id', 'created_at']
