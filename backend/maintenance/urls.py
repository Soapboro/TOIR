from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import MaintenancePlanViewSet, MaintenanceRecordViewSet

router = DefaultRouter()
router.register('plans', MaintenancePlanViewSet, basename='maintenance-plans')
router.register('history', MaintenanceRecordViewSet, basename='maintenance-history')

urlpatterns = [path('', include(router.urls))]
