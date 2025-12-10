from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.utils import timezone
from .models import InspeccionProducto, PeriodoValidacionCertificacion, ConfiguracionInspecciones
from apps.asignaciones.utils import calcular_fecha_fin_periodo, siguiente_dia_laborable


@receiver(post_save, sender=InspeccionProducto)
def actualizar_periodo_y_crear_siguiente(sender, instance, created, **kwargs):
    """
    Al registrar una inspección:
    1. Suma las piezas auditadas al contador del periodo (no cuenta inspecciones, sino piezas)
    2. Si llega a 29 piezas: marca periodo como completado y crea nuevo periodo
    3. Verifica si el periodo ha vencido sin completarse
    """
    if created:
        with transaction.atomic():
            periodo = instance.periodo_validacion
            
            # Sumar las piezas auditadas de esta inspección al contador total
            # El contador almacena el total de piezas auditadas, no el número de inspecciones
            periodo.inspecciones_realizadas += instance.piezas_auditadas
            periodo.save(update_fields=['inspecciones_realizadas', 'fecha_actualizacion'])
            
            config = ConfiguracionInspecciones.get_activa()
            piezas_requeridas = config.inspecciones_minimas if config else 29
            
            # Si se alcanza el número requerido de piezas (29)
            if periodo.inspecciones_realizadas >= piezas_requeridas:
                # Marcar periodo como completado
                periodo.esta_completado = True
                periodo.esta_vigente = False
                periodo.fecha_completado = instance.fecha_inspeccion
                periodo.save(update_fields=['esta_completado', 'esta_vigente', 'fecha_completado', 'fecha_actualizacion'])
                
                # Crear nuevo periodo
                dias_laborables = config.numero_dias_laborales_req if config else 180
                fecha_inicio_nuevo = siguiente_dia_laborable(instance.fecha_inspeccion)
                fecha_fin_nuevo = calcular_fecha_fin_periodo(fecha_inicio_nuevo, dias_laborables)
                
                # Obtener el siguiente número de periodo
                ultimo_periodo = PeriodoValidacionCertificacion.objects.filter(
                    operario_certificacion=periodo.operario_certificacion
                ).order_by('-numero_periodo').first()
                
                nuevo_numero = ultimo_periodo.numero_periodo + 1 if ultimo_periodo else 2
                
                PeriodoValidacionCertificacion.objects.create(
                    operario_certificacion=periodo.operario_certificacion,
                    numero_periodo=nuevo_numero,
                    fecha_inicio_periodo=fecha_inicio_nuevo,
                    fecha_fin_periodo=fecha_fin_nuevo,
                    numero_dias_laborales_req=dias_laborables,
                    inspecciones_requeridas=piezas_requeridas,
                    inspecciones_realizadas=0,
                    esta_completado=False,
                    esta_vigente=True,
                    usuario_creacion=instance.usuario_creacion
                )
            
            # Verificar si el periodo ha vencido sin completarse
            verificar_caducidad_periodo(periodo)


def verificar_caducidad_periodo(periodo):
    """
    Verifica si un periodo ha vencido sin completarse y marca la certificación como caducada.
    """
    from django.utils import timezone
    hoy = timezone.now().date()
    
    if periodo.esta_vigente and not periodo.esta_completado:
        if hoy > periodo.fecha_fin_periodo:
            # Marcar certificación como caducada
            asignacion = periodo.operario_certificacion
            asignacion.esta_activa = False
            asignacion.fecha_caducidad = periodo.fecha_fin_periodo
            asignacion.save(update_fields=['esta_activa', 'fecha_caducidad', 'fecha_actualizacion'])
            
            # Marcar periodo como no vigente
            periodo.esta_vigente = False
            periodo.save(update_fields=['esta_vigente', 'fecha_actualizacion'])


def verificar_caducidades_pendientes():
    """
    Verifica todos los periodos vigentes que han vencido y marca las certificaciones como caducadas.
    Esta función puede ser llamada desde una vista o un comando de gestión.
    """
    from django.utils import timezone
    from .models import PeriodoValidacionCertificacion
    
    hoy = timezone.now().date()
    periodos_vencidos = PeriodoValidacionCertificacion.objects.filter(
        esta_vigente=True,
        esta_completado=False,
        fecha_fin_periodo__lt=hoy
    ).select_related('operario_certificacion')
    
    for periodo in periodos_vencidos:
        verificar_caducidad_periodo(periodo)
    
    return periodos_vencidos.count()
