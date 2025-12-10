from django.urls import path
from . import views

app_name = 'inspecciones'

urlpatterns = [
    path('', views.lista_inspecciones, name='lista'),
    path('crear/', views.crear_inspeccion, name='crear'),
    path('<int:pk>/', views.detalle_inspeccion, name='detalle'),
    path('api/auditorias/', views.obtener_auditorias_por_certificacion, name='api_auditorias'),
]
