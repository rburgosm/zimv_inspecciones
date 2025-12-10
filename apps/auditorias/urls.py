from django.urls import path
from . import views

app_name = 'auditorias'

urlpatterns = [
    path('', views.lista_auditorias, name='lista'),
    path('crear/', views.crear_auditoria, name='crear'),
    path('<int:pk>/editar/', views.editar_auditoria, name='editar'),
]
