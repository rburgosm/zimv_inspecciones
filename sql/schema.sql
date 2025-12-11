PRAGMA foreign_keys = ON;

-- =========================================
-- TABLA: users
-- =========================================
CREATE TABLE users (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_usuario      TEXT NOT NULL UNIQUE,
    hash_contrasena     TEXT NOT NULL,
    fecha_creacion      TEXT NOT NULL DEFAULT (datetime('now')),
    fecha_actualizacion TEXT NOT NULL DEFAULT (datetime('now'))
);

-- =========================================
-- TABLA: auditores
-- =========================================
CREATE TABLE auditores (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre                   TEXT NOT NULL,
    apellidos                TEXT,
    codigo                   TEXT,
    activo                   INTEGER NOT NULL DEFAULT 1,
    fecha_creacion           TEXT NOT NULL DEFAULT (datetime('now')),
    usuario_creacion_id      INTEGER,
    fecha_actualizacion      TEXT NOT NULL DEFAULT (datetime('now')),
    usuario_actualizacion_id INTEGER,
    FOREIGN KEY (usuario_creacion_id)      REFERENCES users(id) ON DELETE RESTRICT,
    FOREIGN KEY (usuario_actualizacion_id) REFERENCES users(id) ON DELETE RESTRICT
);

-- =========================================
-- TABLA: operarios
-- =========================================
CREATE TABLE operarios (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo                   TEXT,
    nombre                   TEXT NOT NULL,
    apellidos                TEXT,
    activo                   INTEGER NOT NULL DEFAULT 1,
    fecha_creacion           TEXT NOT NULL DEFAULT (datetime('now')),
    usuario_creacion_id      INTEGER,
    fecha_actualizacion      TEXT NOT NULL DEFAULT (datetime('now')),
    usuario_actualizacion_id INTEGER,
    FOREIGN KEY (usuario_creacion_id)      REFERENCES users(id) ON DELETE RESTRICT,
    FOREIGN KEY (usuario_actualizacion_id) REFERENCES users(id) ON DELETE RESTRICT
);

-- =========================================
-- TABLA: certificaciones
-- =========================================
CREATE TABLE certificaciones (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre                   TEXT NOT NULL UNIQUE,
    descripcion              TEXT,
    activa                   INTEGER NOT NULL DEFAULT 1,
    fecha_creacion           TEXT NOT NULL DEFAULT (datetime('now')),
    usuario_creacion_id      INTEGER,
    fecha_actualizacion      TEXT NOT NULL DEFAULT (datetime('now')),
    usuario_actualizacion_id INTEGER,
    FOREIGN KEY (usuario_creacion_id)      REFERENCES users(id) ON DELETE RESTRICT,
    FOREIGN KEY (usuario_actualizacion_id) REFERENCES users(id) ON DELETE RESTRICT
);

-- =========================================
-- TABLA: auditorias_producto
-- =========================================
CREATE TABLE auditorias_producto (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    certificacion_id         INTEGER NOT NULL,
    nombre                   TEXT NOT NULL,
    descripcion              TEXT,
    activa                   INTEGER NOT NULL DEFAULT 1,
    fecha_creacion           TEXT NOT NULL DEFAULT (datetime('now')),
    usuario_creacion_id      INTEGER,
    fecha_actualizacion      TEXT NOT NULL DEFAULT (datetime('now')),
    usuario_actualizacion_id INTEGER,
    FOREIGN KEY (certificacion_id)         REFERENCES certificaciones(id) ON DELETE RESTRICT,
    FOREIGN KEY (usuario_creacion_id)      REFERENCES users(id) ON DELETE RESTRICT,
    FOREIGN KEY (usuario_actualizacion_id) REFERENCES users(id) ON DELETE RESTRICT,
    UNIQUE(certificacion_id, nombre)
);

-- =========================================
-- TABLA: operario_certificaciones
-- =========================================
CREATE TABLE operario_certificaciones (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    operario_id              INTEGER NOT NULL,
    certificacion_id         INTEGER NOT NULL,
    fecha_asignacion         TEXT NOT NULL,
    esta_activa              INTEGER NOT NULL DEFAULT 1,
    fecha_caducidad          TEXT,
    observaciones            TEXT,
    fecha_creacion           TEXT NOT NULL DEFAULT (datetime('now')),
    usuario_creacion_id      INTEGER,
    fecha_actualizacion      TEXT NOT NULL DEFAULT (datetime('now')),
    usuario_actualizacion_id INTEGER,
    FOREIGN KEY (operario_id)              REFERENCES operarios(id) ON DELETE RESTRICT,
    FOREIGN KEY (certificacion_id)         REFERENCES certificaciones(id) ON DELETE RESTRICT,
    FOREIGN KEY (usuario_creacion_id)      REFERENCES users(id) ON DELETE RESTRICT,
    FOREIGN KEY (usuario_actualizacion_id) REFERENCES users(id) ON DELETE RESTRICT,
    UNIQUE(operario_id, certificacion_id, fecha_asignacion)
);

