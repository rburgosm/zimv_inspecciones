from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Certificacion
from .forms import CertificacionForm


@login_required
def lista_certificaciones(request):
    """Lista de certificaciones"""
    certificaciones = Certificacion.objects.all().order_by('nombre')
    return render(request, 'certificaciones/lista.html', {'certificaciones': certificaciones})


@login_required
def crear_certificacion(request):
    """Crear nueva certificación"""
    if request.method == 'POST':
        form = CertificacionForm(request.POST)
        if form.is_valid():
            certificacion = form.save(commit=False)
            certificacion.usuario_creacion = request.user
            certificacion.save()
            messages.success(request, 'Certificación creada correctamente')
            return redirect('certificaciones:lista')
    else:
        form = CertificacionForm()
    
    return render(request, 'certificaciones/form.html', {'form': form, 'titulo': 'Crear Certificación'})


@login_required
def editar_certificacion(request, pk):
    """Editar certificación existente"""
    certificacion = get_object_or_404(Certificacion, pk=pk)
    
    if request.method == 'POST':
        form = CertificacionForm(request.POST, instance=certificacion)
        if form.is_valid():
            certificacion = form.save(commit=False)
            certificacion.usuario_actualizacion = request.user
            certificacion.save()
            messages.success(request, 'Certificación actualizada correctamente')
            return redirect('certificaciones:lista')
    else:
        form = CertificacionForm(instance=certificacion)
    
    return render(request, 'certificaciones/form.html', {'form': form, 'titulo': 'Editar Certificación', 'certificacion': certificacion})
