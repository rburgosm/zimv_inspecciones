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
        
        # Si hay una instancia existente, filtrar certificaciones ya asignadas al operario
        if self.instance and self.instance.pk and self.instance.operario:
            certificaciones_asignadas = OperarioCertificacion.objects.filter(
                operario=self.instance.operario,
                esta_activa=True
            ).exclude(pk=self.instance.pk).values_list('certificacion_id', flat=True)
            
            self.fields['certificacion'].queryset = Certificacion.objects.filter(
                activa=True
            ).exclude(id__in=certificaciones_asignadas).order_by('nombre')
        
        # Si hay datos POST, filtrar certificaciones según el operario seleccionado
        if self.data and 'operario' in self.data:
            try:
                operario_id = int(self.data['operario'])
                # Obtener certificaciones ya asignadas a este operario (activas)
                certificaciones_asignadas = OperarioCertificacion.objects.filter(
                    operario_id=operario_id,
                    esta_activa=True
                )
                
                # Si estamos editando, excluir la asignación actual
                if self.instance and self.instance.pk:
                    certificaciones_asignadas = certificaciones_asignadas.exclude(pk=self.instance.pk)
                
                certificaciones_ids = certificaciones_asignadas.values_list('certificacion_id', flat=True)
                
                # Filtrar para mostrar solo las certificaciones que NO están asignadas
                self.fields['certificacion'].queryset = Certificacion.objects.filter(
                    activa=True
                ).exclude(id__in=certificaciones_ids).order_by('nombre')
            except (ValueError,):
                self.fields['certificacion'].queryset = Certificacion.objects.filter(activa=True).order_by('nombre')
    
    def clean(self):
        cleaned_data = super().clean()
        operario = cleaned_data.get('operario')
        certificacion = cleaned_data.get('certificacion')
        
        if operario and certificacion:
            # Verificar si ya existe una asignación activa para este operario y certificación
            asignaciones_existentes = OperarioCertificacion.objects.filter(
                operario=operario,
                certificacion=certificacion,
                esta_activa=True
            )
            
            # Si estamos editando, excluir la instancia actual
            if self.instance and self.instance.pk:
                asignaciones_existentes = asignaciones_existentes.exclude(pk=self.instance.pk)
            
            if asignaciones_existentes.exists():
                raise forms.ValidationError(
                    f"El operario {operario.nombre_completo} ya tiene asignada la certificación "
                    f"{certificacion.nombre}. No se puede asignar la misma certificación dos veces."
                )
        
        return cleaned_data