-- =========================================
-- TABLA: configuracion_inspecciones (opcional, MVP)
-- =========================================
CREATE TABLE configuracion_inspecciones (
    id                           INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_dias_laborales_req    INTEGER NOT NULL,   -- 180
    inspecciones_minimas         INTEGER NOT NULL,   -- 29
    esta_activo                  INTEGER NOT NULL DEFAULT 1,
    fecha_inicio_vigencia        TEXT,
    fecha_fin_vigencia           TEXT,
    fecha_creacion               TEXT NOT NULL DEFAULT (datetime('now')),
    usuario_creacion_id          INTEGER,
    fecha_actualizacion          TEXT NOT NULL DEFAULT (datetime('now')),
    usuario_actualizacion_id     INTEGER,
    FOREIGN KEY (usuario_creacion_id)      REFERENCES users(id) ON DELETE RESTRICT,
    FOREIGN KEY (usuario_actualizacion_id) REFERENCES users(id) ON DELETE RESTRICT
);

-- =========================================
-- TABLA: periodos_validacion_certificacion
-- =========================================
CREATE TABLE periodos_validacion_certificacion (
    id                           INTEGER PRIMARY KEY AUTOINCREMENT,
    operario_certificacion_id    INTEGER NOT NULL,
    numero_periodo               INTEGER NOT NULL,
    fecha_inicio_periodo         TEXT NOT NULL,
    fecha_fin_periodo            TEXT NOT NULL,
    numero_dias_laborales_req    INTEGER NOT NULL,   -- 180
    inspecciones_requeridas      INTEGER NOT NULL,   -- 29
    inspecciones_realizadas      INTEGER NOT NULL DEFAULT 0,
    esta_completado              INTEGER NOT NULL DEFAULT 0,
    fecha_completado             TEXT,
    esta_vigente                 INTEGER NOT NULL DEFAULT 1,
    fecha_creacion               TEXT NOT NULL DEFAULT (datetime('now')),
    usuario_creacion_id          INTEGER,
    fecha_actualizacion          TEXT NOT NULL DEFAULT (datetime('now')),
    usuario_actualizacion_id     INTEGER,
    FOREIGN KEY (operario_certificacion_id) REFERENCES operario_certificaciones(id) ON DELETE RESTRICT,
    FOREIGN KEY (usuario_creacion_id)      REFERENCES users(id) ON DELETE RESTRICT,
    FOREIGN KEY (usuario_actualizacion_id) REFERENCES users(id) ON DELETE RESTRICT,
    UNIQUE(operario_certificacion_id, numero_periodo)
);

-- Índice parcial: un único periodo vigente por certificación de operario
CREATE UNIQUE INDEX idx_periodo_vigente_unico
ON periodos_validacion_certificacion(operario_certificacion_id)
WHERE esta_vigente = 1;

-- =========================================
-- TABLA: inspecciones_producto
-- =========================================
CREATE TABLE inspecciones_producto (
    id                           INTEGER PRIMARY KEY AUTOINCREMENT,
    operario_certificacion_id    INTEGER NOT NULL,
    periodo_validacion_id        INTEGER NOT NULL,
    auditoria_producto_id        INTEGER NOT NULL,
    auditor_id                   INTEGER NOT NULL,
    fecha_inspeccion             TEXT NOT NULL,
    piezas_auditadas             INTEGER NOT NULL,
    resultado_inspeccion         TEXT,
    observaciones                TEXT,
    fecha_creacion               TEXT NOT NULL DEFAULT (datetime('now')),
    usuario_creacion_id          INTEGER,
    fecha_actualizacion          TEXT NOT NULL DEFAULT (datetime('now')),
    usuario_actualizacion_id     INTEGER,
    FOREIGN KEY (operario_certificacion_id) REFERENCES operario_certificaciones(id) ON DELETE RESTRICT,
    FOREIGN KEY (periodo_validacion_id)     REFERENCES periodos_validacion_certificacion(id) ON DELETE RESTRICT,
    FOREIGN KEY (auditoria_producto_id)     REFERENCES auditorias_producto(id) ON DELETE RESTRICT,
    FOREIGN KEY (auditor_id)                REFERENCES auditores(id) ON DELETE RESTRICT,
    FOREIGN KEY (usuario_creacion_id)       REFERENCES users(id) ON DELETE RESTRICT,
    FOREIGN KEY (usuario_actualizacion_id)  REFERENCES users(id) ON DELETE RESTRICT
);

-- Índices recomendados
CREATE INDEX idx_inspecciones_por_operario
    ON inspecciones_producto(operario_certificacion_id, fecha_inspeccion);

CREATE INDEX idx_inspecciones_por_periodo
    ON inspecciones_producto(periodo_validacion_id, fecha_inspeccion);
