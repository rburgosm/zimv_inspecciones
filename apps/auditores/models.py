from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Auditor(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    apellidos = models.CharField(max_length=100, blank=True, null=True, verbose_name="Apellidos")
    codigo = models.CharField(max_length=50, blank=True, null=True, verbose_name="Código")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_creacion = models.DateTimeField(default=timezone.now, verbose_name="Fecha de creación")
    usuario_creacion = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='auditores_creados',
        null=True,
        blank=True,
        verbose_name="Usuario creación"
    )
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")
    usuario_actualizacion = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='auditores_actualizados',
        null=True,
        blank=True,
        verbose_name="Usuario actualización"
    )

    class Meta:
        verbose_name = "Auditor"
        verbose_name_plural = "Auditores"
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
