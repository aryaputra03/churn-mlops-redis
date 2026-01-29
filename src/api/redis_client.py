"""
Redis Client Configuration - Upstash Cloud

Centralized Redis connection management for:
- Rate Limiting
- Response Caching
- Session Management
- Prediction Result Caching
"""
import os
import redis
from typing import Optional, Any, Union
import json
from datetime import timedelta
import logging
from functools import wraps
import hashlib

logger = logging.getLogger(__name__)

class UpstashRedisClient:
    """
    Upstash Redis Client with automatic connection handling
    
    Features:
    - Auto-reconnect on connection failure
    - Fallback to in-memory cache if Redis unavailable
    - TLS/SSL support for Upstash
    - Connection pooling
    """
    _instance = None
    _client = None
    _fallback_cache = {}

    def __new__(cls):
        """Singleton pattern to ensure single Redis connection"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Redis connection"""
        if self._client is None:
            self._connect()

    def _connect(self):
        """Connect to Upstash Redis"""
        try:
            redis_url = os.getenv("UPSTASH_REDIS_URL") or os.getenv("REDIS_URL")

            if not redis_url:
                logger.warning("No Redis URL found, using in-memory fallback")
                return
            
            if redis_url.startswith("rediss://"):
                self._client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30,
                    ssl_cert_reqs=None
                )
            else:
                self._client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )

            self._client.ping()
            logger.info("Connected to Upstash Redis successfully")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            logger.warning("Using in-memory fallback cache")
            self._client = None
    
    def is_avaible(self) -> bool:
        """Check if Redis is available"""
        if not self._client:
            return False
        
        try:
            self._client.ping()
            return True
        except:
            return False
        
    def get(self, key: str, default: Any = None) -> Optional[Any]:
        """
        Get value from Redis with automatic JSON deserialization
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        try:
            if not self._client:
                return self._fallback_cache.get(key, default)
            value = self._client.get(key)
            
            if value is None:
                return default

            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        
        except Exception as e:
            logger.error(f"Redis GET error for key '{key}': {e}")
            return self._fallback_cache.get(key, default)
        
    def set(
            self,
            key: str,
            value: Any,
            ex: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """
        Set value in Redis with automatic JSON serialization
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized if not string)
            ex: Expiration time in seconds or timedelta
            
        Returns:
            True if successful
        """
        try:
            if isinstance(ex, timedelta):
                ex = int(ex.total_seconds())
            
            if not isinstance(value, str):
                value = json.dumps(value)
            
            if not self._client:
                self._fallback_cache[key] = value
                return True
            
            return bool(self._client.set(key, value, ex=ex))
        
        except Exception as e:
            logger.error(f"Redis SET error for key '{key}': {e}")
            self._fallback_cache[key] = value
            return False
    
    def delete(self, *keys: str) -> int:
        """
        Delete one or more keys
        
        Args:
            *keys: Keys to delete
            
        Returns:
            Number of keys deleted
        """
        try:
            if not self._client:
                deleted = 0
                for key in keys:
                    if key in self._fallback_cache:
                        del self._fallback_cache[key]
                        deleted += 1
                return deleted
            
            return self._client.delete(*keys)

        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return 0

    def exists(self, *keys: str) -> int:
        """
        Check if keys exist
        
        Args:
            *keys: Keys to check
            
        Returns:
            Number of existing keys
        """
        try:
            if not self._client:
                return sum(1 for key in keys if key in self._fallback_cache)
            
            return self._client.exists(*keys)
        
        except Exception as e:
            logger.error(f"Redis EXISTS error: {e}")
            return 0
        
    def incr(self, key: str, amount: int = 1) -> int:
        """
        Increment key by amount
        
        Args:
            key: Key to increment
            amount: Amount to increment by
            
        Returns:
            New value after increment
        """

        try:
            if not self._client:
                current = int(self._fallback_cache.get(key, 0))
                new_value = current + amount
                self._fallback_cache[key] = str(new_value)
                return new_value
            
            return self._client.incr(key, amount)

        except Exception as e:
            logger.error(f"Redis INCR error for key '{key}': {e}")
            return 0
        
    def expire(self, key: str, time: Union[int, timedelta]) -> bool:
        """
        Set key expiration
        
        Args:
            key: Key to expire
            time: Expiration time in seconds or timedelta
            
        Returns:
            True if successful
        """
        try:
            if isinstance(time, timedelta):
                time = int(time.total_seconds())

            if not self._client:
                return True
            
            return bool(self._client.expire(key, time))
        
        except Exception as e:
            logger.error(f"Redis EXPIRE error for key '{key}': {e}")
            return False
        
    def ttl(self, key: str) -> int:
        """
        Get time to live for key
        
        Args:
            key: Key to check
            
        Returns:
            TTL in seconds (-1 if no expiration, -2 if key doesn't exist)
        """
        try:
            if not self._client:
                return -1
            
            return self._client.ttl(key)
        
        except Exception as e:
            logger.error(f"Redis TTL error for key '{key}': {e}")
            return -2
    
    def flushdb(self) -> bool:
        """
        Clear all keys in current database
        
        ⚠️  Use with caution!
        
        Returns:
            True if successful
        """
        try:
            if not self._client:
                self._fallback_cache.clear()
                return True
            
            self._client.flushdb()
            return True
        
        except Exception as e:
            logger.error(f"Redis FLUSHDB error: {e}")
            return False
    
    def keys(self, pattern: str = "*") -> list:
        """
        Get keys matching pattern
        
        Args:
            pattern: Key pattern (e.g., "cache:*")
            
        Returns:
            List of matching keys
        """
        try:
            if not self._client:
                return [k for k in self._fallback_cache.keys() if self._match_pattern(k, pattern)]
            
            return self._client.keys(pattern)
        
        except Exception as e:
            logger.error(f"Redis KEYS error: {e}")
            return []
        
    @staticmethod
    def _match_pattern(string: str, pattern: str) -> bool:
        """Simple pattern matching for fallback cache"""
        if pattern == "*":
            return True
        if "*" in pattern:
            import re
            regex = pattern.replace("*", ".*")
            return bool(re.match(f"^{regex}$", string))
        return string == pattern
        
    def get_info(self) -> dict:
        """
        Get Redis server info
        
        Returns:
            Dictionary with Redis info
        """
        try:
            if not self._client:
                return {
                    "status": "fallback",
                    "type": "in-memory",
                    "keys": len(self._fallback_cache)
                }
            
            info = self._client.info()
            return {
                "status": "connected",
                "type": "upstash" if "upstash" in str(self._client) else "redis",
                "version": info.get("redis_version", "unknown"),
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "total_keys": self._client.dbsize()
            }
        
        except Exception as e:
            logger.error(f"Redis INFO error: {e}")
            return {"status": "error", "error": str(e)}
    
redis_client = UpstashRedisClient()

def cache_result(
        prefix: str = "cache",
        ttl: int = 300,
        key_builder : Optional[callable] = None
):
    """
    Decorator to cache function results in Redis
    
    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds (default: 5 minutes)
        key_builder: Optional function to build cache key from arguments
        
    Example:
        @cache_result(prefix="predictions", ttl=600)
        def predict(customer_id: str, data: dict):
            # Expensive operation
            return model.predict(data)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if key_builder:
                cache_key = f"{prefix}:{key_builder(*args, **kwargs)}"
            else:
                args_str = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
                args_hash = hashlib.md5(args_str.encode()).hexdigest()
                cache_key = f"{prefix}:{func.__name__}:{args_hash}"


            cache_value = redis_client.get(cache_key)
            if cache_value is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cache_value
            
            logger.debug(f"Cache MISS: {cache_key}")
            result = func(*args, **kwargs)

            redis_client.set(cache_key, result, ex=ttl)

            return result
        
        return wrapper
    return decorator

def invalidate_cache(pattern: str):
    """
    Delete all cache keys matching pattern
    
    Args:
        pattern: Key pattern (e.g., "predictions:*")
        
    Example:
        invalidate_cache("predictions:customer_*")
    """
    try:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
            logger.info(f"Invalidated {len(keys)} cache keys matching '{pattern}'")
    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")

def check_redis_health() -> dict:
    """
    Check Redis connection health
    
    Returns:
        Dictionary with health status
    """
    return {
        "healthy": redis_client.is_avaible(),
        "info": redis_client.get_info()
    }
