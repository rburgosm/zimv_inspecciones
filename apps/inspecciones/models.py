from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.asignaciones.models import OperarioCertificacion
from apps.auditorias.models import AuditoriaProducto
from apps.auditores.models import Auditor


class ConfiguracionInspecciones(models.Model):
    """Configuración global para inspecciones"""
    numero_dias_laborales_req = models.IntegerField(default=180, verbose_name="Número de días laborables requeridos")
    inspecciones_minimas = models.IntegerField(default=29, verbose_name="Piezas mínimas requeridas",
                                                help_text="Número total de piezas que deben ser auditadas por periodo (29 por defecto)")
    esta_activo = models.BooleanField(default=True, verbose_name="Está activo")
    fecha_inicio_vigencia = models.DateField(blank=True, null=True, verbose_name="Fecha inicio vigencia")
    fecha_fin_vigencia = models.DateField(blank=True, null=True, verbose_name="Fecha fin vigencia")
    fecha_creacion = models.DateTimeField(default=timezone.now, verbose_name="Fecha de creación")
    usuario_creacion = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='configuraciones_creadas',
        null=True,
        blank=True,
        verbose_name="Usuario creación"
    )
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")
    usuario_actualizacion = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='configuraciones_actualizadas',
        null=True,
        blank=True,
        verbose_name="Usuario actualización"
    )

    class Meta:
        verbose_name = "Configuración de Inspecciones"
        verbose_name_plural = "Configuraciones de Inspecciones"

    def __str__(self):
        return f"Configuración: {self.inspecciones_minimas} inspecciones en {self.numero_dias_laborales_req} días"

    @classmethod
    def get_activa(cls):
        """Retorna la configuración activa"""
        return cls.objects.filter(esta_activo=True).first()


class PeriodoValidacionCertificacion(models.Model):
    operario_certificacion = models.ForeignKey(
        OperarioCertificacion,
        on_delete=models.RESTRICT,
        related_name='periodos',
        verbose_name="Asignación Operario-Certificación"
    )
    numero_periodo = models.IntegerField(verbose_name="Número de periodo")
    fecha_inicio_periodo = models.DateField(verbose_name="Fecha inicio periodo")
    fecha_fin_periodo = models.DateField(verbose_name="Fecha fin periodo")
    numero_dias_laborales_req = models.IntegerField(default=180, verbose_name="Número de días laborables requeridos")
    inspecciones_requeridas = models.IntegerField(default=29, verbose_name="Piezas requeridas",
                                                   help_text="Número total de piezas que deben ser auditadas en este periodo (29 por defecto)")
    inspecciones_realizadas = models.IntegerField(default=0, verbose_name="Piezas realizadas", 
                                                  help_text="Total de piezas auditadas en este periodo (suma de piezas_auditadas de todas las inspecciones)")
    esta_completado = models.BooleanField(default=False, verbose_name="Está completado")
    fecha_completado = models.DateField(blank=True, null=True, verbose_name="Fecha completado")
    esta_vigente = models.BooleanField(default=True, verbose_name="Está vigente")
    fecha_creacion = models.DateTimeField(default=timezone.now, verbose_name="Fecha de creación")
    usuario_creacion = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='periodos_creados',
        null=True,
        blank=True,
        verbose_name="Usuario creación"
    )
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")
    usuario_actualizacion = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='periodos_actualizados',
        null=True,
        blank=True,
        verbose_name="Usuario actualización"
    )

    class Meta:
        verbose_name = "Periodo de Validación"
        verbose_name_plural = "Periodos de Validación"
        unique_together = [['operario_certificacion', 'numero_periodo']]
        constraints = [
            models.UniqueConstraint(
                fields=['operario_certificacion'],
                condition=models.Q(esta_vigente=True),
                name='periodo_vigente_unico'
            )
        ]
        ordering = ['operario_certificacion', 'numero_periodo']

    def __str__(self):
        return f"Periodo {self.numero_periodo} - {self.operario_certificacion} ({self.fecha_inicio_periodo} a {self.fecha_fin_periodo})"

    def clean(self):
        if self.fecha_fin_periodo < self.fecha_inicio_periodo:
            raise ValidationError("La fecha de fin no puede ser anterior a la fecha de inicio")


class InspeccionProducto(models.Model):
    RESULTADO_CHOICES = [
        ('OK', 'OK'),
        ('NO OK', 'NO OK'),
    ]

    operario_certificacion = models.ForeignKey(
        OperarioCertificacion,
        on_delete=models.RESTRICT,
        related_name='inspecciones',
        verbose_name="Asignación Operario-Certificación"
    )
    periodo_validacion = models.ForeignKey(
        PeriodoValidacionCertificacion,
        on_delete=models.RESTRICT,
        related_name='inspecciones',
        verbose_name="Periodo de validación"
    )
    auditoria_producto = models.ForeignKey(
        AuditoriaProducto,
        on_delete=models.RESTRICT,
        related_name='inspecciones',
        verbose_name="Auditoría de producto"
    )
    auditor = models.ForeignKey(
        Auditor,
        on_delete=models.RESTRICT,
        related_name='inspecciones',
        verbose_name="Auditor"
    )
    fecha_inspeccion = models.DateField(verbose_name="Fecha de inspección")
    piezas_auditadas = models.IntegerField(verbose_name="Piezas auditadas")
    resultado_inspeccion = models.CharField(
        max_length=10,
        choices=RESULTADO_CHOICES,
        blank=True,
        null=True,
        verbose_name="Resultado inspección"
    )
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    numero_orden = models.CharField(max_length=100, blank=True, null=True, verbose_name="Número de orden",
                                    help_text="Número de orden que generó las piezas")
    fecha_creacion = models.DateTimeField(default=timezone.now, verbose_name="Fecha de creación")
    usuario_creacion = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='inspecciones_creadas',
        null=True,
        blank=True,
        verbose_name="Usuario creación"
    )
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")
    usuario_actualizacion = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='inspecciones_actualizadas',
        null=True,
        blank=True,
        verbose_name="Usuario actualización"
    )

    class Meta:
        verbose_name = "Inspección de Producto"
        verbose_name_plural = "Inspecciones de Producto"
        ordering = ['-fecha_inspeccion', '-fecha_creacion']
        indexes = [
            models.Index(fields=['operario_certificacion', 'fecha_inspeccion']),
            models.Index(fields=['periodo_validacion', 'fecha_inspeccion']),
        ]

    def __str__(self):
        return f"Inspección {self.fecha_inspeccion} - {self.operario_certificacion}"

    def clean(self):
        # Validar que la fecha de inspección esté dentro del periodo
        if self.periodo_validacion:
            if self.fecha_inspeccion < self.periodo_validacion.fecha_inicio_periodo:
                raise ValidationError("La fecha de inspección no puede ser anterior al inicio del periodo")
            if self.fecha_inspeccion > self.periodo_validacion.fecha_fin_periodo:
                raise ValidationError("La fecha de inspección no puede ser posterior al fin del periodo")
        
        # Validar que el periodo esté vigente
        if self.periodo_validacion and not self.periodo_validacion.esta_vigente:
            raise ValidationError("No se pueden registrar inspecciones en periodos no vigentes")
