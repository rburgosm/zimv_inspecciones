from django.urls import path
from . import views

app_name = 'operarios'

urlpatterns = [
    path('', views.lista_operarios, name='lista'),
    path('crear/', views.crear_operario, name='crear'),
    path('<int:pk>/', views.detalle_operario, name='detalle'),
    path('<int:pk>/editar/', views.editar_operario, name='editar'),
]
