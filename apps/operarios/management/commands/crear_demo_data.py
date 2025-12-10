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

        # Crear certificaciones
        self.stdout.write('Creando certificaciones...')
        certificaciones_data = [
            {'nombre': 'Certificación de Laboratorio', 'descripcion': 'Certificación para trabajo en laboratorio dental'},
            {'nombre': 'Certificación de Taller', 'descripcion': 'Certificación para trabajo en taller de prótesis'},
            {'nombre': 'Certificación de Calidad', 'descripcion': 'Certificación de control de calidad'},
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
        self.stdout.write(f'  ✓ Asignaciones creadas para {operarios[2].nombre_completo} (2 certificaciones, se crearán 15 y 10 piezas)')

        # Asignación 4: Operario con periodo próximo a vencer
        fecha_asignacion4 = hoy - timedelta(days=170)  # Cerca del límite de 180 días
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
            periodo4.inspecciones_realizadas = 0
            periodo4.save()
            self.stdout.write(f'  ✓ Asignación creada: {asignacion4.operario.nombre_completo} - {asignacion4.certificacion.nombre} (se crearán 20 piezas, próximo a vencer)')

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
        self.stdout.write(f'  ✓ Asignación creada: {asignacion5.operario.nombre_completo} - {asignacion5.certificacion.nombre} (0 inspecciones)')

        # Crear inspecciones de ejemplo
        # IMPORTANTE: Se cuentan PIEZAS auditadas, no número de inspecciones
        # El objetivo es alcanzar 29 PIEZAS por periodo, no 29 inspecciones
        self.stdout.write('Creando inspecciones de ejemplo...')
        asignaciones_con_periodos = [
            (asignacion1, periodo1, 25),  # 25 piezas (pueden ser de varias inspecciones)
            (asignacion2, periodo2, 5),   # 5 piezas
            (asignacion3a, periodo3a, 15), # 15 piezas
            (asignacion3b, periodo3b, 10), # 10 piezas
            (asignacion4, periodo4, 20),  # 20 piezas
        ]

        total_inspecciones = 0
        total_piezas = 0
        for asignacion, periodo, piezas_objetivo in asignaciones_con_periodos:
            if not periodo:
                continue
            
            # Obtener auditorías de la certificación
            auditorias_cert = [a for a in auditorias if a.certificacion == asignacion.certificacion]
            if not auditorias_cert:
                continue

            # Resetear contador antes de crear inspecciones (los signals sumarán las piezas)
            periodo.inspecciones_realizadas = 0
            periodo.save()

            # Crear inspecciones distribuidas en el periodo
            # Cada inspección puede tener 1 o más piezas auditadas
            # El objetivo es alcanzar el total de piezas requerido
            fecha_inicio = periodo.fecha_inicio_periodo
            fecha_fin = min(periodo.fecha_fin_periodo, hoy)
            dias_totales = max((fecha_fin - fecha_inicio).days, 1)
            
            # Crear inspecciones hasta alcanzar el objetivo de piezas
            piezas_creadas = 0
            num_inspeccion = 0
            fechas_usadas = set()
            
            while piezas_creadas < piezas_objetivo:
                # Distribuir las fechas a lo largo del periodo
                dias_desde_inicio = int((num_inspeccion / max(piezas_objetivo, 1)) * dias_totales) if piezas_objetivo > 0 else 0
                fecha_inspeccion = fecha_inicio + timedelta(days=dias_desde_inicio)
                
                # Asegurar que sea día laborable
                while fecha_inspeccion.weekday() >= 5:  # Sábado o domingo
                    fecha_inspeccion += timedelta(days=1)
                
                if fecha_inspeccion > fecha_fin:
                    fecha_inspeccion = fecha_fin
                
                # Evitar duplicados de fecha (aunque técnicamente se pueden tener varias el mismo día)
                intentos = 0
                while fecha_inspeccion in fechas_usadas and intentos < 10:
                    fecha_inspeccion += timedelta(days=1)
                    while fecha_inspeccion.weekday() >= 5:
                        fecha_inspeccion += timedelta(days=1)
                    intentos += 1
                
                fechas_usadas.add(fecha_inspeccion)
                
                # Calcular cuántas piezas crear en esta inspección
                # Puede ser 1 o más, pero no exceder el objetivo total
                piezas_restantes = piezas_objetivo - piezas_creadas
                piezas_en_inspeccion = min(random.randint(1, 10), piezas_restantes)  # Entre 1 y 10 piezas por inspección
                
                # Crear inspección (el signal sumará las piezas al contador automáticamente)
                inspeccion = InspeccionProducto.objects.create(
                    operario_certificacion=asignacion,
                    periodo_validacion=periodo,
                    auditoria_producto=random.choice(auditorias_cert),
                    auditor=random.choice(auditores),
                    fecha_inspeccion=fecha_inspeccion,
                    piezas_auditadas=piezas_en_inspeccion,
                    resultado_inspeccion=random.choice(['OK', 'NO OK', None]),
                    observaciones=f'Inspección de ejemplo {num_inspeccion+1} ({piezas_en_inspeccion} piezas)',
                    usuario_creacion=admin_user
                )
                total_inspecciones += 1
                piezas_creadas += piezas_en_inspeccion
                num_inspeccion += 1
                
                # Si ya alcanzamos el objetivo, salir
                if piezas_creadas >= piezas_objetivo:
                    break

        self.stdout.write(f'  ✓ {total_inspecciones} inspecciones creadas (totalizando las piezas requeridas por periodo)')

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
