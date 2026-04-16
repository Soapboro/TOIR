from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import MaintenancePlan, MaintenanceHistory
from .serializers import MaintenancePlanSerializer, MaintenanceHistorySerializer


class MaintenancePlanViewSet(viewsets.ModelViewSet):
    queryset = MaintenancePlan.objects.select_related('equipment', 'assigned_to').all()
    serializer_class = MaintenancePlanSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'maintenance_type', 'equipment', 'assigned_to']
    search_fields = ['equipment__name', 'notes']
    ordering_fields = ['scheduled_date', 'status', 'maintenance_type']


class MaintenanceHistoryViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceHistory.objects.select_related('equipment', 'performed_by', 'plan').all()
    serializer_class = MaintenanceHistorySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['maintenance_type', 'equipment', 'performed_by']
    search_fields = ['equipment__name', 'work_performed']
    ordering_fields = ['performed_at']
