import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import transaction
from .models import InspeccionProducto, PeriodoValidacionCertificacion
from .forms import InspeccionProductoForm
from .signals import verificar_caducidades_pendientes
from apps.asignaciones.models import OperarioCertificacion
from apps.certificaciones.models import Certificacion
from apps.operarios.models import Operario


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
    
    # Filtros: operario y certificación (pueden usarse juntos o por separado)
    operario_id = request.GET.get('operario', '').strip()
    certificacion_id = request.GET.get('certificacion', '').strip()
    
    operario_filtro = None
    certificacion_filtro = None
    
    if operario_id:
        try:
            operario_filtro = int(operario_id)
            inspecciones = inspecciones.filter(operario_certificacion__operario_id=operario_filtro)
        except (ValueError, TypeError):
            operario_filtro = None
    
    if certificacion_id:
        try:
            certificacion_filtro = int(certificacion_id)
            inspecciones = inspecciones.filter(operario_certificacion__certificacion_id=certificacion_filtro)
        except (ValueError, TypeError):
            certificacion_filtro = None
    
    # Listados para los selects
    operarios_qs = Operario.objects.filter(activo=True).order_by('nombre', 'apellidos')
    certificaciones_qs = Certificacion.objects.filter(activa=True).order_by('nombre')
    
    if operario_filtro:
        certificaciones_ids = OperarioCertificacion.objects.filter(
            operario_id=operario_filtro,
            esta_activa=True
        ).values_list('certificacion_id', flat=True)
        certificaciones_qs = certificaciones_qs.filter(id__in=certificaciones_ids)
    
    if certificacion_filtro:
        operarios_ids = OperarioCertificacion.objects.filter(
            certificacion_id=certificacion_filtro,
            esta_activa=True
        ).values_list('operario_id', flat=True)
        operarios_qs = operarios_qs.filter(id__in=operarios_ids)
    
    operarios = list(operarios_qs)
    certificaciones = list(certificaciones_qs)
    
    # Paginación
    paginator = Paginator(inspecciones, 25)  # 25 inspecciones por página
    page = request.GET.get('page', 1)
    
    try:
        inspecciones_paginadas = paginator.page(page)
    except PageNotAnInteger:
        inspecciones_paginadas = paginator.page(1)
    except EmptyPage:
        inspecciones_paginadas = paginator.page(paginator.num_pages)
    
    # Construir query params para mantener filtros en la paginación
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    query_string = query_params.urlencode()
    
    return render(request, 'inspecciones/lista.html', {
        'inspecciones': inspecciones_paginadas,
        'operarios': operarios,
        'certificaciones': certificaciones,
        'operario_filtro': operario_filtro,
        'certificacion_filtro': certificacion_filtro,
        'query_string': query_string,
        'certificaciones_json': json.dumps([
            {'id': c.id, 'nombre': c.nombre} for c in Certificacion.objects.filter(activa=True).order_by('nombre')
        ]),
        'operarios_json': json.dumps([
            {'id': o.id, 'nombre': o.nombre_completo} for o in Operario.objects.filter(activo=True).order_by('nombre', 'apellidos')
        ]),
    })


@login_required
@transaction.atomic
def crear_inspeccion(request):
    """Crear nueva inspección"""
    asignacion_id = request.GET.get('asignacion')
    preloaded_instance = None
    
    # Pre-cargar datos cuando se llega desde el dashboard
    if asignacion_id and request.method == 'GET':
        try:
            asignacion = OperarioCertificacion.objects.select_related('operario', 'certificacion').get(
                pk=asignacion_id,
                esta_activa=True
            )
            periodo_vigente = PeriodoValidacionCertificacion.objects.filter(
                operario_certificacion=asignacion,
                esta_vigente=True
            ).first()
            
            preloaded_instance = InspeccionProducto(
                operario_certificacion=asignacion,
                periodo_validacion=periodo_vigente
            )
        except OperarioCertificacion.DoesNotExist:
            messages.error(request, 'La asignación indicada no está activa o no existe.')
        except Exception as e:
            messages.error(request, f'No se pudieron precargar los datos: {str(e)}')
    
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
        form = InspeccionProductoForm(instance=preloaded_instance)
    
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
def obtener_operarios_por_certificacion(request):
    """Vista AJAX para obtener operarios según la certificación seleccionada"""
    from django.http import JsonResponse
    from apps.asignaciones.models import OperarioCertificacion
    
    certificacion_id = request.GET.get('certificacion_id')
    
    if not certificacion_id:
        return JsonResponse({'error': 'ID de certificación requerido'}, status=400)
    
    try:
        operarios_ids = OperarioCertificacion.objects.filter(
            certificacion_id=certificacion_id,
            esta_activa=True
        ).values_list('operario_id', flat=True)
        
        operarios = Operario.objects.filter(
            id__in=operarios_ids,
            activo=True
        ).order_by('nombre', 'apellidos')
        
        data = {
            'operarios': [
                {'id': o.id, 'nombre': o.nombre_completo} for o in operarios
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
