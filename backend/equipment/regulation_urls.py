"""
Плоские маршруты регламентов: /api/regulations/{id}/
Используются для PUT / PATCH / DELETE без привязки к equipment_id в URL.
"""
from django.urls import path

from .views import MaintenanceRegulationViewSet

regulation_detail = MaintenanceRegulationViewSet.as_view({
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy',
})

urlpatterns = [
    path('<int:pk>/', regulation_detail, name='regulation-detail'),
]
