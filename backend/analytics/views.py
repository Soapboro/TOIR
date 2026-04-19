from datetime import date, timedelta

from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from rest_framework import viewsets, serializers as drf_serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from equipment.models import Equipment
from maintenance.models import MaintenancePlan, MaintenanceHistory, PlanStatus
from repair_requests.models import RepairRequest, RequestStatus
from .models import EquipmentReliability, FailurePrediction
from .serializers import EquipmentReliabilitySerializer, FailurePredictionSerializer
from .services import predict_next_failure, calculate_mtbf


# ── inline response schemas for drf-spectacular ──────────────────────────────

class _MaintenanceWeekSerializer(drf_serializers.Serializer):
    this_week = drf_serializers.IntegerField()
    overdue = drf_serializers.IntegerField()


class _SummaryEquipmentSerializer(drf_serializers.Serializer):
    total = drf_serializers.IntegerField()
    by_status = drf_serializers.DictField(child=drf_serializers.IntegerField())


class SummaryResponseSerializer(drf_serializers.Serializer):
    equipment = _SummaryEquipmentSerializer()
    open_requests = drf_serializers.IntegerField()
    maintenance = _MaintenanceWeekSerializer()


class _LastMaintenanceSerializer(drf_serializers.Serializer):
    performed_at = drf_serializers.DateTimeField(allow_null=True)
    maintenance_type = drf_serializers.CharField(allow_null=True)


class _NextPlannedSerializer(drf_serializers.Serializer):
    scheduled_date = drf_serializers.DateField(allow_null=True)
    maintenance_type = drf_serializers.CharField(allow_null=True)
    status = drf_serializers.CharField(allow_null=True)


class EquipmentStatsResponseSerializer(drf_serializers.Serializer):
    equipment_id = drf_serializers.IntegerField()
    equipment_name = drf_serializers.CharField()
    repair_count = drf_serializers.IntegerField()
    mtbf_hours = drf_serializers.FloatField(allow_null=True)
    last_maintenance = _LastMaintenanceSerializer(allow_null=True)
    next_planned_maintenance = _NextPlannedSerializer(allow_null=True)


class _RepairsReportSerializer(drf_serializers.Serializer):
    completed = drf_serializers.IntegerField()
    by_priority = drf_serializers.DictField(child=drf_serializers.IntegerField())


class _MaintenanceReportSerializer(drf_serializers.Serializer):
    performed = drf_serializers.IntegerField()
    by_type = drf_serializers.DictField(child=drf_serializers.IntegerField())


class _PeriodSerializer(drf_serializers.Serializer):
    date_from = drf_serializers.DateField()
    date_to = drf_serializers.DateField()


class ReportResponseSerializer(drf_serializers.Serializer):
    period = _PeriodSerializer()
    repairs = _RepairsReportSerializer()
    maintenance = _MaintenanceReportSerializer()
    new_requests = drf_serializers.IntegerField()


# ── existing viewsets ─────────────────────────────────────────────────────────

class EquipmentReliabilityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EquipmentReliability.objects.select_related('equipment').all()
    serializer_class = EquipmentReliabilitySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['equipment']
    ordering_fields = ['availability_percent', 'mtbf_hours', 'failure_count']


class FailurePredictionViewSet(viewsets.ModelViewSet):
    queryset = FailurePrediction.objects.select_related('equipment').all()
    serializer_class = FailurePredictionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['equipment', 'is_acknowledged']
    ordering_fields = ['predicted_failure_date', 'confidence_percent']


class DashboardView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def summary(self, request):
        now = timezone.now()
        data = {
            'equipment': {
                'total': Equipment.objects.count(),
                'by_status': dict(
                    Equipment.objects.values_list('status')
                    .annotate(count=Count('id'))
                    .values_list('status', 'count')
                ),
            },
            'requests': {
                'total': RepairRequest.objects.count(),
                'open': RepairRequest.objects.exclude(
                    status__in=[RequestStatus.COMPLETED, RequestStatus.CANCELLED]
                ).count(),
                'by_priority': dict(
                    RepairRequest.objects.values_list('priority')
                    .annotate(count=Count('id'))
                    .values_list('priority', 'count')
                ),
            },
            'maintenance': {
                'planned_this_month': MaintenancePlan.objects.filter(
                    scheduled_date__year=now.year,
                    scheduled_date__month=now.month,
                ).count(),
                'overdue': MaintenancePlan.objects.filter(
                    status=PlanStatus.OVERDUE
                ).count(),
                'completed_this_month': MaintenancePlan.objects.filter(
                    status=PlanStatus.COMPLETED,
                    scheduled_date__year=now.year,
                    scheduled_date__month=now.month,
                ).count(),
            },
        }
        return Response(data)


# ── prediction views ──────────────────────────────────────────────────────────

class LivePredictionsView(APIView):
    """
    GET /api/analytics/predictions/
    Прогнозы следующего отказа по всему парку оборудования.
    Сортировка по срочности: сначала ближайшие отказы, в конце — оборудование
    без достаточной истории аварийных ремонтов.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        equipment_qs = Equipment.objects.values_list('id', 'name')
        predictions = []
        for eq_id, eq_name in equipment_qs:
            pred = predict_next_failure(eq_id)
            predictions.append({
                'equipment_id': eq_id,
                'equipment_name': eq_name,
                **pred,
            })

        def sort_key(p):
            d = p['days_until_failure']
            return (0, d) if d is not None else (1, 0)

        predictions.sort(key=sort_key)
        return Response(predictions)


class EquipmentPredictionView(APIView):
    """
    GET /api/analytics/equipment/{id}/prediction/
    Прогноз следующего отказа для конкретного станка.
    Возвращает null-поля с пояснением, если записей об отказах меньше 2.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, equipment_id):
        equipment = get_object_or_404(Equipment, pk=equipment_id)
        pred = predict_next_failure(equipment_id)
        return Response({
            'equipment_id': equipment.id,
            'equipment_name': equipment.name,
            **pred,
        })


