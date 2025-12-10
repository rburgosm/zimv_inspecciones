# Sistema de Inspecciones Zimvie

Sistema web para controlar que los operarios mantienen sus certificaciones activas mediante periodos de validación de 180 días laborables con 29 inspecciones requeridas.

## Tecnologías

- **Backend**: Django 6.0
- **Base de datos**: SQLite
- **Frontend**: Tailwind CSS (via CDN)
- **Python**: 3.12+

## Instalación

1. Crear y activar el entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Aplicar migraciones:
```bash
python manage.py migrate
```

4. Crear superusuario:
```bash
python manage.py createsuperuser
```

5. Crear configuración inicial (opcional):
```bash
python manage.py shell
>>> from apps.inspecciones.models import ConfiguracionInspecciones
>>> ConfiguracionInspecciones.objects.create(
...     numero_dias_laborales_req=180,
...     inspecciones_minimas=29,
...     esta_activo=True
... )
```

6. Ejecutar servidor de desarrollo:
```bash
python manage.py runserver
```

Acceder a: http://127.0.0.1:8000/

## Estructura del Proyecto

```
Inspecciones_Zimvie/
├── apps/
│   ├── usuarios/          # Autenticación
│   ├── operarios/         # CRUD operarios
│   ├── certificaciones/   # CRUD certificaciones
│   ├── auditores/         # CRUD auditores
│   ├── auditorias/        # CRUD auditorías de producto
│   ├── asignaciones/      # Asignación certificaciones a operarios
│   ├── inspecciones/      # Registro de inspecciones
│   └── consultas/         # Consulta de estado
├── templates/             # Templates HTML
├── static/                # Archivos estáticos
└── sql/                   # Schema SQL original
```

## Funcionalidades

### 1. Autenticación
- Login con usuario y contraseña
- Protección de rutas con `@login_required`

### 2. Gestión de Catálogos
- **Operarios**: CRUD completo
- **Certificaciones**: CRUD completo
- **Auditores**: CRUD completo
- **Auditorías de Producto**: CRUD completo (ligadas a certificaciones)

### 3. Asignación de Certificaciones
- Asignar certificaciones a operarios
- Creación automática del periodo inicial (nº1) al crear asignación
- Cálculo automático de fecha fin (180 días laborables)

### 4. Registro de Inspecciones
- Registro de inspecciones de producto
- Validación automática de fecha dentro del periodo vigente
- Incremento automático de contador de inspecciones
- Cierre automático de periodo al alcanzar 29 inspecciones
- Creación automática de nuevo periodo

### 5. Consulta de Estado
- Vista completa de operario con todas sus certificaciones
- Periodos de validación con estado
- Historial de inspecciones por periodo

## Reglas de Negocio

1. **Periodos de validación**: 180 días laborables (excluye sábados y domingos)
2. **Inspecciones requeridas**: 29 por periodo
3. **Al completar 29 inspecciones**: 
   - Se marca el periodo como completado
   - Se crea automáticamente un nuevo periodo (día laborable siguiente)
4. **Caducidad**: Si un periodo vence sin alcanzar 29 inspecciones, la certificación se marca como caducada

## Uso

1. **Crear datos básicos**:
   - Crear operarios
   - Crear certificaciones
   - Crear auditores
   - Crear auditorías de producto (ligadas a certificaciones)

2. **Asignar certificaciones**:
   - Ir a "Asignaciones"
   - Crear nueva asignación (operario + certificación + fecha)
   - El sistema crea automáticamente el periodo inicial

3. **Registrar inspecciones**:
   - Ir a "Inspecciones"
   - Crear nueva inspección
   - El sistema determina automáticamente el periodo vigente
   - Al alcanzar 29 inspecciones, se cierra el periodo y se crea uno nuevo

4. **Consultar estado**:
   - Ver detalle de operario para ver todas sus certificaciones y periodos
   - Ver detalle de asignación para ver periodos e inspecciones

## Notas

- Los días laborables excluyen sábados y domingos
- No se pueden registrar inspecciones fuera del periodo vigente
- Una vez completado un periodo (29 inspecciones), no se pueden agregar más inspecciones a ese periodo
- Para reactivar una certificación caducada, se debe crear una nueva asignación
