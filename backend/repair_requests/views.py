from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.models import Role
from users.permissions import IsAdminOrManager
from .filters import RepairRequestFilter
from .models import RepairRequest, RequestStatus
from .serializers import (
    AssignSerializer,
    RepairRequestCreateSerializer,
    RepairRequestDetailSerializer,
    RepairRequestListSerializer,
    RepairRequestUpdateSerializer,
    StatusTransitionSerializer,
)

SELF_ASSIGN_DELAY = timedelta(hours=2)


class RepairRequestViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    GET    /api/requests/              — список с фильтрами
    GET    /api/requests/{id}/         — детальная карточка
    POST   /api/requests/              — создать (любой аутентифицированный)
    PUT    /api/requests/{id}/         — редактировать поля заявки
    PATCH  /api/requests/{id}/         — частично редактировать
    DELETE /api/requests/{id}/         — удалить (admin/manager)
    PUT    /api/requests/{id}/assign/  — назначить исполнителя (admin/manager)
    PUT    /api/requests/{id}/status/  — сменить статус
    """

    filterset_class = RepairRequestFilter
    search_fields = [
        'title', 'description',
        'equipment__name', 'equipment__inventory_number',
    ]
    ordering_fields = ['created_at', 'updated_at', 'priority', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        self_assign_cutoff = timezone.now() - SELF_ASSIGN_DELAY
        qs = (
            RepairRequest.objects
            .select_related('equipment', 'created_by', 'assigned_to')
            .order_by('-created_at')
        )
        user = self.request.user
        if not user.is_authenticated:
            return qs.none()
        if user.role in (Role.ADMIN, Role.MANAGER):
            return qs
        if user.role == Role.MECHANIC:
            return qs.filter(
                Q(assigned_to=user)
                | Q(created_by=user)
                | Q(
                    status=RequestStatus.NEW,
                    assigned_to__isnull=True,
                    created_at__lte=self_assign_cutoff,
                )
            )
        if user.role == Role.OPERATOR:
            return qs.filter(created_by=user)
        return qs.none()

    def get_permissions(self):
        if self.action in ('assign', 'destroy', 'update', 'partial_update'):
            return [IsAdminOrManager()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'list':
            return RepairRequestListSerializer
        if self.action == 'create':
            return RepairRequestCreateSerializer
        if self.action in ('update', 'partial_update'):
            return RepairRequestUpdateSerializer
        if self.action == 'assign':
            return AssignSerializer
        if self.action == 'set_status':
            return StatusTransitionSerializer
        return RepairRequestDetailSerializer

    def perform_create(self, serializer):
        """created_by берётся из токена, не из тела запроса."""
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        allowed_roles = {Role.ADMIN, Role.MECHANIC, Role.OPERATOR}
        if request.user.role not in allowed_roles:
            return Response(
                {'detail': 'Создавать заявки могут оператор, механик и администратор.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().create(request, *args, **kwargs)

    # ── Кастомные actions ────────────────────────────────────────────────────

    @action(detail=True, methods=['put'], url_path='assign',
            permission_classes=[IsAdminOrManager])
    def assign(self, request, pk=None):
        """
        PUT /api/requests/{id}/assign/
        Тело: { "user_id": <id> }
        Назначает исполнителя и переводит заявку в статус 'assigned'.
        """
        repair_request = self.get_object()
        serializer = AssignSerializer(
            data=request.data,
            context={'request': request, 'repair_request': repair_request},
        )
        serializer.is_valid(raise_exception=True)

        repair_request.assigned_to = serializer.validated_data['assigned_to']
        repair_request.status = RequestStatus.ASSIGNED
        repair_request.save(update_fields=['assigned_to', 'status', 'updated_at'])

        return Response(
            RepairRequestDetailSerializer(repair_request, context={'request': request}).data
        )

    @action(detail=True, methods=['put'], url_path='take',
            permission_classes=[IsAuthenticated])
    def take(self, request, pk=None):
        """
        PUT /api/requests/{id}/take/
        РњРµС…Р°РЅРёРє РјРѕР¶РµС‚ СЃР°Рј РІР·СЏС‚СЊ РЅРµРЅР°Р·РЅР°С‡РµРЅРЅСѓСЋ РЅРѕРІСѓСЋ Р·Р°СЏРІРєСѓ РІ СЂР°Р±РѕС‚Сѓ,
        РµСЃР»Рё СЃ РјРѕРјРµРЅС‚Р° СЃРѕР·РґР°РЅРёСЏ РїСЂРѕС€Р»Рѕ РЅРµ РјРµРЅРµРµ 2 С‡Р°СЃРѕРІ.
        """
        if request.user.role != Role.MECHANIC:
            return Response(
                {'detail': 'Р’Р·СЏС‚СЊ Р·Р°СЏРІРєСѓ РІ СЂР°Р±РѕС‚Сѓ РјРѕР¶РµС‚ С‚РѕР»СЊРєРѕ РјРµС…Р°РЅРёРє.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        with transaction.atomic():
            try:
                repair_request = (
                    RepairRequest.objects
                    .select_for_update()
                    .select_related('equipment', 'created_by', 'assigned_to')
                    .get(pk=pk)
                )
            except RepairRequest.DoesNotExist:
                return Response(
                    {'detail': 'Р—Р°СЏРІРєР° РЅРµ РЅР°Р№РґРµРЅР°.'},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if repair_request.assigned_to_id is not None:
                return Response(
                    {'detail': 'Р—Р°СЏРІРєР° СѓР¶Рµ РЅР°Р·РЅР°С‡РµРЅР° РёСЃРїРѕР»РЅРёС‚РµР»СЋ.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if repair_request.status != RequestStatus.NEW:
                return Response(
                    {'detail': 'РЎР°РјРѕСЃС‚РѕСЏС‚РµР»СЊРЅРѕ РІР·СЏС‚СЊ РјРѕР¶РЅРѕ С‚РѕР»СЊРєРѕ РЅРѕРІСѓСЋ Р·Р°СЏРІРєСѓ.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if repair_request.created_at > timezone.now() - SELF_ASSIGN_DELAY:
                return Response(
                    {'detail': 'Р—Р°СЏРІРєСѓ РјРѕР¶РЅРѕ РІР·СЏС‚СЊ РІ СЂР°Р±РѕС‚Сѓ, РµСЃР»Рё РѕРЅР° РЅРµ РЅР°Р·РЅР°С‡РµРЅР° РІ С‚РµС‡РµРЅРёРµ 2 С‡Р°СЃРѕРІ.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            repair_request.assigned_to = request.user
            repair_request.status = RequestStatus.IN_PROGRESS
            repair_request.save(update_fields=['assigned_to', 'status', 'updated_at'])

        return Response(
            RepairRequestDetailSerializer(repair_request, context={'request': request}).data
        )

    @action(detail=True, methods=['put'], url_path='status',
            permission_classes=[IsAuthenticated])
    def set_status(self, request, pk=None):
        """
        PUT /api/requests/{id}/status/
        Тело: { "status": "<new_status>", "resolution_notes": "..." }
        Переводит заявку по разрешённой цепочке статусов.
        """
        repair_request = self.get_object()
        if not self._can_change_status(request.user, repair_request):
            return Response(
                {'detail': 'Нет прав на смену статуса этой заявки.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = StatusTransitionSerializer(
            data=request.data,
            context={'request': request, 'repair_request': repair_request},
        )
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        update_fields = ['status', 'updated_at']

        repair_request.status = new_status

        if new_status == RequestStatus.COMPLETED:
            repair_request.completed_at = timezone.now()
            update_fields.append('completed_at')
            notes = serializer.validated_data.get('resolution_notes', '')
            if notes:
                repair_request.resolution_notes = notes
                update_fields.append('resolution_notes')

        repair_request.save(update_fields=update_fields)

        return Response(
            RepairRequestDetailSerializer(repair_request, context={'request': request}).data
        )

    def _can_change_status(self, user, repair_request):
        if user.role in (Role.ADMIN, Role.MANAGER):
            return True
        if user.role == Role.MECHANIC and repair_request.assigned_to_id == user.pk:
            return True
        if user.role == Role.OPERATOR:
            return (
                repair_request.created_by_id == user.pk
                and repair_request.status == RequestStatus.NEW
            )
        return False
