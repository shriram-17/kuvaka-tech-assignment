# src/utils/cache.py
import redis
import json
from typing import Optional, List, Dict
from src.core.config import settings

# Initialize Redis client
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    db=settings.REDIS_DB,
    decode_responses=True,
    ssl=settings.REDIS_SSL,
)

# --- CHATROOM CACHE ---
def cache_chatrooms(user_id: str, chatrooms: List[Dict]) -> None:
    """Cache user’s chatroom list with 5-minute TTL"""
    key = f"chatrooms:user:{user_id}"
    redis_client.setex(key, 300, json.dumps(chatrooms))

def get_cached_chatrooms(user_id: str) -> Optional[List[Dict]]:
    """Get cached chatrooms, return None if not found or expired"""
    key = f"chatrooms:user:{user_id}"
    data = redis_client.get(key)
    if data:
        return json.loads(data)
    return None

def invalidate_chatrooms_cache(user_id: str) -> None:
    """Delete cache when chatroom is created/deleted"""
    key = f"chatrooms:user:{user_id}"
    redis_client.delete(key)

# --- MESSAGE COUNT CACHE (Optional future enhancement) ---
# Can be used to cache daily message count for rate-limiting if needed
def get_daily_message_count(user_id: str) -> Optional[int]:
    key = f"msgcount:user:{user_id}"
    count = redis_client.get(key)
    return int(count) if count else None

def set_daily_message_count(user_id: str, count: int) -> None:
    key = f"msgcount:user:{user_id}"
    redis_client.setex(key, 86400, str(count))  # 24h TTL