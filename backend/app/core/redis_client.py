import json
import redis
from app.config import settings

_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    decode_responses=True,
)

def save_refresh_token(token: str, user_data: dict, ttl_days: int = 7):
    key = f"refresh_token:{token}"
    _client.setex(key, ttl_days * 86400, json.dumps(user_data))

def get_refresh_token(token: str) -> dict | None:
    key = f"refresh_token:{token}"
    data = _client.get(key)
    return json.loads(data) if data else None

def delete_refresh_token(token: str):
    key = f"refresh_token:{token}"
    _client.delete(key)
