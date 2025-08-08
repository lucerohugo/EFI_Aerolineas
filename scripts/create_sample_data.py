"""
Script para crear datos de ejemplo en el sistema de aerolíneas
Ejecutar: python scripts/create_sample_data.py
"""
import os
import sys
import django
from datetime import datetime, timedelta, date
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aerolineas_efi.settings')
django.setup()

from gestion.models import Avion, Vuelo, Pasajero, Reserva, Asiento, Boleto
from django.contrib.auth.models import User

def limpiar_datos_anteriores():
    """Limpiar datos anteriores si existen"""
    print("🧹 Limpiando datos anteriores...")
    
    # Eliminar en orden para evitar problemas de claves foráneas
    Boleto.objects.all().delete()
    Reserva.objects.all().delete()
    Asiento.objects.all().delete()
    Vuelo.objects.all().delete()
    Pasajero.objects.all().delete()
    Avion.objects.all().delete()
    
    # Mantener solo usuarios admin y usuario
    User.objects.exclude(username__in=['admin', 'usuario']).delete()
    
    print("✓ Datos anteriores eliminados")

def crear_usuarios():
    """Crear usuarios del sistema"""
    print("👥 Creando usuarios...")
    
    # Crear superusuario si no existe
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin', 
            email='admin@aerolineas.com', 
            password='admin123',
            first_name='Administrador',
            last_name='Sistema'
        )
        print("✓ Superusuario creado: admin/admin123")
    else:
        print("✓ Superusuario ya existe: admin/admin123")
    
    # Crear usuario regular
    if not User.objects.filter(username='usuario').exists():
        User.objects.create_user(
            username='usuario', 
            email='usuario@email.com', 
            password='usuario123',
            first_name='Juan', 
            last_name='Pérez'
        )
        print("✓ Usuario regular creado: usuario/usuario123")
    else:
        print("✓ Usuario regular ya existe: usuario/usuario123")

def crear_aviones():
    """Crear flota de aviones"""
    print("✈️ Creando flota de aviones...")
    
    aviones_data = [
        {'modelo': 'Boeing 737-800', 'filas': 30, 'columnas': 6},
        {'modelo': 'Airbus A320', 'filas': 28, 'columnas': 6},
        {'modelo': 'Boeing 777-300', 'filas': 42, 'columnas': 9},
        {'modelo': 'Embraer E190', 'filas': 20, 'columnas': 4},
        {'modelo': 'Airbus A330', 'filas': 38, 'columnas': 8},
        {'modelo': 'Boeing 787-9', 'filas': 35, 'columnas': 9},
    ]
    
    aviones = []
    for avion_data in aviones_data:
        avion = Avion.objects.create(**avion_data)
        aviones.append(avion)
        print(f"✓ Avión creado: {avion.modelo} ({avion.capacidad} asientos)")
    
    return aviones

