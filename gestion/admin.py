from django.contrib import admin
from .models import Avion, Vuelo, Pasajero, Asiento, Reserva, Boleto

@admin.register(Avion)
class AvionAdmin(admin.ModelAdmin):
    list_display = ['modelo', 'capacidad', 'filas', 'columnas', 'fecha_creacion']
    list_filter = ['fecha_creacion']
    search_fields = ['modelo']
    readonly_fields = ['fecha_creacion']

@admin.register(Vuelo)
class VueloAdmin(admin.ModelAdmin):
    list_display = ['origen', 'destino', 'fecha_salida', 'fecha_llegada', 'avion', 'estado', 'precio_base']
    list_filter = ['estado', 'origen', 'destino', 'fecha_salida']
    search_fields = ['origen', 'destino']
    date_hierarchy = 'fecha_salida'
    readonly_fields = ['fecha_creacion']

@admin.register(Pasajero)
class PasajeroAdmin(admin.ModelAdmin):
    list_display = ['nombre_completo', 'documento', 'tipo_documento', 'email', 'telefono', 'fecha_registro']
    list_filter = ['tipo_documento', 'fecha_registro']
    search_fields = ['nombre', 'apellido', 'documento', 'email']
    readonly_fields = ['fecha_registro']

@admin.register(Asiento)
class AsientoAdmin(admin.ModelAdmin):
    list_display = ['numero', 'avion', 'fila', 'columna', 'tipo', 'estado']
    list_filter = ['tipo', 'estado', 'avion']
    search_fields = ['numero', 'avion__modelo']

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ['codigo_reserva', 'pasajero', 'vuelo', 'asiento', 'estado', 'precio', 'fecha_reserva']
    list_filter = ['estado', 'fecha_reserva', 'vuelo__origen', 'vuelo__destino']
    search_fields = ['codigo_reserva', 'pasajero__nombre', 'pasajero__apellido', 'pasajero__documento']
    readonly_fields = ['codigo_reserva', 'fecha_reserva']

@admin.register(Boleto)
class BoletoAdmin(admin.ModelAdmin):
    list_display = ['codigo_barra', 'reserva', 'estado', 'fecha_emision']
    list_filter = ['estado', 'fecha_emision']
    search_fields = ['codigo_barra', 'reserva__codigo_reserva']
    readonly_fields = ['codigo_barra', 'fecha_emision']
