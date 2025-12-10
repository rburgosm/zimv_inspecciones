from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import OperarioCertificacion
from .forms import OperarioCertificacionForm
from apps.operarios.models import Operario
from apps.inspecciones.signals import verificar_caducidades_pendientes


@login_required
def lista_asignaciones(request):
    """Lista de asignaciones"""
    # Verificar caducidades pendientes al acceder a la lista
    verificar_caducidades_pendientes()
    
    asignaciones = OperarioCertificacion.objects.select_related(
        'operario', 'certificacion'
    ).all().order_by('-fecha_asignacion')
    
    # Filtro por operario si se proporciona
    operario_id = request.GET.get('operario')
    if operario_id:
        asignaciones = asignaciones.filter(operario_id=operario_id)
    
    operarios = Operario.objects.filter(activo=True).order_by('nombre', 'apellidos')
    
    return render(request, 'asignaciones/lista.html', {
        'asignaciones': asignaciones,
        'operarios': operarios,
        'operario_filtro': int(operario_id) if operario_id else None
    })


@login_required
@transaction.atomic
def crear_asignacion(request):
    """Crear nueva asignación operario-certificación"""
    if request.method == 'POST':
        form = OperarioCertificacionForm(request.POST)
        if form.is_valid():
            asignacion = form.save(commit=False)
            asignacion.usuario_creacion = request.user
            asignacion.save()
            # El periodo inicial se crea automáticamente mediante signal
            messages.success(request, 'Asignación creada correctamente. Se ha creado el periodo inicial automáticamente.')
            return redirect('asignaciones:lista')
    else:
        form = OperarioCertificacionForm()
    
    return render(request, 'asignaciones/form.html', {'form': form, 'titulo': 'Crear Asignación'})


@login_required
def detalle_asignacion(request, pk):
    """Detalle de asignación con periodos e inspecciones"""
    asignacion = get_object_or_404(
        OperarioCertificacion.objects.select_related('operario', 'certificacion'),
        pk=pk
    )
    periodos = asignacion.periodos.all().order_by('-numero_periodo')
    
    return render(request, 'asignaciones/detalle.html', {
        'asignacion': asignacion,
        'periodos': periodos
    })
