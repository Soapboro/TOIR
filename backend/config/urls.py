from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerUIView, SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),

    # API
    path('api/auth/',        include('users.urls')),
    path('api/users/',       include('users.admin_urls')),
    path('api/equipment/',   include('equipment.urls')),
    path('api/regulations/', include('equipment.regulation_urls')),
    path('api/requests/',    include('repair_requests.urls')),
    path('api/maintenance/',         include('maintenance.urls')),
    path('api/maintenance-records/', include('maintenance.record_urls')),
    path('api/schedules/',           include('maintenance.schedule_urls')),
    path('api/analytics/',   include('analytics.urls')),
    path('api/notifications/', include('notifications.urls')),

    # OpenAPI / Swagger
    path('api/schema/',         SpectacularAPIView.as_view(),                         name='schema'),
    path('api/docs/',           SpectacularSwaggerUIView.as_view(url_name='schema'),  name='swagger-ui'),
    path('api/schema/swagger/', SpectacularSwaggerUIView.as_view(url_name='schema'),  name='swagger-ui-legacy'),
    path('api/schema/redoc/',   SpectacularRedocView.as_view(url_name='schema'),      name='redoc'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
