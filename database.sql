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
CREATE TYPE estado_transferencia_enum AS ENUM ('pendiente', 'confirmada');

-- =========================================================
-- USUARIOS
-- =========================================================

CREATE TABLE usuarios (
    id VARCHAR(9) PRIMARY KEY,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    correo TEXT NOT NULL UNIQUE,
    telefono VARCHAR(10),
    password TEXT NOT NULL,
    verificado BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_registro TIMESTAMP NOT NULL DEFAULT now(),
    rol rol_usuario_enum NOT NULL DEFAULT 'user',

    CONSTRAINT ck_usuarios_telefono_10_digitos
        CHECK (telefono ~ '^[0-9]{10}$')
);

CREATE INDEX idx_usuarios_correo ON usuarios(correo);
CREATE INDEX idx_usuarios_telefono ON usuarios(telefono);

-- =========================================================
-- CUENTAS
-- =========================================================

CREATE TABLE cuentas (
    id SERIAL PRIMARY KEY,
    usuario_id VARCHAR(9) NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    nombre TEXT NOT NULL,
    UNIQUE(usuario_id, nombre)
);

CREATE INDEX idx_cuentas_usuario ON cuentas(usuario_id);

-- =========================================================
-- CATEGORÍAS
-- =========================================================

CREATE TABLE categorias (
    id SERIAL PRIMARY KEY,
    usuario_id VARCHAR(9) NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    nombre TEXT NOT NULL,
    tipo_movimiento tipo_movimiento_enum NOT NULL,
    UNIQUE(usuario_id, nombre, tipo_movimiento)
);

CREATE INDEX idx_categorias_usuario ON categorias(usuario_id);

-- =========================================================
-- TRANSFERENCIAS
-- =========================================================

CREATE TABLE transferencias (
    id INT PRIMARY KEY,
    usuario_id VARCHAR(9) NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    cuenta_origen_id INT NOT NULL REFERENCES cuentas(id) ON DELETE RESTRICT,
    cuenta_destino_id INT NOT NULL REFERENCES cuentas(id) ON DELETE RESTRICT,
    monto NUMERIC(14,2) NOT NULL CHECK (monto > 0),
    descripcion TEXT,
    estado estado_transferencia_enum NOT NULL,
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
    usuario_id VARCHAR(9) NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    fecha DATE NOT NULL DEFAULT CURRENT_DATE,
    descripcion TEXT,

    categoria_id INT REFERENCES categorias(id) ON DELETE RESTRICT,
    cuenta_id INT NOT NULL REFERENCES cuentas(id) ON DELETE RESTRICT,

    tipo_movimiento tipo_movimiento_enum NOT NULL,
    estado estado_movimiento_enum NOT NULL DEFAULT 'confirmado',

    monto NUMERIC(14,2) NOT NULL CHECK (monto >= 0),

    transferencia_id INT REFERENCES transferencias(id) ON DELETE CASCADE,

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
    usuario_id VARCHAR(9) REFERENCES usuarios(id) ON DELETE SET NULL,
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
-- REFRESH TOKENS
-- =========================================================
CREATE TABLE refresh_tokens (
    id SERIAL PRIMARY KEY,
    usuario_id VARCHAR(9) NOT NULL,
    token TEXT NOT NULL UNIQUE,
    expira TIMESTAMP WITH TIME ZONE NOT NULL,
    fecha_creacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    CONSTRAINT fk_refresh_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_refresh_tokens_usuario_id
    ON refresh_tokens(usuario_id);

CREATE INDEX idx_refresh_tokens_expira
    ON refresh_tokens(expira);


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
