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
    operario_cert_id = request.GET.get('asignacion', '').strip()
    periodo_id = request.GET.get('periodo', '').strip()
    
    asignacion_filtro = None
    periodo_filtro = None
    
    if operario_cert_id:
        try:
            asignacion_filtro = int(operario_cert_id)
            inspecciones = inspecciones.filter(operario_certificacion_id=asignacion_filtro)
        except (ValueError, TypeError):
            asignacion_filtro = None
    
    if periodo_id:
        try:
            periodo_filtro = int(periodo_id)
            inspecciones = inspecciones.filter(periodo_validacion_id=periodo_filtro)
        except (ValueError, TypeError):
            periodo_filtro = None
    
    asignaciones = OperarioCertificacion.objects.filter(esta_activa=True).select_related('operario', 'certificacion').order_by('operario__nombre', 'certificacion__nombre')
    
    return render(request, 'inspecciones/lista.html', {
        'inspecciones': inspecciones,
        'asignaciones': asignaciones,
        'asignacion_filtro': asignacion_filtro,
        'periodo_filtro': periodo_filtro,
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
            if not periodo:
                messages.error(request, 'No se pudo determinar el periodo de validación')
                return render(request, 'inspecciones/form.html', {'form': form, 'titulo': 'Crear Inspección'})
            
            if inspeccion.fecha_inspeccion < periodo.fecha_inicio_periodo:
                messages.error(request, 'La fecha de inspección no puede ser anterior al inicio del periodo')
                return render(request, 'inspecciones/form.html', {'form': form, 'titulo': 'Crear Inspección'})
            
            if inspeccion.fecha_inspeccion > periodo.fecha_fin_periodo:
                messages.error(request, 'La fecha de inspección no puede ser posterior al fin del periodo')
                return render(request, 'inspecciones/form.html', {'form': form, 'titulo': 'Crear Inspección'})
            
            if not periodo.esta_vigente:
                messages.error(request, 'No se pueden registrar inspecciones en periodos no vigentes')
                return render(request, 'inspecciones/form.html', {'form': form, 'titulo': 'Crear Inspección'})
            
            try:
                inspeccion.save()
                # El contador y la lógica de periodos se manejan mediante signal
                messages.success(request, 'Inspección registrada correctamente')
                return redirect('inspecciones:lista')
            except Exception as e:
                messages.error(request, f'Error al guardar la inspección: {str(e)}')
        else:
            # Mostrar errores del formulario
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
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
def obtener_certificaciones_por_operario(request):
    """Vista AJAX para obtener certificaciones según el operario seleccionado"""
    from django.http import JsonResponse
    from apps.asignaciones.models import OperarioCertificacion
    from apps.certificaciones.models import Certificacion
    
    operario_id = request.GET.get('operario_id')
    
    if not operario_id:
        return JsonResponse({'error': 'ID de operario requerido'}, status=400)
    
    try:
        certificaciones_ids = OperarioCertificacion.objects.filter(
            operario_id=operario_id,
            esta_activa=True
        ).values_list('certificacion_id', flat=True)
        
        certificaciones = Certificacion.objects.filter(
            id__in=certificaciones_ids,
            activa=True
        ).order_by('nombre')
        
        data = {
            'certificaciones': [
                {'id': c.id, 'nombre': c.nombre} for c in certificaciones
            ]
        }
        
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def obtener_auditorias_por_certificacion(request):
    """Vista AJAX para obtener auditorías según la certificación seleccionada"""
    from django.http import JsonResponse
    from apps.asignaciones.models import OperarioCertificacion
    from apps.auditorias.models import AuditoriaProducto
    
    operario_id = request.GET.get('operario_id')
    certificacion_id = request.GET.get('certificacion_id')
    
    if not operario_id or not certificacion_id:
        return JsonResponse({'error': 'ID de operario y certificación requeridos'}, status=400)
    
    try:
        # Buscar la asignación
        asignacion = OperarioCertificacion.objects.get(
            operario_id=operario_id,
            certificacion_id=certificacion_id,
            esta_activa=True
        )
        
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
                'inspecciones_realizadas': periodo_vigente.inspecciones_realizadas,
                'inspecciones_requeridas': periodo_vigente.inspecciones_requeridas,
            }
        
        return JsonResponse(data)
    except OperarioCertificacion.DoesNotExist:
        return JsonResponse({'error': 'Asignación no encontrada'}, status=404)