def crear_vuelos(aviones):
    """Crear vuelos para los próximos días"""
    print("🛫 Creando vuelos...")
    
    # Rutas principales de Argentina
    rutas = [
        ('Buenos Aires', 'Córdoba'),
        ('Buenos Aires', 'Mendoza'),
        ('Buenos Aires', 'Bariloche'),
        ('Buenos Aires', 'Salta'),
        ('Buenos Aires', 'Rosario'),
        ('Buenos Aires', 'Mar del Plata'),
        ('Buenos Aires', 'Tucumán'),
        ('Buenos Aires', 'Neuquén'),
        ('Córdoba', 'Mendoza'),
        ('Córdoba', 'Bariloche'),
        ('Mendoza', 'Bariloche'),
        ('Salta', 'Tucumán'),
    ]
    
    vuelos_creados = []
    
    # Crear vuelos para los próximos 45 días
    for dia in range(45):
        fecha_base = datetime.now() + timedelta(days=dia)
        
        # Crear 3-5 vuelos por día
        vuelos_del_dia = min(5, len(rutas)) if dia < 30 else min(3, len(rutas))
        
        for i in range(vuelos_del_dia):
            origen, destino = rutas[i % len(rutas)]
            avion = aviones[i % len(aviones)]
            
            # Vuelo de ida (mañana)
            hora_salida = 6 + (i * 3) + (dia % 4)  # Distribuir horarios
            fecha_salida = fecha_base.replace(
                hour=hora_salida, 
                minute=0, 
                second=0, 
                microsecond=0
            )
            
            # Duración según distancia (simulada)
            duraciones = {
                ('Buenos Aires', 'Córdoba'): 1.5,
                ('Buenos Aires', 'Mendoza'): 2.0,
                ('Buenos Aires', 'Bariloche'): 2.5,
                ('Buenos Aires', 'Salta'): 2.2,
                ('Buenos Aires', 'Rosario'): 1.0,
                ('Buenos Aires', 'Mar del Plata'): 1.2,
                ('Buenos Aires', 'Tucumán'): 2.0,
                ('Buenos Aires', 'Neuquén'): 2.3,
            }
            
            duracion_horas = duraciones.get((origen, destino), 2.0)
            fecha_llegada = fecha_salida + timedelta(hours=duracion_horas)
            
            # Precio base según ruta y temporada
            precio_base = Decimal('12000')
            if 'Bariloche' in [origen, destino]:
                precio_base += Decimal('8000')  # Destino turístico
            if 'Mendoza' in [origen, destino]:
                precio_base += Decimal('5000')
            if dia < 7:  # Próximos 7 días más caros
                precio_base += Decimal('3000')
            
            # Agregar variación aleatoria
            precio_base += Decimal(str((dia * 200) % 5000))
            
            vuelo = Vuelo.objects.create(
                avion=avion,
                origen=origen,
                destino=destino,
                fecha_salida=fecha_salida,
                fecha_llegada=fecha_llegada,
                duracion=fecha_llegada - fecha_salida,
                precio_base=precio_base,
                estado='programado'
            )
            vuelos_creados.append(vuelo)
            
            # Vuelo de vuelta (tarde/noche)
            if i < 3:  # Solo algunos vuelos tienen vuelta el mismo día
                hora_vuelta = 14 + (i * 2) + (dia % 3)
                fecha_salida_vuelta = fecha_base.replace(
                    hour=hora_vuelta, 
                    minute=30, 
                    second=0, 
                    microsecond=0
                )
                fecha_llegada_vuelta = fecha_salida_vuelta + timedelta(hours=duracion_horas)
                
                vuelo_vuelta = Vuelo.objects.create(
                    avion=aviones[(i + 1) % len(aviones)],
                    origen=destino,
                    destino=origen,
                    fecha_salida=fecha_salida_vuelta,
                    fecha_llegada=fecha_llegada_vuelta,
                    duracion=fecha_llegada_vuelta - fecha_salida_vuelta,
                    precio_base=precio_base + Decimal('1000'),
                    estado='programado'
                )
                vuelos_creados.append(vuelo_vuelta)
    
    print(f"✓ {len(vuelos_creados)} vuelos creados")
    return vuelos_creados

def crear_pasajeros():
    """Crear pasajeros de ejemplo"""
    print("👤 Creando pasajeros...")
    
    pasajeros_data = [
        {
            'nombre': 'María', 'apellido': 'González',
            'documento': '12345678', 'tipo_documento': 'dni',
            'email': 'maria.gonzalez@email.com',
            'telefono': '+54 11 1234-5678',
            'fecha_nacimiento': date(1985, 3, 15)
        },
        {
            'nombre': 'Carlos', 'apellido': 'Rodríguez',
            'documento': '87654321', 'tipo_documento': 'dni',
            'email': 'carlos.rodriguez@email.com',
            'telefono': '+54 11 8765-4321',
            'fecha_nacimiento': date(1990, 7, 22)
        },
        {
            'nombre': 'Ana', 'apellido': 'Martínez',
            'documento': '11223344', 'tipo_documento': 'dni',
            'email': 'ana.martinez@email.com',
            'telefono': '+54 11 1122-3344',
            'fecha_nacimiento': date(1988, 12, 8)
        },
        {
            'nombre': 'Luis', 'apellido': 'López',
            'documento': 'AB123456', 'tipo_documento': 'pasaporte',
            'email': 'luis.lopez@email.com',
            'telefono': '+54 11 5566-7788',
            'fecha_nacimiento': date(1975, 5, 30)
        },
        {
            'nombre': 'Sofia', 'apellido': 'Fernández',
            'documento': '55667788', 'tipo_documento': 'dni',
            'email': 'sofia.fernandez@email.com',
            'telefono': '+54 11 5566-7788',
            'fecha_nacimiento': date(1992, 9, 12)
        },
        {
            'nombre': 'Diego', 'apellido': 'Morales',
            'documento': '99887766', 'tipo_documento': 'dni',
            'email': 'diego.morales@email.com',
            'telefono': '+54 11 9988-7766',
            'fecha_nacimiento': date(1983, 1, 25)
        },
        {
            'nombre': 'Valentina', 'apellido': 'Silva',
            'documento': 'CD789012', 'tipo_documento': 'pasaporte',
            'email': 'valentina.silva@email.com',
            'telefono': '+54 11 7890-1234',
            'fecha_nacimiento': date(1995, 11, 3)
        },
        {
            'nombre': 'Roberto', 'apellido': 'Herrera',
            'documento': '33445566', 'tipo_documento': 'dni',
            'email': 'roberto.herrera@email.com',
            'telefono': '+54 11 3344-5566',
            'fecha_nacimiento': date(1978, 4, 18)
        },
    ]
    
    pasajeros = []
    for pasajero_data in pasajeros_data:
        pasajero = Pasajero.objects.create(**pasajero_data)
        pasajeros.append(pasajero)
        print(f"✓ Pasajero creado: {pasajero.nombre_completo()}")
    
    return pasajeros

