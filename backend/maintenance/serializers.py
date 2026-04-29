from django.contrib.auth import get_user_model
from rest_framework import serializers

from equipment.serializers import EquipmentListSerializer
from .models import MaintenancePlan, MaintenanceHistory, MaintenanceSchedule

User = get_user_model()


# ── План ТО ───────────────────────────────────────────────────────────────────

class _AssignedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email']


class MaintenancePlanSerializer(serializers.ModelSerializer):
    maintenance_type_display = serializers.CharField(
        source='get_maintenance_type_display', read_only=True,
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    equipment_detail = EquipmentListSerializer(source='equipment', read_only=True)
    assigned_to_detail = _AssignedUserSerializer(source='assigned_to', read_only=True)

    class Meta:
        model = MaintenancePlan
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


# ── Вспомогательный сериализатор пользователя ────────────────────────────────

class _PerformerSerializer(serializers.ModelSerializer):
    """Минимальное представление исполнителя для вложения в запись ТО."""

    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'role']


# ── Записи о выполненном ТО (MaintenanceHistory) ─────────────────────────────

class MaintenanceRecordListSerializer(serializers.ModelSerializer):
    """Облегчённый сериализатор для GET /api/maintenance-records/ (список)."""

    maintenance_type_display = serializers.CharField(
        source='get_maintenance_type_display', read_only=True,
    )
    equipment_name = serializers.CharField(source='equipment.name', read_only=True)
    equipment_inventory = serializers.CharField(
        source='equipment.inventory_number', read_only=True,
    )
    performed_by_name = serializers.CharField(
        source='performed_by.full_name', read_only=True,
    )

    class Meta:
        model = MaintenanceHistory
        fields = [
            'id', 'equipment', 'equipment_name', 'equipment_inventory',
            'maintenance_type', 'maintenance_type_display',
            'performed_at', 'performed_by', 'performed_by_name',
            'duration_hours', 'next_due_date',
        ]


class MaintenanceRecordDetailSerializer(serializers.ModelSerializer):
    """Полный сериализатор для GET /api/maintenance-records/{id}/."""

    maintenance_type_display = serializers.CharField(
        source='get_maintenance_type_display', read_only=True,
    )
    equipment_detail = EquipmentListSerializer(source='equipment', read_only=True)
    performed_by_detail = _PerformerSerializer(source='performed_by', read_only=True)

    class Meta:
        model = MaintenanceHistory
        fields = [
            'id',
            'equipment', 'equipment_detail',
            'plan',
            'maintenance_type', 'maintenance_type_display',
            'performed_at',
            'performed_by', 'performed_by_detail',
            'duration_hours', 'work_performed', 'parts_replaced',
            'next_due_date', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class MaintenanceRecordCreateSerializer(serializers.ModelSerializer):
    """
    POST /api/maintenance-records/ — зафиксировать выполненную работу.
    performed_by ставится из request.user автоматически в perform_create().
    Если указан plan — он переводится в статус 'completed'.
    """

    class Meta:
        model = MaintenanceHistory
        fields = [
            'equipment', 'plan',
            'maintenance_type', 'performed_at',
            'duration_hours', 'work_performed', 'parts_replaced',
            'next_due_date',
        ]
        extra_kwargs = {
            'plan': {'required': False},
            'duration_hours': {'required': False},
            'parts_replaced': {'required': False},
            'next_due_date': {'required': False},
        }

    def validate(self, attrs):
        plan = attrs.get('plan')
        equipment = attrs.get('equipment')
        if plan and plan.equipment_id != equipment.pk:
            raise serializers.ValidationError(
                {'plan': 'Указанный план относится к другому оборудованию.'}
            )
        return attrs

    def to_representation(self, instance):
        return MaintenanceRecordDetailSerializer(instance, context=self.context).data


# Алиас для обратной совместимости (используется в equipment/views.py history action)
MaintenanceHistorySerializer = MaintenanceRecordDetailSerializer


# ── График ТО (MaintenanceSchedule) ──────────────────────────────────────────

class MaintenanceScheduleSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    equipment_name = serializers.CharField(source='equipment.name', read_only=True)
    equipment_inventory = serializers.CharField(
        source='equipment.inventory_number', read_only=True,
    )
    maintenance_type = serializers.CharField(
        source='regulation.maintenance_type', read_only=True,
    )
    maintenance_type_display = serializers.CharField(
        source='regulation.get_maintenance_type_display', read_only=True,
    )
    interval_days = serializers.IntegerField(source='regulation.interval_days', read_only=True)
    regulation_description = serializers.CharField(
        source='regulation.description', read_only=True,
    )

    class Meta:
        model = MaintenanceSchedule
        fields = [
            'id',
            'regulation', 'regulation_description',
            'equipment', 'equipment_name', 'equipment_inventory',
            'maintenance_type', 'maintenance_type_display',
            'interval_days',
            'scheduled_date',
            'status', 'status_display',
            'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'regulation', 'equipment', 'scheduled_date',
            'created_at', 'updated_at',
        ]
