---
name: Desarrollo Web Inspecciones Zimvie
overview: Desarrollo de una aplicación web Django con Tailwind CSS para gestionar certificaciones de operarios, periodos de validación de 180 días laborables, y registro de inspecciones de producto con lógica de negocio para controlar caducidades.
todos: []
---

# Plan de Desarrollo - Sistema de Inspecciones Zimvie

## Arquitectura Tecnológica

- **Backend**: Django (Python)
- **Base de datos**: SQLite (según schema.sql)
- **Frontend**: Templates Django + Tailwind CSS
- **Autenticación**: Sistema de usuarios Django

## Estructura del Proyecto

```
Inspecciones_Zimvie/
├── manage.py
├── requirements.txt
├── inspecciones_zimvie/          # Proyecto Django principal
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── usuarios/                 # Autenticación
│   ├── operarios/                # CRUD operarios
│   ├── certificaciones/          # CRUD certificaciones
│   ├── auditores/                # CRUD auditores
│   ├── auditorias/               # CRUD auditorías de producto
│   ├── asignaciones/             # Asignación certificaciones a operarios
│   ├── inspecciones/             # Registro de inspecciones
│   └── consultas/                # Consulta de estado
├── static/
│   ├── css/                      # Tailwind compilado
│   └── js/
├── templates/
│   ├── base.html                 # Layout base con Tailwind
│   ├── login.html
│   └── [vistas específicas]
└── sql/
    └── schema.sql
```

## Fases de Implementación

### Fase 1: Configuración Inicial

1. **Setup del proyecto Django**

   - Crear proyecto Django
   - Configurar settings.py (SQLite, timezone, idioma español)
   - Crear estructura de apps
   - Configurar archivos estáticos y media

2. **Integración de Tailwind CSS**

   - Instalar y configurar Tailwind CSS vía CDN o build process
   - Crear template base.html con layout responsive
   - Configurar sistema de componentes reutilizables

3. **Migración de base de datos**

   - Adaptar schema.sql a modelos Django
   - Crear migraciones iniciales
   - Configurar relaciones y constraints

### Fase 2: Modelos de Datos

1. **Modelos principales** (basados en schema.sql)

   - `User` (extender AbstractUser o usar modelo personalizado)
   - `Operario`
   - `Certificacion`
   - `AuditoriaProducto`
   - `Auditor`
   - `OperarioCertificacion`
   - `PeriodoValidacionCertificacion`
   - `InspeccionProducto`
   - `ConfiguracionInspecciones`

2. **Lógica de negocio en modelos**

   - Métodos para calcular días laborables
   - Métodos para gestionar periodos
   - Validaciones de reglas de negocio

### Fase 3: Autenticación

1. **Sistema de login**

   - Vista de login con formulario
   - Autenticación Django estándar
   - Protección de rutas con `@login_required`
   - Template de login con Tailwind

### Fase 4: CRUD de Catálogos

1. **Operarios** (`apps/operarios/`)

   - Lista de operarios (activos/inactivos)
   - Crear/editar operario
   - Desactivar operario
   - Vistas y templates con Tailwind

2. **Certificaciones** (`apps/certificaciones/`)

   - Lista de certificaciones
   - Crear/editar certificación
   - Desactivar certificación

3. **Auditores** (`apps/auditores/`)

   - Lista de auditores
   - Crear/editar auditor

4. **Auditorías de Producto** (`apps/auditorias/`)

   - Lista filtrada por certificación
   - Crear/editar auditoría
   - Validar relación con certificación

### Fase 5: Asignación de Certificaciones

1. **Gestión de asignaciones** (`apps/asignaciones/`)

   - Vista para crear asignación operario-certificación
   - Formulario con selección de operario y certificación
   - Al guardar: crear asignación + periodo inicial (nº1)
   - Cálculo automático de fecha fin (180 días laborables)
   - Lista de asignaciones por operario

### Fase 6: Lógica de Periodos y Días Laborables

1. **Utilidades de días laborables**

   - Función para calcular días laborables (excluir fines de semana)
   - Función para obtener siguiente día laborable
   - Integrar en creación de periodos

2. **Gestión automática de periodos**

   - Al crear asignación: crear periodo nº1
   - Al registrar inspección: actualizar contador
   - Al alcanzar 29: cerrar periodo y crear siguiente
   - Verificación de caducidad al finalizar periodo

### Fase 7: Registro de Inspecciones

1. **Formulario de inspección** (`apps/inspecciones/`)

   - Selección de operario (filtra certificaciones activas)
   - Selección de certificación (solo activas del operario)
   - Sistema determina periodo vigente automáticamente
   - Selección de auditoría de producto (filtrada por certificación)
   - Selección de auditor
   - Fecha de inspección (validar dentro del periodo)
   - Piezas auditadas, resultado, observaciones

2. **Lógica de guardado**

   - Validar fecha dentro del periodo vigente
   - Incrementar contador de inspecciones
   - Si llega a 29: marcar periodo como completado y crear nuevo
   - Si periodo vencido sin 29: marcar certificación como caducada

3. **Lista de inspecciones**

   - Vista con filtros (operario, certificación, periodo)
   - Tabla con detalles de inspecciones

### Fase 8: Consulta de Estado

1. **Vista de detalle de operario** (`apps/consultas/`)

   - Información del operario
   - Lista de certificaciones (activas y caducadas)
   - Para cada certificación:
     - Periodo vigente: fechas, inspecciones realizadas/requeridas
     - Historial de periodos anteriores
     - Lista de inspecciones del periodo

2. **Dashboard básico** (opcional MVP)

   - Resumen de certificaciones activas
   - Alertas de periodos próximos a vencer

### Fase 9: Configuración

1. **Gestión de configuración**

   - Tabla `ConfiguracionInspecciones` para días e inspecciones
   - Vista de administración (opcional en MVP)
   - O usar constantes en código si es más simple

## Consideraciones Técnicas

1. **Días laborables**: Implementar función que excluya sábados y domingos
2. **Transacciones**: Usar `@transaction.atomic` en operaciones críticas (crear periodo, registrar inspección)
3. **Validaciones**: Validar en formularios y modelos
4. **Índices**: Los índices del schema.sql se manejan automáticamente con Django
5. **Auditoría**: Campos `usuario_creacion_id` y `fecha_creacion` en todos los modelos

## Archivos Clave a Crear

- `manage.py`
- `inspecciones_zimvie/settings.py` - Configuración Django
- `apps/*/models.py` - Modelos de datos
- `apps/*/views.py` - Vistas y lógica
- `apps/*/forms.py` - Formularios Django
- `apps/*/urls.py` - Rutas
- `templates/base.html` - Layout con Tailwind
- `templates/*/*.html` - Templates específicos
- `requirements.txt` - Dependencias Python