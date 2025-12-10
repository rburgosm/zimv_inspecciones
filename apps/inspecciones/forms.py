from django import forms
from .models import InspeccionProducto, PeriodoValidacionCertificacion
from apps.asignaciones.models import OperarioCertificacion
from apps.auditorias.models import AuditoriaProducto
from apps.auditores.models import Auditor
from apps.operarios.models import Operario
from apps.certificaciones.models import Certificacion


class InspeccionProductoForm(forms.ModelForm):
    operario = forms.ModelChoiceField(
        queryset=Operario.objects.filter(activo=True).order_by('nombre', 'apellidos'),
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'id': 'id_operario'
        }),
        label='Operario',
        required=True
    )
    
    certificacion = forms.ModelChoiceField(
        queryset=Certificacion.objects.none(),
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'id': 'id_certificacion'
        }),
        label='Certificación',
        required=True
    )
    
    class Meta:
        model = InspeccionProducto
        fields = [
            'operario_certificacion',
            'auditoria_producto',
            'auditor',
            'fecha_inspeccion',
            'piezas_auditadas',
            'resultado_inspeccion',
            'observaciones',
            'numero_orden'
        ]
        # Excluir operario y certificacion de los campos del modelo
        # porque son campos adicionales solo para la UI
        widgets = {
            'operario_certificacion': forms.HiddenInput(),
            'auditoria_producto': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}),
            'auditor': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}),
            'fecha_inspeccion': forms.DateInput(attrs={'type': 'date', 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}),
            'piezas_auditadas': forms.NumberInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500', 'min': 1}),
            'resultado_inspeccion': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}),
            'observaciones': forms.Textarea(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500', 'rows': 3}),
            'numero_orden': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}),
        }
        labels = {
            'operario_certificacion': 'Operario - Certificación',
            'auditoria_producto': 'Auditoría de Producto',
            'auditor': 'Auditor',
            'fecha_inspeccion': 'Fecha de inspección',
            'piezas_auditadas': 'Piezas auditadas',
            'resultado_inspeccion': 'Resultado',
            'observaciones': 'Observaciones',
            'numero_orden': 'Número de orden',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Hacer que operario_certificacion no sea requerido (se establece en clean())
        self.fields['operario_certificacion'].required = False
        
        # Configurar queryset de operarios
        self.fields['operario'].queryset = Operario.objects.filter(activo=True).order_by('nombre', 'apellidos')
        
        # Si hay una instancia existente, establecer valores iniciales
        if self.instance and self.instance.pk:
            if self.instance.operario_certificacion:
                self.fields['operario'].initial = self.instance.operario_certificacion.operario
                # Filtrar certificaciones del operario
                certificaciones_ids = OperarioCertificacion.objects.filter(
                    operario=self.instance.operario_certificacion.operario,
                    esta_activa=True
                ).values_list('certificacion_id', flat=True)
                self.fields['certificacion'].queryset = Certificacion.objects.filter(
                    id__in=certificaciones_ids,
                    activa=True
                ).order_by('nombre')
                self.fields['certificacion'].initial = self.instance.operario_certificacion.certificacion
        
        # Si hay datos POST, filtrar certificaciones según el operario seleccionado
        if self.data and 'operario' in self.data:
            try:
                operario_id = int(self.data['operario'])
                certificaciones_ids = OperarioCertificacion.objects.filter(
                    operario_id=operario_id,
                    esta_activa=True
                ).values_list('certificacion_id', flat=True)
                self.fields['certificacion'].queryset = Certificacion.objects.filter(
                    id__in=certificaciones_ids,
                    activa=True
                ).order_by('nombre')
                
                # Si hay certificación seleccionada, filtrar auditorías
                if 'certificacion' in self.data and self.data['certificacion']:
                    try:
                        certificacion_id = int(self.data['certificacion'])
                        self.fields['auditoria_producto'].queryset = AuditoriaProducto.objects.filter(
                            certificacion_id=certificacion_id,
                            activa=True
                        ).order_by('nombre')
                    except (ValueError,):
                        self.fields['auditoria_producto'].queryset = AuditoriaProducto.objects.none()
                else:
                    self.fields['auditoria_producto'].queryset = AuditoriaProducto.objects.none()
            except (ValueError,):
                self.fields['certificacion'].queryset = Certificacion.objects.none()
                self.fields['auditoria_producto'].queryset = AuditoriaProducto.objects.none()
        else:
            self.fields['certificacion'].queryset = Certificacion.objects.none()
            self.fields['auditoria_producto'].queryset = AuditoriaProducto.objects.none()
        
        self.fields['auditor'].queryset = Auditor.objects.filter(activo=True).order_by('nombre', 'apellidos')

    def clean(self):
        cleaned_data = super().clean()
        operario = cleaned_data.get('operario')
        certificacion = cleaned_data.get('certificacion')
        
        # Validar que se hayan seleccionado operario y certificación
        if not operario:
            raise forms.ValidationError({'operario': 'Debe seleccionar un operario'})
        
        if not certificacion:
            raise forms.ValidationError({'certificacion': 'Debe seleccionar una certificación'})
        
        if operario and certificacion:
            # Buscar la asignación OperarioCertificacion correspondiente
            try:
                operario_certificacion = OperarioCertificacion.objects.get(
                    operario=operario,
                    certificacion=certificacion,
                    esta_activa=True
                )
                # Asignar la operario_certificacion al campo hidden
                cleaned_data['operario_certificacion'] = operario_certificacion
                self.instance.operario_certificacion = operario_certificacion
                
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
                if auditoria_producto and auditoria_producto.certificacion != certificacion:
                    raise forms.ValidationError({'auditoria_producto': 'La auditoría de producto debe pertenecer a la misma certificación'})
            except OperarioCertificacion.DoesNotExist:
                raise forms.ValidationError('No existe una asignación activa para este operario y certificación')
        
        return cleaned_data
