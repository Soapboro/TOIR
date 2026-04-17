from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.permissions import IsAdminOrManager
from .filters import EquipmentFilter
from .models import Equipment, MaintenanceRegulation
from .serializers import (
    EquipmentDetailSerializer,
    EquipmentListSerializer,
    EquipmentWriteSerializer,
    MaintenanceRegulationSerializer,
)


class EquipmentViewSet(viewsets.ModelViewSet):
    """
    GET    /api/equipment/           — список с фильтрами
    GET    /api/equipment/{id}/      — карточка с историей ТО
    POST   /api/equipment/           — создание (admin, manager)
    PUT    /api/equipment/{id}/      — редактирование (admin, manager)
    PATCH  /api/equipment/{id}/      — частичное редактирование (admin, manager)
    DELETE /api/equipment/{id}/      — удаление (admin, manager)
    GET    /api/equipment/{id}/history/ — полная история всех работ
    """

    filterset_class = EquipmentFilter
    search_fields = [
        'name', 'inventory_number', 'serial_number',
        'manufacturer', 'model', 'category', 'location',
    ]
    ordering_fields = ['name', 'status', 'category', 'installation_date', 'updated_at']
    ordering = ['name']

    def get_queryset(self):
        if self.action == 'retrieve':
            # Для детальной карточки подтягиваем регламенты одним запросом
            return Equipment.objects.prefetch_related('regulations').order_by('name')
        return Equipment.objects.all().order_by('name')

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAdminOrManager()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'list':
            return EquipmentListSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return EquipmentWriteSerializer
        return EquipmentDetailSerializer

    @action(detail=True, methods=['get'], url_path='history', permission_classes=[IsAuthenticated])
    def history(self, request, pk=None):
        """GET /api/equipment/{id}/history/ — полная история всех работ с пагинацией."""
        from maintenance.models import MaintenanceHistory
        from maintenance.serializers import MaintenanceHistorySerializer

        equipment = self.get_object()
        qs = (
            MaintenanceHistory.objects
            .filter(equipment=equipment)
            .select_related('performed_by', 'plan')
            .order_by('-performed_at')
        )

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = MaintenanceHistorySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = MaintenanceHistorySerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='maintenance-records',
            permission_classes=[IsAuthenticated])
    def maintenance_records(self, request, pk=None):
        """
        GET /api/equipment/{id}/maintenance-records/
        Список записей о выполненных работах ТО для конкретного оборудования.
        Поддерживает пагинацию и фильтрацию по дате через ?performed_after= / ?performed_before=.
        """
        from maintenance.models import MaintenanceHistory
        from maintenance.serializers import MaintenanceRecordListSerializer
        from maintenance.filters import MaintenanceHistoryFilter
        from django_filters.rest_framework import DjangoFilterBackend

        equipment = self.get_object()
        qs = (
            MaintenanceHistory.objects
            .filter(equipment=equipment)
            .select_related('performed_by', 'plan')
            .order_by('-performed_at')
        )

        # Применяем фильтры из строки запроса (performed_after, performed_before, etc.)
        filterset = MaintenanceHistoryFilter(request.query_params, queryset=qs, request=request)
        qs = filterset.qs

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = MaintenanceRecordListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = MaintenanceRecordListSerializer(qs, many=True)
        return Response(serializer.data)


class MaintenanceRegulationViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    Вложенные маршруты (оборудование → регламенты):
      GET  /api/equipment/{equipment_id}/regulations/  — список регламентов
      POST /api/equipment/{equipment_id}/regulations/  — создать регламент

    Плоские маршруты (прямой доступ к регламенту):
      PUT    /api/regulations/{id}/  — изменить
      PATCH  /api/regulations/{id}/  — частично изменить
      DELETE /api/regulations/{id}/  — удалить
    """

    serializer_class = MaintenanceRegulationSerializer

    def get_permissions(self):
        if self.action == 'list':
            return [IsAuthenticated()]
        return [IsAdminOrManager()]

    def get_queryset(self):
        """
        Если в URL есть equipment_id — фильтруем по нему (вложенный маршрут).
        Иначе — возвращаем все регламенты (плоский маршрут).
        """
        equipment_id = self.kwargs.get('equipment_id')
        qs = MaintenanceRegulation.objects.select_related('equipment').order_by('interval_days')
        if equipment_id is not None:
            qs = qs.filter(equipment_id=equipment_id)
        return qs

    def perform_create(self, serializer):
        equipment = get_object_or_404(Equipment, pk=self.kwargs['equipment_id'])
        serializer.save(equipment=equipment)
