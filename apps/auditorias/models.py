from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from apps.certificaciones.models import Certificacion


class AuditoriaProducto(models.Model):
    certificacion = models.ForeignKey(
        Certificacion,
        on_delete=models.RESTRICT,
        related_name='auditorias',
        verbose_name="Certificación"
    )
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    activa = models.BooleanField(default=True, verbose_name="Activa")
    fecha_creacion = models.DateTimeField(default=timezone.now, verbose_name="Fecha de creación")
    usuario_creacion = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='auditorias_creadas',
        null=True,
        blank=True,
        verbose_name="Usuario creación"
    )
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")
    usuario_actualizacion = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='auditorias_actualizadas',
        null=True,
        blank=True,
        verbose_name="Usuario actualización"
    )

    class Meta:
        verbose_name = "Auditoría de Producto"
        verbose_name_plural = "Auditorías de Producto"
        unique_together = [['certificacion', 'nombre']]
        ordering = ['certificacion', 'nombre']

    def __str__(self):
        return f"{self.certificacion.nombre} - {self.nombre}"
