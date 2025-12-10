from django.contrib import admin
from .models import ConfiguracionInspecciones, PeriodoValidacionCertificacion, InspeccionProducto


@admin.register(ConfiguracionInspecciones)
class ConfiguracionInspeccionesAdmin(admin.ModelAdmin):
    list_display = ['numero_dias_laborales_req', 'inspecciones_minimas', 'esta_activo', 'fecha_inicio_vigencia']
    list_filter = ['esta_activo']
    search_fields = []


@admin.register(PeriodoValidacionCertificacion)
class PeriodoValidacionCertificacionAdmin(admin.ModelAdmin):
    list_display = ['operario_certificacion', 'numero_periodo', 'fecha_inicio_periodo', 'fecha_fin_periodo', 
                    'inspecciones_realizadas', 'inspecciones_requeridas', 'esta_vigente', 'esta_completado']
    list_filter = ['esta_vigente', 'esta_completado']
    search_fields = ['operario_certificacion__operario__nombre', 'operario_certificacion__certificacion__nombre']


@admin.register(InspeccionProducto)
class InspeccionProductoAdmin(admin.ModelAdmin):
    list_display = ['fecha_inspeccion', 'operario_certificacion', 'auditoria_producto', 'auditor', 
                    'piezas_auditadas', 'resultado_inspeccion']
    list_filter = ['fecha_inspeccion', 'resultado_inspeccion']
    search_fields = ['operario_certificacion__operario__nombre', 'auditor__nombre']
    date_hierarchy = 'fecha_inspeccion'
