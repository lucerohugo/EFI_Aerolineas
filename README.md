# AeroEFI - Sistema de Gestión de Aerolíneas
# Parte 1 ------------------------------------------------------------------------------------
## DSW-2025-Ingeniería de Software - Matías Lucero

AeroEFI es una aplicación web desarrollada en Django para la gestión integral de vuelos, reservas y pasajeros de una aerolínea. Permite administrar vuelos, gestionar reservas, consultar pasajeros y realizar búsquedas de manera eficiente y sencilla.

## Características principales
- Registro e inicio de sesión de usuarios 
- Panel de control con estadísticas de vuelos, reservas y pasajeros
- Gestión de vuelos: listado, búsqueda y detalle
- Gestión de reservas: creación, consulta, cancelación
- Gestión de pasajeros: listado y detalle
- Interfaz moderna y responsiva (Bootstrap 5, FontAwesome, Bootstrap Icons)
- Notificaciones emergentes (toasts) para acciones importantes
- Soporte multilenguaje (español/inglés)

## Tecnologías utilizadas
- Python 3.12
- Django 4.2
- Bootstrap 5
- SQLite3 

## Instalación y uso rápido
1. Clona el repositorio:
   ```bash
   git clone https://github.com/lucerohugo/EFI_Aerolineas.git
   cd EFI_Aerolineas
   ```
2. Crea y activa un entorno virtual:
   ```bash
   python3 -m venv .enviroment
   source .enviroment/bin/activate
   ```
3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Aplica migraciones y carga datos de ejemplo (opcional):
   ```bash
   python manage.py migrate
   python scripts/create_sample_data.py
   ```
5. Ejecuta el servidor de desarrollo:
   ```bash
   python manage.py runserver
   ```
