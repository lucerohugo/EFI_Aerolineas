from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
def login_view(request):
    from django.contrib.auth.forms import AuthenticationForm
    login_form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and 'username' in request.POST:
        if login_form.is_valid():
            user = login_form.get_user()
            auth_login(request, user)
            return redirect('home')
    return render(request, 'registration/login.html', {'form': login_form})

from django.views.decorators.csrf import csrf_protect
@csrf_protect
def registro_view(request):
    registro_errores = []
    registro_exito = False
    if request.method == 'POST':
        first_name = request.POST.get('reg_first_name', '').strip()
        last_name = request.POST.get('reg_last_name', '').strip()
        username = request.POST.get('reg_username', '').strip()
        email = request.POST.get('reg_email', '').strip()
        password1 = request.POST.get('reg_password1', '')
        password2 = request.POST.get('reg_password2', '')
        # Validaciones básicas
        if not all([first_name, last_name, username, email, password1, password2]):
            registro_errores.append('Todos los campos son obligatorios.')
        if password1 != password2:
            registro_errores.append('Las contraseñas no coinciden.')
        if User.objects.filter(username=username).exists():
            registro_errores.append('El usuario ya existe.')
        if User.objects.filter(email=email).exists():
            registro_errores.append('El email ya está registrado.')
        if not registro_errores:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name
            )
            user.is_staff = False
            user.is_superuser = False
            user.save()
            # Login automático y redirección
            from django.contrib.auth import login as auth_login
            auth_login(request, user)
            from django.contrib import messages
            messages.success(request, '¡Usuario creado exitosamente! Bienvenido/a.')
            from django.shortcuts import redirect
            return redirect('home')
    return render(request, 'registration/registro.html', {
        'registro_errores': registro_errores,
        'registro_exito': registro_exito,
    })

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, date
from .models import Vuelo, Pasajero, Reserva, Asiento, Boleto
from .forms import PasajeroForm, ReservaForm, BusquedaVueloForm

def home(request):
    """Vista principal del sistema"""
    vuelos_proximos = Vuelo.objects.filter(
        fecha_salida__gte=timezone.now(),
        estado='programado'
    ).order_by('fecha_salida')[:5]

    total_vuelos = Vuelo.objects.count()
    total_pasajeros = Pasajero.objects.count()
    total_reservas = Reserva.objects.count()
    vuelos_hoy = Vuelo.objects.filter(fecha_salida__date=date.today()).count()

    context = {
        'vuelos_proximos': vuelos_proximos,
        'total_vuelos': total_vuelos,
        'total_pasajeros': total_pasajeros,
        'total_reservas': total_reservas,
        'vuelos_hoy': vuelos_hoy,
    }
    return render(request, 'gestion/home.html', context)

def buscar_vuelos(request):
    """Vista para buscar vuelos disponibles"""
    vuelos = []
    from .models import Vuelo
    if request.method == 'POST':
        # Obtener origen y destino seleccionados para filtrar fechas
        post_data = request.POST.copy()
        origen = post_data.get('origen', '')
        destino = post_data.get('destino', '')
        fechas_disponibles = []
        if origen and destino:
            vuelos_filtrados = Vuelo.objects.filter(estado='programado', origen=origen, destino=destino)
            fechas_disponibles = sorted(set(v.fecha_salida.date() for v in vuelos_filtrados))
            post_data = post_data.copy()
            # Si la fecha seleccionada no está en las opciones, limpiar
            if post_data.get('fecha_salida') not in [f.strftime('%Y-%m-%d') for f in fechas_disponibles]:
                post_data['fecha_salida'] = ''
        form = BusquedaVueloForm(post_data)
        # Sobrescribir las opciones de fecha según origen/destino
        if origen and destino:
            form.fields['fecha_salida'].choices = [('', '---------')] + [ (f.strftime('%Y-%m-%d'), f.strftime('%d/%m/%Y')) for f in fechas_disponibles ]
        if form.is_valid():
            fecha_salida = form.cleaned_data['fecha_salida']
            # Convertir fecha_salida a date si es string
            if isinstance(fecha_salida, str):
                from datetime import datetime
                try:
                    fecha_salida = datetime.strptime(fecha_salida, '%Y-%m-%d').date()
                except Exception:
                    fecha_salida = None
            filtros = {
                'origen': origen,
                'destino': destino,
                'estado': 'programado',
            }
            if fecha_salida:
                filtros['fecha_salida__date'] = fecha_salida
            vuelos = Vuelo.objects.filter(**filtros).distinct().order_by('fecha_salida')
    else:
        form = BusquedaVueloForm()
    context = {
        'form': form,
        'vuelos': vuelos,
    }
    return render(request, 'gestion/buscar_vuelos.html', context)

