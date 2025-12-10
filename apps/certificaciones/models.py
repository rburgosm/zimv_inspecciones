from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Certificacion(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    activa = models.BooleanField(default=True, verbose_name="Activa")
    fecha_creacion = models.DateTimeField(default=timezone.now, verbose_name="Fecha de creación")
    usuario_creacion = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='certificaciones_creadas',
        null=True,
        blank=True,
        verbose_name="Usuario creación"
    )
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")
    usuario_actualizacion = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='certificaciones_actualizadas',
        null=True,
        blank=True,
        verbose_name="Usuario actualización"
    )

    class Meta:
        verbose_name = "Certificación"
        verbose_name_plural = "Certificaciones"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre
