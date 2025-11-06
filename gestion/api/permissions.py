"""
Permisos personalizados para la API REST de AeroEFI

Este módulo define permisos específicos para diferentes tipos de usuarios
y operaciones en la API REST.
"""
from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permiso que permite operaciones de lectura a cualquier usuario autenticado,
    pero solo permite operaciones de escritura a administradores.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Permisos de lectura para cualquier usuario autenticado
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Permisos de escritura solo para administradores
        return request.user.is_staff


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permiso que permite acceso a los propietarios del recurso o administradores.
    """
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Los administradores pueden acceder a cualquier objeto
        if request.user.is_staff:
            return True
        
        # Verificar si el usuario es el propietario del objeto
        if hasattr(obj, 'usuario'):
            return obj.usuario == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class IsOwnerOrAdminReservation(permissions.BasePermission):
    """
    Permiso específico para reservas: permite acceso al usuario que hizo la reserva
    o a administradores.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Los administradores pueden acceder a cualquier reserva
        if request.user.is_staff:
            return True
        
        # Los usuarios pueden acceder solo a sus propias reservas
        return obj.usuario == request.user


class IsAdminOnly(permissions.BasePermission):
    """
    Permiso que solo permite acceso a administradores.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff


class IsAuthenticatedAndOwnerOrAdmin(permissions.BasePermission):
    """
    Permiso que permite acceso a usuarios autenticados que sean propietarios
    del recurso o administradores.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Los administradores tienen acceso completo
        if request.user.is_staff:
            return True
        
        # Verificar propietario según el tipo de objeto
        if hasattr(obj, 'usuario'):
            return obj.usuario == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class CanCreateReservation(permissions.BasePermission):
    """
    Permiso para crear reservas: usuarios autenticados pueden crear reservas
    para sí mismos, administradores pueden crear para cualquiera.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Los administradores pueden gestionar cualquier reserva
        if request.user.is_staff:
            return True
        
        # Los usuarios regulares solo pueden gestionar sus propias reservas
        if hasattr(obj, 'usuario') and obj.usuario:
            return obj.usuario == request.user
        
        return False


class CanViewPasajero(permissions.BasePermission):
    """
    Permiso para ver información de pasajeros:
    - Administradores pueden ver todos los pasajeros
    - Usuarios regulares pueden ver solo sus propios datos de pasajero
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Los administradores pueden ver cualquier pasajero
        if request.user.is_staff:
            return True
        
        # Los usuarios regulares pueden ver solo si tienen reservas asociadas
        # o si el email del pasajero coincide con el del usuario
        if obj.email == request.user.email:
            return True
        
        # Verificar si el usuario tiene reservas como este pasajero
        return obj.reservas.filter(usuario=request.user).exists()


class CanManageVuelos(permissions.BasePermission):
    """
    Permiso para gestión de vuelos:
    - Lectura: cualquier usuario autenticado
    - Escritura: solo administradores
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user.is_staff


class CanAccessReports(permissions.BasePermission):
    """
    Permiso para acceder a reportes:
    - Administradores: acceso completo a todos los reportes
    - Usuarios regulares: acceso limitado a sus propios datos
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Los administradores tienen acceso completo
        if request.user.is_staff:
            return True
        
        # Los usuarios regulares tienen acceso limitado
        return False  # Se maneja la lógica específica en las vistas