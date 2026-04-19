from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    EquipmentReliabilityViewSet,
    FailurePredictionViewSet,
    DashboardView,
    LivePredictionsView,
    EquipmentPredictionView,
    SummaryView,
    EquipmentStatsView,
    ReportView,
)

router = DefaultRouter()
router.register('reliability', EquipmentReliabilityViewSet, basename='reliability')
router.register('stored-predictions', FailurePredictionViewSet, basename='stored-predictions')
router.register('dashboard', DashboardView, basename='dashboard')

urlpatterns = [
    # Predictive analytics
    path('predictions/', LivePredictionsView.as_view(), name='live-predictions'),
    path('equipment/<int:equipment_id>/prediction/', EquipmentPredictionView.as_view(), name='equipment-prediction'),

    # Analytical routes
    path('summary/', SummaryView.as_view(), name='analytics-summary'),
    path('equipment/<int:equipment_id>/stats/', EquipmentStatsView.as_view(), name='equipment-stats'),
    path('report/', ReportView.as_view(), name='analytics-report'),

    path('', include(router.urls)),
]
