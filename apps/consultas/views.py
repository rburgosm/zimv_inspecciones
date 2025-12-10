from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from apps.operarios.models import Operario
from apps.asignaciones.models import OperarioCertificacion
from apps.inspecciones.signals import verificar_caducidades_pendientes


@login_required
def detalle_operario_completo(request, pk):
    """Vista completa del operario con todas sus certificaciones, periodos e inspecciones"""
    # Verificar caducidades pendientes antes de mostrar el detalle
    verificar_caducidades_pendientes()
    
    operario = get_object_or_404(Operario, pk=pk)
    
    asignaciones = OperarioCertificacion.objects.filter(
        operario=operario
    ).select_related('certificacion').prefetch_related(
        'periodos__inspecciones__auditoria_producto',
        'periodos__inspecciones__auditor'
    ).order_by('-fecha_asignacion')
    
    return render(request, 'consultas/detalle_operario.html', {
        'operario': operario,
        'asignaciones': asignaciones
    })
