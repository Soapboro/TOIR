from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MaintenancePlanViewSet, MaintenanceHistoryViewSet

router = DefaultRouter()
router.register('plans', MaintenancePlanViewSet, basename='maintenance-plans')
router.register('history', MaintenanceHistoryViewSet, basename='maintenance-history')

urlpatterns = [path('', include(router.urls))]
