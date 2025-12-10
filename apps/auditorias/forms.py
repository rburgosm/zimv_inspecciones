from django import forms
from .models import AuditoriaProducto
from apps.certificaciones.models import Certificacion


class AuditoriaProductoForm(forms.ModelForm):
    class Meta:
        model = AuditoriaProducto
        fields = ['certificacion', 'nombre', 'descripcion', 'activa']
        widgets = {
            'certificacion': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}),
            'nombre': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}),
            'descripcion': forms.Textarea(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500', 'rows': 3}),
            'activa': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'}),
        }
        labels = {
            'certificacion': 'Certificación',
            'nombre': 'Nombre',
            'descripcion': 'Descripción',
            'activa': 'Activa',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['certificacion'].queryset = Certificacion.objects.filter(activa=True)
