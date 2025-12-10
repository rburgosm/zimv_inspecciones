from django.urls import path
from . import views

app_name = 'consultas'

urlpatterns = [
    path('operario/<int:pk>/', views.detalle_operario_completo, name='detalle_operario'),
]