def detalle_vuelo(request, vuelo_id):
    """Vista detallada de un vuelo específico"""
    vuelo = get_object_or_404(Vuelo, id=vuelo_id)

    # Obtener información de asientos
    asientos = vuelo.avion.asientos.all().order_by('fila', 'columna')
    reservas_vuelo = Reserva.objects.filter(
        vuelo=vuelo,
        estado__in=['confirmada', 'pagada']
    ).select_related('asiento')
    asientos_reservados = {reserva.asiento.id for reserva in reservas_vuelo}

    # Organizar asientos por fila
    asientos_por_fila = {}
    for asiento in asientos:
        if asiento.fila not in asientos_por_fila:
            asientos_por_fila[asiento.fila] = []
        asiento.reservado = asiento.id in asientos_reservados
        asientos_por_fila[asiento.fila].append(asiento)

    if request.method == 'POST' and request.user.is_authenticated:
        asiento_id = request.POST.get('asiento_id')
        metodo_pago = request.POST.get('metodo_pago')
        if not asiento_id or not metodo_pago:
            messages.error(request, 'Debes seleccionar un asiento y un método de pago.')
        else:
            try:
                asiento = Asiento.objects.get(id=asiento_id, avion=vuelo.avion, estado='disponible')
            except Asiento.DoesNotExist:
                messages.error(request, 'El asiento seleccionado no está disponible.')
            else:
                # Verificar que el asiento no esté reservado
                if Reserva.objects.filter(vuelo=vuelo, asiento=asiento, estado__in=['confirmada', 'pagada']).exists():
                    messages.error(request, 'El asiento ya fue reservado.')
                else:
                    # Crear reserva con método de pago
                    reserva = Reserva.objects.create(
                        vuelo=vuelo,
                        pasajero=request.user.pasajero if hasattr(request.user, 'pasajero') else None,
                        asiento=asiento,
                        estado='confirmada',
                        precio=vuelo.precio_base,
                        usuario=request.user,
                        metodo_pago=metodo_pago
                    )
                    asiento.estado = 'reservado'
                    asiento.save()
                    Boleto.objects.create(reserva=reserva)
                    messages.success(request, f'¡Reserva exitosa! Asiento {asiento.numero} reservado y pago por {"tarjeta" if metodo_pago=="tarjeta" else "efectivo"}.')

    context = {
        'vuelo': vuelo,
        'asientos_por_fila': asientos_por_fila,
        'asientos_disponibles': vuelo.asientos_disponibles(),
        'porcentaje_ocupacion': vuelo.porcentaje_ocupacion(),
    }
    return render(request, 'gestion/detalle_vuelo.html', context)

