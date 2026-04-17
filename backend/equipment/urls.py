from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import EquipmentViewSet, MaintenanceRegulationViewSet

router = DefaultRouter()
router.register('', EquipmentViewSet, basename='equipment')

# Вложенный маршрут: GET/POST /api/equipment/{equipment_id}/regulations/
regulation_list_create = MaintenanceRegulationViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

urlpatterns = [
    path('', include(router.urls)),
    path('<int:equipment_id>/regulations/', regulation_list_create, name='equipment-regulation-list'),
]
