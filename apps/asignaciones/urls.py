from django.urls import path
from . import views

app_name = 'asignaciones'

urlpatterns = [
    path('', views.lista_asignaciones, name='lista'),
    path('crear/', views.crear_asignacion, name='crear'),
    path('<int:pk>/', views.detalle_asignacion, name='detalle'),
]