# ── new analytical views ──────────────────────────────────────────────────────

@extend_schema(
    summary='Общая статистика парка',
    description=(
        'Возвращает сводку по оборудованию (кол-во по статусам), '
        'открытые ремонтные заявки, количество ТО на текущей неделе '
        'и просроченные планы ТО.'
    ),
    responses={200: SummaryResponseSerializer},
    tags=['analytics'],
)
class SummaryView(APIView):
    """GET /api/analytics/summary/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())   # понедельник
        week_end = week_start + timedelta(days=6)              # воскресенье

        return Response({
            'equipment': {
                'total': Equipment.objects.count(),
                'by_status': dict(
                    Equipment.objects.values('status')
                    .annotate(count=Count('id'))
                    .values_list('status', 'count')
                ),
            },
            'open_requests': RepairRequest.objects.exclude(
                status__in=[
                    RequestStatus.COMPLETED,
                    RequestStatus.CLOSED,
                    RequestStatus.CANCELLED,
                ]
            ).count(),
            'maintenance': {
                'this_week': MaintenancePlan.objects.filter(
                    scheduled_date__gte=week_start,
                    scheduled_date__lte=week_end,
                ).count(),
                'overdue': MaintenancePlan.objects.filter(
                    status=PlanStatus.OVERDUE,
                ).count(),
            },
        })


@extend_schema(
    summary='Статистика конкретного станка',
    description=(
        'Возвращает кол-во ремонтных заявок, MTBF (часы), '
        'дату последнего выполненного ТО и ближайшее плановое ТО.'
    ),
    responses={200: EquipmentStatsResponseSerializer},
    tags=['analytics'],
)
class EquipmentStatsView(APIView):
    """GET /api/analytics/equipment/{id}/stats/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, equipment_id):
        equipment = get_object_or_404(Equipment, pk=equipment_id)

        repair_count = RepairRequest.objects.filter(equipment=equipment).count()

        mtbf = calculate_mtbf(equipment_id)

        last_maintenance = (
            MaintenanceHistory.objects
            .filter(equipment=equipment)
            .order_by('-performed_at')
            .values('performed_at', 'maintenance_type')
            .first()
        )

        next_planned = (
            MaintenancePlan.objects
            .filter(
                equipment=equipment,
                status__in=[PlanStatus.PLANNED, PlanStatus.IN_PROGRESS],
                scheduled_date__gte=timezone.now().date(),
            )
            .order_by('scheduled_date')
            .values('scheduled_date', 'maintenance_type', 'status')
            .first()
        )

        return Response({
            'equipment_id': equipment.id,
            'equipment_name': equipment.name,
            'repair_count': repair_count,
            'mtbf_hours': round(mtbf, 2) if mtbf is not None else None,
            'last_maintenance': last_maintenance,
            'next_planned_maintenance': next_planned,
        })


@extend_schema(
    summary='Отчёт за период',
    description=(
        'Возвращает агрегированную статистику за указанный период: '
        'выполненные ремонты по приоритетам, проведённые ТО по типам, '
        'новые заявки.'
    ),
    parameters=[
        OpenApiParameter(
            name='date_from',
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Начало периода (YYYY-MM-DD)',
            examples=[OpenApiExample('Пример', value='2024-01-01')],
        ),
        OpenApiParameter(
            name='date_to',
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Конец периода (YYYY-MM-DD)',
            examples=[OpenApiExample('Пример', value='2024-12-31')],
        ),
    ],
    responses={
        200: ReportResponseSerializer,
        400: drf_serializers.Serializer,
    },
    tags=['analytics'],
)
class ReportView(APIView):
    """GET /api/analytics/report/?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_from_str = request.query_params.get('date_from')
        date_to_str = request.query_params.get('date_to')

        if not date_from_str or not date_to_str:
            return Response(
                {'error': 'Параметры date_from и date_to обязательны'},
                status=400,
            )

        try:
            date_from = date.fromisoformat(date_from_str)
            date_to = date.fromisoformat(date_to_str)
        except ValueError:
            return Response(
                {'error': 'Неверный формат даты. Используйте YYYY-MM-DD'},
                status=400,
            )

        if date_from > date_to:
            return Response(
                {'error': 'date_from не может быть позже date_to'},
                status=400,
            )

        repairs = RepairRequest.objects.filter(
            completed_at__date__gte=date_from,
            completed_at__date__lte=date_to,
            status__in=[RequestStatus.COMPLETED, RequestStatus.CLOSED],
        )

        maintenance_done = MaintenanceHistory.objects.filter(
            performed_at__date__gte=date_from,
            performed_at__date__lte=date_to,
        )

        return Response({
            'period': {'date_from': date_from, 'date_to': date_to},
            'repairs': {
                'completed': repairs.count(),
                'by_priority': dict(
                    repairs.values('priority')
                    .annotate(count=Count('id'))
                    .values_list('priority', 'count')
                ),
            },
            'maintenance': {
                'performed': maintenance_done.count(),
                'by_type': dict(
                    maintenance_done.values('maintenance_type')
                    .annotate(count=Count('id'))
                    .values_list('maintenance_type', 'count')
                ),
            },
            'new_requests': RepairRequest.objects.filter(
                created_at__date__gte=date_from,
                created_at__date__lte=date_to,
            ).count(),
        })
