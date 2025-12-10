from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import OperarioCertificacion
from apps.inspecciones.models import PeriodoValidacionCertificacion, ConfiguracionInspecciones
from .utils import calcular_fecha_fin_periodo


@receiver(post_save, sender=OperarioCertificacion)
def crear_periodo_inicial(sender, instance, created, **kwargs):
    """
    Al crear una nueva asignación operario-certificación,
    se crea automáticamente el periodo de validación nº1.
    """
    if created and instance.esta_activa:
        config = ConfiguracionInspecciones.get_activa()
        if not config:
            # Valores por defecto si no hay configuración
            dias_laborables = 180
            piezas_requeridas = 29  # 29 piezas, no 29 inspecciones
        else:
            dias_laborables = config.numero_dias_laborales_req
            piezas_requeridas = config.inspecciones_minimas  # Este campo realmente representa piezas, no inspecciones

        fecha_fin = calcular_fecha_fin_periodo(instance.fecha_asignacion, dias_laborables)
        
        PeriodoValidacionCertificacion.objects.create(
            operario_certificacion=instance,
            numero_periodo=1,
            fecha_inicio_periodo=instance.fecha_asignacion,
            fecha_fin_periodo=fecha_fin,
            numero_dias_laborales_req=dias_laborables,
            inspecciones_requeridas=piezas_requeridas,  # Piezas requeridas (29)
            inspecciones_realizadas=0,  # Contador de piezas auditadas (suma de piezas_auditadas)
            esta_completado=False,
            esta_vigente=True,
            usuario_creacion=instance.usuario_creacion
        )
