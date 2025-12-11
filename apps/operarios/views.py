import json
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
    """Detalle de operario con estadísticas de inspecciones"""
    operario = get_object_or_404(Operario, pk=pk)
    
    # Calcular todas las estadísticas
    estadisticas = {
        # Fase 1: Estadísticas principales
        'total_inspecciones': operario.total_inspecciones(),
        'total_piezas_auditadas': operario.total_piezas_auditadas(),
        'promedio_piezas': operario.promedio_piezas_por_inspeccion(),
        'primera_inspeccion': operario.primera_inspeccion(),
        'ultima_inspeccion': operario.ultima_inspeccion(),
        'dias_desde_ultima': operario.dias_desde_ultima_inspeccion(),
        'inspecciones_ok': operario.inspecciones_ok(),
        'inspecciones_no_ok': operario.inspecciones_no_ok(),
        'inspecciones_sin_resultado': operario.inspecciones_sin_resultado(),
        'tasa_exito': operario.tasa_exito(),
        'tasa_no_conformidad': operario.tasa_no_conformidad(),
        
        # Fase 1: Estadísticas por certificación
        'por_certificacion': operario.estadisticas_por_certificacion(),
        
        # Fase 2: Estadísticas por períodos
        'ultimo_mes': operario.estadisticas_ultimo_mes(),
        'ultimos_3_meses': operario.estadisticas_ultimos_3_meses(),
        'ultimo_ano': operario.estadisticas_ultimo_ano(),
        
        # Fase 2: Estadísticas por auditor
        'por_auditor': operario.estadisticas_por_auditor(),
        
        # Fase 2: Estadísticas por auditoría de producto
        'por_auditoria': operario.estadisticas_por_auditoria_producto(),
        
        # Fase 2: Datos para gráfico
        'grafico_evolucion': (lambda datos: json.dumps(datos, ensure_ascii=False) if datos and datos.get('labels') and len(datos.get('labels', [])) > 0 else None)(operario.datos_grafico_evolucion(12)),
        
        # Alertas
        'ultima_no_ok': operario.ultima_inspeccion_no_ok(),
    }
    
    return render(request, 'operarios/detalle.html', {
        'operario': operario,
        'estadisticas': estadisticas
    })
