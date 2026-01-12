import json
import redis.asyncio as redis
from typing import Any, Optional

from core.settings import settings


# =====================================================
# Redis client (async)
# =====================================================
redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    decode_responses=True
)


# =====================================================
# Cache helpers
# =====================================================
async def cache_get(key: str) -> Optional[Any]:
    """
    Obtiene un valor desde Redis y lo deserializa desde JSON.
    """
    value = await redis_client.get(key)

    if value is None:
        return None

    return json.loads(value)


async def cache_set(
    key: str,
    value: Any,
    ttl: int | None = None
) -> None:
    """
    Guarda un valor en Redis serializado como JSON.
    """
    await redis_client.set(
        key,
        json.dumps(value),
        ex=ttl or settings.redis_ttl
    )


async def cache_delete_pattern(pattern: str) -> None:
    """
    Elimina múltiples keys usando un patrón (wildcard).
    Ideal para invalidaciones masivas.
    """
    async for key in redis_client.scan_iter(pattern):
        await redis_client.delete(key)
