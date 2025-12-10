from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Operario
from .forms import OperarioForm


@login_required
def lista_operarios(request):
    """Lista de operarios"""
    operarios = Operario.objects.all().order_by('nombre', 'apellidos')
    return render(request, 'operarios/lista.html', {'operarios': operarios})


@login_required
def crear_operario(request):
    """Crear nuevo operario"""
    if request.method == 'POST':
        form = OperarioForm(request.POST)
        if form.is_valid():
            operario = form.save(commit=False)
            operario.usuario_creacion = request.user
            operario.save()
            messages.success(request, 'Operario creado correctamente')
            return redirect('operarios:lista')
    else:
        form = OperarioForm()
    
    return render(request, 'operarios/form.html', {'form': form, 'titulo': 'Crear Operario'})


@login_required
def editar_operario(request, pk):
    """Editar operario existente"""
    operario = get_object_or_404(Operario, pk=pk)
    
    if request.method == 'POST':
        form = OperarioForm(request.POST, instance=operario)
        if form.is_valid():
            operario = form.save(commit=False)
            operario.usuario_actualizacion = request.user
            operario.save()
            messages.success(request, 'Operario actualizado correctamente')
            return redirect('operarios:lista')
    else:
        form = OperarioForm(instance=operario)
    
    return render(request, 'operarios/form.html', {'form': form, 'titulo': 'Editar Operario', 'operario': operario})


@login_required
def detalle_operario(request, pk):
    """Detalle de operario"""
    operario = get_object_or_404(Operario, pk=pk)
    return render(request, 'operarios/detalle.html', {'operario': operario})
