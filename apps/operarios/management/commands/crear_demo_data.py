"""
Comando de gestión para crear datos de demostración.
Uso: python manage.py crear_demo_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date
import random

from apps.operarios.models import Operario
from apps.certificaciones.models import Certificacion
from apps.auditores.models import Auditor
from apps.auditorias.models import AuditoriaProducto
from apps.asignaciones.models import OperarioCertificacion
from apps.inspecciones.models import InspeccionProducto, PeriodoValidacionCertificacion, ConfiguracionInspecciones
from apps.asignaciones.utils import calcular_fecha_fin_periodo, siguiente_dia_laborable


class Command(BaseCommand):
    help = 'Crea datos de demostración para el sistema de inspecciones'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-limpiar',
            action='store_true',
            help='NO elimina los datos existentes antes de crear los de demostración (por defecto se limpian)',
        )

    def limpiar_datos(self):
        """Elimina todos los datos de demostración existentes"""
        self.stdout.write(self.style.WARNING('Eliminando datos existentes...'))
        
        # Eliminar en orden para respetar foreign keys
        InspeccionProducto.objects.all().delete()
        PeriodoValidacionCertificacion.objects.all().delete()
        OperarioCertificacion.objects.all().delete()
        AuditoriaProducto.objects.all().delete()
        Auditor.objects.all().delete()
        Operario.objects.all().delete()
        Certificacion.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS('Datos eliminados.'))

    def handle(self, *args, **options):
        # Por defecto, limpiar datos antes de crear nuevos
        if not options['no_limpiar']:
            self.limpiar_datos()
        else:
            self.stdout.write(self.style.WARNING('Manteniendo datos existentes (--no-limpiar activado)'))

        # Obtener o crear usuario admin (no se elimina al limpiar)
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@example.com', 'is_superuser': True, 'is_staff': True}
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write('  ✓ Usuario admin creado')
        elif not admin_user.check_password('admin123'):
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write('  ✓ Contraseña de admin actualizada')

        # Crear configuración si no existe (se recrea si se limpió)
        config, created = ConfiguracionInspecciones.objects.get_or_create(
            esta_activo=True,
            defaults={
                'numero_dias_laborales_req': 180,
                'inspecciones_minimas': 29,
                'usuario_creacion': admin_user
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('  ✓ Configuración creada.'))
        else:
            # Asegurar valores correctos
            config.numero_dias_laborales_req = 180
            config.inspecciones_minimas = 29
            config.save()
            self.stdout.write(self.style.SUCCESS('  ✓ Configuración verificada.'))

        def asegurar_periodos_minimos(asignacion, periodo_vigente, periodos_minimos=4):
            """Garantiza al menos N periodos por asignación, con historial completado."""
            if not periodo_vigente or not asignacion:
                return periodo_vigente

            periodos_actuales = asignacion.periodos.order_by('numero_periodo')
            total_actual = periodos_actuales.count()
            if total_actual >= periodos_minimos:
                return periodo_vigente

            dias_laborales = config.numero_dias_laborales_req if config else 180
            piezas_requeridas = config.inspecciones_minimas if config else 29

            ultimo_numero = periodos_actuales.last().numero_periodo if total_actual else 0
            siguiente_numero = ultimo_numero + 1

            # Construir periodos históricos contiguos: el fin de uno es el inicio del siguiente (sin huecos)
            # Usamos límites inclusivos: fin = inicio siguiente - 1 día
            missing = periodos_minimos - total_actual
            next_start = periodo_vigente.fecha_inicio_periodo
            for _ in range(missing):
                fecha_fin_cursor = next_start - timedelta(days=1)
                fecha_inicio_cursor = fecha_fin_cursor - timedelta(days=dias_laborales - 1)
                PeriodoValidacionCertificacion.objects.get_or_create(
                    operario_certificacion=asignacion,
                    numero_periodo=siguiente_numero,
                    defaults={
                        'fecha_inicio_periodo': fecha_inicio_cursor,
                        'fecha_fin_periodo': fecha_fin_cursor,
                        'numero_dias_laborales_req': dias_laborales,
                        'inspecciones_requeridas': piezas_requeridas,
                        'inspecciones_realizadas': piezas_requeridas,
                        'esta_completado': True,
                        'esta_vigente': False,
                        'fecha_completado': fecha_fin_cursor,
                        'usuario_creacion': admin_user,
                    }
                )
                siguiente_numero += 1
                next_start = fecha_inicio_cursor

            # Asegurar que el vigente quede con el siguiente número para mantener la secuencia
            if periodo_vigente.numero_periodo < siguiente_numero:
                periodo_vigente.numero_periodo = siguiente_numero
                periodo_vigente.save(update_fields=['numero_periodo'])

            return periodo_vigente

        # Crear certificaciones
        self.stdout.write('Creando certificaciones...')
        certificaciones_data = [
            {'nombre': 'Certificación de Laboratorio', 'descripcion': 'Certificación para trabajo en laboratorio dental'},
            {'nombre': 'Certificación de Taller', 'descripcion': 'Certificación para trabajo en taller de prótesis'},
            {'nombre': 'Certificación de Calidad', 'descripcion': 'Certificación de control de calidad'},
            {'nombre': 'Certificación de Implantología', 'descripcion': 'Protocolos críticos de implantología'},
            {'nombre': 'Certificación Exprés', 'descripcion': 'Procesos urgentes con ventanas muy cortas'},
        ]
        certificaciones = []
        for cert_data in certificaciones_data:
            cert, created = Certificacion.objects.get_or_create(
                nombre=cert_data['nombre'],
                defaults={
                    'descripcion': cert_data['descripcion'],
                    'activa': True,
                    'usuario_creacion': admin_user
                }
            )
            certificaciones.append(cert)
            if created:
                self.stdout.write(f'  ✓ Certificación creada: {cert.nombre}')

        # Crear auditorías de producto
        self.stdout.write('Creando auditorías de producto...')
        auditorias_data = [
            {'certificacion': certificaciones[0], 'nombre': 'Dientes', 'descripcion': 'Inspección de dientes'},
            {'certificacion': certificaciones[0], 'nombre': 'Coronas', 'descripcion': 'Inspección de coronas'},
            {'certificacion': certificaciones[0], 'nombre': 'Puentes', 'descripcion': 'Inspección de puentes'},
            {'certificacion': certificaciones[1], 'nombre': 'Prótesis Fijas', 'descripcion': 'Inspección de prótesis fijas'},
            {'certificacion': certificaciones[1], 'nombre': 'Prótesis Removibles', 'descripcion': 'Inspección de prótesis removibles'},
            {'certificacion': certificaciones[2], 'nombre': 'Control Dimensional', 'descripcion': 'Control de dimensiones'},
            {'certificacion': certificaciones[2], 'nombre': 'Control de Materiales', 'descripcion': 'Control de calidad de materiales'},
            {'certificacion': certificaciones[3], 'nombre': 'Implantes Unitarios', 'descripcion': 'Evaluación de implantes unitarios'},
            {'certificacion': certificaciones[3], 'nombre': 'Implantes Múltiples', 'descripcion': 'Evaluación de implantes múltiples'},
            {'certificacion': certificaciones[4], 'nombre': 'Urgencia Exprés', 'descripcion': 'Inspecciones rápidas en menos de 72h'},
        ]
        auditorias = []
        for aud_data in auditorias_data:
            aud, created = AuditoriaProducto.objects.get_or_create(
                certificacion=aud_data['certificacion'],
                nombre=aud_data['nombre'],
                defaults={
                    'descripcion': aud_data['descripcion'],
                    'activa': True,
                    'usuario_creacion': admin_user
                }
            )
            auditorias.append(aud)
            if created:
                self.stdout.write(f'  ✓ Auditoría creada: {aud.certificacion.nombre} - {aud.nombre}')

        # Crear auditores
        self.stdout.write('Creando auditores...')
        auditores_data = [
            {'nombre': 'María', 'apellidos': 'García López', 'codigo': 'AUD001'},
            {'nombre': 'Juan', 'apellidos': 'Martínez Ruiz', 'codigo': 'AUD002'},
            {'nombre': 'Ana', 'apellidos': 'Fernández Sánchez', 'codigo': 'AUD003'},
            {'nombre': 'Carlos', 'apellidos': 'Rodríguez Pérez', 'codigo': 'AUD004'},
        ]
        auditores = []
        for aud_data in auditores_data:
            auditor, created = Auditor.objects.get_or_create(
                codigo=aud_data['codigo'],
                defaults={
                    'nombre': aud_data['nombre'],
                    'apellidos': aud_data['apellidos'],
                    'activo': True,
                    'usuario_creacion': admin_user
                }
            )
            auditores.append(auditor)
            if created:
                self.stdout.write(f'  ✓ Auditor creado: {auditor.nombre_completo}')

        # Crear operarios
        self.stdout.write('Creando operarios...')
        operarios_data = [
            {'nombre': 'Pedro', 'apellidos': 'Sánchez González', 'codigo': 'OP001'},
            {'nombre': 'Laura', 'apellidos': 'Torres Jiménez', 'codigo': 'OP002'},
            {'nombre': 'Miguel', 'apellidos': 'Díaz Moreno', 'codigo': 'OP003'},
            {'nombre': 'Carmen', 'apellidos': 'Vázquez Romero', 'codigo': 'OP004'},
            {'nombre': 'David', 'apellidos': 'Herrera Navarro', 'codigo': 'OP005'},
            {'nombre': 'Silvia', 'apellidos': 'Ramos Cortés', 'codigo': 'OP006'},
            {'nombre': 'Andrés', 'apellidos': 'Luna Prieto', 'codigo': 'OP007'},
        ]
        operarios = []
        for op_data in operarios_data:
            operario, created = Operario.objects.get_or_create(
                codigo=op_data['codigo'],
                defaults={
                    'nombre': op_data['nombre'],
                    'apellidos': op_data['apellidos'],
                    'activo': True,
                    'usuario_creacion': admin_user
                }
            )
            operarios.append(operario)
            if created:
                self.stdout.write(f'  ✓ Operario creado: {operario.nombre_completo}')

        # Crear asignaciones y periodos
        self.stdout.write('Creando asignaciones y periodos...')
        hoy = timezone.now().date()

        def ajustar_fin(periodo, dias_restantes):
            """Acerca la fecha fin para generar urgencia en periodos vigentes."""
            if periodo:
                periodo.fecha_fin_periodo = hoy + timedelta(days=dias_restantes)
                periodo.save(update_fields=['fecha_fin_periodo'])

        def renumerar_periodos_por_fecha(asignacion):
            """Asegura que los números de periodo sigan el orden cronológico (más antiguo = número menor)."""
            periodos = list(asignacion.periodos.order_by('fecha_inicio_periodo'))
            # Paso 1: mover a números temporales para evitar colisiones del UNIQUE
            for idx, periodo in enumerate(periodos, start=1):
                tmp_num = idx + 1000
                if periodo.numero_periodo != tmp_num:
                    periodo.numero_periodo = tmp_num
                    periodo.save(update_fields=['numero_periodo'])
            # Paso 2: asignar numeración definitiva
            for idx, periodo in enumerate(periodos, start=1):
                if periodo.numero_periodo != idx:
                    periodo.numero_periodo = idx
                    periodo.save(update_fields=['numero_periodo'])
        
        # Asignación 1: Operario con periodo casi completado (25/29 piezas)
        asignacion1, _ = OperarioCertificacion.objects.get_or_create(
            operario=operarios[0],
            certificacion=certificaciones[0],
            fecha_asignacion=hoy - timedelta(days=150),
            defaults={
                'esta_activa': True,
                'usuario_creacion': admin_user
            }
        )
        periodo1 = asignacion1.periodos.filter(esta_vigente=True).first()
        if periodo1:
            # Resetear contador - los signals sumarán las piezas al crear inspecciones
            periodo1.inspecciones_realizadas = 0
            periodo1.save()
            ajustar_fin(periodo1, 45)  # menos de 2 meses para ver avance
            periodo1 = asegurar_periodos_minimos(asignacion1, periodo1)
            renumerar_periodos_por_fecha(asignacion1)
            self.stdout.write(f'  ✓ Asignación creada: {asignacion1.operario.nombre_completo} - {asignacion1.certificacion.nombre} (se crearán 25 piezas)')

        # Asignación 2: Operario con periodo recién iniciado (5/29 inspecciones)
        asignacion2, _ = OperarioCertificacion.objects.get_or_create(
            operario=operarios[1],
            certificacion=certificaciones[0],
            fecha_asignacion=hoy - timedelta(days=30),
            defaults={
                'esta_activa': True,
                'usuario_creacion': admin_user
            }
        )
        periodo2 = asignacion2.periodos.filter(esta_vigente=True).first()
        if periodo2:
            periodo2.inspecciones_realizadas = 0
            periodo2.save()
            ajustar_fin(periodo2, 25)  # ventana corta para urgencia media
            periodo2 = asegurar_periodos_minimos(asignacion2, periodo2)
            renumerar_periodos_por_fecha(asignacion2)
            self.stdout.write(f'  ✓ Asignación creada: {asignacion2.operario.nombre_completo} - {asignacion2.certificacion.nombre} (se crearán 5 piezas)')

        # Asignación 3: Operario con múltiples certificaciones
        asignacion3a, _ = OperarioCertificacion.objects.get_or_create(
            operario=operarios[2],
            certificacion=certificaciones[0],
            fecha_asignacion=hoy - timedelta(days=60),
            defaults={
                'esta_activa': True,
                'usuario_creacion': admin_user
            }
        )
        periodo3a = asignacion3a.periodos.filter(esta_vigente=True).first()
        if periodo3a:
            periodo3a.inspecciones_realizadas = 0
            periodo3a.save()
            ajustar_fin(periodo3a, 60)  # ~2 meses
            periodo3a = asegurar_periodos_minimos(asignacion3a, periodo3a)
            renumerar_periodos_por_fecha(asignacion3a)

        asignacion3b, _ = OperarioCertificacion.objects.get_or_create(
            operario=operarios[2],
            certificacion=certificaciones[1],
            fecha_asignacion=hoy - timedelta(days=45),
            defaults={
                'esta_activa': True,
                'usuario_creacion': admin_user
            }
        )
        periodo3b = asignacion3b.periodos.filter(esta_vigente=True).first()
        if periodo3b:
            periodo3b.inspecciones_realizadas = 0
            periodo3b.save()
            ajustar_fin(periodo3b, 30)  # poco tiempo para terminar
            periodo3b = asegurar_periodos_minimos(asignacion3b, periodo3b)
            renumerar_periodos_por_fecha(asignacion3b)
        self.stdout.write(f'  ✓ Asignaciones creadas para {operarios[2].nombre_completo} (2 certificaciones, se crearán 15 y 10 piezas)')

        # Asignación 4: Operario con periodo CRÍTICO - próximo a vencer
        # Crear asignación hace 175 días, pero ajustar manualmente la fecha fin para que queden solo 5 días
        fecha_asignacion4 = hoy - timedelta(days=175)
        asignacion4, _ = OperarioCertificacion.objects.get_or_create(
            operario=operarios[3],
            certificacion=certificaciones[1],
            fecha_asignacion=fecha_asignacion4,
            defaults={
                'esta_activa': True,
                'usuario_creacion': admin_user
            }
        )
        periodo4 = asignacion4.periodos.filter(esta_vigente=True).first()
        if periodo4:
            # Ajustar fecha fin para que queden solo 5 días
            periodo4.fecha_fin_periodo = hoy + timedelta(days=5)
            periodo4.inspecciones_realizadas = 0
            periodo4.save()
            periodo4 = asegurar_periodos_minimos(asignacion4, periodo4)
            self.stdout.write(f'  ✓ Asignación CRÍTICA creada: {asignacion4.operario.nombre_completo} - {asignacion4.certificacion.nombre} (se crearán 15 piezas, CRÍTICO - vence en 5 días)')

        # Asignación 5: Operario nuevo sin inspecciones
        asignacion5, _ = OperarioCertificacion.objects.get_or_create(
            operario=operarios[4],
            certificacion=certificaciones[2],
            fecha_asignacion=hoy - timedelta(days=10),
            defaults={
                'esta_activa': True,
                'usuario_creacion': admin_user
            }
        )
        periodo5 = asignacion5.periodos.filter(esta_vigente=True).first()
        if periodo5:
            ajustar_fin(periodo5, 75)  # no demasiado lejos
            periodo5 = asegurar_periodos_minimos(asignacion5, periodo5)
            renumerar_periodos_por_fecha(asignacion5)
        self.stdout.write(f'  ✓ Asignación creada: {asignacion5.operario.nombre_completo} - {asignacion5.certificacion.nombre} (0 inspecciones)')
        
        # Asignación 6: Operario con periodo CRÍTICO - bajo progreso (mucho tiempo transcurrido, pocas piezas)
        # Periodo iniciado hace 120 días (más del 60% del tiempo), solo tiene 8 piezas de 29 requeridas
        fecha_asignacion6 = hoy - timedelta(days=120)
        asignacion6, _ = OperarioCertificacion.objects.get_or_create(
            operario=operarios[0],  # Reutilizar operario 1 pero con otra certificación
            certificacion=certificaciones[1],
            fecha_asignacion=fecha_asignacion6,
            defaults={
                'esta_activa': True,
                'usuario_creacion': admin_user
            }
        )
        periodo6 = asignacion6.periodos.filter(esta_vigente=True).first()
        if periodo6:
            # Ajustar fecha fin para que queden 60 días (total ~180 días)
            periodo6.fecha_fin_periodo = hoy + timedelta(days=60)
            periodo6.inspecciones_realizadas = 0
            periodo6.save()
            periodo6 = asegurar_periodos_minimos(asignacion6, periodo6)
            self.stdout.write(f'  ✓ Asignación CRÍTICA creada: {asignacion6.operario.nombre_completo} - {asignacion6.certificacion.nombre} (se crearán 8 piezas, CRÍTICO - bajo progreso: 66% tiempo, solo 27% piezas)')

        # Asignación 7: Operario con certificación de implantología, ventana mínima restante
        fecha_asignacion7 = hoy - timedelta(days=165)
        asignacion7, _ = OperarioCertificacion.objects.get_or_create(
            operario=operarios[5],
            certificacion=certificaciones[3],
            fecha_asignacion=fecha_asignacion7,
            defaults={
                'esta_activa': True,
                'usuario_creacion': admin_user
            }
        )
        periodo7 = asignacion7.periodos.filter(esta_vigente=True).first()
        if periodo7:
            periodo7.fecha_fin_periodo = hoy + timedelta(days=4)
            periodo7.inspecciones_realizadas = 0
            periodo7.save()
            periodo7 = asegurar_periodos_minimos(asignacion7, periodo7)
            self.stdout.write(f'  ✓ Asignación CRÍTICA creada: {asignacion7.operario.nombre_completo} - {asignacion7.certificacion.nombre} (se crearán 18 piezas, vence en 4 días)')

        # Asignación 8: Certificación exprés con casi todo el tiempo consumido
        fecha_asignacion8 = hoy - timedelta(days=178)
        asignacion8, _ = OperarioCertificacion.objects.get_or_create(
            operario=operarios[6],
            certificacion=certificaciones[4],
            fecha_asignacion=fecha_asignacion8,
            defaults={
                'esta_activa': True,
                'usuario_creacion': admin_user
            }
        )
        periodo8 = asignacion8.periodos.filter(esta_vigente=True).first()
        if periodo8:
            periodo8.fecha_fin_periodo = hoy + timedelta(days=2)
            periodo8.inspecciones_realizadas = 0
            periodo8.save()
            periodo8 = asegurar_periodos_minimos(asignacion8, periodo8)
            self.stdout.write(f'  ✓ Asignación CRÍTICA creada: {asignacion8.operario.nombre_completo} - {asignacion8.certificacion.nombre} (se crearán 20 piezas, apenas 2 días restantes)')

        def crear_inspecciones_para_periodo(asignacion, periodo, piezas_objetivo, prefijo_orden, auditorias_cert, auditores, hoy, es_vigente=False):
            """
            Crea inspecciones distribuidas en un periodo y devuelve (inspecciones, piezas).
            Prioriza los últimos 3 meses (y el mes actual) para que la app luzca más viva.
            """
            if not periodo or piezas_objetivo <= 0:
                return 0, 0

            estado_completado_original = periodo.esta_completado
            periodo.inspecciones_realizadas = 0
            periodo.save(update_fields=['inspecciones_realizadas'])

            fecha_inicio = periodo.fecha_inicio_periodo
            fecha_fin = min(periodo.fecha_fin_periodo, hoy)
            dias_totales = max((fecha_fin - fecha_inicio).days, 1)

            piezas_creadas = 0
            num_inspeccion = 0
            fechas_usadas = set()
            ventana_reciente_inicio = max(fecha_inicio, hoy - timedelta(days=90))
            inicio_mes_actual = date(hoy.year, hoy.month, 1)
            piezas_meta = min(piezas_objetivo, 29)  # Nunca superar 29 por periodo
            max_piezas = 29

            def siguiente_fecha_unica(fecha_base):
                """Desplaza a día laborable y evita duplicados cercanos."""
                fecha_candidata = fecha_base
                while fecha_candidata.weekday() >= 5:
                    fecha_candidata += timedelta(days=1)
                intentos = 0
                while fecha_candidata in fechas_usadas and intentos < 12:
                    fecha_candidata += timedelta(days=1)
                    while fecha_candidata.weekday() >= 5:
                        fecha_candidata += timedelta(days=1)
                    intentos += 1
                return min(fecha_candidata, fecha_fin)

            def agregar_inspeccion(fecha_objetivo, piezas_sugeridas=None):
                nonlocal piezas_creadas, num_inspeccion
                if fecha_objetivo > fecha_fin or piezas_creadas >= max_piezas:
                    return
                fecha_inspeccion = siguiente_fecha_unica(fecha_objetivo)
                fechas_usadas.add(fecha_inspeccion)
                piezas_restantes = max_piezas - piezas_creadas
                piezas_en_inspeccion = piezas_sugeridas or min(random.randint(1, 6), piezas_restantes)
                numero_orden = f"{prefijo_orden}-P{periodo.numero_periodo:02d}-{num_inspeccion+1:03d}-{fecha_inspeccion.strftime('%Y%m%d')}"
                InspeccionProducto.objects.create(
                    operario_certificacion=asignacion,
                    periodo_validacion=periodo,
                    auditoria_producto=random.choice(auditorias_cert),
                    auditor=random.choice(auditores),
                    fecha_inspeccion=fecha_inspeccion,
                    piezas_auditadas=piezas_en_inspeccion,
                    resultado_inspeccion=random.choice(['OK', 'NO OK']),
                    numero_orden=numero_orden,
                    observaciones=f'Inspección de ejemplo {num_inspeccion+1} ({piezas_en_inspeccion} piezas)',
                    usuario_creacion=admin_user
                )
                piezas_creadas += piezas_en_inspeccion
                num_inspeccion += 1

            while piezas_creadas < piezas_meta:
                if random.random() < 0.7:
                    # Sesgo fuerte a los últimos 90 días
                    rango_dias = max((fecha_fin - ventana_reciente_inicio).days, 1)
                    desplazamiento = random.randint(0, rango_dias)
                    fecha_inspeccion = ventana_reciente_inicio + timedelta(days=desplazamiento)
                else:
                    # Distribución más clásica a lo largo del periodo
                    dias_desde_inicio = int((num_inspeccion / max(piezas_objetivo, 1)) * dias_totales) if piezas_objetivo > 0 else 0
                    fecha_inspeccion = fecha_inicio + timedelta(days=dias_desde_inicio)

                agregar_inspeccion(fecha_inspeccion)

            # Refuerza presencia reciente (últimos 90 días) con inspecciones adicionales pequeñas
            fechas_recientes = [f for f in fechas_usadas if f >= ventana_reciente_inicio]
            objetivo_reciente = max(6, num_inspeccion // 2)
            while fecha_fin >= ventana_reciente_inicio and len(fechas_recientes) < objetivo_reciente and piezas_creadas < max_piezas:
                desplazamiento = random.randint(0, max((fecha_fin - ventana_reciente_inicio).days, 1))
                fecha_extra = ventana_reciente_inicio + timedelta(days=desplazamiento)
                agregar_inspeccion(fecha_extra, piezas_sugeridas=min(4, max_piezas - piezas_creadas))
                fechas_recientes = [f for f in fechas_usadas if f >= ventana_reciente_inicio]

            # Garantiza actividad en el mes actual (mínimo dos inspecciones si la ventana lo permite)
            if fecha_fin >= inicio_mes_actual:
                fechas_mes = [f for f in fechas_usadas if f >= inicio_mes_actual]
                while len(fechas_mes) < 2 and piezas_creadas < max_piezas:
                    desplazamiento = random.randint(0, max((fecha_fin - inicio_mes_actual).days, 0))
                    fecha_mes = inicio_mes_actual + timedelta(days=desplazamiento)
                    agregar_inspeccion(fecha_mes, piezas_sugeridas=min(3, max_piezas - piezas_creadas))
                    fechas_mes = [f for f in fechas_usadas if f >= inicio_mes_actual]

            # Refuerzo específico para periodos vigentes: asegurar actividad muy reciente (últimos 30 días)
            if es_vigente and fecha_fin >= hoy - timedelta(days=30):
                fechas_ultimos_30 = [f for f in fechas_usadas if f >= hoy - timedelta(days=30)]
                objetivo_reciente_vigente = 3
                while len(fechas_ultimos_30) < objetivo_reciente_vigente and piezas_creadas < max_piezas:
                    desplazamiento = random.randint(0, max((fecha_fin - max(fecha_inicio, hoy - timedelta(days=30))).days, 0))
                    fecha_reciente = max(fecha_inicio, hoy - timedelta(days=30)) + timedelta(days=desplazamiento)
                    agregar_inspeccion(fecha_reciente, piezas_sugeridas=min(3, max_piezas - piezas_creadas))
                    fechas_ultimos_30 = [f for f in fechas_usadas if f >= hoy - timedelta(days=30)]

            if estado_completado_original:
                periodo.esta_completado = True
                if not periodo.fecha_completado:
                    periodo.fecha_completado = fecha_fin
                periodo.save(update_fields=['esta_completado', 'fecha_completado'])

            return num_inspeccion, piezas_creadas

        # Crear inspecciones de ejemplo
        # IMPORTANTE: Se cuentan PIEZAS auditadas, no número de inspecciones
        # El objetivo es alcanzar 29 PIEZAS por periodo, no 29 inspecciones
        self.stdout.write('Creando inspecciones de ejemplo (todos los periodos)...')
        asignaciones_con_periodos = [
            (asignacion1, periodo1, 25, 'OP-001'),   # periodo vigente
            (asignacion2, periodo2, 7, 'OP-002'),    # subimos a 7 para asegurar piezas
            (asignacion3a, periodo3a, 15, 'OP-003'),
            (asignacion3b, periodo3b, 12, 'OP-004'), # un poco más para que no quede corto
            (asignacion4, periodo4, 15, 'OP-005'),
            (asignacion5, periodo5, 8, 'OP-006'),    # antes estaba sin inspecciones; ahora vivo
        ]

        if 'asignacion6' in locals() and periodo6:
            asignaciones_con_periodos.append((asignacion6, periodo6, 8, 'OP-007'))
        if 'asignacion7' in locals() and periodo7:
            asignaciones_con_periodos.append((asignacion7, periodo7, 18, 'OP-008'))
        if 'asignacion8' in locals() and periodo8:
            asignaciones_con_periodos.append((asignacion8, periodo8, 20, 'OP-009'))

        total_inspecciones = 0
        total_piezas = 0

        for asignacion, periodo_vigente, piezas_objetivo_vigente, prefijo_orden in asignaciones_con_periodos:
            if not periodo_vigente:
                continue

            auditorias_cert = [a for a in auditorias if a.certificacion == asignacion.certificacion]
            if not auditorias_cert:
                continue

            # Generar inspecciones para todos los periodos de la asignación
            for periodo in asignacion.periodos.order_by('numero_periodo'):
                objetivo_periodo = piezas_objetivo_vigente if periodo.id == periodo_vigente.id else (periodo.inspecciones_requeridas or piezas_objetivo_vigente)
                inspecciones_creadas, piezas_creadas = crear_inspecciones_para_periodo(
                    asignacion,
                    periodo,
                    objetivo_periodo,
                    prefijo_orden,
                    auditorias_cert,
                    auditores,
                    hoy,
                    es_vigente=(periodo.id == periodo_vigente.id)
                )
                total_inspecciones += inspecciones_creadas
                total_piezas += piezas_creadas

        self.stdout.write(f'  ✓ {total_inspecciones} inspecciones creadas (cubriendo historiales y vigentes)')

        # Resumen
        self.stdout.write(self.style.SUCCESS('\n=== Resumen de datos creados ==='))
        self.stdout.write(f'  Operarios: {Operario.objects.count()}')
        self.stdout.write(f'  Certificaciones: {Certificacion.objects.count()}')
        self.stdout.write(f'  Auditores: {Auditor.objects.count()}')
        self.stdout.write(f'  Auditorías de Producto: {AuditoriaProducto.objects.count()}')
        self.stdout.write(f'  Asignaciones: {OperarioCertificacion.objects.count()}')
        self.stdout.write(f'  Periodos: {PeriodoValidacionCertificacion.objects.count()}')
        self.stdout.write(f'  Inspecciones: {InspeccionProducto.objects.count()}')
        self.stdout.write(self.style.SUCCESS('\n¡Datos de demostración creados exitosamente!'))
        self.stdout.write(self.style.SUCCESS('\nLos contadores de periodos se actualizaron automáticamente mediante signals.'))
