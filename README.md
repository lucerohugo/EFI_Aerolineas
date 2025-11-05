# AeroEFI - Sistema de Gestión de Aerolíneas
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

## Créditos
<<<<<<< HEAD
Desarrollado por Cugiani, Lucero y Perotti 
2025
=======
Desarrollado por Lucero y Perotti 

---
>>>>>>> 317f0e2 (EFI casi terminada, puliendo cosas del FRONT/ 5/11/25)

