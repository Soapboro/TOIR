from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from notifications.services import notify_request_assigned, notify_request_status_changed
from .models import RepairRequest, RequestStatus
from .serializers import RepairRequestSerializer


class RepairRequestViewSet(viewsets.ModelViewSet):
    queryset = RepairRequest.objects.select_related(
        'equipment', 'created_by', 'assigned_to'
    ).all()
    serializer_class = RepairRequestSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'priority', 'equipment', 'assigned_to']
    search_fields = ['title', 'description', 'equipment__name']
    ordering_fields = ['created_at', 'priority', 'status']

    @action(detail=True, methods=['post'], url_path='assign')
    def assign(self, request, pk=None):
        obj = self.get_object()
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'detail': 'user_id обязателен.'}, status=status.HTTP_400_BAD_REQUEST)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        assignee = User.objects.get(pk=user_id)
        obj.assigned_to = assignee
        obj.status = RequestStatus.IN_PROGRESS
        obj.save()
        notify_request_assigned(obj)
        return Response(RepairRequestSerializer(obj, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        obj = self.get_object()
        obj.status = RequestStatus.COMPLETED
        obj.completed_at = timezone.now()
        obj.resolution_notes = request.data.get('resolution_notes', '')
        obj.save()
        notify_request_status_changed(obj)
        return Response(RepairRequestSerializer(obj, context={'request': request}).data)
