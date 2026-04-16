from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RepairRequestViewSet

router = DefaultRouter()
router.register('', RepairRequestViewSet, basename='repair-requests')

urlpatterns = [path('', include(router.urls))]
