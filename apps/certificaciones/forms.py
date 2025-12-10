from django import forms
from .models import Certificacion


class CertificacionForm(forms.ModelForm):
    class Meta:
        model = Certificacion
        fields = ['nombre', 'descripcion', 'activa']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}),
            'descripcion': forms.Textarea(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500', 'rows': 3}),
            'activa': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'}),
        }
        labels = {
            'nombre': 'Nombre',
            'descripcion': 'Descripción',
            'activa': 'Activa',
        }
