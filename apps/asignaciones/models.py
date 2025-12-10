from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.operarios.models import Operario
from apps.certificaciones.models import Certificacion
from .utils import calcular_fecha_fin_periodo, siguiente_dia_laborable


class OperarioCertificacion(models.Model):
    operario = models.ForeignKey(
        Operario,
        on_delete=models.RESTRICT,
        related_name='certificaciones',
        verbose_name="Operario"
    )
    certificacion = models.ForeignKey(
        Certificacion,
        on_delete=models.RESTRICT,
        related_name='operarios',
        verbose_name="Certificación"
    )
    fecha_asignacion = models.DateField(verbose_name="Fecha de asignación")
    esta_activa = models.BooleanField(default=True, verbose_name="Está activa")
    fecha_caducidad = models.DateField(blank=True, null=True, verbose_name="Fecha de caducidad")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    fecha_creacion = models.DateTimeField(default=timezone.now, verbose_name="Fecha de creación")
    usuario_creacion = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='asignaciones_creadas',
        null=True,
        blank=True,
        verbose_name="Usuario creación"
    )
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")
    usuario_actualizacion = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='asignaciones_actualizadas',
        null=True,
        blank=True,
        verbose_name="Usuario actualización"
    )

    class Meta:
        verbose_name = "Asignación Operario-Certificación"
        verbose_name_plural = "Asignaciones Operario-Certificación"
        unique_together = [['operario', 'certificacion', 'fecha_asignacion']]
        ordering = ['-fecha_asignacion']

    def __str__(self):
        return f"{self.operario.nombre_completo} - {self.certificacion.nombre} ({self.fecha_asignacion})"

    def clean(self):
        if self.fecha_caducidad and self.fecha_asignacion:
            if self.fecha_caducidad < self.fecha_asignacion:
                raise ValidationError("La fecha de caducidad no puede ser anterior a la fecha de asignación")
