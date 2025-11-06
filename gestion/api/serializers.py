"""
Serializers para la API REST de AeroEFI

Este módulo contiene todos los serializers necesarios para transformar
los modelos de Django en representaciones JSON para la API REST.
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from ..models import Vuelo, Pasajero, Reserva, Asiento, Avion, Boleto


class UserSerializer(serializers.ModelSerializer):
    """Serializer para el modelo User de Django"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class AvionSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Avion"""
    
    asientos_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Avion
        fields = ['id', 'modelo', 'capacidad', 'asientos_count']
        read_only_fields = ['id']
    
    def get_asientos_count(self, obj):
        """Retorna el número total de asientos del avión"""
        return obj.asientos.count()


class AsientoSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Asiento"""
    
    avion_modelo = serializers.CharField(source='avion.modelo', read_only=True)
    esta_disponible = serializers.SerializerMethodField()
    
    class Meta:
        model = Asiento
        fields = [
            'id', 'numero', 'fila', 'columna', 'tipo', 'estado',
            'avion', 'avion_modelo', 'esta_disponible'
        ]
        read_only_fields = ['id']
    
    def get_esta_disponible(self, obj):
        """Verifica si el asiento está disponible"""
        return obj.estado == 'disponible'


class AsientoSimpleSerializer(serializers.ModelSerializer):
    """Serializer simplificado para asientos (para usar en otros serializers)"""
    
    class Meta:
        model = Asiento
        fields = ['id', 'numero', 'fila', 'columna', 'tipo']


class VueloSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Vuelo"""
    
    avion_info = AvionSerializer(source='avion', read_only=True)
    asientos_disponibles_count = serializers.SerializerMethodField()
    porcentaje_ocupacion = serializers.SerializerMethodField()
    duracion_estimada = serializers.SerializerMethodField()
    
    class Meta:
        model = Vuelo
        fields = [
            'id', 'origen', 'destino', 
            'fecha_salida', 'fecha_llegada', 'precio_base', 
            'estado', 'avion', 'avion_info',
            'asientos_disponibles_count', 'porcentaje_ocupacion', 'duracion_estimada'
        ]
        read_only_fields = ['id']
    
    def get_asientos_disponibles_count(self, obj):
        """Retorna el número de asientos disponibles"""
        return obj.asientos_disponibles()
    
    def get_porcentaje_ocupacion(self, obj):
        """Retorna el porcentaje de ocupación del vuelo"""
        return obj.porcentaje_ocupacion()
    
    def get_duracion_estimada(self, obj):
        """Calcula la duración estimada del vuelo"""
        if obj.fecha_llegada and obj.fecha_salida:
            duracion = obj.fecha_llegada - obj.fecha_salida
            return str(duracion)
        return None
    
    def validate(self, data):
        """Validaciones personalizadas para el vuelo"""
        if 'fecha_salida' in data and 'fecha_llegada' in data:
            if data['fecha_salida'] >= data['fecha_llegada']:
                raise serializers.ValidationError(
                    "La fecha de salida debe ser anterior a la fecha de llegada"
                )
        
        if 'precio_base' in data and data['precio_base'] <= 0:
            raise serializers.ValidationError(
                "El precio base debe ser mayor a 0"
            )
        
        return data


class VueloSimpleSerializer(serializers.ModelSerializer):
    """Serializer simplificado para vuelos (para usar en otros serializers)"""
    
    class Meta:
        model = Vuelo
        fields = [
            'id', 'origen', 'destino', 
            'fecha_salida', 'fecha_llegada', 'precio_base', 'estado'
        ]


class PasajeroSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Pasajero"""
    
    reservas_count = serializers.SerializerMethodField()
    nombre_completo = serializers.SerializerMethodField()
    
    class Meta:
        model = Pasajero
        fields = [
            'id', 'nombre', 'apellido', 'nombre_completo', 'documento', 
            'tipo_documento', 'email', 'telefono', 'fecha_nacimiento',
            'reservas_count'
        ]
        read_only_fields = ['id', 'nombre_completo', 'reservas_count']
    
    def get_reservas_count(self, obj):
        """Retorna el número de reservas del pasajero"""
        return obj.reservas.count()
    
    def get_nombre_completo(self, obj):
        """Retorna el nombre completo del pasajero"""
        return f"{obj.nombre} {obj.apellido}"
    
    def validate_email(self, value):
        """Valida que el email tenga un formato correcto"""
        if not value:
            raise serializers.ValidationError("El email es obligatorio")
        return value
    
    def validate_documento(self, value):
        """Valida que el documento no esté duplicado"""
        if self.instance and self.instance.documento == value:
            return value  # No cambió, permitir
            
        if Pasajero.objects.filter(documento=value).exists():
            raise serializers.ValidationError(
                "Ya existe un pasajero con este número de documento"
            )
        return value


class BoletoSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Boleto"""
    
    reserva_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Boleto
        fields = [
            'id', 'codigo_barra', 'fecha_emision', 'reserva', 'reserva_info'
        ]
        read_only_fields = ['id', 'codigo_barra', 'fecha_emision']
    
    def get_reserva_info(self, obj):
        """Información básica de la reserva asociada"""
        return {
            'codigo_reserva': obj.reserva.codigo_reserva,
            'vuelo': f"{obj.reserva.vuelo.origen} → {obj.reserva.vuelo.destino}",
            'fecha_vuelo': obj.reserva.vuelo.fecha_salida,
            'pasajero': f"{obj.reserva.pasajero.nombre} {obj.reserva.pasajero.apellido}",
            'asiento': obj.reserva.asiento.numero if obj.reserva.asiento else None
        }


