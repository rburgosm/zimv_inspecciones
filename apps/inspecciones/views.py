from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import InspeccionProducto, PeriodoValidacionCertificacion
from .forms import InspeccionProductoForm
from .signals import verificar_caducidades_pendientes
from apps.asignaciones.models import OperarioCertificacion


@login_required
def lista_inspecciones(request):
    """Lista de inspecciones"""
    # Verificar caducidades pendientes al acceder a la lista
    verificar_caducidades_pendientes()
    
    inspecciones = InspeccionProducto.objects.select_related(
        'operario_certificacion__operario',
        'operario_certificacion__certificacion',
        'periodo_validacion',
        'auditoria_producto',
        'auditor'
    ).all().order_by('-fecha_inspeccion', '-fecha_creacion')
    
    # Filtros
    operario_cert_id = request.GET.get('asignacion')
    periodo_id = request.GET.get('periodo')
    
    if operario_cert_id:
        inspecciones = inspecciones.filter(operario_certificacion_id=operario_cert_id)
    if periodo_id:
        inspecciones = inspecciones.filter(periodo_validacion_id=periodo_id)
    
    asignaciones = OperarioCertificacion.objects.filter(esta_activa=True).select_related('operario', 'certificacion')
    
    return render(request, 'inspecciones/lista.html', {
        'inspecciones': inspecciones,
        'asignaciones': asignaciones,
        'asignacion_filtro': int(operario_cert_id) if operario_cert_id else None,
        'periodo_filtro': int(periodo_id) if periodo_id else None,
    })


@login_required
@transaction.atomic
def crear_inspeccion(request):
    """Crear nueva inspección"""
    if request.method == 'POST':
        form = InspeccionProductoForm(request.POST)
        if form.is_valid():
            inspeccion = form.save(commit=False)
            inspeccion.usuario_creacion = request.user
            
            # Validar que la fecha esté dentro del periodo
            periodo = inspeccion.periodo_validacion
            if inspeccion.fecha_inspeccion < periodo.fecha_inicio_periodo:
                messages.error(request, 'La fecha de inspección no puede ser anterior al inicio del periodo')
                return render(request, 'inspecciones/form.html', {'form': form, 'titulo': 'Crear Inspección'})
            
            if inspeccion.fecha_inspeccion > periodo.fecha_fin_periodo:
                messages.error(request, 'La fecha de inspección no puede ser posterior al fin del periodo')
                return render(request, 'inspecciones/form.html', {'form': form, 'titulo': 'Crear Inspección'})
            
            if not periodo.esta_vigente:
                messages.error(request, 'No se pueden registrar inspecciones en periodos no vigentes')
                return render(request, 'inspecciones/form.html', {'form': form, 'titulo': 'Crear Inspección'})
            
            inspeccion.save()
            # El contador y la lógica de periodos se manejan mediante signal
            messages.success(request, 'Inspección registrada correctamente')
            return redirect('inspecciones:lista')
    else:
        form = InspeccionProductoForm()
    
    return render(request, 'inspecciones/form.html', {'form': form, 'titulo': 'Crear Inspección'})


@login_required
def detalle_inspeccion(request, pk):
    """Detalle de inspección"""
    inspeccion = get_object_or_404(
        InspeccionProducto.objects.select_related(
            'operario_certificacion__operario',
            'operario_certificacion__certificacion',
            'periodo_validacion',
            'auditoria_producto',
            'auditor'
        ),
        pk=pk
    )
    
    return render(request, 'inspecciones/detalle.html', {'inspeccion': inspeccion})


@login_required
def obtener_auditorias_por_certificacion(request):
    """Vista AJAX para obtener auditorías según la asignación seleccionada"""
    from django.http import JsonResponse
    from apps.asignaciones.models import OperarioCertificacion
    from apps.auditorias.models import AuditoriaProducto
    
    asignacion_id = request.GET.get('asignacion_id')
    
    if not asignacion_id:
        return JsonResponse({'error': 'ID de asignación requerido'}, status=400)
    
    try:
        asignacion = OperarioCertificacion.objects.get(pk=asignacion_id)
        auditorias = AuditoriaProducto.objects.filter(
            certificacion=asignacion.certificacion,
            activa=True
        ).order_by('nombre')
        
        # Obtener también el periodo vigente
        periodo_vigente = PeriodoValidacionCertificacion.objects.filter(
            operario_certificacion=asignacion,
            esta_vigente=True
        ).first()
        
        data = {
            'auditorias': [
                {'id': a.id, 'nombre': a.nombre} for a in auditorias
            ],
            'periodo': None
        }
        
        if periodo_vigente:
            data['periodo'] = {
                'numero': periodo_vigente.numero_periodo,
                'fecha_inicio': periodo_vigente.fecha_inicio_periodo.strftime('%Y-%m-%d'),
                'fecha_fin': periodo_vigente.fecha_fin_periodo.strftime('%Y-%m-%d'),
                'inspecciones_realizadas': periodo_vigente.inspecciones_realizadas,  # Total de piezas auditadas
                'inspecciones_requeridas': periodo_vigente.inspecciones_requeridas,  # Piezas requeridas (29)
            }
        
        return JsonResponse(data)
    except OperarioCertificacion.DoesNotExist:
        return JsonResponse({'error': 'Asignación no encontrada'}, status=404)