@login_required
def crear_reserva(request, vuelo_id):
    """Vista para crear una nueva reserva"""
    vuelo = get_object_or_404(Vuelo, id=vuelo_id)
    
    # Obtener información de asientos para el mapa visual
    asientos = vuelo.avion.asientos.all().order_by('fila', 'columna')
    reservas_vuelo = Reserva.objects.filter(
        vuelo=vuelo,
        estado__in=['confirmada', 'pagada']
    ).select_related('asiento')
    asientos_reservados = {reserva.asiento.id for reserva in reservas_vuelo}
    asientos_por_fila = {}
    for asiento in asientos:
        if asiento.fila not in asientos_por_fila:
            asientos_por_fila[asiento.fila] = []
        asiento.reservado = asiento.id in asientos_reservados
        asientos_por_fila[asiento.fila].append(asiento)

    asiento_id_preseleccionado = request.GET.get('asiento')
    reserva_exitosa_codigo = request.session.pop('reserva_exitosa_codigo', None)
    if request.method == 'POST':
        print('DEBUG: POST recibido en crear_reserva')
        pasajero_form = PasajeroForm(request.POST)
        reserva_form = ReservaForm(request.POST, vuelo_id=vuelo_id)
        print('DEBUG: pasajero_form valido?', pasajero_form.is_valid())
        print('DEBUG: reserva_form valido?', reserva_form.is_valid())
        if pasajero_form.is_valid() and reserva_form.is_valid():
            # Limitar a 5 reservas por vuelo, eliminar solo las más antiguas si ya hay 5
            reservas_vuelo = Reserva.objects.filter(vuelo=vuelo).order_by('fecha_reserva')
            if reservas_vuelo.count() >= 5:
                reservas_a_eliminar = reservas_vuelo[:reservas_vuelo.count() - 4]
                for r in reservas_a_eliminar:
                    if hasattr(r, 'boleto'):
                        r.boleto.delete()
                    r.delete()
            documento = pasajero_form.cleaned_data['documento']
            pasajero, created = Pasajero.objects.get_or_create(
                documento=documento,
                defaults=pasajero_form.cleaned_data
            )
            print('DEBUG: Pasajero', pasajero, 'Creado:', created)
            if Reserva.objects.filter(vuelo=vuelo, pasajero=pasajero).exists():
                messages.error(request, 'Este pasajero ya tiene una reserva para este vuelo.')
                return redirect('detalle_vuelo', vuelo_id=vuelo.id)
            # Asignar asiento seleccionado manualmente si viene del input hidden
            asiento_id = request.POST.get('asiento')
            if asiento_id:
                try:
                    asiento = Asiento.objects.get(id=asiento_id, avion=vuelo.avion, estado='disponible')
                except Asiento.DoesNotExist:
                    messages.error(request, 'El asiento seleccionado no está disponible.')
                    return redirect('crear_reserva', vuelo_id=vuelo.id)
                reserva = reserva_form.save(commit=False)
                reserva.vuelo = vuelo
                reserva.pasajero = pasajero
                reserva.precio = vuelo.precio_base
                reserva.usuario = request.user
                reserva.estado = 'confirmada'
                reserva.asiento = asiento
                reserva.save()
                print('DEBUG: Reserva creada:', reserva)
                asiento.estado = 'reservado'
                asiento.save()
                Boleto.objects.create(reserva=reserva)
                # Guardar el código de reserva en la sesión para mostrarlo en el modal
                request.session['reserva_exitosa_codigo'] = reserva.codigo_reserva
                return redirect('crear_reserva', vuelo_id=vuelo.id)
            else:
                messages.error(request, 'Debe seleccionar un asiento.')
                return redirect('crear_reserva', vuelo_id=vuelo.id)
    else:
        pasajero_form = PasajeroForm()
        if asiento_id_preseleccionado:
            reserva_form = ReservaForm(vuelo_id=vuelo_id, initial={'asiento': asiento_id_preseleccionado})
            reserva_form.fields['asiento'].widget.attrs['readonly'] = True
            reserva_form.fields['asiento'].widget.attrs['disabled'] = True
        else:
            reserva_form = ReservaForm(vuelo_id=vuelo_id)

    context = {
        'vuelo': vuelo,
        'pasajero_form': pasajero_form,
        'reserva_form': reserva_form,
        'asientos_por_fila': asientos_por_fila,
        'asientos_reservados': asientos_reservados,
        'reserva_exitosa_codigo': reserva_exitosa_codigo,
    }
    return render(request, 'gestion/crear_reserva.html', context)

    context = {
        'vuelo': vuelo,
        'pasajero_form': pasajero_form,
        'reserva_form': reserva_form,
        'asientos_por_fila': asientos_por_fila,
        'asientos_reservados': asientos_reservados,
    }
    return render(request, 'gestion/crear_reserva.html', context)

def detalle_reserva(request, reserva_id):
    """Vista detallada de una reserva"""
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    context = {
        'reserva': reserva,
    }
    return render(request, 'gestion/detalle_reserva.html', context)

def lista_vuelos(request):
    """Vista para listar todos los vuelos"""
    # Filtros con opciones precargadas
    origen = request.GET.get('origen', '')
    destino = request.GET.get('destino', '')
    estado = request.GET.get('estado', '')

    # Obtener todos los origenes y destinos únicos de vuelos
    origenes = Vuelo.objects.values_list('origen', flat=True).distinct().order_by('origen')
    destinos = Vuelo.objects.values_list('destino', flat=True).distinct().order_by('destino')

    vuelos_list = Vuelo.objects.all().order_by('-fecha_salida')
    if origen:
        vuelos_list = vuelos_list.filter(origen=origen)
    if destino:
        vuelos_list = vuelos_list.filter(destino=destino)
    if estado:
        vuelos_list = vuelos_list.filter(estado=estado)

    # Paginación
    paginator = Paginator(vuelos_list, 10)
    page_number = request.GET.get('page')
    vuelos = paginator.get_page(page_number)

    context = {
        'vuelos': vuelos,
        'estados_vuelo': Vuelo.ESTADOS_VUELO,
        'origenes': origenes,
        'destinos': destinos,
        'origen_seleccionado': origen,
        'destino_seleccionado': destino,
        'estado_seleccionado': estado,
    }
    return render(request, 'gestion/lista_vuelos.html', context)

