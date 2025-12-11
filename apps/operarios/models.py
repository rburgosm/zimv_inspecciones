from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Sum, Avg, Q, Max, Min
from django.utils import timezone as tz


class Operario(models.Model):
    codigo = models.CharField(max_length=50, blank=True, null=True, verbose_name="Código")
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    apellidos = models.CharField(max_length=100, blank=True, null=True, verbose_name="Apellidos")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_creacion = models.DateTimeField(default=timezone.now, verbose_name="Fecha de creación")
    usuario_creacion = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='operarios_creados',
        null=True,
        blank=True,
        verbose_name="Usuario creación"
    )
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")
    usuario_actualizacion = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='operarios_actualizados',
        null=True,
        blank=True,
        verbose_name="Usuario actualización"
    )

    class Meta:
        verbose_name = "Operario"
        verbose_name_plural = "Operarios"
        ordering = ['nombre', 'apellidos']

    def __str__(self):
        if self.apellidos:
            return f"{self.nombre} {self.apellidos}"
        return self.nombre

    @property
    def nombre_completo(self):
        if self.apellidos:
            return f"{self.nombre} {self.apellidos}"
        return self.nombre

    def obtener_inspecciones(self):
        """Obtiene todas las inspecciones del operario"""
        from apps.inspecciones.models import InspeccionProducto
        return InspeccionProducto.objects.filter(
            operario_certificacion__operario=self
        ).select_related(
            'operario_certificacion__certificacion',
            'auditoria_producto',
            'auditor'
        ).order_by('-fecha_inspeccion')

    def total_inspecciones(self):
        """Total de inspecciones realizadas"""
        return self.obtener_inspecciones().count()

    def total_piezas_auditadas(self):
        """Total de piezas auditadas en todas las inspecciones"""
        resultado = self.obtener_inspecciones().aggregate(
            total=Sum('piezas_auditadas')
        )
        return resultado['total'] or 0

    def promedio_piezas_por_inspeccion(self):
        """Promedio de piezas auditadas por inspección"""
        total = self.total_inspecciones()
        if total == 0:
            return 0
        return round(self.total_piezas_auditadas() / total, 2)

    def primera_inspeccion(self):
        """Fecha de la primera inspección"""
        primera = self.obtener_inspecciones().aggregate(
            primera=Min('fecha_inspeccion')
        )
        return primera['primera']

    def ultima_inspeccion(self):
        """Fecha de la última inspección"""
        ultima = self.obtener_inspecciones().aggregate(
            ultima=Max('fecha_inspeccion')
        )
        return ultima['ultima']

    def dias_desde_ultima_inspeccion(self):
        """Días transcurridos desde la última inspección"""
        ultima = self.ultima_inspeccion()
        if not ultima:
            return None
        hoy = tz.now().date()
        return (hoy - ultima).days

    def inspecciones_ok(self):
        """Número de inspecciones con resultado OK"""
        return self.obtener_inspecciones().filter(resultado_inspeccion='OK').count()

    def inspecciones_no_ok(self):
        """Número de inspecciones con resultado NO OK"""
        return self.obtener_inspecciones().filter(resultado_inspeccion='NO OK').count()

    def inspecciones_sin_resultado(self):
        """Número de inspecciones sin resultado"""
        return self.obtener_inspecciones().filter(
            Q(resultado_inspeccion__isnull=True) | Q(resultado_inspeccion='')
        ).count()

    def tasa_exito(self):
        """Porcentaje de inspecciones con resultado OK"""
        total = self.total_inspecciones()
        if total == 0:
            return 0
        ok = self.inspecciones_ok()
        return round((ok / total) * 100, 2)

    def tasa_no_conformidad(self):
        """Porcentaje de inspecciones con resultado NO OK"""
        total = self.total_inspecciones()
        if total == 0:
            return 0
        no_ok = self.inspecciones_no_ok()
        return round((no_ok / total) * 100, 2)

    def estadisticas_por_periodo(self, dias):
        """Estadísticas de inspecciones en los últimos N días"""
        fecha_limite = tz.now().date() - timedelta(days=dias)
        inspecciones = self.obtener_inspecciones().filter(
            fecha_inspeccion__gte=fecha_limite
        )
        
        total = inspecciones.count()
        piezas = inspecciones.aggregate(total=Sum('piezas_auditadas'))['total'] or 0
        ok = inspecciones.filter(resultado_inspeccion='OK').count()
        no_ok = inspecciones.filter(resultado_inspeccion='NO OK').count()
        tasa_exito = round((ok / total * 100), 2) if total > 0 else 0
        
        return {
            'total': total,
            'piezas': piezas,
            'ok': ok,
            'no_ok': no_ok,
            'tasa_exito': tasa_exito
        }

    def estadisticas_ultimo_mes(self):
        """Estadísticas del último mes (30 días)"""
        return self.estadisticas_por_periodo(30)

    def estadisticas_ultimos_3_meses(self):
        """Estadísticas de los últimos 3 meses (90 días)"""
        return self.estadisticas_por_periodo(90)

    def estadisticas_ultimo_ano(self):
        """Estadísticas del último año (365 días)"""
        return self.estadisticas_por_periodo(365)

    def estadisticas_por_certificacion(self):
        """Estadísticas agrupadas por certificación"""
        from django.db.models import Count, Sum, Avg
        from apps.asignaciones.models import OperarioCertificacion
        
        certificaciones = OperarioCertificacion.objects.filter(
            operario=self
        ).select_related('certificacion').prefetch_related('inspecciones')
        
        estadisticas = []
        for cert in certificaciones:
            inspecciones = cert.inspecciones.all()
            total_inspecciones = inspecciones.count()
            total_piezas = sum(i.piezas_auditadas for i in inspecciones)
            ok = inspecciones.filter(resultado_inspeccion='OK').count()
            no_ok = inspecciones.filter(resultado_inspeccion='NO OK').count()
            tasa_exito = round((ok / total_inspecciones * 100), 2) if total_inspecciones > 0 else 0
            
            estadisticas.append({
                'certificacion': cert.certificacion,
                'asignacion': cert,
                'total_inspecciones': total_inspecciones,
                'total_piezas': total_piezas,
                'ok': ok,
                'no_ok': no_ok,
                'tasa_exito': tasa_exito,
                'esta_activa': cert.esta_activa
            })
        
        return estadisticas

    def estadisticas_por_auditor(self):
        """Estadísticas agrupadas por auditor"""
        from django.db.models import Count, Sum
        
        inspecciones = self.obtener_inspecciones().exclude(auditor__isnull=True)
        
        resultados = inspecciones.values('auditor__id', 'auditor__nombre', 'auditor__apellidos').annotate(
            total_inspecciones=Count('id'),
            total_piezas=Sum('piezas_auditadas'),
            ok=Count('id', filter=Q(resultado_inspeccion='OK')),
            no_ok=Count('id', filter=Q(resultado_inspeccion='NO OK'))
        ).order_by('-total_inspecciones')
        
        estadisticas = []
        for resultado in resultados:
            total = resultado['total_inspecciones']
            tasa_exito = round((resultado['ok'] / total * 100), 2) if total > 0 else 0
            
            nombre_completo = resultado['auditor__nombre']
            if resultado['auditor__apellidos']:
                nombre_completo += f" {resultado['auditor__apellidos']}"
            
            estadisticas.append({
                'auditor_id': resultado['auditor__id'],
                'auditor_nombre': nombre_completo,
                'total_inspecciones': total,
                'total_piezas': resultado['total_piezas'] or 0,
                'ok': resultado['ok'],
                'no_ok': resultado['no_ok'],
                'tasa_exito': tasa_exito
            })
        
        return estadisticas

    def estadisticas_por_auditoria_producto(self):
        """Estadísticas agrupadas por auditoría de producto"""
        from django.db.models import Count, Sum
        
        inspecciones = self.obtener_inspecciones().exclude(auditoria_producto__isnull=True)
        
        resultados = inspecciones.values(
            'auditoria_producto__id', 
            'auditoria_producto__nombre'
        ).annotate(
            total_inspecciones=Count('id'),
            total_piezas=Sum('piezas_auditadas'),
            ok=Count('id', filter=Q(resultado_inspeccion='OK')),
            no_ok=Count('id', filter=Q(resultado_inspeccion='NO OK'))
        ).order_by('-total_inspecciones')
        
        estadisticas = []
        for resultado in resultados:
            total = resultado['total_inspecciones']
            tasa_exito = round((resultado['ok'] / total * 100), 2) if total > 0 else 0
            
            estadisticas.append({
                'auditoria_id': resultado['auditoria_producto__id'],
                'auditoria_nombre': resultado['auditoria_producto__nombre'],
                'total_inspecciones': total,
                'total_piezas': resultado['total_piezas'] or 0,
                'ok': resultado['ok'],
                'no_ok': resultado['no_ok'],
                'tasa_exito': tasa_exito
            })
        
        return estadisticas

    def datos_grafico_evolucion(self, meses=12):
        """Datos para gráfico de evolución temporal"""
        from django.db.models import Count, Sum
        from datetime import datetime, timedelta
        import calendar
        
        # Calcular fecha de inicio (N meses atrás)
        hoy = tz.now().date()
        fecha_inicio = hoy - timedelta(days=meses * 30)
        
        inspecciones = self.obtener_inspecciones().filter(
            fecha_inspeccion__gte=fecha_inicio
        )
        
        # Agrupar por mes
        datos_mensuales = {}
        meses_esp = {
            1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun',
            7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
        }
        
        for inspeccion in inspecciones:
            mes_anio = inspeccion.fecha_inspeccion.strftime('%Y-%m')
            if mes_anio not in datos_mensuales:
                mes_num = inspeccion.fecha_inspeccion.month
                anio = inspeccion.fecha_inspeccion.year
                datos_mensuales[mes_anio] = {
                    'mes': f"{meses_esp[mes_num]} {anio}",
                    'inspecciones': 0,
                    'piezas': 0,
                    'ok': 0,
                    'no_ok': 0
                }
            
            datos_mensuales[mes_anio]['inspecciones'] += 1
            datos_mensuales[mes_anio]['piezas'] += inspeccion.piezas_auditadas
            if inspeccion.resultado_inspeccion == 'OK':
                datos_mensuales[mes_anio]['ok'] += 1
            elif inspeccion.resultado_inspeccion == 'NO OK':
                datos_mensuales[mes_anio]['no_ok'] += 1
        
        # Ordenar por fecha
        meses_ordenados = sorted(datos_mensuales.keys())
        
        return {
            'labels': [datos_mensuales[m]['mes'] for m in meses_ordenados],
            'inspecciones': [datos_mensuales[m]['inspecciones'] for m in meses_ordenados],
            'piezas': [datos_mensuales[m]['piezas'] for m in meses_ordenados],
            'ok': [datos_mensuales[m]['ok'] for m in meses_ordenados],
            'no_ok': [datos_mensuales[m]['no_ok'] for m in meses_ordenados],
            'tasa_exito': [
                round((datos_mensuales[m]['ok'] / datos_mensuales[m]['inspecciones'] * 100), 2) 
                if datos_mensuales[m]['inspecciones'] > 0 else 0 
                for m in meses_ordenados
            ]
        }

    def ultima_inspeccion_no_ok(self):
        """Información de la última inspección con resultado NO OK"""
        return self.obtener_inspecciones().filter(
            resultado_inspeccion='NO OK'
        ).first()