def crear_reservas(vuelos, pasajeros):
    """Crear reservas de ejemplo"""
    print("🎫 Creando reservas...")
    
    usuario = User.objects.get(username='usuario')
    reservas_creadas = 0
    
    # Crear reservas para los primeros vuelos
    vuelos_con_reservas = vuelos[:20]  # Solo los primeros 20 vuelos
    
    for i, vuelo in enumerate(vuelos_con_reservas):
        # Crear 1-5 reservas por vuelo
        num_reservas = min(len(pasajeros), (i % 5) + 1)
        
        for j in range(num_reservas):
            if j < len(pasajeros):
                pasajero = pasajeros[j]
                
                # Verificar que no exista ya una reserva
                if not Reserva.objects.filter(vuelo=vuelo, pasajero=pasajero).exists():
                    # Obtener un asiento disponible
                    asientos_disponibles = vuelo.avion.asientos.filter(
                        estado='disponible'
                    ).exclude(
                        reservas__vuelo=vuelo,
                        reservas__estado__in=['confirmada', 'pagada']
                    )
                    
                    if asientos_disponibles.exists():
                        asiento = asientos_disponibles.first()
                        
                        # Estados posibles para las reservas
                        estados = ['confirmada', 'pagada', 'pendiente']
                        estado = estados[j % len(estados)]
                        
                        reserva = Reserva.objects.create(
                            vuelo=vuelo,
                            pasajero=pasajero,
                            asiento=asiento,
                            precio=vuelo.precio_base,
                            estado=estado,
                            usuario=usuario
                        )
                        
                        # Crear boleto si la reserva está confirmada o pagada
                        if estado in ['confirmada', 'pagada']:
                            Boleto.objects.create(reserva=reserva)
                        
                        reservas_creadas += 1
    
    print(f"✓ {reservas_creadas} reservas creadas")

def mostrar_estadisticas():
    """Mostrar estadísticas del sistema"""
    print("\n📊 ESTADÍSTICAS DEL SISTEMA:")
    print("=" * 50)
    
    total_aviones = Avion.objects.count()
    total_vuelos = Vuelo.objects.count()
    total_pasajeros = Pasajero.objects.count()
    total_reservas = Reserva.objects.count()
    total_boletos = Boleto.objects.count()
    total_usuarios = User.objects.count()
    
    print(f"✈️  Aviones: {total_aviones}")
    print(f"🛫 Vuelos: {total_vuelos}")
    print(f"👥 Pasajeros: {total_pasajeros}")
    print(f"🎫 Reservas: {total_reservas}")
    print(f"🎟️  Boletos: {total_boletos}")
    print(f"👤 Usuarios: {total_usuarios}")
    
    # Estadísticas por estado
    print(f"\n📈 RESERVAS POR ESTADO:")
    for estado, nombre in Reserva.ESTADOS_RESERVA:
        count = Reserva.objects.filter(estado=estado).count()
        if count > 0:
            print(f"   {nombre}: {count}")
    
    # Vuelos próximos
    vuelos_proximos = Vuelo.objects.filter(
        fecha_salida__gte=datetime.now(),
        estado='programado'
    ).count()
    print(f"\n🕐 Vuelos próximos: {vuelos_proximos}")
    
    # Vuelos de hoy
    vuelos_hoy = Vuelo.objects.filter(
        fecha_salida__date=date.today()
    ).count()
    print(f"📅 Vuelos de hoy: {vuelos_hoy}")

def main():
    """Función principal"""
    print("🚀 CREANDO DATOS DE EJEMPLO PARA AEROEFI")
    print("=" * 50)
    
    try:
        # Limpiar datos anteriores
        limpiar_datos_anteriores()
        
        # Crear usuarios
        crear_usuarios()
        
        # Crear aviones
        aviones = crear_aviones()
        
        # Crear vuelos
        vuelos = crear_vuelos(aviones)
        
        # Crear pasajeros
        pasajeros = crear_pasajeros()
        
        # Crear reservas
        crear_reservas(vuelos, pasajeros)
        
        # Mostrar estadísticas
        mostrar_estadisticas()
        
        print("\n🎉 ¡DATOS DE EJEMPLO CREADOS EXITOSAMENTE!")
        print("=" * 50)
        print("\n🔑 CREDENCIALES DE ACCESO:")
        print("   👨‍💼 Administrador: admin / admin123")
        print("   👤 Usuario regular: usuario / usuario123")
        print("\n🌐 ACCESOS:")
        print("   🏠 Sistema: http://127.0.0.1:8000/")
        print("   ⚙️  Admin: http://127.0.0.1:8000/admin/")
        print("\n▶️  Para ejecutar el servidor:")
        print("   python manage.py runserver")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("Verifica que Django esté configurado correctamente.")
        sys.exit(1)

if __name__ == '__main__':
    main()


