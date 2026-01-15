BEGIN;

CREATE SCHEMA IF NOT EXISTS finanzas;
SET search_path TO finanzas;

-- =========================================================
-- ENUMS (MEJOR QUE CHECK STRINGS)
-- =========================================================

CREATE TYPE tipo_movimiento_enum AS ENUM ('Ingreso', 'Egreso');
CREATE TYPE estado_movimiento_enum AS ENUM ('Pendiente', 'Confirmado');
CREATE TYPE tipo_egreso_enum AS ENUM ('Fijo', 'Variable');
CREATE TYPE rol_usuario_enum AS ENUM ('user', 'admin');
CREATE TYPE estado_transferencia_enum AS ENUM ('Pendiente', 'Confirmado');

-- =========================================================
-- USUARIOS
-- =========================================================

CREATE TABLE IF NOT EXISTS usuarios (
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

CREATE INDEX IF NOT EXISTS idx_usuarios_correo ON usuarios(correo);
CREATE INDEX IF NOT EXISTS idx_usuarios_telefono ON usuarios(telefono);

-- =========================================================
-- CUENTAS
-- =========================================================

CREATE TABLE IF NOT EXISTS cuentas (
    id SERIAL PRIMARY KEY,
    usuario_id VARCHAR(9) NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    nombre TEXT NOT NULL,
    UNIQUE(usuario_id, nombre)
);

CREATE INDEX IF NOT EXISTS idx_cuentas_usuario ON cuentas(usuario_id);

-- =========================================================
-- CATEGORÍAS
-- =========================================================

CREATE TABLE IF NOT EXISTS categorias (
    id SERIAL PRIMARY KEY,
    usuario_id VARCHAR(9) NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    nombre TEXT NOT NULL,
    tipo_movimiento tipo_movimiento_enum NOT NULL,
    UNIQUE(usuario_id, nombre, tipo_movimiento)
);

CREATE INDEX IF NOT EXISTS idx_categorias_usuario ON categorias(usuario_id);

-- =========================================================
-- TRANSFERENCIAS
-- =========================================================

CREATE TABLE IF NOT EXISTS transferencias (
    id SERIAL PRIMARY KEY,
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

CREATE INDEX IF NOT EXISTS idx_transferencias_usuario ON transferencias(usuario_id);
CREATE INDEX IF NOT EXISTS idx_transferencias_cuentas ON transferencias(cuenta_origen_id, cuenta_destino_id);

-- =========================================================
-- FLUJO (MOVIMIENTOS CONTABLES)
-- =========================================================

CREATE TABLE IF NOT EXISTS flujo (
    id SERIAL PRIMARY KEY,
    usuario_id VARCHAR(9) NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    fecha DATE NOT NULL DEFAULT CURRENT_DATE,
    descripcion TEXT,

    categoria_id INT REFERENCES categorias(id) ON DELETE RESTRICT,
    cuenta_id INT NOT NULL REFERENCES cuentas(id) ON DELETE RESTRICT,

    tipo_movimiento tipo_movimiento_enum NOT NULL,
    estado estado_movimiento_enum NOT NULL DEFAULT 'Confirmado',

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
CREATE INDEX IF NOT EXISTS idx_flujo_usuario ON flujo(usuario_id);
CREATE INDEX IF NOT EXISTS idx_flujo_fecha ON flujo(usuario_id, fecha);
CREATE INDEX IF NOT EXISTS idx_flujo_cuenta ON flujo(cuenta_id);
CREATE INDEX IF NOT EXISTS idx_flujo_categoria ON flujo(categoria_id);
CREATE INDEX IF NOT EXISTS idx_flujo_transferencia ON flujo(transferencia_id);
CREATE INDEX IF NOT EXISTS idx_flujo_estado ON flujo(estado);

-- =========================================================
-- AUDITORÍA (LOGS FIRMADOS)
-- =========================================================

CREATE TABLE IF NOT EXISTS auditoria (
    id BIGSERIAL PRIMARY KEY,
    fecha TIMESTAMPTZ NOT NULL DEFAULT now(),
    usuario_id VARCHAR(9) NULL REFERENCES usuarios(id) ON DELETE SET NULL,
    metodo TEXT NOT NULL,
    ruta TEXT NOT NULL,
    status_code INTEGER DEFAULT 500,
    ip INET,
    body JSONB,
    error TEXT,
    duracion_ms INTEGER NOT NULL,

    -- 🔐 Seguridad
    firma TEXT NOT NULL,
    firma_anterior TEXT
);

CREATE INDEX IF NOT EXISTS idx_auditoria_fecha ON auditoria(fecha);
CREATE INDEX IF NOT EXISTS idx_auditoria_usuario ON auditoria(usuario_id);
CREATE INDEX IF NOT EXISTS idx_auditoria_ruta ON auditoria(ruta);

-- =========================================================
-- REFRESH TOKENS
-- =========================================================
CREATE TABLE IF NOT EXISTS refresh_tokens (
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

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_usuario_id
    ON refresh_tokens(usuario_id);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expira
    ON refresh_tokens(expira);


-- =========================================================
-- FUNCIONES OPTIMIZADAS
-- =========================================================

-- 🔹 Saldo por cuenta
CREATE OR REPLACE FUNCTION fn_saldo_por_cuenta(uid VARCHAR(9))
RETURNS TABLE(
    cuenta_id INTEGER,
    cuenta TEXT,
    saldo NUMERIC(14,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id AS cuenta_id,
        c.nombre AS cuenta,
        COALESCE(SUM(
            CASE
                WHEN f.tipo_movimiento = 'Ingreso' THEN f.monto
                WHEN f.tipo_movimiento = 'Egreso' THEN -f.monto
            END
        ), 0) AS saldo
    FROM cuentas c
    LEFT JOIN flujo f
        ON f.cuenta_id = c.id
        AND f.estado = 'Confirmado'
    WHERE c.usuario_id = uid
    GROUP BY c.id, c.nombre
    ORDER BY c.nombre;
END;
$$ LANGUAGE plpgsql STABLE;



-- 🔹 Saldo por rango
CREATE OR REPLACE FUNCTION fn_saldo_rango(
    uid VARCHAR(9),
    fecha_inicio DATE,
    fecha_fin DATE
)
RETURNS TABLE(
    cuenta_id INTEGER,
    cuenta TEXT,
    saldo NUMERIC(14,2)
) AS $$
BEGIN
    -- 🔒 Validaciones duras
    IF uid IS NULL THEN
        RAISE EXCEPTION 'El usuario no puede ser NULL';
    END IF;

    IF fecha_inicio IS NULL OR fecha_fin IS NULL THEN
        RAISE EXCEPTION 'Las fechas no pueden ser NULL';
    END IF;

    IF fecha_inicio > fecha_fin THEN
        RAISE EXCEPTION
            'La fecha inicial (%) no puede ser mayor que la final (%)',
            fecha_inicio,
            fecha_fin;
    END IF;

    RETURN QUERY
    SELECT
        c.id AS cuenta_id,
        c.nombre AS cuenta,
        COALESCE(
            SUM(
                CASE
                    WHEN f.tipo_movimiento = 'Ingreso' THEN f.monto
                    WHEN f.tipo_movimiento = 'Egreso' THEN -f.monto
                END
            ),
            0
        )::NUMERIC(14,2) AS saldo
    FROM cuentas c
    LEFT JOIN flujo f
        ON f.cuenta_id = c.id
        AND f.estado = 'Confirmado'
        AND f.fecha BETWEEN fecha_inicio AND fecha_fin
    WHERE c.usuario_id = uid
    GROUP BY c.id, c.nombre
    ORDER BY c.nombre;
END;
$$ LANGUAGE plpgsql STABLE;

-- Función para reajustar el saldo de una cuenta
CREATE OR REPLACE FUNCTION fn_reajustar_saldo_cuenta(
    p_usuario_id VARCHAR(9),
    p_cuenta_id INT,
    p_saldo_real NUMERIC(14,2),
    p_descripcion TEXT DEFAULT 'Reajuste de saldo'
)
RETURNS VOID AS $$
DECLARE
    v_saldo_actual NUMERIC(14,2);
    v_diferencia NUMERIC(14,2);
    v_tipo_movimiento tipo_movimiento_enum;
    v_monto NUMERIC(14,2);
    v_categoria_id INT;
BEGIN
    -- 🔒 Validaciones
    IF p_usuario_id IS NULL THEN
        RAISE EXCEPTION 'usuario_id no puede ser NULL';
    END IF;

    IF p_saldo_real < 0 THEN
        RAISE EXCEPTION 'El saldo real no puede ser negativo';
    END IF;

    -- 🔐 Verificar que la cuenta pertenece al usuario
    PERFORM 1
    FROM cuentas
    WHERE id = p_cuenta_id
      AND usuario_id = p_usuario_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'La cuenta no pertenece al usuario';
    END IF;

    -- 📊 Obtener saldo actual
    SELECT saldo
    INTO v_saldo_actual
    FROM fn_saldo_por_cuenta(p_usuario_id)
    WHERE cuenta_id = p_cuenta_id;

    v_saldo_actual := COALESCE(v_saldo_actual, 0);

    -- 🧮 Calcular diferencia
    v_diferencia := p_saldo_real - v_saldo_actual;

    -- 🟰 Si no hay diferencia, no hacer nada
    IF v_diferencia = 0 THEN
        RETURN;
    END IF;

    -- 🧭 Determinar tipo
    IF v_diferencia > 0 THEN
        v_tipo_movimiento := 'Ingreso';
        v_monto := v_diferencia;
    ELSE
        v_tipo_movimiento := 'Egreso';
        v_monto := ABS(v_diferencia);
    END IF;

    -- 🗂 Obtener o crear categoría "Reajuste de saldo"
    SELECT id
    INTO v_categoria_id
    FROM categorias
    WHERE usuario_id = p_usuario_id
      AND nombre = 'Reajuste de saldo'
      AND tipo_movimiento = v_tipo_movimiento;

    IF v_categoria_id IS NULL THEN
        INSERT INTO categorias (usuario_id, nombre, tipo_movimiento)
        VALUES (p_usuario_id, 'Reajuste de saldo', v_tipo_movimiento)
        RETURNING id INTO v_categoria_id;
    END IF;

    -- 📝 Insertar movimiento
    INSERT INTO flujo (
        usuario_id,
        fecha,
        descripcion,
        categoria_id,
        cuenta_id,
        tipo_movimiento,
        estado,
        monto,
        tipo_egreso
    ) VALUES (
        p_usuario_id,
        CURRENT_DATE,
        p_descripcion,
        v_categoria_id,
        p_cuenta_id,
        v_tipo_movimiento,
        'Confirmado',
        v_monto,
        CASE
            WHEN v_tipo_movimiento = 'Egreso' THEN 'Variable'::tipo_egreso_enum
            ELSE NULL
        END
    );

END;
$$ LANGUAGE plpgsql;

COMMIT;