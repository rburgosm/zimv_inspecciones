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

    niveles = {'critico': 0, 'alto': 1, 'medio': 2, 'normal': 3}

    def escalar(nivel_actual, nivel_nuevo):
        """Devuelve el nivel más severo entre actual y nuevo."""
        return nivel_nuevo if niveles.get(nivel_nuevo, 3) < niveles.get(nivel_actual, 3) else nivel_actual

    def evaluar_criticidad(periodo):
        dias_restantes = (periodo.fecha_fin_periodo - hoy).days
        dias_transcurridos = max((hoy - periodo.fecha_inicio_periodo).days, 0)
        dias_totales = max((periodo.fecha_fin_periodo - periodo.fecha_inicio_periodo).days, 1)

        porcentaje_piezas = (periodo.inspecciones_realizadas / periodo.inspecciones_requeridas * 100) if periodo.inspecciones_requeridas > 0 else 0
        porcentaje_tiempo = (dias_transcurridos / dias_totales * 100)

        nivel_criticidad = 'normal'
        es_critico = False

        # C0: periodo vencido pero marcado como vigente -> crítico duro
        if dias_restantes <= 0:
            return True, 'critico'

        # C1: Vence en <=30 días
        if dias_restantes <= 30:
            es_critico = True
            if dias_restantes <= 7:
                nivel_criticidad = escalar(nivel_criticidad, 'critico')
            elif dias_restantes <= 15:
                nivel_criticidad = escalar(nivel_criticidad, 'alto')
            else:
                nivel_criticidad = escalar(nivel_criticidad, 'medio')

        # C2: <50% piezas y >50% tiempo
        if porcentaje_piezas < 50 and porcentaje_tiempo > 50:
            es_critico = True
            if porcentaje_piezas < 25:
                nivel_criticidad = escalar(nivel_criticidad, 'critico')
            elif porcentaje_piezas < 35:
                nivel_criticidad = escalar(nivel_criticidad, 'alto')
            else:
                nivel_criticidad = escalar(nivel_criticidad, 'medio')

        # C3: <10 piezas y <60 días restantes
        if periodo.inspecciones_realizadas < 10 and dias_restantes < 60:
            es_critico = True
            nivel_criticidad = escalar(nivel_criticidad, 'alto')

        # C4: <40% piezas y >40% tiempo
        if porcentaje_piezas < 40 and porcentaje_tiempo > 40:
            es_critico = True
            if porcentaje_piezas < 20:
                nivel_criticidad = escalar(nivel_criticidad, 'critico')
            elif porcentaje_piezas < 30:
                nivel_criticidad = escalar(nivel_criticidad, 'alto')
            else:
                nivel_criticidad = escalar(nivel_criticidad, 'medio')

        # C5: <=90 días restantes y <60% piezas
        if dias_restantes <= 90 and porcentaje_piezas < 60:
            es_critico = True
            if dias_restantes <= 30:
                nivel_criticidad = escalar(nivel_criticidad, 'critico')
            elif dias_restantes <= 60:
                nivel_criticidad = escalar(nivel_criticidad, 'alto')
            else:
                nivel_criticidad = escalar(nivel_criticidad, 'medio')

        return es_critico, nivel_criticidad
    
    # Calcular criticidad y métricas por periodo
    for periodo in periodos_vigentes_qs:
        dias_restantes = (periodo.fecha_fin_periodo - hoy).days
        dias_transcurridos = max((hoy - periodo.fecha_inicio_periodo).days, 0)
        dias_totales = max((periodo.fecha_fin_periodo - periodo.fecha_inicio_periodo).days, 1)

        porcentaje_piezas = (periodo.inspecciones_realizadas / periodo.inspecciones_requeridas * 100) if periodo.inspecciones_requeridas > 0 else 0
        porcentaje_tiempo = (dias_transcurridos / dias_totales * 100)

        es_critico, nivel_criticidad = evaluar_criticidad(periodo)

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
    
    # Ordenar todos los vigentes por criticidad y distancia a completarse
    periodos_vigentes_lista.sort(key=lambda x: (
        niveles.get(x['nivel_criticidad'], 3),
        -x['piezas_faltantes'],  # más lejos de completar primero
        x['dias_restantes']
    ))

    # Ordenar críticos por severidad, avance y proximidad de vencimiento
    periodos_criticos_lista.sort(key=lambda x: (
        niveles.get(x['nivel_criticidad'], 3),
        x['porcentaje_piezas'],  # menos avance primero
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
