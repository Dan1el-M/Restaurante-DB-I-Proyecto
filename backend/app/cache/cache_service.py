import json
import os
from backend.app.cache.redis_client import redis_client

CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS")) # Time To Live, el tiempo que va a vivir el cache


def get_cache(key: str):
    data = redis_client.get(key)

    if data is None:
        return None

    return json.loads(data)


def set_cache(key: str, value, ttl: int = CACHE_TTL_SECONDS):
    redis_client.setex(
        key,
        ttl,
        json.dumps(value, default=str)
    )


def delete_cache(key: str):
    redis_client.delete(key)


def delete_cache_pattern(pattern: str):
    keys = list(redis_client.scan_iter(match=pattern))
    if keys:
        redis_client.delete(*keys)
