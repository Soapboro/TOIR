from django.utils import timezone
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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
        return (
            RepairRequest.objects
            .select_related('equipment', 'created_by', 'assigned_to')
            .order_by('-created_at')
        )

    def get_permissions(self):
        if self.action in ('assign', 'destroy'):
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

    @action(detail=True, methods=['put'], url_path='status',
            permission_classes=[IsAuthenticated])
    def set_status(self, request, pk=None):
        """
        PUT /api/requests/{id}/status/
        Тело: { "status": "<new_status>", "resolution_notes": "..." }
        Переводит заявку по разрешённой цепочке статусов.
        """
        repair_request = self.get_object()
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
