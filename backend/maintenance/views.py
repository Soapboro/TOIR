from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from users.permissions import IsAdminOrMechanic, IsManager
from .filters import MaintenanceHistoryFilter, MaintenancePlanFilter, MaintenanceScheduleFilter
from .models import MaintenancePlan, MaintenanceHistory, MaintenanceSchedule, PlanStatus
from .serializers import (
    MaintenancePlanSerializer,
    MaintenanceRecordListSerializer,
    MaintenanceRecordDetailSerializer,
    MaintenanceRecordCreateSerializer,
    MaintenanceScheduleSerializer,
)


class MaintenancePlanViewSet(viewsets.ModelViewSet):
    """
    CRUD планов ТО.
    GET/POST /api/maintenance/plans/
    GET/PUT/PATCH/DELETE /api/maintenance/plans/{id}/
    """

    queryset = MaintenancePlan.objects.select_related(
        'equipment', 'assigned_to', 'regulation',
    ).order_by('scheduled_date')
    serializer_class = MaintenancePlanSerializer
    filterset_class = MaintenancePlanFilter
    search_fields = ['equipment__name', 'notes']
    ordering_fields = ['scheduled_date', 'status', 'maintenance_type']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsManager()]
        return [IsAuthenticated()]


class MaintenanceRecordViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """
    GET  /api/maintenance-records/       — список с фильтрами
    GET  /api/maintenance-records/{id}/  — детальная запись
    POST /api/maintenance-records/       — зафиксировать выполненную работу (mechanic/admin)
    """

    filterset_class = MaintenanceHistoryFilter
    search_fields = [
        'equipment__name', 'equipment__inventory_number',
        'work_performed', 'parts_replaced',
    ]
    ordering_fields = ['performed_at', 'created_at', 'next_due_date']
    ordering = ['-performed_at']

    def get_queryset(self):
        return (
            MaintenanceHistory.objects
            .select_related('equipment', 'performed_by', 'plan')
            .order_by('-performed_at')
        )

    def get_permissions(self):
        if self.action == 'create':
            return [IsAdminOrMechanic()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'list':
            return MaintenanceRecordListSerializer
        if self.action == 'create':
            return MaintenanceRecordCreateSerializer
        return MaintenanceRecordDetailSerializer

    def perform_create(self, serializer):
        """
        Автоматически устанавливает performed_by из токена.
        Если запись привязана к плану — переводит план в статус 'completed'.
        """
        record = serializer.save(performed_by=self.request.user)

        if record.plan_id:
            MaintenancePlan.objects.filter(
                pk=record.plan_id,
            ).update(status=PlanStatus.COMPLETED)


class MaintenanceScheduleViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    GET /api/schedules/       — список графиков ТО (фильтр по месяцу, оборудованию, статусу)
    GET /api/schedules/{id}/  — детальная запись
    PUT /api/schedules/{id}/  — смена статуса (admin/manager)
    """

    queryset = MaintenanceSchedule.objects.select_related(
        'equipment', 'regulation',
    ).order_by('scheduled_date')
    serializer_class = MaintenanceScheduleSerializer
    filterset_class = MaintenanceScheduleFilter
    search_fields = ['equipment__name', 'equipment__inventory_number', 'regulation__description']
    ordering_fields = ['scheduled_date', 'status']

    def get_permissions(self):
        if self.action in ('update', 'partial_update'):
            return [IsManager()]
        return [IsAuthenticated()]
