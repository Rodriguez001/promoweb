"""
Redis configuration and connection management for PromoWeb Africa.
Handles caching, sessions, and background task queuing.
"""

import json
import logging
from typing import Any, Dict, Optional, Union, List
from datetime import timedelta

# Conditionally import aioredis if available
try:
    import aioredis
    from aioredis import Redis
    REDIS_AVAILABLE = True
except ImportError:
    # Mock Redis for development
    REDIS_AVAILABLE = False
    
    class MockRedis:
        """Mock Redis implementation for development"""
        
        def __init__(self, *args, **kwargs):
            self.data = {}
            self.expirations = {}
            
        async def ping(self):
            return True
            
        async def info(self):
            return {"redis_version": "mock", "used_memory_human": "0B", 
                    "used_memory_peak_human": "0B", "connected_clients": 1, 
                    "uptime_in_seconds": 0}
            
        async def get(self, key):
            return self.data.get(key)
            
        async def set(self, key, value, ex=None, nx=False, xx=False):
            if nx and key in self.data:
                return False
            if xx and key not in self.data:
                return False
            self.data[key] = value
            if ex:
                self.expirations[key] = ex
            return True
            
        async def delete(self, *keys):
            count = 0
            for key in keys:
                if key in self.data:
                    del self.data[key]
                    count += 1
            return count
            
        async def exists(self, key):
            return key in self.data
            
        async def expire(self, key, ttl):
            if key in self.data:
                self.expirations[key] = ttl
                return True
            return False
            
        async def ttl(self, key):
            if key not in self.data:
                return -2
            return self.expirations.get(key, -1)
            
        async def incr(self, key, amount=1):
            if key not in self.data:
                self.data[key] = "0"
            self.data[key] = str(int(self.data[key]) + amount)
            return int(self.data[key])
            
        async def decr(self, key, amount=1):
            return await self.incr(key, -amount)
            
        async def mget(self, keys):
            return [self.data.get(key) for key in keys]
            
        async def mset(self, mapping):
            for key, value in mapping.items():
                self.data[key] = value
            return True
            
        async def scan_iter(self, match=None):
            import re
            pattern = re.compile(match.replace("*", ".*"))
            for key in self.data.keys():
                if pattern.match(key):
                    yield key
                    
        async def close(self):
            self.data = {}
            self.expirations = {}
    
    # Mock Redis class
    Redis = MockRedis

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Global Redis connection
redis_client: Optional[Redis] = None


async def init_redis() -> None:
    """Initialize Redis connection."""
    global redis_client
    
    try:
        if REDIS_AVAILABLE:
            redis_client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30,
            )
            
            # Test connection
            await redis_client.ping()
            logger.info("✅ Redis connection established")
        else:
            # Use mock Redis for development
            redis_client = Redis()
            logger.warning("⚠️ Using mock Redis for development (aioredis not installed)")
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to Redis: {e}")
        if not REDIS_AVAILABLE:
            # Use mock Redis as fallback
            redis_client = Redis()
            logger.warning("⚠️ Using mock Redis as fallback due to connection error")
        else:
            raise


async def close_redis() -> None:
    """Close Redis connection."""
    global redis_client
    
    if redis_client:
        try:
            await redis_client.close()
            logger.info("✅ Redis connection closed")
        except Exception as e:
            logger.error(f"❌ Error closing Redis connection: {e}")


async def get_redis_status() -> Dict[str, Any]:
    """
    Get Redis connection status for health checks.
    
    Returns:
        Dict[str, Any]: Redis status information
    """
    if not redis_client:
        return {"status": "unhealthy", "error": "Redis client not initialized"}
    
    try:
        # Test connection
        pong = await redis_client.ping()
        
        if pong:
            # Get Redis info
            info = await redis_client.info()
            
            return {
                "status": "healthy",
                "version": info.get("redis_version"),
                "memory": {
                    "used": info.get("used_memory_human"),
                    "peak": info.get("used_memory_peak_human"),
                },
                "connections": info.get("connected_clients"),
                "uptime": info.get("uptime_in_seconds"),
            }
        else:
            return {"status": "unhealthy", "error": "Ping failed"}
            
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
        }


