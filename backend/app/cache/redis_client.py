import os
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

redis_client = redis.Redis.from_url( # Inicializa el cliente
    REDIS_URL,
    decode_responses=True
)