from django.apps import AppConfig


class InspeccionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.inspecciones'

    def ready(self):
        import apps.inspecciones.signals
