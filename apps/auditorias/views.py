from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import AuditoriaProducto
from .forms import AuditoriaProductoForm


@login_required
def lista_auditorias(request):
    """Lista de auditorías de producto"""
    auditorias = AuditoriaProducto.objects.select_related('certificacion').all().order_by('certificacion__nombre', 'nombre')
    return render(request, 'auditorias/lista.html', {'auditorias': auditorias})


@login_required
def crear_auditoria(request):
    """Crear nueva auditoría de producto"""
    if request.method == 'POST':
        form = AuditoriaProductoForm(request.POST)
        if form.is_valid():
            auditoria = form.save(commit=False)
            auditoria.usuario_creacion = request.user
            auditoria.save()
            messages.success(request, 'Auditoría de producto creada correctamente')
            return redirect('auditorias:lista')
    else:
        form = AuditoriaProductoForm()
    
    return render(request, 'auditorias/form.html', {'form': form, 'titulo': 'Crear Auditoría de Producto'})


@login_required
def editar_auditoria(request, pk):
    """Editar auditoría existente"""
    auditoria = get_object_or_404(AuditoriaProducto, pk=pk)
    
    if request.method == 'POST':
        form = AuditoriaProductoForm(request.POST, instance=auditoria)
        if form.is_valid():
            auditoria = form.save(commit=False)
            auditoria.usuario_actualizacion = request.user
            auditoria.save()
            messages.success(request, 'Auditoría actualizada correctamente')
            return redirect('auditorias:lista')
    else:
        form = AuditoriaProductoForm(instance=auditoria)
    
    return render(request, 'auditorias/form.html', {'form': form, 'titulo': 'Editar Auditoría de Producto', 'auditoria': auditoria})
