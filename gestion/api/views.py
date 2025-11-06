
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import datetime, date

from ..models import Vuelo, Pasajero, Reserva, Asiento, Avion, Boleto
from .serializers import (
    VueloSerializer, PasajeroSerializer, ReservaSerializer,
    AsientoSerializer, AvionSerializer, BoletoSerializer,
    ReservaCreateSerializer, ReservaUpdateSerializer,
    ReporteVueloSerializer, ReportePasajeroSerializer
)
from .permissions import (
    IsAdminOrReadOnly, IsOwnerOrAdminReservation, IsAdminOnly,
    CanViewPasajero, CanManageVuelos, CanAccessReports
)



class VueloViewSet(viewsets.ModelViewSet):
    queryset = Vuelo.objects.all().select_related('avion')
    serializer_class = VueloSerializer
    permission_classes = [CanManageVuelos]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['origen', 'destino', 'estado', 'avion']
    search_fields = ['origen', 'destino']
    ordering_fields = ['fecha_salida', 'precio_base', 'origen', 'destino']
    ordering = ['fecha_salida']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        fecha_salida = self.request.query_params.get('fecha_salida')
        if fecha_salida:
            try:
                fecha = datetime.strptime(fecha_salida, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_salida__date=fecha)
            except ValueError:
                pass
        
        fecha_desde = self.request.query_params.get('fecha_desde')
        fecha_hasta = self.request.query_params.get('fecha_hasta')
        
        if fecha_desde:
            try:
                fecha = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_salida__date__gte=fecha)
            except ValueError:
                pass
        
        if fecha_hasta:
            try:
                fecha = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_salida__date__lte=fecha)
            except ValueError:
                pass
        
                solo_futuros = self.request.query_params.get('solo_futuros', 'true').lower() == 'true'
            queryset = queryset.filter(fecha_salida__gte=timezone.now())
        
        return queryset
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def asientos(self, request, pk=None):
        vuelo = self.get_object()
        asientos = vuelo.avion.asientos.all().order_by('fila', 'columna')
        reservas_confirmadas = Reserva.objects.filter(
            vuelo=vuelo,
            estado__in=['confirmada', 'pagada']
        ).values_list('asiento_id', flat=True)
        
        asientos_data = []
        for asiento in asientos:
            asiento_info = AsientoSerializer(asiento).data
            asiento_info['reservado'] = asiento.id in reservas_confirmadas
            asientos_data.append(asiento_info)
        
        asientos_por_fila = {}
        for asiento in asientos_data:
            fila = asiento['fila']
            if fila not in asientos_por_fila:
                asientos_por_fila[fila] = []
            asientos_por_fila[fila].append(asiento)
        
        return Response({
            'vuelo': VueloSerializer(vuelo).data,
            'asientos_por_fila': asientos_por_fila,
            'total_asientos': len(asientos_data),
            'asientos_disponibles': len([a for a in asientos_data if not a['reservado']])
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def buscar(self, request):
        origen = request.query_params.get('origen')
        destino = request.query_params.get('destino')
        fecha_salida = request.query_params.get('fecha_salida')
        pasajeros = request.query_params.get('pasajeros', 1)
        
        queryset = self.get_queryset()
        
        if origen:
            queryset = queryset.filter(origen__icontains=origen)
        
        if destino:
            queryset = queryset.filter(destino__icontains=destino)
        
        if fecha_salida:
            try:
                fecha = datetime.strptime(fecha_salida, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_salida__date=fecha)
            except ValueError:
                return Response(
                    {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Filtrar por disponibilidad de asientos
        try:
            num_pasajeros = int(pasajeros)
            vuelos_disponibles = []
            
            for vuelo in queryset:
                if vuelo.asientos_disponibles() >= num_pasajeros:
                    vuelos_disponibles.append(vuelo)
            
            serializer = self.get_serializer(vuelos_disponibles, many=True)
            return Response({
                'count': len(vuelos_disponibles),
                'results': serializer.data
            })
            
        except ValueError:
            return Response(
                {'error': 'Número de pasajeros inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )


class PasajeroViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de pasajeros
    
    Funcionalidades:
    - Registrar un pasajero
    - Consultar información de un pasajero
    - Listar reservas asociadas a un pasajero
    """
    
    queryset = Pasajero.objects.all()
    serializer_class = PasajeroSerializer
    permission_classes = [CanViewPasajero]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo_documento']
    search_fields = ['nombre', 'apellido', 'documento', 'email']
    ordering_fields = ['nombre', 'apellido', 'fecha_nacimiento']
    ordering = ['apellido', 'nombre']
    
    def get_queryset(self):
        """Filtrar pasajeros según permisos del usuario"""
        queryset = super().get_queryset()
        
        # Los administradores pueden ver todos los pasajeros
        if self.request.user.is_staff:
            return queryset
        
        # Los usuarios regulares solo pueden ver pasajeros con los que tienen relación
        return queryset.filter(
            Q(email=self.request.user.email) |
            Q(reservas__usuario=self.request.user)
        ).distinct()
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def reservas(self, request, pk=None):
        """Obtiene todas las reservas de un pasajero específico"""
        pasajero = self.get_object()
        
        # Verificar permisos
        if not request.user.is_staff and pasajero.email != request.user.email:
            # Verificar si el usuario tiene reservas con este pasajero
            if not pasajero.reservas.filter(usuario=request.user).exists():
                return Response(
                    {'error': 'No tienes permisos para ver las reservas de este pasajero'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        reservas = pasajero.reservas.all().order_by('-fecha_reserva')
        
        # Si no es admin, filtrar solo reservas del usuario actual
        if not request.user.is_staff:
            reservas = reservas.filter(usuario=request.user)
        
        serializer = ReservaSerializer(reservas, many=True)
        return Response({
            'pasajero': PasajeroSerializer(pasajero).data,
            'reservas': serializer.data,
            'total_reservas': reservas.count()
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def buscar_por_documento(self, request):
        """Busca un pasajero por número de documento"""
        documento = request.query_params.get('documento')
        
        if not documento:
            return Response(
                {'error': 'Debe proporcionar el número de documento'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            pasajero = Pasajero.objects.get(documento=documento)
            
            # Verificar permisos
            if not request.user.is_staff:
                if (pasajero.email != request.user.email and 
                    not pasajero.reservas.filter(usuario=request.user).exists()):
                    return Response(
                        {'error': 'No tienes permisos para ver este pasajero'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            serializer = self.get_serializer(pasajero)
            return Response(serializer.data)
            
        except Pasajero.DoesNotExist:
            return Response(
                {'error': 'No se encontró un pasajero con ese documento'},
                status=status.HTTP_404_NOT_FOUND
            )


class ReservaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión del sistema de reservas
    
    Funcionalidades:
    - Crear una reserva para un pasajero en un vuelo
    - Seleccionar asiento disponible
    - Cambiar estado de una reserva (confirmar, cancelar)
    """
    
    queryset = Reserva.objects.all().select_related(
        'vuelo', 'pasajero', 'asiento', 'usuario'
    )
    permission_classes = [IsOwnerOrAdminReservation]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'metodo_pago', 'vuelo']
    search_fields = ['codigo_reserva', 'pasajero__nombre', 'pasajero__apellido', 'pasajero__documento']
    ordering_fields = ['fecha_reserva', 'precio']
    ordering = ['-fecha_reserva']
    
    def get_serializer_class(self):
        """Seleccionar serializer según la acción"""
        if self.action == 'create':
            return ReservaCreateSerializer
        elif self.action == 'cambiar_estado':
            return ReservaUpdateSerializer
        return ReservaSerializer
    
    def get_queryset(self):
        """Filtrar reservas según permisos del usuario"""
        queryset = super().get_queryset()
        
        # Los administradores pueden ver todas las reservas
        if self.request.user.is_staff:
            return queryset
        
        # Los usuarios regulares solo pueden ver sus propias reservas
        return queryset.filter(usuario=self.request.user)
    
    def perform_create(self, serializer):
        """Lógica personalizada al crear una reserva"""
        # Asignar el usuario actual si no es admin
        if not self.request.user.is_staff:
            serializer.validated_data['usuario'] = self.request.user
        
        # Guardar la reserva
        reserva = serializer.save()
        
        # Marcar el asiento como reservado
        if reserva.asiento:
            reserva.asiento.estado = 'reservado'
            reserva.asiento.save()
        
        # Generar boleto automáticamente si la reserva está confirmada
        if reserva.estado == 'confirmada':
            Boleto.objects.create(reserva=reserva)
    
    @action(detail=True, methods=['patch'], permission_classes=[IsOwnerOrAdminReservation])
    def cambiar_estado(self, request, pk=None):
        """Cambia el estado de una reserva"""
        reserva = self.get_object()
        serializer = ReservaUpdateSerializer(reserva, data=request.data, partial=True)
        
        if serializer.is_valid():
            nuevo_estado = serializer.validated_data['estado']
            estado_anterior = reserva.estado
            
            # Lógica específica según el cambio de estado
            if nuevo_estado == 'cancelada' and estado_anterior != 'cancelada':
                # Liberar el asiento
                if reserva.asiento:
                    reserva.asiento.estado = 'disponible'
                    reserva.asiento.save()
                
                # Eliminar boleto si existe
                if hasattr(reserva, 'boleto'):
                    reserva.boleto.delete()
            
            elif nuevo_estado == 'confirmada' and estado_anterior == 'pendiente':
                # Generar boleto si no existe
                if not hasattr(reserva, 'boleto'):
                    Boleto.objects.create(reserva=reserva)
            
            serializer.save()
            
            return Response({
                'message': f'Estado de la reserva cambiado de "{estado_anterior}" a "{nuevo_estado}"',
                'reserva': ReservaSerializer(reserva).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def buscar_por_codigo(self, request):
        """Busca una reserva por código"""
        codigo = request.query_params.get('codigo')
        
        if not codigo:
            return Response(
                {'error': 'Debe proporcionar el código de reserva'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            reserva = Reserva.objects.get(codigo_reserva__iexact=codigo)
            
            # Verificar permisos
            if not request.user.is_staff and reserva.usuario != request.user:
                return Response(
                    {'error': 'No tienes permisos para ver esta reserva'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = self.get_serializer(reserva)
            return Response(serializer.data)
            
        except Reserva.DoesNotExist:
            return Response(
                {'error': 'No se encontró una reserva con ese código'},
                status=status.HTTP_404_NOT_FOUND
            )


class AvionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para gestión de aviones y asientos (solo lectura)
    
    Funcionalidades:
    - Listar aviones registrados
    - Obtener layout de asientos de un avión  
    - Verificar disponibilidad de un asiento en un vuelo
    """
    
    queryset = Avion.objects.all().prefetch_related('asientos')
    serializer_class = AvionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['modelo']
    ordering = ['modelo']
    
    @action(detail=True, methods=['get'])
    def asientos(self, request, pk=None):
        """Obtiene el layout de asientos de un avión"""
        avion = self.get_object()
        asientos = avion.asientos.all().order_by('fila', 'columna')
        
        # Organizar asientos por fila
        asientos_por_fila = {}
        for asiento in asientos:
            fila = asiento.fila
            if fila not in asientos_por_fila:
                asientos_por_fila[fila] = []
            asientos_por_fila[fila].append(AsientoSerializer(asiento).data)
        
        return Response({
            'avion': AvionSerializer(avion).data,
            'asientos_por_fila': asientos_por_fila,
            'total_asientos': asientos.count()
        })
    
    @action(detail=True, methods=['get'])
    def verificar_disponibilidad(self, request, pk=None):
        """Verifica disponibilidad de asientos en un vuelo específico"""
        avion = self.get_object()
        vuelo_id = request.query_params.get('vuelo_id')
        
        if not vuelo_id:
            return Response(
                {'error': 'Debe proporcionar el ID del vuelo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            vuelo = Vuelo.objects.get(id=vuelo_id, avion=avion)
        except Vuelo.DoesNotExist:
            return Response(
                {'error': 'No se encontró el vuelo especificado para este avión'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Obtener asientos reservados para este vuelo
        asientos_reservados = Reserva.objects.filter(
            vuelo=vuelo,
            estado__in=['confirmada', 'pagada']
        ).values_list('asiento_id', flat=True)
        
        # Obtener todos los asientos del avión
        asientos = avion.asientos.all().order_by('fila', 'columna')
        
        asientos_data = []
        for asiento in asientos:
            asiento_info = AsientoSerializer(asiento).data
            asiento_info['disponible'] = asiento.id not in asientos_reservados
            asientos_data.append(asiento_info)
        
        return Response({
            'vuelo': {
                'id': vuelo.id,
                'numero_vuelo': vuelo.numero_vuelo,
                'origen': vuelo.origen,
                'destino': vuelo.destino,
                'fecha_salida': vuelo.fecha_salida
            },
            'avion': AvionSerializer(avion).data,
            'asientos': asientos_data,
            'asientos_disponibles': len([a for a in asientos_data if a['disponible']]),
            'asientos_ocupados': len([a for a in asientos_data if not a['disponible']])
        })


class BoletoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para gestión de boletos
    
    Funcionalidades:
    - Generar boleto a partir de una reserva confirmada
    - Consultar información de un boleto por código
    """
    
    queryset = Boleto.objects.all().select_related('reserva__vuelo', 'reserva__pasajero')
    serializer_class = BoletoSerializer
    permission_classes = [IsOwnerOrAdminReservation]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['codigo_barra', 'reserva__codigo_reserva']
    ordering = ['-fecha_emision']
    
    def get_queryset(self):
        """Filtrar boletos según permisos del usuario"""
        queryset = super().get_queryset()
        
        # Los administradores pueden ver todos los boletos
        if self.request.user.is_staff:
            return queryset
        
        # Los usuarios regulares solo pueden ver boletos de sus reservas
        return queryset.filter(reserva__usuario=self.request.user)
    
    @action(detail=False, methods=['post'], permission_classes=[IsOwnerOrAdminReservation])
    def generar_desde_reserva(self, request):
        """Genera un boleto desde una reserva confirmada"""
        reserva_id = request.data.get('reserva_id')
        
        if not reserva_id:
            return Response(
                {'error': 'Debe proporcionar el ID de la reserva'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            reserva = Reserva.objects.get(id=reserva_id)
            
            # Verificar permisos
            if not request.user.is_staff and reserva.usuario != request.user:
                return Response(
                    {'error': 'No tienes permisos para generar boleto de esta reserva'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Verificar que la reserva esté confirmada
            if reserva.estado not in ['confirmada', 'pagada']:
                return Response(
                    {'error': 'Solo se pueden generar boletos para reservas confirmadas o pagadas'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verificar si ya existe un boleto
            if hasattr(reserva, 'boleto'):
                return Response(
                    {'error': 'La reserva ya tiene un boleto generado'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Crear el boleto
            boleto = Boleto.objects.create(reserva=reserva)
            
            return Response({
                'message': 'Boleto generado exitosamente',
                'boleto': BoletoSerializer(boleto).data
            }, status=status.HTTP_201_CREATED)
            
        except Reserva.DoesNotExist:
            return Response(
                {'error': 'No se encontró la reserva especificada'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def buscar_por_codigo(self, request):
        """Busca un boleto por código de barra"""
        codigo = request.query_params.get('codigo')
        
        if not codigo:
            return Response(
                {'error': 'Debe proporcionar el código de boleto'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            boleto = Boleto.objects.get(codigo_barra=codigo)
            
            # Verificar permisos
            if not request.user.is_staff and boleto.reserva.usuario != request.user:
                return Response(
                    {'error': 'No tienes permisos para ver este boleto'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = self.get_serializer(boleto)
            return Response(serializer.data)
            
        except Boleto.DoesNotExist:
            return Response(
                {'error': 'No se encontró un boleto con ese código'},
                status=status.HTTP_404_NOT_FOUND
            )


class ReportesViewSet(viewsets.ViewSet):
    """
    ViewSet para reportes y estadísticas
    
    Funcionalidades:
    - Endpoint para obtener listado de pasajeros por vuelo
    - Endpoint para obtener reservas activas de un pasajero
    """
    
    permission_classes = [CanAccessReports]
    
    @action(detail=False, methods=['get'])
    def pasajeros_por_vuelo(self, request):
        """Obtiene el listado de pasajeros de un vuelo específico"""
        vuelo_id = request.query_params.get('vuelo_id')
        
        if not vuelo_id:
            return Response(
                {'error': 'Debe proporcionar el ID del vuelo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Solo administradores pueden acceder a este reporte
        if not request.user.is_staff:
            return Response(
                {'error': 'No tienes permisos para acceder a este reporte'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            vuelo = Vuelo.objects.get(id=vuelo_id)
        except Vuelo.DoesNotExist:
            return Response(
                {'error': 'No se encontró el vuelo especificado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Obtener reservas confirmadas para el vuelo
        reservas = Reserva.objects.filter(
            vuelo=vuelo,
            estado__in=['confirmada', 'pagada']
        ).select_related('pasajero', 'asiento').order_by('asiento__fila', 'asiento__columna')
        
        return Response({
            'vuelo': VueloSerializer(vuelo).data,
            'total_pasajeros': reservas.count(),
            'reservas': ReservaSerializer(reservas, many=True).data,
            'estadisticas': {
                'asientos_ocupados': reservas.count(),
                'asientos_disponibles': vuelo.asientos_disponibles(),
                'porcentaje_ocupacion': vuelo.porcentaje_ocupacion(),
                'ingresos_totales': sum(r.precio for r in reservas)
            }
        })
    
    @action(detail=False, methods=['get'])
    def reservas_activas_pasajero(self, request):
        """Obtiene las reservas activas de un pasajero específico"""
        pasajero_id = request.query_params.get('pasajero_id')
        
        if not pasajero_id:
            return Response(
                {'error': 'Debe proporcionar el ID del pasajero'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            pasajero = Pasajero.objects.get(id=pasajero_id)
        except Pasajero.DoesNotExist:
            return Response(
                {'error': 'No se encontró el pasajero especificado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar permisos
        if not request.user.is_staff:
            # Los usuarios regulares solo pueden ver sus propios datos
            if (pasajero.email != request.user.email and 
                not pasajero.reservas.filter(usuario=request.user).exists()):
                return Response(
                    {'error': 'No tienes permisos para ver las reservas de este pasajero'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Obtener reservas activas (no canceladas)
        reservas_activas = pasajero.reservas.exclude(
            estado='cancelada'
        ).select_related('vuelo', 'asiento').order_by('-fecha_reserva')
        
        # Si no es admin, filtrar solo reservas del usuario actual
        if not request.user.is_staff:
            reservas_activas = reservas_activas.filter(usuario=request.user)
        
        return Response({
            'pasajero': PasajeroSerializer(pasajero).data,
            'reservas_activas': ReservaSerializer(reservas_activas, many=True).data,
            'total_reservas_activas': reservas_activas.count(),
            'estadisticas': {
                'reservas_confirmadas': reservas_activas.filter(estado='confirmada').count(),
                'reservas_pagadas': reservas_activas.filter(estado='pagada').count(),
                'reservas_pendientes': reservas_activas.filter(estado='pendiente').count(),
                'valor_total': sum(r.precio for r in reservas_activas)
            }
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdminOnly])
    def estadisticas_generales(self, request):
        """Obtiene estadísticas generales del sistema (solo administradores)"""
        
        # Estadísticas de vuelos
        total_vuelos = Vuelo.objects.count()
        vuelos_activos = Vuelo.objects.filter(estado='programado').count()
        vuelos_hoy = Vuelo.objects.filter(fecha_salida__date=date.today()).count()
        
        # Estadísticas de reservas
        total_reservas = Reserva.objects.count()
        reservas_confirmadas = Reserva.objects.filter(estado='confirmada').count()
        reservas_pagadas = Reserva.objects.filter(estado='pagada').count()
        reservas_canceladas = Reserva.objects.filter(estado='cancelada').count()
        
        # Estadísticas de pasajeros
        total_pasajeros = Pasajero.objects.count()
        
        # Ingresos
        ingresos_totales = sum(
            r.precio for r in Reserva.objects.filter(estado__in=['confirmada', 'pagada'])
        )
        
        # Ocupación promedio
        vuelos_con_reservas = Vuelo.objects.filter(
            reservas__estado__in=['confirmada', 'pagada']
        ).distinct()
        
        ocupacion_promedio = 0
        if vuelos_con_reservas.exists():
            ocupaciones = [vuelo.porcentaje_ocupacion() for vuelo in vuelos_con_reservas]
            ocupacion_promedio = sum(ocupaciones) / len(ocupaciones)
        
        return Response({
            'vuelos': {
                'total': total_vuelos,
                'activos': vuelos_activos,
                'hoy': vuelos_hoy
            },
            'reservas': {
                'total': total_reservas,
                'confirmadas': reservas_confirmadas,
                'pagadas': reservas_pagadas,
                'canceladas': reservas_canceladas
            },
            'pasajeros': {
                'total': total_pasajeros
            },
            'financiero': {
                'ingresos_totales': ingresos_totales,
                'ocupacion_promedio': round(ocupacion_promedio, 2)
            },
            'fecha_reporte': timezone.now().isoformat()
        })