from django.contrib.auth import get_user_model
from rest_framework import serializers

from equipment.serializers import EquipmentListSerializer
from users.models import Role
from .models import RepairRequest, RequestStatus, VALID_STATUS_TRANSITIONS

User = get_user_model()


# ── Вспомогательные вложенные сериализаторы ──────────────────────────────────

class UserBriefSerializer(serializers.ModelSerializer):
    """Минимальное представление пользователя для вложения в заявку."""

    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'role']


# ── Сериализаторы заявок ─────────────────────────────────────────────────────

class RepairRequestListSerializer(serializers.ModelSerializer):
    """Облегчённый сериализатор для GET /api/requests/ (список)."""

    equipment_name = serializers.CharField(source='equipment.name', read_only=True)
    equipment_inventory = serializers.CharField(
        source='equipment.inventory_number', read_only=True,
    )
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    assigned_to_name = serializers.CharField(
        source='assigned_to.full_name', read_only=True, default=None,
    )
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = RepairRequest
        fields = [
            'id', 'title',
            'equipment', 'equipment_name', 'equipment_inventory',
            'priority', 'priority_display',
            'status', 'status_display',
            'created_by', 'created_by_name',
            'assigned_to', 'assigned_to_name',
            'created_at', 'updated_at',
        ]


class RepairRequestDetailSerializer(serializers.ModelSerializer):
    """Полный сериализатор для GET /api/requests/{id}/."""

    equipment_detail = EquipmentListSerializer(source='equipment', read_only=True)
    created_by_detail = UserBriefSerializer(source='created_by', read_only=True)
    assigned_to_detail = UserBriefSerializer(source='assigned_to', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = RepairRequest
        fields = [
            'id', 'title', 'description',
            'equipment', 'equipment_detail',
            'priority', 'priority_display',
            'status', 'status_display',
            'created_by', 'created_by_detail',
            'assigned_to', 'assigned_to_detail',
            'resolution_notes', 'completed_at',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'completed_at', 'created_at', 'updated_at']


class RepairRequestCreateSerializer(serializers.ModelSerializer):
    """POST /api/requests/ — создать заявку. created_by берётся из токена."""

    class Meta:
        model = RepairRequest
        fields = ['equipment', 'title', 'description', 'priority']

    def to_representation(self, instance):
        return RepairRequestDetailSerializer(instance, context=self.context).data


class RepairRequestUpdateSerializer(serializers.ModelSerializer):
    """PUT/PATCH /api/requests/{id}/ — редактирование полей (не статуса)."""

    class Meta:
        model = RepairRequest
        fields = ['title', 'description', 'priority', 'equipment']

    def to_representation(self, instance):
        return RepairRequestDetailSerializer(instance, context=self.context).data


# ── Сериализаторы для кастомных actions ──────────────────────────────────────

class AssignSerializer(serializers.Serializer):
    """PUT /api/requests/{id}/assign — назначить исполнителя."""

    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True, role=Role.MECHANIC),
        source='assigned_to',
    )

    def validate(self, attrs):
        request = self.context.get('request')
        repair_request = self.context.get('repair_request')
        if repair_request and repair_request.status not in (
            RequestStatus.NEW, RequestStatus.ASSIGNED,
        ):
            raise serializers.ValidationError(
                f'Нельзя переназначить заявку со статусом «{repair_request.get_status_display()}».'
            )
        return attrs


class StatusTransitionSerializer(serializers.Serializer):
    """PUT /api/requests/{id}/status — сменить статус по разрешённому переходу."""

    status = serializers.ChoiceField(choices=RequestStatus.choices)
    resolution_notes = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_status(self, new_status):
        if new_status == RequestStatus.ASSIGNED:
            raise serializers.ValidationError(
                'Переход в статус «Назначена» выполняется через /assign.'
            )
        return new_status

    def validate(self, attrs):
        repair_request = self.context['repair_request']
        current = repair_request.status
        new = attrs['status']
        allowed = VALID_STATUS_TRANSITIONS.get(current, set())
        if new not in allowed:
            allowed_display = [
                RequestStatus(s).label for s in allowed
            ] if allowed else ['нет допустимых переходов']
            raise serializers.ValidationError({
                'status': (
                    f'Переход «{repair_request.get_status_display()}» → «{RequestStatus(new).label}» '
                    f'не разрешён. Допустимо: {", ".join(allowed_display)}.'
                )
            })
        return attrs
