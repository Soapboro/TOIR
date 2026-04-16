from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EquipmentReliabilityViewSet, FailurePredictionViewSet, DashboardView

router = DefaultRouter()
router.register('reliability', EquipmentReliabilityViewSet, basename='reliability')
router.register('predictions', FailurePredictionViewSet, basename='predictions')
router.register('dashboard', DashboardView, basename='dashboard')

urlpatterns = [path('', include(router.urls))]
