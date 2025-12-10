from datetime import timedelta
from django.utils import timezone


def es_dia_laborable(fecha):
    """
    Verifica si una fecha es un día laborable (lunes a viernes).
    """
    return fecha.weekday() < 5  # 0-4 son lunes a viernes


def siguiente_dia_laborable(fecha):
    """
    Retorna el siguiente día laborable a partir de la fecha dada.
    """
    fecha = fecha + timedelta(days=1)
    while not es_dia_laborable(fecha):
        fecha = fecha + timedelta(days=1)
    return fecha


def calcular_fecha_fin_periodo(fecha_inicio, dias_laborables=180):
    """
    Calcula la fecha de fin de un periodo sumando días laborables.
    
    Args:
        fecha_inicio: Fecha de inicio del periodo
        dias_laborables: Número de días laborables requeridos (default: 180)
    
    Returns:
        Fecha de fin del periodo
    """
    fecha = fecha_inicio
    dias_agregados = 0
    
    while dias_agregados < dias_laborables:
        if es_dia_laborable(fecha):
            dias_agregados += 1
        if dias_agregados < dias_laborables:
            fecha = fecha + timedelta(days=1)
    
    return fecha
