BEGIN;

CREATE SCHEMA IF NOT EXISTS finanzas;
SET search_path TO finanzas;

-- =========================================================
-- ENUMS (MEJOR QUE CHECK STRINGS)
-- =========================================================

CREATE TYPE tipo_movimiento_enum AS ENUM ('Ingreso', 'Egreso');
CREATE TYPE estado_movimiento_enum AS ENUM ('pendiente', 'confirmado');
CREATE TYPE tipo_egreso_enum AS ENUM ('Fijo', 'Variable');
CREATE TYPE rol_usuario_enum AS ENUM ('user', 'admin');

-- =========================================================
-- USUARIOS
-- =========================================================

CREATE TABLE usuarios (
    id VARCHAR(9) PRIMARY KEY,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    correo TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    verificado BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_registro TIMESTAMP NOT NULL DEFAULT now(),
    rol rol_usuario_enum NOT NULL DEFAULT 'user'
);

CREATE INDEX idx_usuarios_correo ON usuarios(correo);

-- =========================================================
-- CUENTAS
-- =========================================================

CREATE TABLE cuentas (
    id SERIAL PRIMARY KEY,
    usuario_id VARCHAR(7) NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    nombre TEXT NOT NULL,
    UNIQUE(usuario_id, nombre)
);

CREATE INDEX idx_cuentas_usuario ON cuentas(usuario_id);

-- =========================================================
-- CATEGORÍAS
-- =========================================================

CREATE TABLE categorias (
    id SERIAL PRIMARY KEY,
    usuario_id VARCHAR(7) NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    nombre TEXT NOT NULL,
    tipo_movimiento tipo_movimiento_enum NOT NULL,
    UNIQUE(usuario_id, nombre)
);

CREATE INDEX idx_categorias_usuario ON categorias(usuario_id);

-- =========================================================
-- TRANSFERENCIAS
-- =========================================================

CREATE TABLE transferencias (
    id UUID PRIMARY KEY,
    usuario_id VARCHAR(7) NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    cuenta_origen_id INT NOT NULL REFERENCES cuentas(id) ON DELETE RESTRICT,
    cuenta_destino_id INT NOT NULL REFERENCES cuentas(id) ON DELETE RESTRICT,
    monto NUMERIC(14,2) NOT NULL CHECK (monto > 0),
    descripcion TEXT,
    estado VARCHAR(20) NOT NULL DEFAULT 'confirmada',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_transferencia_cuentas_distintas
        CHECK (cuenta_origen_id <> cuenta_destino_id)
);

CREATE INDEX idx_transferencias_usuario ON transferencias(usuario_id);
CREATE INDEX idx_transferencias_cuentas ON transferencias(cuenta_origen_id, cuenta_destino_id);

-- =========================================================
-- FLUJO (MOVIMIENTOS CONTABLES)
-- =========================================================

CREATE TABLE flujo (
    id SERIAL PRIMARY KEY,
    usuario_id VARCHAR(7) NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    fecha DATE NOT NULL DEFAULT CURRENT_DATE,
    descripcion TEXT,

    categoria_id INT REFERENCES categorias(id) ON DELETE RESTRICT,
    cuenta_id INT NOT NULL REFERENCES cuentas(id) ON DELETE RESTRICT,

    tipo_movimiento tipo_movimiento_enum NOT NULL,
    estado estado_movimiento_enum NOT NULL DEFAULT 'confirmado',

    monto NUMERIC(14,2) NOT NULL CHECK (monto >= 0),

    transferencia_id UUID REFERENCES transferencias(id) ON DELETE RESTRICT,

    tipo_egreso tipo_egreso_enum,

    -- 🔒 Reglas lógicas
    CONSTRAINT chk_tipo_egreso_solo_egresos
        CHECK (
            (tipo_movimiento = 'Egreso' AND tipo_egreso IS NOT NULL)
            OR
            (tipo_movimiento = 'Ingreso' AND tipo_egreso IS NULL)
        )
);

-- Índices críticos
CREATE INDEX idx_flujo_usuario ON flujo(usuario_id);
CREATE INDEX idx_flujo_fecha ON flujo(usuario_id, fecha);
CREATE INDEX idx_flujo_cuenta ON flujo(cuenta_id);
CREATE INDEX idx_flujo_categoria ON flujo(categoria_id);
CREATE INDEX idx_flujo_transferencia ON flujo(transferencia_id);
CREATE INDEX idx_flujo_estado ON flujo(estado);

-- =========================================================
-- AUDITORÍA (LOGS FIRMADOS)
-- =========================================================

CREATE TABLE auditoria (
    id BIGSERIAL PRIMARY KEY,
    fecha TIMESTAMPTZ NOT NULL DEFAULT now(),
    usuario_id VARCHAR(7) REFERENCES usuarios(id) ON DELETE SET NULL,
    metodo TEXT NOT NULL,
    ruta TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    ip INET,
    body JSONB,
    error TEXT,
    duracion_ms INTEGER NOT NULL,

    -- 🔐 Seguridad
    firma TEXT NOT NULL,
    firma_anterior TEXT
);

CREATE INDEX idx_auditoria_fecha ON auditoria(fecha);
CREATE INDEX idx_auditoria_usuario ON auditoria(usuario_id);
CREATE INDEX idx_auditoria_ruta ON auditoria(ruta);

-- =========================================================
-- FUNCIONES OPTIMIZADAS
-- =========================================================

-- 🔹 Saldo por cuenta
CREATE OR REPLACE FUNCTION fn_saldo_por_cuenta(uid VARCHAR(7))
RETURNS TABLE(
    cuenta TEXT,
    saldo NUMERIC(14,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.nombre,
        COALESCE(SUM(
            CASE
                WHEN f.tipo_movimiento = 'Ingreso' THEN f.monto
                WHEN f.tipo_movimiento = 'Egreso' THEN -f.monto
            END
        ),0)
    FROM cuentas c
    LEFT JOIN flujo f
        ON f.cuenta_id = c.id
        AND f.estado = 'confirmado'
    WHERE c.usuario_id = uid
    GROUP BY c.nombre
    ORDER BY c.nombre;
END;
$$ LANGUAGE plpgsql STABLE;

-- 🔹 Saldo por rango
CREATE OR REPLACE FUNCTION fn_saldo_rango(
    uid VARCHAR(7),
    fecha_inicio DATE,
    fecha_fin DATE
)
RETURNS TABLE(
    cuenta TEXT,
    saldo NUMERIC(14,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.nombre,
        COALESCE(SUM(
            CASE
                WHEN f.tipo_movimiento = 'Ingreso' THEN f.monto
                WHEN f.tipo_movimiento = 'Egreso' THEN -f.monto
            END
        ),0)
    FROM cuentas c
    LEFT JOIN flujo f
        ON f.cuenta_id = c.id
        AND f.estado = 'confirmado'
        AND f.fecha BETWEEN fecha_inicio AND fecha_fin
    WHERE c.usuario_id = uid
    GROUP BY c.nombre
    ORDER BY c.nombre;
END;
$$ LANGUAGE plpgsql STABLE;

COMMIT;
