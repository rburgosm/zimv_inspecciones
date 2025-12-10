from django.urls import path
from . import views

app_name = 'auditores'

urlpatterns = [
    path('', views.lista_auditores, name='lista'),
    path('crear/', views.crear_auditor, name='crear'),
    path('<int:pk>/editar/', views.editar_auditor, name='editar'),
]