6. Accede a la app en [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Comandos útiles
- `python manage.py createsuperuser` — Crear usuario administrador
- `python manage.py makemigrations` — Crear nuevas migraciones
- `python manage.py migrate` — Aplicar migraciones
- `python manage.py runserver` — Iniciar servidor local

# AeroEFI API REST - Documentación
# Parte 2 -----------------------------------------------------------------------------------

## Descripción

API REST completa para el Sistema de Gestión de Aerolíneas AeroEFI desarrollada con Django Rest Framework (DRF). 

Esta API permite a terceros (aplicaciones móviles, portales externos) acceder de forma segura y documentada a las funcionalidades del sistema de gestión de aerolíneas.

## 🚀 Características Principales

- **Autenticación segura** con JWT (JSON Web Tokens)
- **Permisos granulares** basados en roles de usuario
- **Documentación automática** con Swagger/OpenAPI
- **Filtrado avanzado** y paginación
- **Validaciones robustas** y manejo de errores consistente
- **Endpoints RESTful** siguiendo mejores prácticas

## 📋 Funcionalidades

### 🛫 Gestión de Vuelos
- ✅ Listar todos los vuelos disponibles
- ✅ Obtener detalle de un vuelo
- ✅ Filtrar vuelos por origen, destino y fecha
- ✅ Crear, editar y eliminar vuelos (solo administradores)

### 👥 Gestión de Pasajeros
- ✅ Registrar un pasajero
- ✅ Consultar información de un pasajero
- ✅ Listar reservas asociadas a un pasajero

### 🎫 Sistema de Reservas
- ✅ Crear una reserva para un pasajero en un vuelo
- ✅ Seleccionar asiento disponible
- ✅ Cambiar estado de una reserva (confirmar, cancelar)

### ✈️ Gestión de Aviones y Asientos
- ✅ Listar aviones registrados
- ✅ Obtener layout de asientos de un avión
- ✅ Verificar disponibilidad de un asiento en un vuelo

### 🎟️ Boletos
- ✅ Generar boleto a partir de una reserva confirmada
- ✅ Consultar información de un boleto por código

### 📊 Reportes
- ✅ Listado de pasajeros por vuelo
- ✅ Reservas activas de un pasajero
- ✅ Estadísticas generales del sistema

## 🔐 Autenticación

La API utiliza JWT (JSON Web Tokens) para la autenticación. 

### Obtener Token

```bash
POST /api/v1/auth/login/
Content-Type: application/json

{
    "username": "tu_usuario",
    "password": "tu_contraseña"
}
```

**Respuesta:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Usar Token

Incluir el token en el header de Authorization:

```bash
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Renovar Token

```bash
POST /api/v1/auth/refresh/
Content-Type: application/json

{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## 🛣️ Endpoints Principales

### Base URL
```
http://localhost:8000/api/v1/
```

### Vuelos
- `GET /vuelos/` - Listar vuelos
- `POST /vuelos/` - Crear vuelo (admin)
- `GET /vuelos/{id}/` - Detalle de vuelo
- `PUT /vuelos/{id}/` - Actualizar vuelo (admin)
- `DELETE /vuelos/{id}/` - Eliminar vuelo (admin)
- `GET /vuelos/{id}/asientos/` - Mapa de asientos del vuelo
- `GET /vuelos/buscar/` - Búsqueda avanzada

### Pasajeros
- `GET /pasajeros/` - Listar pasajeros
- `POST /pasajeros/` - Registrar pasajero
- `GET /pasajeros/{id}/` - Detalle de pasajero
- `GET /pasajeros/{id}/reservas/` - Reservas del pasajero
- `GET /pasajeros/buscar_por_documento/` - Buscar por documento

### Reservas
- `GET /reservas/` - Listar reservas del usuario
- `POST /reservas/` - Crear reserva
- `GET /reservas/{id}/` - Detalle de reserva
- `PATCH /reservas/{id}/cambiar_estado/` - Cambiar estado
- `GET /reservas/buscar_por_codigo/` - Buscar por código

### Aviones
- `GET /aviones/` - Listar aviones
- `GET /aviones/{id}/` - Detalle de avión
- `GET /aviones/{id}/asientos/` - Layout de asientos
- `GET /aviones/{id}/verificar_disponibilidad/` - Verificar disponibilidad

### Boletos
- `GET /boletos/` - Listar boletos del usuario
- `GET /boletos/{id}/` - Detalle de boleto
- `POST /boletos/generar_desde_reserva/` - Generar boleto
- `GET /boletos/buscar_por_codigo/` - Buscar por código

### Reportes
- `GET /reportes/pasajeros_por_vuelo/` - Pasajeros por vuelo
- `GET /reportes/reservas_activas_pasajero/` - Reservas activas
- `GET /reportes/estadisticas_generales/` - Estadísticas (admin)

## 🔍 Filtros y Búsqueda

### Vuelos
```bash
# Filtrar por origen y destino
GET /api/v1/vuelos/?origen=Buenos Aires&destino=Córdoba

# Filtrar por fecha
GET /api/v1/vuelos/?fecha_salida=2025-12-25

# Filtrar por rango de fechas
GET /api/v1/vuelos/?fecha_desde=2025-12-01&fecha_hasta=2025-12-31

# Búsqueda por texto
GET /api/v1/vuelos/?search=Buenos Aires

# Ordenar
GET /api/v1/vuelos/?ordering=fecha_salida
```

### Reservas
```bash
# Filtrar por estado
GET /api/v1/reservas/?estado=confirmada

# Buscar por código de reserva
GET /api/v1/reservas/?search=ABC123

# Filtrar por método de pago
GET /api/v1/reservas/?metodo_pago=tarjeta
```

## 👮 Permisos

### Tipos de Usuarios

1. **Usuarios Regulares**: 
   - Pueden ver vuelos y aviones
   - Pueden crear y gestionar sus propias reservas
   - Pueden ver solo sus propios pasajeros y boletos

2. **Administradores**: 
   - Acceso completo a todos los recursos
   - Pueden crear, editar y eliminar vuelos
   - Pueden ver todas las reservas y generar reportes

### Matriz de Permisos

| Recurso | Lectura | Crear | Actualizar | Eliminar |
|---------|---------|--------|------------|----------|
| Vuelos | Todos | Admin | Admin | Admin |
| Pasajeros | Propios/Admin | Todos | Propios/Admin | Propios/Admin |
| Reservas | Propias/Admin | Todos | Propias/Admin | Propias/Admin |
| Aviones | Todos | - | - | - |
| Boletos | Propios/Admin | Automático | - | - |
| Reportes | Limitado/Admin | - | - | - |

## 📖 Documentación Interactiva

### Swagger UI
Accede a la documentación interactiva en:
```
http://localhost:8000/swagger/
```

### ReDoc
Documentación alternativa en:
```
http://localhost:8000/redoc/
```

### Schema JSON/YAML
```
http://localhost:8000/swagger.json
http://localhost:8000/swagger.yaml
```

## 🚨 Códigos de Estado HTTP

- `200 OK` - Éxito
- `201 Created` - Recurso creado
- `400 Bad Request` - Datos inválidos
- `401 Unauthorized` - No autenticado
- `403 Forbidden` - Sin permisos
- `404 Not Found` - Recurso no encontrado
- `422 Unprocessable Entity` - Error de lógica de negocio
- `500 Internal Server Error` - Error del servidor

## 📝 Ejemplos de Uso

### Crear una Reserva

1. **Buscar vuelos disponibles:**
```bash
GET /api/v1/vuelos/buscar/?origen=Buenos Aires&destino=Córdoba&fecha_salida=2025-12-25
```

2. **Ver asientos disponibles:**
```bash
GET /api/v1/vuelos/{vuelo_id}/asientos/
```

3. **Crear o obtener pasajero:**
```bash
POST /api/v1/pasajeros/
{
    "nombre": "Juan",
    "apellido": "Pérez",
    "documento": "12345678",
    "tipo_documento": "DNI",
    "email": "juan@email.com"
}
```

4. **Crear reserva:**
```bash
POST /api/v1/reservas/
{
    "vuelo": 1,
    "pasajero": 1,
    "asiento": 5,
    "metodo_pago": "tarjeta"
}
```

### Consultar una Reserva

```bash
GET /api/v1/reservas/buscar_por_codigo/?codigo=ABC123
```

### Generar Boleto

```bash
POST /api/v1/boletos/generar_desde_reserva/
{
    "reserva_id": 1
}
```

## 🔧 Configuración para Desarrollo

1. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

2. **Configurar base de datos:**
```bash
python manage.py migrate
```

3. **Crear superusuario:**
```bash
python manage.py createsuperuser
```

4. **Ejecutar servidor:**
```bash
python manage.py runserver
```

5. **Acceder a la API:**
```
http://localhost:8000/api/v1/
```

## 🔒 Configuración de Seguridad

### CORS (Cross-Origin Resource Sharing)
Para producción, configurar los dominios permitidos en `settings.py`:

```python
CORS_ALLOWED_ORIGINS = [
    "https://tu-frontend.com",
]
```

### Rate Limiting
Se recomienda implementar rate limiting para prevenir abuso:

```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '1000/hour'
    }
}
```

## 🐛 Solución de Problemas Comunes

### Error 401 - Unauthorized
- Verificar que el token sea válido
- Verificar formato del header: `Authorization: Bearer <token>`

### Error 403 - Forbidden
- Verificar permisos del usuario
- Los usuarios regulares solo pueden acceder a sus propios recursos

### Error 400 - Bad Request
- Verificar formato de los datos enviados
- Revisar validaciones en los serializers

## 📞 Soporte

Para reportar bugs o solicitar nuevas funcionalidades, crear un issue en el repositorio del proyecto.

## 📄 Licencia

MIT License - Ver archivo LICENSE para más detalles.

---

**Desarrollado con ❤️ usando Django Rest Framework por Lucero/Cugiani/Perotti**

