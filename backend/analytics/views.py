from django.db.models import Count, Avg, Sum
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from equipment.models import Equipment
from maintenance.models import MaintenanceHistory, MaintenancePlan, PlanStatus
from repair_requests.models import RepairRequest, RequestStatus
from .models import EquipmentReliability, FailurePrediction
from .serializers import EquipmentReliabilitySerializer, FailurePredictionSerializer


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
