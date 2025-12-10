from django import forms
from .models import Auditor


class AuditorForm(forms.ModelForm):
    class Meta:
        model = Auditor
        fields = ['codigo', 'nombre', 'apellidos', 'activo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}),
            'nombre': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}),
            'apellidos': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}),
            'activo': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'}),
        }
        labels = {
            'codigo': 'Código',
            'nombre': 'Nombre',
            'apellidos': 'Apellidos',
            'activo': 'Activo',
        }
