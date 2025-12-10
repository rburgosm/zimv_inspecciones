from django import forms
from .models import OperarioCertificacion
from apps.operarios.models import Operario
from apps.certificaciones.models import Certificacion


class OperarioCertificacionForm(forms.ModelForm):
    class Meta:
        model = OperarioCertificacion
        fields = ['operario', 'certificacion', 'fecha_asignacion', 'observaciones']
        widgets = {
            'operario': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}),
            'certificacion': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}),
            'fecha_asignacion': forms.DateInput(attrs={'type': 'date', 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}),
            'observaciones': forms.Textarea(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500', 'rows': 3}),
        }
        labels = {
            'operario': 'Operario',
            'certificacion': 'Certificación',
            'fecha_asignacion': 'Fecha de asignación',
            'observaciones': 'Observaciones',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['operario'].queryset = Operario.objects.filter(activo=True).order_by('nombre', 'apellidos')
        self.fields['certificacion'].queryset = Certificacion.objects.filter(activa=True).order_by('nombre')
