import time
import json
import os
from threading import Lock
from fastapi import Request, HTTPException
from jose import jwt, JWTError
from database import SessionLocal
from models.auditoria import Auditoria
from security.log_signer import sign_log

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = os.environ["ALGORITHM"]

# ===============================
# RATE LIMIT CONFIG
# ===============================

"""
Configuración de límites de solicitudes (rate limiting) por endpoint.

Formato:
    ruta: (cantidad_maxima, ventana_en_segundos)

Ejemplos:
- /auth/login: 5 intentos cada 5 minutos
- /usuarios: 5 registros por minuto
- /transferencias: 20 operaciones por minuto
"""
RATE_LIMIT_RULES = {
    "/auth/login": (5, 300),
    "/usuarios": (5, 60),
    "/transferencias": (20, 60),
}

"""
Límite por defecto para endpoints no especificados explícitamente.
"""
DEFAULT_LIMIT = (100, 60)

"""
Almacén en memoria para control de rate limit.

Estructura:
{
    "ip:method:path": {
        "count": int,
        "reset": timestamp
    }
}
"""
_rate_limit_store = {}

"""
Lock para asegurar consistencia en ambientes concurrentes.
"""
_rate_limit_lock = Lock()


def is_rate_limited(key: str, limit: int, window: int) -> bool:
    """
    Evalúa si una clave ha excedido el límite de solicitudes permitido.

    Este método implementa un rate limit en memoria basado en ventana fija.

    Args:
        key (str): Identificador único del request (IP + método + ruta).
        limit (int): Número máximo de solicitudes permitidas.
        window (int): Ventana de tiempo en segundos.

    Returns:
        bool: True si el límite fue excedido, False en caso contrario.

    Seguridad:
        - Protege contra fuerza bruta
        - Protege contra abuso de endpoints críticos
        - No requiere almacenamiento externo (Redis)

    Nota:
        Este rate limit es por proceso y no distribuido.
    """
    now = time.time()

    with _rate_limit_lock:
        record = _rate_limit_store.get(key)

        # Reiniciar ventana si expiró
        if not record or now > record["reset"]:
            _rate_limit_store[key] = {
                "count": 1,
                "reset": now + window
            }
            return False

        record["count"] += 1
        return record["count"] > limit


# ===============================
# AUDITORÍA + RATE LIMIT
# ===============================

async def auditoria_middleware(request: Request, call_next):
    """
    Middleware global de auditoría, seguridad y rate limiting.

    Funciones principales:
    - Aplica rate limiting antes de ejecutar el endpoint
    - Registra auditoría legal de cada solicitud
    - Firma criptográficamente cada log (hash encadenado)
    - Identifica usuario autenticado (si existe)
    - Registra errores y tiempos de ejecución

    Auditoría registrada:
    - Usuario
    - IP
    - Método HTTP
    - Ruta
    - Código de respuesta
    - Body (cuando aplica)
    - Error (si ocurre)
    - Duración del request
    - Firma criptográfica
    - Firma anterior (anti-borrado)

    Args:
        request (Request): Request entrante de FastAPI.
        call_next: Función que ejecuta el siguiente middleware o endpoint.

    Returns:
        Response: Respuesta HTTP del endpoint.

    Seguridad:
        - Diseñado para auditoría legal
        - Prevención de fuerza bruta
        - Trazabilidad completa de cambios financieros
    """
    start = time.time()

    usuario_id = None
    body_data = None
    error_message = None
    status_code = 500

    ip = request.client.host if request.client else "unknown"
    path = request.url.path
    method = request.method

    # 🔹 Rate limit (ANTES de ejecutar el endpoint)
    limit, window = RATE_LIMIT_RULES.get(path, DEFAULT_LIMIT)
    rate_key = f"{ip}:{method}:{path}"

    if is_rate_limited(rate_key, limit, window):
        status_code = 429
        error_message = "Rate limit excedido"

        raise HTTPException(
            status_code=429,
            detail="Demasiadas solicitudes, intenta más tarde"
        )

    # 🔹 Capturar body solo para operaciones que mutan estado
    if method in ("POST", "PUT", "PATCH", "DELETE"):
        try:
            body_bytes = await request.body()
            body_data = json.loads(body_bytes.decode()) if body_bytes else None
        except Exception:
            body_data = {"error": "Body no serializable"}

    # 🔹 Extraer usuario desde JWT si existe
    auth = request.headers.get("authorization")
    if auth and auth.startswith("Bearer "):
        try:
            token = auth.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            usuario_id = payload.get("sub")
        except JWTError:
            usuario_id = None

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response

    except Exception as e:
        error_message = str(e)
        raise

    finally:
        duration_ms = int((time.time() - start) * 1000)

        db = SessionLocal()
        try:
            # 🔗 Obtener firma anterior (hash encadenado)
            last = (
                db.query(Auditoria.firma)
                .order_by(Auditoria.id.desc())
                .first()
            )
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
