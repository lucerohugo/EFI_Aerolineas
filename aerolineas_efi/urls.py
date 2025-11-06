"""
URL configuration for aerolineas_efi project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls.i18n import i18n_patterns
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Configuración de Swagger/OpenAPI
schema_view = get_schema_view(
    openapi.Info(
        title="AeroEFI API",
        default_version='v1',
        description="API REST para el Sistema de Gestión de Aerolíneas AeroEFI",
        terms_of_service="https://www.aeroéfi.com/terms/",
        contact=openapi.Contact(email="api@aeroéfi.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# URLs sin traducir (incluyendo la API)
urlpatterns = [

    # Internacionalización
    path('i18n/', include('django.conf.urls.i18n')),
    
    # API REST (sin traducir para mantener consistencia)
    path('api/v1/', include('gestion.api.urls')),
    
    # Documentación de la API
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# URLs con traducción (interfaz web)
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('gestion.urls')),
    prefix_default_language=False
)
