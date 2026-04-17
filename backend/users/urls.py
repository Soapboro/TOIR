from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenBlacklistView

from .views import CustomTokenObtainPairView, MeView, RegisterView, UserViewSet

router = DefaultRouter()
router.register('users', UserViewSet, basename='users')

urlpatterns = [
    # Auth endpoints
    path('register/', RegisterView.as_view(),              name='auth_register'),
    path('login/',    CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/',  TokenRefreshView.as_view(),          name='token_refresh'),
    path('logout/',   TokenBlacklistView.as_view(),        name='token_blacklist'),
    path('me/',       MeView.as_view(),                    name='auth_me'),

    # User management (admin)
    path('', include(router.urls)),
]
