from rest_framework import serializers

from maintenance.models import MaintenanceHistory
from .models import Equipment, MaintenanceRegulation


# ── Вспомогательные вложенные сериализаторы ──────────────────────────────────

class MaintenanceRegulationSerializer(serializers.ModelSerializer):
    maintenance_type_display = serializers.CharField(
        source='get_maintenance_type_display', read_only=True,
    )
    equipment_name = serializers.CharField(source='equipment.name', read_only=True)
    equipment_inventory = serializers.CharField(source='equipment.inventory_number', read_only=True)
    # equipment только для чтения — при создании берётся из URL /{equipment_id}/
    equipment = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = MaintenanceRegulation
        fields = [
            'id', 'equipment', 'equipment_name', 'equipment_inventory',
            'maintenance_type', 'maintenance_type_display',
            'interval_days', 'description',
        ]


class MaintenanceHistoryInlineSerializer(serializers.ModelSerializer):
    """Облегчённая история ТО для вложения в карточку оборудования."""

    maintenance_type_display = serializers.CharField(
        source='get_maintenance_type_display', read_only=True,
    )
    performed_by_name = serializers.CharField(
        source='performed_by.full_name', read_only=True,
    )

    class Meta:
        model = MaintenanceHistory
        fields = [
            'id', 'maintenance_type', 'maintenance_type_display',
            'performed_at', 'performed_by', 'performed_by_name',
            'duration_hours', 'work_performed', 'parts_replaced', 'next_due_date',
        ]


# ── Основные сериализаторы оборудования ──────────────────────────────────────

class EquipmentListSerializer(serializers.ModelSerializer):
    """Облегчённый сериализатор для GET /api/equipment/ (список)."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Equipment
        fields = [
            'id', 'name', 'inventory_number', 'category',
            'location', 'status', 'status_display',
            'installation_date', 'updated_at',
        ]


class EquipmentDetailSerializer(serializers.ModelSerializer):
    """
    Полный сериализатор для GET /api/equipment/{id}/.
    Включает регламенты ТО и последние 10 записей истории.
    """

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    regulations = MaintenanceRegulationSerializer(many=True, read_only=True)
    recent_history = serializers.SerializerMethodField()

    class Meta:
        model = Equipment
        fields = [
            'id', 'name', 'inventory_number', 'serial_number',
            'manufacturer', 'model', 'category', 'location',
            'installation_date', 'warranty_expiry_date',
            'status', 'status_display',
            'specifications', 'passport_file', 'notes',
            'regulations', 'recent_history',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_recent_history(self, obj):
        qs = (
            obj.maintenance_history
            .select_related('performed_by')
            .order_by('-performed_at')[:10]
        )
        return MaintenanceHistoryInlineSerializer(qs, many=True).data


class EquipmentWriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для POST / PUT / PATCH.
    После сохранения возвращает полный EquipmentDetailSerializer.
    """

    class Meta:
        model = Equipment
        fields = [
            'name', 'inventory_number', 'serial_number',
            'manufacturer', 'model', 'category', 'location',
            'installation_date', 'warranty_expiry_date',
            'status', 'specifications', 'passport_file', 'notes',
        ]

    def to_representation(self, instance):
        return EquipmentDetailSerializer(instance, context=self.context).data
