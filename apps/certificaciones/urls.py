from django.urls import path
from . import views

app_name = 'certificaciones'

urlpatterns = [
    path('', views.lista_certificaciones, name='lista'),
    path('crear/', views.crear_certificacion, name='crear'),
    path('<int:pk>/editar/', views.editar_certificacion, name='editar'),
]
