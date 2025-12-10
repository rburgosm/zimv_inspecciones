from django import forms
from .models import InspeccionProducto, PeriodoValidacionCertificacion
from apps.asignaciones.models import OperarioCertificacion
from apps.auditorias.models import AuditoriaProducto
from apps.auditores.models import Auditor


class InspeccionProductoForm(forms.ModelForm):
    class Meta:
        model = InspeccionProducto
        fields = [
            'operario_certificacion',
            'auditoria_producto',
            'auditor',
            'fecha_inspeccion',
            'piezas_auditadas',
            'resultado_inspeccion',
            'observaciones'
        ]
        widgets = {
            'operario_certificacion': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'id': 'id_operario_certificacion'
            }),
            'auditoria_producto': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}),
            'auditor': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}),
            'fecha_inspeccion': forms.DateInput(attrs={'type': 'date', 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}),
            'piezas_auditadas': forms.NumberInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500', 'min': 1}),
            'resultado_inspeccion': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}),
            'observaciones': forms.Textarea(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500', 'rows': 3}),
        }
        labels = {
            'operario_certificacion': 'Operario - Certificación',
            'auditoria_producto': 'Auditoría de Producto',
            'auditor': 'Auditor',
            'fecha_inspeccion': 'Fecha de inspección',
            'piezas_auditadas': 'Piezas auditadas',
            'resultado_inspeccion': 'Resultado',
            'observaciones': 'Observaciones',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['operario_certificacion'].queryset = OperarioCertificacion.objects.filter(
            esta_activa=True
        ).select_related('operario', 'certificacion').order_by('operario__nombre', 'certificacion__nombre')
        
        self.fields['auditor'].queryset = Auditor.objects.filter(activo=True).order_by('nombre', 'apellidos')
        
        # Filtrar auditorías según la certificación seleccionada (si existe)
        if self.data and 'operario_certificacion' in self.data:
            try:
                asignacion_id = int(self.data['operario_certificacion'])
                asignacion = OperarioCertificacion.objects.get(pk=asignacion_id)
                self.fields['auditoria_producto'].queryset = AuditoriaProducto.objects.filter(
                    certificacion=asignacion.certificacion,
                    activa=True
                ).order_by('nombre')
            except (ValueError, OperarioCertificacion.DoesNotExist):
                self.fields['auditoria_producto'].queryset = AuditoriaProducto.objects.none()
        else:
            self.fields['auditoria_producto'].queryset = AuditoriaProducto.objects.filter(activa=True).order_by('nombre')
        
        # Si hay una instancia, establecer el periodo vigente
        if self.instance and self.instance.pk:
            self.fields['periodo_validacion'] = forms.ModelChoiceField(
                queryset=PeriodoValidacionCertificacion.objects.filter(
                    operario_certificacion=self.instance.operario_certificacion,
                    esta_vigente=True
                ),
                widget=forms.HiddenInput(),
                required=False
            )

    def clean(self):
        cleaned_data = super().clean()
        operario_certificacion = cleaned_data.get('operario_certificacion')
        
        if operario_certificacion:
            # Obtener el periodo vigente
            periodo_vigente = PeriodoValidacionCertificacion.objects.filter(
                operario_certificacion=operario_certificacion,
                esta_vigente=True
            ).first()
            
            if not periodo_vigente:
                raise forms.ValidationError('No hay un periodo vigente para esta asignación')
            
            # Asignar el periodo vigente
            self.instance.periodo_validacion = periodo_vigente
            
            # Validar auditoría de producto
            auditoria_producto = cleaned_data.get('auditoria_producto')
            if auditoria_producto and auditoria_producto.certificacion != operario_certificacion.certificacion:
                raise forms.ValidationError('La auditoría de producto debe pertenecer a la misma certificación')
        
        return cleaned_data
