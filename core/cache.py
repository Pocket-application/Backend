import json
import redis.asyncio as redis
from typing import Any, Optional

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)

DEFAULT_TTL = 60 * 5  # 5 minutos


async def cache_get(key: str) -> Optional[Any]:
    value = await redis_client.get(key)

    if value is None:
        return None

    return json.loads(value)


async def cache_set(
    key: str,
    value: Any,
    ttl: int = DEFAULT_TTL
) -> None:
    await redis_client.set(
        key,
        json.dumps(value),
        ex=ttl
    )


async def cache_delete_pattern(pattern: str) -> None:
    async for key in redis_client.scan_iter(pattern):
        await redis_client.delete(key)
