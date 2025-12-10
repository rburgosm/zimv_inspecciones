from django.apps import AppConfig


class AsignacionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.asignaciones'

    def ready(self):
        import apps.asignaciones.signals