class RedisCache:
    """Redis cache manager with JSON serialization support."""
    
    def __init__(self, client: Redis = None):
        self.client = client or redis_client
        self._initialized = bool(self.client)
    
    async def _ensure_client(self):
        """Ensure Redis client is initialized."""
        global redis_client
        if not self.client:
            if not redis_client:
                # Create a mock Redis client if needed
                self.client = Redis()
                logger.warning("⚠️ Using mock Redis client as fallback")
            else:
                self.client = redis_client
            self._initialized = True
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            await self._ensure_client()
            value = await self.client.get(key)
            if value is None:
                return None
            
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            nx: Only set if key doesn't exist
            xx: Only set if key exists
            
        Returns:
            True if set successfully
        """
        try:
            await self._ensure_client()
            
            # Serialize value if it's not a string
            if not isinstance(value, (str, int, float)):
                value = json.dumps(value, default=str)
            
            # Set TTL
            expire = ttl or settings.REDIS_CACHE_TTL
            
            result = await self.client.set(
                key, value, ex=expire, nx=nx, xx=xx
            )
            return bool(result)
            
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False
    
    async def delete(self, *keys: str) -> int:
        """
        Delete keys from cache.
        
        Args:
            keys: Keys to delete
            
        Returns:
            Number of keys deleted
        """
        try:
            await self._ensure_client()
            if not keys:
                return 0
            return await self.client.delete(*keys)
        except Exception as e:
            logger.error(f"Error deleting cache keys {keys}: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists
        """
        try:
            await self._ensure_client()
            return bool(await self.client.exists(key))
        except Exception as e:
            logger.error(f"Error checking cache key {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration for key.
        
        Args:
            key: Cache key
            ttl: Time to live in seconds
            
        Returns:
            True if expiration set successfully
        """
        try:
            await self._ensure_client()
            return bool(await self.client.expire(key, ttl))
        except Exception as e:
            logger.error(f"Error setting expiration for key {key}: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """
        Get time to live for key.
        
        Args:
            key: Cache key
            
        Returns:
            Time to live in seconds (-1 if no expiration, -2 if key doesn't exist)
        """
        try:
            await self._ensure_client()
            return await self.client.ttl(key)
        except Exception as e:
            logger.error(f"Error getting TTL for key {key}: {e}")
            return -2
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """
        Increment value by amount.
        
        Args:
            key: Cache key
            amount: Amount to increment
            
        Returns:
            New value after increment
        """
        try:
            await self._ensure_client()
            return await self.client.incr(key, amount)
        except Exception as e:
            logger.error(f"Error incrementing key {key}: {e}")
            return 0
    
    async def decr(self, key: str, amount: int = 1) -> int:
        """
        Decrement value by amount.
        
        Args:
            key: Cache key
            amount: Amount to decrement
            
        Returns:
            New value after decrement
        """
        try:
            await self._ensure_client()
            return await self.client.decr(key, amount)
        except Exception as e:
            logger.error(f"Error decrementing key {key}: {e}")
            return 0
    
    async def mget(self, keys: List[str]) -> List[Optional[Any]]:
        """
        Get multiple values from cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            List of values (None for missing keys)
        """
        try:
            await self._ensure_client()
            values = await self.client.mget(keys)
            result = []
            
            for value in values:
                if value is None:
                    result.append(None)
                else:
                    try:
                        result.append(json.loads(value))
                    except (json.JSONDecodeError, TypeError):
                        result.append(value)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting multiple cache keys {keys}: {e}")
            return [None] * len(keys)
    
    async def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Set multiple values in cache.
        
        Args:
            mapping: Dictionary of key-value pairs
            ttl: Time to live in seconds
            
        Returns:
            True if all values set successfully
        """
        try:
            await self._ensure_client()
            # Serialize values
            serialized = {}
            for key, value in mapping.items():
                if not isinstance(value, (str, int, float)):
                    value = json.dumps(value, default=str)
                serialized[key] = value
            
            # Set values
            result = await self.client.mset(serialized)
            
            # Set expiration if specified
            if ttl and result:
                expire_time = ttl or settings.REDIS_CACHE_TTL
                for key in mapping.keys():
                    await self.client.expire(key, expire_time)
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Error setting multiple cache keys: {e}")
            return False
    
    async def flush_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., "user:*")
            
        Returns:
            Number of keys deleted
        """
        try:
            await self._ensure_client()
            keys = []
            async for key in self.client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await self.client.delete(*keys)
            return 0
            
        except Exception as e:
            logger.error(f"Error flushing pattern {pattern}: {e}")
            return 0


# Global cache instance
cache: Optional[RedisCache] = None


def get_cache() -> RedisCache:
    """Get global cache instance."""
    global cache
    if not cache:
        cache = RedisCache()
    return cache
