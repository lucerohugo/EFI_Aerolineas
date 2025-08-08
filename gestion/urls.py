
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('registro/', views.registro_view, name='registro'),
    path('vuelos/', views.lista_vuelos, name='lista_vuelos'),
    path('vuelos/buscar/', views.buscar_vuelos, name='buscar_vuelos'),
    path('vuelos/<int:vuelo_id>/', views.detalle_vuelo, name='detalle_vuelo'),
    path('vuelos/<int:vuelo_id>/reporte/', views.reporte_pasajeros_vuelo, name='reporte_pasajeros_vuelo'),
    path('reservas/', views.lista_reservas, name='lista_reservas'),
    path('reservas/buscar/', views.buscar_reserva, name='buscar_reserva'),
    path('reservas/<int:reserva_id>/', views.detalle_reserva, name='detalle_reserva'),
    path('reservas/<int:reserva_id>/cancelar/', views.cancelar_reserva, name='cancelar_reserva'),
    path('vuelos/<int:vuelo_id>/reservar/', views.crear_reserva, name='crear_reserva'),
    path('pasajeros/', views.lista_pasajeros, name='lista_pasajeros'),
    path('pasajeros/<int:pasajero_id>/', views.detalle_pasajero, name='detalle_pasajero'),
]
