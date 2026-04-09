"""
Kyro — Redis Cache Manager

Provides a simple interface for caching JSON-serializable data.
"""

import json
from typing import Any, Optional
import redis
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("core.cache")

# Singleton Redis client
_client: Optional[redis.Redis] = None
_enabled: bool = True

def get_redis_client() -> Optional[redis.Redis]:
    """Return the initialised Redis client, or None if disabled/failed."""
    global _client, _enabled
    if not _enabled:
        return None
        
    if _client is None:
        try:
            _client = redis.from_url(settings.redis.URL, decode_responses=True)
            # Test connection
            _client.ping()
            logger.info("Redis client connected to %s", settings.redis.URL)
        except Exception as e:
            logger.error("Failed to connect to Redis: %s. Caching will be disabled for this session.", e)
            _enabled = False
            _client = None
    return _client

def get_json(key: str) -> Optional[Any]:
    """Retrieve and decode JSON data from cache."""
    try:
        client = get_redis_client()
        if not client:
            return None
            
        data = client.get(key)
        if data:
            logger.debug("Cache HIT [%s]", key)
            return json.loads(data)
        logger.debug("Cache MISS [%s]", key)
        return None
    except Exception as e:
        logger.warning("Cache GET failed [%s]: %s", key, e)
        return None

def set_json(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """Serialize and store JSON data in cache."""
    try:
        client = get_redis_client()
        if not client:
            return False
            
        ttl = ttl or settings.redis.DEFAULT_TTL
        client.set(key, json.dumps(value), ex=ttl)
        logger.debug("Cache SET [%s] (ttl=%ds)", key, ttl)
        return True
    except Exception as e:
        logger.warning("Cache SET failed [%s]: %s", key, e)
        return False

def delete(key: str) -> bool:
    """Remove a key from cache."""
    try:
        client = get_redis_client()
        if not client:
            return False
            
        client.delete(key)
        logger.debug("Cache DEL [%s]", key)
        return True
    except Exception as e:
        logger.warning("Cache DEL failed [%s]: %s", key, e)
        return False

def delete_pattern(pattern: str) -> int:
    """Remove all keys matching a pattern."""
    try:
        client = get_redis_client()
        if not client:
            return 0
            
        keys = client.keys(pattern)
        if keys:
            client.delete(*keys)
            logger.debug("Cache DEL pattern [%s] (%d keys)", pattern, len(keys))
            return len(keys)
        return 0
    except Exception as e:
        logger.warning("Cache DEL pattern failed [%s]: %s", pattern, e)
        return 0