class ReservaSerializer(serializers.ModelSerializer):
    """Serializer completo para el modelo Reserva"""
    
    vuelo_info = VueloSimpleSerializer(source='vuelo', read_only=True)
    pasajero_info = PasajeroSerializer(source='pasajero', read_only=True)
    asiento_info = AsientoSimpleSerializer(source='asiento', read_only=True)
    usuario_info = UserSerializer(source='usuario', read_only=True)
    boleto_info = BoletoSerializer(source='boleto', read_only=True)
    
    class Meta:
        model = Reserva
        fields = [
            'id', 'codigo_reserva', 'fecha_reserva', 'estado', 'precio',
            'metodo_pago', 'vuelo', 'vuelo_info', 'pasajero', 'pasajero_info',
            'asiento', 'asiento_info', 'usuario', 'usuario_info', 'boleto_info'
        ]
        read_only_fields = ['id', 'codigo_reserva', 'fecha_reserva']
    
    def validate(self, data):
        """Validaciones personalizadas para la reserva"""
        # Validar que el asiento esté disponible
        if 'asiento' in data and 'vuelo' in data:
            asiento = data['asiento']
            vuelo = data['vuelo']
            
            # Verificar que el asiento pertenece al avión del vuelo
            if asiento.avion != vuelo.avion:
                raise serializers.ValidationError(
                    "El asiento seleccionado no pertenece a este vuelo"
                )
            
            # Verificar que el asiento esté disponible
            if asiento.estado != 'disponible':
                raise serializers.ValidationError(
                    "El asiento seleccionado no está disponible"
                )
            
            # Verificar que no haya otra reserva confirmada para este asiento y vuelo
            reservas_conflicto = Reserva.objects.filter(
                vuelo=vuelo,
                asiento=asiento,
                estado__in=['confirmada', 'pagada']
            )
            
            if self.instance:
                reservas_conflicto = reservas_conflicto.exclude(id=self.instance.id)
            
            if reservas_conflicto.exists():
                raise serializers.ValidationError(
                    "Ya existe una reserva confirmada para este asiento"
                )
        
        # Validar que el pasajero no tenga otra reserva para el mismo vuelo
        if 'pasajero' in data and 'vuelo' in data:
            reservas_pasajero = Reserva.objects.filter(
                vuelo=data['vuelo'],
                pasajero=data['pasajero'],
                estado__in=['confirmada', 'pagada']
            )
            
            if self.instance:
                reservas_pasajero = reservas_pasajero.exclude(id=self.instance.id)
            
            if reservas_pasajero.exists():
                raise serializers.ValidationError(
                    "El pasajero ya tiene una reserva para este vuelo"
                )
        
        return data


class ReservaCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear reservas (campos mínimos requeridos)"""
    
    class Meta:
        model = Reserva
        fields = [
            'vuelo', 'pasajero', 'asiento', 'metodo_pago', 'usuario'
        ]
    
    def validate(self, data):
        """Reutilizar validaciones del serializer principal"""
        serializer = ReservaSerializer()
        return serializer.validate(data)


class ReservaUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar el estado de reservas"""
    
    class Meta:
        model = Reserva
        fields = ['estado']
    
    def validate_estado(self, value):
        """Validar transiciones de estado permitidas"""
        if self.instance:
            estado_actual = self.instance.estado
            
            # Definir transiciones válidas
            transiciones_validas = {
                'pendiente': ['confirmada', 'cancelada'],
                'confirmada': ['pagada', 'cancelada'],
                'pagada': ['cancelada'],
                'cancelada': []  # No se puede cambiar desde cancelada
            }
            
            if value not in transiciones_validas.get(estado_actual, []):
                raise serializers.ValidationError(
                    f"No se puede cambiar el estado de '{estado_actual}' a '{value}'"
                )
        
        return value


# Serializer para reportes
class ReporteVueloSerializer(serializers.Serializer):
    """Serializer para el reporte de pasajeros por vuelo"""
    
    vuelo_id = serializers.IntegerField()
    vuelo_info = VueloSimpleSerializer(read_only=True)
    total_pasajeros = serializers.IntegerField(read_only=True)
    reservas = ReservaSerializer(many=True, read_only=True)


class ReportePasajeroSerializer(serializers.Serializer):
    """Serializer para el reporte de reservas por pasajero"""
    
    pasajero_id = serializers.IntegerField()
    pasajero_info = PasajeroSerializer(read_only=True)
    reservas_activas = ReservaSerializer(many=True, read_only=True)
    total_reservas_activas = serializers.IntegerField(read_only=True)