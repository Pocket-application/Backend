import time
import json
from threading import Lock
from fastapi import Request, HTTPException
from jose import jwt, JWTError
from database import SessionLocal
from models.auditoria import Auditoria
from security.log_signer import sign_log
from core.settings import settings

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm

PUBLIC_PATH_PREFIXES = (
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
    "/static",
)

NO_AUDIT_PATHS = (
    "/auth/login",
    "/auth/refresh",
    "/usuarios",
)

RATE_LIMIT_RULES = {
    "/auth/login": (5, 300),
    "/usuarios": (5, 60),
}

DEFAULT_LIMIT = (100, 60)

_rate_limit_store = {}
_rate_limit_lock = Lock()


def is_rate_limited(key: str, limit: int, window: int) -> bool:
    now = time.time()
    with _rate_limit_lock:
        record = _rate_limit_store.get(key)
        if not record or now > record["reset"]:
            _rate_limit_store[key] = {"count": 1, "reset": now + window}
            return False
        record["count"] += 1
        return record["count"] > limit


# ======================================================
# MIDDLEWARE FUNCIONAL (CORRECTO)
# ======================================================
async def auditoria_middleware(request: Request, call_next):

    # 🔴 CORS preflight
    if request.method == "OPTIONS":
        return await call_next(request)

    path = request.url.path

    # 🔓 Rutas públicas
    if path.startswith(PUBLIC_PATH_PREFIXES):
        return await call_next(request)

    start = time.time()
    usuario_id = None
    status_code = 500
    ip = request.client.host if request.client else "unknown"
    method = request.method

    # 🔹 Rate limit
    limit, window = RATE_LIMIT_RULES.get(path, DEFAULT_LIMIT)
    rate_key = f"{ip}:{method}:{path}"

    if is_rate_limited(rate_key, limit, window):
        raise HTTPException(429, "Demasiadas solicitudes")

    # 🔹 JWT (NO rompe)
    auth = request.headers.get("authorization")
    if auth and auth.startswith("Bearer "):
        try:
            payload = jwt.decode(
                auth.split(" ", 1)[1],
                SECRET_KEY,
                algorithms=[ALGORITHM],
                options={"verify_exp": True},
            )
            usuario_id = payload.get("sub")
        except JWTError:
            pass

    # 🔹 Ejecutar request
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response

    finally:
        # ❗ Auditoría JAMÁS debe romper la app
        if path in NO_AUDIT_PATHS:
            pass

        try:
            duration_ms = int((time.time() - start) * 1000)

            db = SessionLocal()
            last = db.query(Auditoria.firma).order_by(Auditoria.id.desc()).first()
            firma_anterior = last[0] if last else None

            log_data = {
                "usuario_id": usuario_id,
                "metodo": method,
                "ruta": path,
                "status_code": status_code,
                "ip": ip,
                "duracion_ms": duration_ms,
            }

            firma = sign_log(log_data, firma_anterior)

            db.add(
                Auditoria(
                    usuario_id=usuario_id,
                    metodo=method,
                    ruta=path,
                    status_code=status_code,
                    ip=ip,
                    duracion_ms=duration_ms,
                    firma=firma,
                    firma_anterior=firma_anterior,
                )
            )
            db.commit()

        except Exception as e:
            print("⚠️ Auditoría falló:", e)

        finally:
            try:
                db.close()  # type: ignore
            except Exception:
                pass
