from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

class Avion(models.Model):
    modelo = models.CharField(max_length=100)
    capacidad = models.IntegerField(validators=[MinValueValidator(1)])
    filas = models.IntegerField(validators=[MinValueValidator(1)])
    columnas = models.IntegerField(validators=[MinValueValidator(1)])
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Avión"
        verbose_name_plural = "Aviones"
    
    def __str__(self):
        return f"{self.modelo} - Capacidad: {self.capacidad}"
    
    def save(self, *args, **kwargs):
        if self.capacidad != self.filas * self.columnas:
            self.capacidad = self.filas * self.columnas
        super().save(*args, **kwargs)
        if not self.asientos.exists():
            self.crear_asientos()
    
    def crear_asientos(self):
        letras = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        for fila in range(1, self.filas + 1):
            for col in range(self.columnas):
                letra = letras[col] if col < len(letras) else f"A{col}"
                numero = f"{fila}{letra}"
                Asiento.objects.create(
                    avion=self,
                    numero=numero,
                    fila=fila,
                    columna=letra,
                    tipo='economica'
                )

class Vuelo(models.Model):
    ESTADOS_VUELO = [
        ('programado', 'Programado'),
        ('en_vuelo', 'En Vuelo'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
        ('retrasado', 'Retrasado'),
    ]
    
    avion = models.ForeignKey(Avion, on_delete=models.CASCADE, related_name='vuelos')
    origen = models.CharField(max_length=100)
    destino = models.CharField(max_length=100)
    fecha_salida = models.DateTimeField()
    fecha_llegada = models.DateTimeField()
    duracion = models.DurationField()
    estado = models.CharField(max_length=20, choices=ESTADOS_VUELO, default='programado')
    precio_base = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Vuelo"
        verbose_name_plural = "Vuelos"
        ordering = ['fecha_salida']
    
    def __str__(self):
        return f"{self.origen} → {self.destino} - {self.fecha_salida.strftime('%d/%m/%Y %H:%M')}"
    
    def asientos_disponibles(self):
        total_asientos = self.avion.capacidad
        reservados = self.reservas.filter(estado__in=['confirmada', 'pagada']).count()
        return total_asientos - reservados

    def porcentaje_ocupacion(self):
        if self.avion.capacidad == 0:
            return 0
        ocupados = self.reservas.filter(estado__in=['confirmada', 'pagada']).count()
        return (ocupados / self.avion.capacidad) * 100

class Pasajero(models.Model):
    TIPOS_DOCUMENTO = [
        ('dni', 'DNI'),
        ('pasaporte', 'Pasaporte'),
        ('cedula', 'Cédula'),
    ]
    
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    documento = models.CharField(max_length=20, unique=True)
    tipo_documento = models.CharField(max_length=20, choices=TIPOS_DOCUMENTO, default='dni')
    email = models.EmailField()
    telefono = models.CharField(max_length=20)
    fecha_nacimiento = models.DateField()
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Pasajero"
        verbose_name_plural = "Pasajeros"
    
    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.documento}"
    
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    def edad(self):
        from datetime import date
        today = date.today()
        return today.year - self.fecha_nacimiento.year - ((today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))

class Asiento(models.Model):
    TIPOS_ASIENTO = [
        ('economica', 'Económica'),
        ('ejecutiva', 'Ejecutiva'),
        ('primera', 'Primera Clase'),
    ]
    
    ESTADOS_ASIENTO = [
        ('disponible', 'Disponible'),
        ('reservado', 'Reservado'),
        ('ocupado', 'Ocupado'),
        ('mantenimiento', 'En Mantenimiento'),
    ]
    
    avion = models.ForeignKey(Avion, on_delete=models.CASCADE, related_name='asientos')
    numero = models.CharField(max_length=10)
    fila = models.IntegerField()
    columna = models.CharField(max_length=5)
    tipo = models.CharField(max_length=20, choices=TIPOS_ASIENTO, default='economica')
    estado = models.CharField(max_length=20, choices=ESTADOS_ASIENTO, default='disponible')
    
    class Meta:
        verbose_name = "Asiento"
        verbose_name_plural = "Asientos"
        unique_together = ['avion', 'numero']
        ordering = ['fila', 'columna']
    
    def __str__(self):
        return f"Asiento {self.numero} - {self.avion.modelo}"

class Reserva(models.Model):
    ESTADOS_RESERVA = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('pagada', 'Pagada'),
        ('cancelada', 'Cancelada'),
        ('completada', 'Completada'),
    ]
    
    vuelo = models.ForeignKey(Vuelo, on_delete=models.CASCADE, related_name='reservas')
    pasajero = models.ForeignKey(Pasajero, on_delete=models.CASCADE, related_name='reservas')
    asiento = models.ForeignKey(Asiento, on_delete=models.CASCADE, related_name='reservas')
    estado = models.CharField(max_length=20, choices=ESTADOS_RESERVA, default='pendiente')
    fecha_reserva = models.DateTimeField(auto_now_add=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    METODOS_PAGO = [
        ('tarjeta', 'Tarjeta'),
        ('efectivo', 'Efectivo'),
    ]
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, default='efectivo')
    codigo_reserva = models.CharField(max_length=10, unique=True, blank=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        unique_together = ['vuelo', 'pasajero']
        ordering = ['-fecha_reserva']
    
    def __str__(self):
        return f"Reserva {self.codigo_reserva} - {self.pasajero.nombre_completo()}"
    
    def save(self, *args, **kwargs):
        if not self.codigo_reserva:
            self.codigo_reserva = self.generar_codigo_reserva()
        super().save(*args, **kwargs)

    def generar_codigo_reserva(self):
        import random
        import string
        while True:
            codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not Reserva.objects.filter(codigo_reserva=codigo).exists():
                return codigo

class Boleto(models.Model):
    ESTADOS_BOLETO = [
        ('emitido', 'Emitido'),
        ('usado', 'Usado'),
        ('cancelado', 'Cancelado'),
    ]
    
    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE, related_name='boleto')
    codigo_barra = models.CharField(max_length=50, unique=True, blank=True)
    fecha_emision = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS_BOLETO, default='emitido')
    
    class Meta:
        verbose_name = "Boleto"
        verbose_name_plural = "Boletos"
    
    def __str__(self):
        return f"Boleto {self.codigo_barra} - {self.reserva.codigo_reserva}"
    
    def save(self, *args, **kwargs):
        if not self.codigo_barra:
            self.codigo_barra = self.generar_codigo_barra()
        super().save(*args, **kwargs)

    def generar_codigo_barra(self):
        import random
        while True:
            codigo = ''.join(random.choices('0123456789', k=12))
            if not Boleto.objects.filter(codigo_barra=codigo).exists():
                return codigo
