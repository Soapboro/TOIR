from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Equipment
from .serializers import EquipmentSerializer, EquipmentListSerializer


class EquipmentViewSet(viewsets.ModelViewSet):
    queryset = Equipment.objects.all()
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'category', 'location']
    search_fields = ['name', 'inventory_number', 'serial_number', 'manufacturer', 'model']
    ordering_fields = ['name', 'installation_date', 'status', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return EquipmentListSerializer
        return EquipmentSerializer
