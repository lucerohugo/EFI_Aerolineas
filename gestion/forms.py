from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Pasajero, Reserva, Vuelo
from datetime import date, datetime

class PasajeroForm(forms.ModelForm):
    class Meta:
        model = Pasajero
        fields = ['nombre', 'apellido', 'documento', 'tipo_documento', 'email', 'telefono', 'fecha_nacimiento']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'documento': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data['fecha_nacimiento']
        if fecha > date.today():
            raise forms.ValidationError("La fecha de nacimiento no puede ser futura.")
        if fecha.year < 1900:
            raise forms.ValidationError("La fecha de nacimiento no puede ser anterior a 1900.")
        return fecha

class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['vuelo', 'pasajero', 'asiento']
        widgets = {
            'vuelo': forms.Select(attrs={'class': 'form-control'}),
            'pasajero': forms.HiddenInput(),
            'asiento': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        vuelo_id = kwargs.pop('vuelo_id', None)
        super().__init__(*args, **kwargs)
        self.fields['pasajero'].required = False
        if vuelo_id:
            try:
                vuelo = Vuelo.objects.get(id=vuelo_id)
                self.fields['vuelo'].initial = vuelo
                self.fields['vuelo'].widget = forms.HiddenInput()
                asientos_reservados = Reserva.objects.filter(
                    vuelo=vuelo,
                    estado__in=['confirmada', 'pagada']
                ).values_list('asiento_id', flat=True)
                self.fields['asiento'].queryset = vuelo.avion.asientos.exclude(
                    id__in=asientos_reservados
                ).filter(estado='disponible')
            except Vuelo.DoesNotExist:
                pass

class BusquedaVueloForm(forms.Form):
    origen = forms.ChoiceField(choices=[], widget=forms.Select(attrs={'class': 'form-control'}))
    destino = forms.ChoiceField(choices=[], widget=forms.Select(attrs={'class': 'form-control'}))
    fecha_salida = forms.ChoiceField(choices=[], widget=forms.Select(attrs={'class': 'form-control'}))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        vuelos = Vuelo.objects.filter(estado='programado')
        origenes = sorted(set(v.origen for v in vuelos))
        destinos = sorted(set(v.destino for v in vuelos))
        fechas = sorted(set(v.fecha_salida.date() for v in vuelos))
        self.fields['origen'].choices = [('', '---------')] + [(o, o) for o in origenes]
        self.fields['destino'].choices = [('', '---------')] + [(d, d) for d in destinos]
        self.fields['fecha_salida'].choices = [('', '---------')] + [ (f.strftime('%Y-%m-%d'), f.strftime('%d/%m/%Y')) for f in fechas ]

    def clean_fecha_salida(self):
        fecha = self.cleaned_data['fecha_salida']
        if isinstance(fecha, str):
            try:
                fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
            except Exception:
                raise forms.ValidationError("Fecha inválida.")
        if fecha < date.today():
            raise forms.ValidationError("La fecha de salida no puede ser anterior a hoy.")
        return fecha

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user