@login_required
def lista_reservas(request):
    """Vista para listar reservas del usuario"""
    if request.user.is_staff:
        reservas_list = Reserva.objects.all().order_by('-fecha_reserva')
    else:
        reservas_list = Reserva.objects.filter(usuario=request.user).order_by('-fecha_reserva')
    
    # Filtros
    estado = request.GET.get('estado')
    codigo = request.GET.get('codigo')
    
    if estado:
        reservas_list = reservas_list.filter(estado=estado)
    if codigo:
        reservas_list = reservas_list.filter(codigo_reserva__icontains=codigo)
    
    # Paginación
    paginator = Paginator(reservas_list, 10)
    page_number = request.GET.get('page')
    reservas = paginator.get_page(page_number)
    
    context = {
        'reservas': reservas,
        'estados_reserva': Reserva.ESTADOS_RESERVA,
    }
    return render(request, 'gestion/lista_reservas.html', context)

def lista_pasajeros(request):
    """Vista para listar pasajeros"""
    pasajeros_list = Pasajero.objects.all().order_by('apellido', 'nombre')
    
    # Filtros
    nombre = request.GET.get('nombre')
    documento = request.GET.get('documento')
    
    if nombre:
        from django.db.models import Q
        pasajeros_list = pasajeros_list.filter(
            Q(nombre__icontains=nombre) | Q(apellido__icontains=nombre)
        )
    if documento:
        pasajeros_list = pasajeros_list.filter(documento__icontains=documento)
    
    # Paginación
    paginator = Paginator(pasajeros_list, 15)
    page_number = request.GET.get('page')
    pasajeros = paginator.get_page(page_number)
    
    context = {
        'pasajeros': pasajeros,
    }
    return render(request, 'gestion/lista_pasajeros.html', context)

def detalle_pasajero(request, pasajero_id):
    """Vista detallada de un pasajero"""
    pasajero = get_object_or_404(Pasajero, id=pasajero_id)
    reservas = pasajero.reservas.all().order_by('-fecha_reserva')
    
    context = {
        'pasajero': pasajero,
        'reservas': reservas,
    }
    return render(request, 'gestion/detalle_pasajero.html', context)

def reporte_pasajeros_vuelo(request, vuelo_id):
    """Reporte de pasajeros por vuelo"""
    vuelo = get_object_or_404(Vuelo, id=vuelo_id)
    reservas = Reserva.objects.filter(
        vuelo=vuelo,
        estado__in=['confirmada', 'pagada']
    ).select_related('pasajero', 'asiento').order_by('asiento__fila', 'asiento__columna')
    
    context = {
        'vuelo': vuelo,
        'reservas': reservas,
        'total_pasajeros': reservas.count(),
    }
    return render(request, 'gestion/reporte_pasajeros_vuelo.html', context)

# Vista para buscar una reserva por código
def buscar_reserva(request):
    reserva = None
    error = None
    codigo = None
    if request.method == 'POST':
        codigo = request.POST.get('codigo_reserva')
    else:
        codigo = request.GET.get('codigo_reserva')

    if codigo:
        try:
            reserva = Reserva.objects.get(codigo_reserva__iexact=codigo)
            # Si el usuario no es staff, solo puede ver su propia reserva
            if not request.user.is_staff:
                if reserva.usuario != request.user:
                    reserva = None
                    error = "No tienes permiso para ver esta reserva."
        except Reserva.DoesNotExist:
            error = "No se encontró ninguna reserva con ese código."
    context = {
        'reserva': reserva,
        'codigo_reserva': codigo,
        'error': error,
        'estados_reserva': Reserva.ESTADOS_RESERVA,
    }
    return render(request, 'gestion/buscar_reserva.html', context)


# Vista para cancelar una reserva
@login_required
def cancelar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    if request.method == 'POST':
        if reserva.estado == 'cancelada':
            messages.info(request, 'La reserva ya estaba cancelada.')
        else:
            reserva.estado = 'cancelada'
            reserva.save()
            # Liberar asiento si corresponde
            if reserva.asiento:
                asiento = reserva.asiento
                asiento.estado = 'disponible'
                asiento.save()
            # Eliminar boleto si existe
            if hasattr(reserva, 'boleto'):
                reserva.boleto.delete()
            messages.success(request, 'La reserva fue cancelada correctamente.')
        return redirect('detalle_reserva', reserva_id=reserva.id)
    else:
        # Mostrar confirmación de cancelación
        return render(request, 'gestion/cancelar_reserva.html', {'reserva': reserva})
