"""
Redis client configuration and service
"""

import logging
import redis
from typing import Optional, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisService:
    def __init__(self):
        self.redis_client = None
        self._connect()

    def _connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None

    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        try:
            if self.redis_client:
                self.redis_client.ping()
                return True
        except Exception:
            pass
        return False

    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Set a key-value pair in Redis"""
        try:
            if not self.redis_client:
                return False
            return self.redis_client.set(key, value, ex=ex)
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False

    def get(self, key: str) -> Optional[str]:
        """Get a value from Redis"""
        try:
            if not self.redis_client:
                return None
            return self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None

    def delete(self, key: str) -> bool:
        """Delete a key from Redis"""
        try:
            if not self.redis_client:
                return False
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False

    def lpush(self, key: str, value: Any) -> Optional[int]:
        """Push value to the left of a list"""
        try:
            if not self.redis_client:
                return None
            return self.redis_client.lpush(key, value)
        except Exception as e:
            logger.error(f"Redis LPUSH error: {e}")
            return None

    def rpush(self, key: str, value: Any) -> Optional[int]:
        """Push value to the right of a list"""
        try:
            if not self.redis_client:
                return None
            return self.redis_client.rpush(key, value)
        except Exception as e:
            logger.error(f"Redis RPUSH error: {e}")
            return None

    def lpop(self, key: str) -> Optional[str]:
        """Pop value from the left of a list"""
        try:
            if not self.redis_client:
                return None
            return self.redis_client.lpop(key)
        except Exception as e:
            logger.error(f"Redis LPOP error: {e}")
            return None

    def rpop(self, key: str) -> Optional[str]:
        """Pop value from the right of a list"""
        try:
            if not self.redis_client:
                return None
            return self.redis_client.rpop(key)
        except Exception as e:
            logger.error(f"Redis RPOP error: {e}")
            return None

    def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            if not self.redis_client:
                return False
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS error: {e}")
            return False

    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time for a key"""
        try:
            if not self.redis_client:
                return False
            return bool(self.redis_client.expire(key, seconds))
        except Exception as e:
            logger.error(f"Redis EXPIRE error: {e}")
            return False

    def flushdb(self) -> bool:
        """Flush current database"""
        try:
            if not self.redis_client:
                return False
            self.redis_client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Redis FLUSHDB error: {e}")
            return False

    def close(self):
        """Close Redis connection"""
        try:
            if self.redis_client:
                self.redis_client.close()
                logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")


# Global Redis service instance
redis_service = RedisService()


def get_redis_service() -> RedisService:
    """Get Redis service instance"""
    return redis_service


async def init_redis():
    """Initialize Redis connection"""
    global redis_service
    redis_service = RedisService()
    logger.info("Redis service initialized")


async def close_redis():
    """Close Redis connection"""
    global redis_service
    if redis_service:
        redis_service.close()
    logger.info("Redis service closed")
