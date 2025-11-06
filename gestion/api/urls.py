"""
URLs para la API REST de AeroEFI

Este módulo define todas las rutas de la API REST utilizando
Django Rest Framework routers.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from .views import (
    VueloViewSet,
    PasajeroViewSet,
    ReservaViewSet,
    AvionViewSet,
    BoletoViewSet,
    ReportesViewSet,
)

# Configurar el router de DRF
router = DefaultRouter()

# Registrar los ViewSets con el router
router.register(r'vuelos', VueloViewSet, basename='vuelo')
router.register(r'pasajeros', PasajeroViewSet, basename='pasajero')
router.register(r'reservas', ReservaViewSet, basename='reserva')
router.register(r'aviones', AvionViewSet, basename='avion')
router.register(r'boletos', BoletoViewSet, basename='boleto')
router.register(r'reportes', ReportesViewSet, basename='reporte')

# URLs de la API
urlpatterns = [
    # Rutas principales de la API
    path('', include(router.urls)),
    
    # Autenticación JWT
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Rutas de DRF para autenticación por sesión (útil para desarrollo)
    path('auth/session/', include('rest_framework.urls')),
]