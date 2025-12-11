from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from apps.inspecciones.models import PeriodoValidacionCertificacion
from apps.inspecciones.signals import verificar_caducidades_pendientes


def login_view(request):
    """Vista de login"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenido, {user.username}')
            return redirect('home')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    
    return render(request, 'usuarios/login.html')


@login_required
def logout_view(request):
    """Vista de logout"""
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente')
    return redirect('usuarios:login')


@login_required
def home_view(request):
    """Vista principal del sistema con dashboard"""
    # Verificar caducidades pendientes
    verificar_caducidades_pendientes()
    
    hoy = timezone.now().date()
    fecha_limite = hoy + timedelta(days=30)  # Próximos 30 días
    
    # Obtener todos los periodos vigentes para calcular métricas y criticidad
    periodos_vigentes_qs = PeriodoValidacionCertificacion.objects.filter(
        esta_vigente=True,
        esta_completado=False
    ).select_related(
        'operario_certificacion__operario',
        'operario_certificacion__certificacion'
    ).order_by('fecha_fin_periodo')
    
    periodos_vigentes_lista = []
    periodos_criticos_lista = []
    
    # Calcular criticidad y métricas por periodo
    for periodo in periodos_vigentes_qs:
        dias_restantes = (periodo.fecha_fin_periodo - hoy).days
        dias_transcurridos = (hoy - periodo.fecha_inicio_periodo).days
        dias_totales = (periodo.fecha_fin_periodo - periodo.fecha_inicio_periodo).days
        
        porcentaje_piezas = (periodo.inspecciones_realizadas / periodo.inspecciones_requeridas * 100) if periodo.inspecciones_requeridas > 0 else 0
        porcentaje_tiempo = (dias_transcurridos / dias_totales * 100) if dias_totales > 0 else 0
        
        es_critico = False
        nivel_criticidad = 'normal'
        
        # Criterio 1: Vence en menos de 30 días
        if dias_restantes <= 30 and dias_restantes > 0:
            es_critico = True
            if dias_restantes <= 7:
                nivel_criticidad = 'critico'
            elif dias_restantes <= 15:
                nivel_criticidad = 'alto'
            else:
                nivel_criticidad = 'medio'
        
        # Criterio 2: Menos del 50% de piezas y más del 50% del tiempo transcurrido
        if porcentaje_piezas < 50 and porcentaje_tiempo > 50:
            es_critico = True
            if porcentaje_piezas < 25:
                nivel_criticidad = 'critico'
            elif porcentaje_piezas < 35:
                nivel_criticidad = 'alto'
            else:
                nivel_criticidad = 'medio'
        
        # Criterio 3: Menos de 10 piezas y quedan menos de 60 días
        if periodo.inspecciones_realizadas < 10 and dias_restantes < 60 and dias_restantes > 0:
            es_critico = True
            nivel_criticidad = 'alto'
        
        # Criterio 4: Menos del 40% de piezas y más del 40% del tiempo (más flexible)
        if porcentaje_piezas < 40 and porcentaje_tiempo > 40:
            es_critico = True
            if porcentaje_piezas < 20:
                nivel_criticidad = 'critico'
            elif porcentaje_piezas < 30:
                nivel_criticidad = 'alto'
            else:
                nivel_criticidad = 'medio'
        
        # Criterio 5: Vence en menos de 90 días y tiene menos del 60% de piezas
        if dias_restantes <= 90 and dias_restantes > 0 and porcentaje_piezas < 60:
            es_critico = True
            if dias_restantes <= 30:
                nivel_criticidad = 'critico' if nivel_criticidad == 'normal' else nivel_criticidad
            elif dias_restantes <= 60:
                nivel_criticidad = 'alto' if nivel_criticidad == 'normal' else nivel_criticidad
            else:
                nivel_criticidad = 'medio' if nivel_criticidad == 'normal' else nivel_criticidad
        
        periodo_data = {
            'periodo': periodo,
            'dias_restantes': dias_restantes,
            'porcentaje_piezas': round(porcentaje_piezas, 1),
            'porcentaje_tiempo': round(porcentaje_tiempo, 1),
            'nivel_criticidad': nivel_criticidad,
            'piezas_faltantes': periodo.inspecciones_requeridas - periodo.inspecciones_realizadas
        }
        periodos_vigentes_lista.append(periodo_data)
        
        if es_critico:
            periodos_criticos_lista.append(periodo_data)
    
    # Ordenar por nivel de criticidad y días restantes
    periodos_criticos_lista.sort(key=lambda x: (
        {'critico': 0, 'alto': 1, 'medio': 2, 'normal': 3}[x['nivel_criticidad']],
        x['dias_restantes']
    ))
    
    # Estadísticas generales
    from apps.operarios.models import Operario
    from apps.certificaciones.models import Certificacion
    from apps.asignaciones.models import OperarioCertificacion
    from apps.inspecciones.models import InspeccionProducto
    from django.db.models import Count, Q
    from datetime import datetime
    
    stats = {
        'operarios_activos': Operario.objects.filter(activo=True).count(),
        'certificaciones_activas': Certificacion.objects.filter(activa=True).count(),
        'asignaciones_activas': OperarioCertificacion.objects.filter(esta_activa=True).count(),
        'periodos_vigentes': PeriodoValidacionCertificacion.objects.filter(esta_vigente=True).count(),
        'inspecciones_mes': InspeccionProducto.objects.filter(
            fecha_inspeccion__year=hoy.year,
            fecha_inspeccion__month=hoy.month
        ).count(),
        'periodos_criticos_count': len(periodos_criticos_lista),
    }
    
    return render(request, 'home.html', {
        'periodos_criticos': periodos_criticos_lista[:10],  # Mostrar solo los 10 más críticos
        'periodos_vigentes': periodos_vigentes_lista,
        'stats': stats
    })
