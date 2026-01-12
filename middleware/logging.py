import time
import json
import os
from threading import Lock
from fastapi import Request, HTTPException
from jose import jwt, JWTError
from database import SessionLocal
from models.auditoria import Auditoria
from security.log_signer import sign_log
from core.settings import settings

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm

# ===============================
# RUTAS PÚBLICAS (Swagger / OpenAPI)
# ===============================
PUBLIC_PATH_PREFIXES = (
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
    "/static"
)

# ===============================
# RATE LIMIT CONFIG
# ===============================

RATE_LIMIT_RULES = {
    "/auth/login": (5, 300),
    "/usuarios": (5, 60),
    "/transferencias": (20, 60),
}

# ===============================
# SESNSITIVE FIELDS
# ===============================

SENSITIVE_FIELDS = {
    "password",
    "password_confirm",
    "current_password",
    "new_password",
    "token",
    "access_token",
    "refresh_token"
}

# ===============================
# RUTAS DONDE NO SE LOGUEA EL BODY
# ===============================

NO_BODY_LOG_PATHS = (
    "/auth/login",
    "/auth/refresh"
)


DEFAULT_LIMIT = (100, 60)

_rate_limit_store = {}
_rate_limit_lock = Lock()


def is_rate_limited(key: str, limit: int, window: int) -> bool:
    """
    Evalúa si una clave ha excedido el límite de solicitudes permitido.
    """
    now = time.time()

    with _rate_limit_lock:
        record = _rate_limit_store.get(key)

        if not record or now > record["reset"]:
            _rate_limit_store[key] = {
                "count": 1,
                "reset": now + window
            }
            return False

        record["count"] += 1
        return record["count"] > limit


def sanitize_body(data):
    """
    Elimina o enmascara campos sensibles del body antes de auditar.
    """
    if isinstance(data, dict):
        return {
            key: "***REDACTED***" if key.lower() in SENSITIVE_FIELDS else sanitize_body(value)
            for key, value in data.items()
        }

    if isinstance(data, list):
        return [sanitize_body(item) for item in data]

    return data


# ===============================
# AUDITORÍA + RATE LIMIT
# ===============================

async def auditoria_middleware(request: Request, call_next):
    """
    Middleware global de auditoría, seguridad y rate limiting.
    """
    path = request.url.path

    # 🔓 SALIDA TEMPRANA PARA RUTAS PÚBLICAS
    if path.startswith(PUBLIC_PATH_PREFIXES):
        return await call_next(request)

    start = time.time()
    usuario_id = None
    body_data = None
    error_message = None
    status_code = 500
    ip = request.client.host if request.client else "unknown"
    method = request.method

    # 🔹 Rate limit
    limit, window = RATE_LIMIT_RULES.get(path, DEFAULT_LIMIT)
    rate_key = f"{ip}:{method}:{path}"

    if is_rate_limited(rate_key, limit, window):
        status_code = 429
        error_message = "Rate limit excedido"

        raise HTTPException(
            status_code=429,
            detail="Demasiadas solicitudes, intenta más tarde"
        )

    # 🔹 Capturar body solo si muta estado
    if method in ("POST", "PUT", "PATCH", "DELETE") and path not in NO_BODY_LOG_PATHS:
        try:
            body_bytes = await request.body()
            raw_body = json.loads(body_bytes.decode()) if body_bytes else None
            body_data = sanitize_body(raw_body)
        except Exception:
            body_data = {"error": "Body no serializable"}

    # 🔹 Extraer usuario desde JWT
    auth = request.headers.get("authorization")
    if auth and auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": True})
            usuario_id = payload.get("sub")
            request.state.user = payload  # opcional, si quieres usarlo en rutas
        except JWTError:
            usuario_id = None

    # 🔹 Ejecutar la petición
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception as e:
        error_message = str(e)
        raise
    finally:
        # 🔹 Guardar auditoría
        duration_ms = int((time.time() - start) * 1000)
        db = SessionLocal()
        try:
            last = db.query(Auditoria.firma).order_by(Auditoria.id.desc()).first()
            firma_anterior = last[0] if last else None

            log_data = {
                "usuario_id": usuario_id,
                "metodo": method,
                "ruta": path,
                "status_code": status_code,
                "ip": ip,
                "body": body_data,
                "error": error_message,
                "duracion_ms": duration_ms
            }

            firma = sign_log(log_data, firma_anterior)

            auditoria = Auditoria(
                usuario_id=usuario_id,
                metodo=method,
                ruta=path,
                status_code=status_code,
                ip=ip,
                body=body_data,
                error=error_message,
                duracion_ms=duration_ms,
                firma=firma,
                firma_anterior=firma_anterior
            )

            db.add(auditoria)
            db.commit()
        finally:
            db.close()