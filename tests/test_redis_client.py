"""
Unit tests for Redis client service
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
from datetime import datetime, timedelta

from app.core.redis_client import RedisService
from app.core.exceptions import InternalServerErrorException


class TestRedisService:
    """Test Redis service functionality"""

    @pytest.fixture
    def mock_redis_pool(self):
        """Mock Redis connection pool"""
        mock_pool = MagicMock()
        mock_redis = AsyncMock()
        mock_pool.get.return_value = mock_redis
        return mock_pool, mock_redis

    @pytest.fixture
    def redis_service(self, mock_redis_pool):
        """Create RedisService instance with mocked pool"""
        mock_pool, mock_redis = mock_redis_pool
        service = RedisService()
        service.pool = mock_pool
        return service, mock_redis

    @pytest.mark.asyncio
    async def test_get_existing_key(self, redis_service):
        """Test getting an existing key"""
        service, mock_redis = redis_service
        mock_redis.get.return_value = b"test_value"
        
        result = await service.get("test_key")
        
        assert result == "test_value"
        mock_redis.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_non_existing_key(self, redis_service):
        """Test getting a non-existing key"""
        service, mock_redis = redis_service
        mock_redis.get.return_value = None
        
        result = await service.get("non_existing_key")
        
        assert result is None
        mock_redis.get.assert_called_once_with("non_existing_key")

    @pytest.mark.asyncio
    async def test_get_json_valid(self, redis_service):
        """Test getting valid JSON data"""
        service, mock_redis = redis_service
        test_data = {"key": "value", "number": 42}
        mock_redis.get.return_value = json.dumps(test_data).encode()
        
        result = await service.get_json("test_key")
        
        assert result == test_data
        mock_redis.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_json_invalid(self, redis_service):
        """Test getting invalid JSON data"""
        service, mock_redis = redis_service
        mock_redis.get.return_value = b"invalid_json"
        
        result = await service.get_json("test_key")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_set_string_value(self, redis_service):
        """Test setting a string value"""
        service, mock_redis = redis_service
        mock_redis.set.return_value = True
        
        result = await service.set("test_key", "test_value")
        
        assert result is True
        mock_redis.set.assert_called_once_with("test_key", "test_value", ex=None)

    @pytest.mark.asyncio
    async def test_set_with_expiration(self, redis_service):
        """Test setting a value with expiration"""
        service, mock_redis = redis_service
        mock_redis.set.return_value = True
        
        result = await service.set("test_key", "test_value", expire_seconds=3600)
        
        assert result is True
        mock_redis.set.assert_called_once_with("test_key", "test_value", ex=3600)

    @pytest.mark.asyncio
    async def test_set_json_data(self, redis_service):
        """Test setting JSON data"""
        service, mock_redis = redis_service
        mock_redis.set.return_value = True
        test_data = {"key": "value", "number": 42}
        
        result = await service.set_json("test_key", test_data)
        
        assert result is True
        expected_json = json.dumps(test_data)
        mock_redis.set.assert_called_once_with("test_key", expected_json, ex=None)

    @pytest.mark.asyncio
    async def test_delete_existing_key(self, redis_service):
        """Test deleting an existing key"""
        service, mock_redis = redis_service
        mock_redis.delete.return_value = 1
        
        result = await service.delete("test_key")
        
        assert result is True
        mock_redis.delete.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_delete_non_existing_key(self, redis_service):
        """Test deleting a non-existing key"""
        service, mock_redis = redis_service
        mock_redis.delete.return_value = 0
        
        result = await service.delete("non_existing_key")
        
        assert result is False
        mock_redis.delete.assert_called_once_with("non_existing_key")

    @pytest.mark.asyncio
    async def test_exists_true(self, redis_service):
        """Test checking if key exists (true case)"""
        service, mock_redis = redis_service
        mock_redis.exists.return_value = 1
        
        result = await service.exists("test_key")
        
        assert result is True
        mock_redis.exists.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_exists_false(self, redis_service):
        """Test checking if key exists (false case)"""
        service, mock_redis = redis_service
        mock_redis.exists.return_value = 0
        
        result = await service.exists("test_key")
        
        assert result is False
        mock_redis.exists.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_expire_key(self, redis_service):
        """Test setting expiration on a key"""
        service, mock_redis = redis_service
        mock_redis.expire.return_value = True
        
        result = await service.expire("test_key", 3600)
        
        assert result is True
        mock_redis.expire.assert_called_once_with("test_key", 3600)

    @pytest.mark.asyncio
    async def test_increment_existing_key(self, redis_service):
        """Test incrementing an existing key"""
        service, mock_redis = redis_service
        mock_redis.incr.return_value = 5
        
        result = await service.increment("counter_key")
        
        assert result == 5
        mock_redis.incr.assert_called_once_with("counter_key", 1)

    @pytest.mark.asyncio
    async def test_increment_with_amount(self, redis_service):
        """Test incrementing with custom amount"""
        service, mock_redis = redis_service
        mock_redis.incr.return_value = 10
        
        result = await service.increment("counter_key", 5)
        
        assert result == 10
        mock_redis.incr.assert_called_once_with("counter_key", 5)

    @pytest.mark.asyncio
    async def test_lpush_single_value(self, redis_service):
        """Test pushing single value to list"""
        service, mock_redis = redis_service
        mock_redis.lpush.return_value = 1
        
        result = await service.lpush("list_key", "value1")
        
        assert result == 1
        mock_redis.lpush.assert_called_once_with("list_key", "value1")

    @pytest.mark.asyncio
    async def test_lpush_multiple_values(self, redis_service):
        """Test pushing multiple values to list"""
        service, mock_redis = redis_service
        mock_redis.lpush.return_value = 3
        
        result = await service.lpush("list_key", "value1", "value2", "value3")
        
        assert result == 3
        mock_redis.lpush.assert_called_once_with(
            "list_key", "value1", "value2", "value3"
        )

    @pytest.mark.asyncio
    async def test_lpop_with_value(self, redis_service):
        """Test popping value from list"""
        service, mock_redis = redis_service
        mock_redis.lpop.return_value = b"value1"
        
        result = await service.lpop("list_key")
        
        assert result == "value1"
        mock_redis.lpop.assert_called_once_with("list_key")

    @pytest.mark.asyncio
    async def test_lpop_empty_list(self, redis_service):
        """Test popping from empty list"""
        service, mock_redis = redis_service
        mock_redis.lpop.return_value = None
        
        result = await service.lpop("empty_list")
        
        assert result is None
        mock_redis.lpop.assert_called_once_with("empty_list")

    @pytest.mark.asyncio
    async def test_rpush_single_value(self, redis_service):
        """Test pushing single value to right of list"""
        service, mock_redis = redis_service
        mock_redis.rpush.return_value = 1
        
        result = await service.rpush("list_key", "value1")
        
        assert result == 1
        mock_redis.rpush.assert_called_once_with("list_key", "value1")

    @pytest.mark.asyncio
    async def test_llen_list_length(self, redis_service):
        """Test getting list length"""
        service, mock_redis = redis_service
        mock_redis.llen.return_value = 5
        
        result = await service.llen("list_key")
        
        assert result == 5
        mock_redis.llen.assert_called_once_with("list_key")

    @pytest.mark.asyncio
    async def test_publish_message(self, redis_service):
        """Test publishing message to channel"""
        service, mock_redis = redis_service
        mock_redis.publish.return_value = 1
        
        result = await service.publish("channel", "message")
        
        assert result == 1
        mock_redis.publish.assert_called_once_with("channel", "message")

    @pytest.mark.asyncio
    async def test_publish_json_message(self, redis_service):
        """Test publishing JSON message to channel"""
        service, mock_redis = redis_service
        mock_redis.publish.return_value = 1
        test_data = {"type": "notification", "data": "test"}
        
        result = await service.publish_json("channel", test_data)
        
        assert result == 1
        expected_json = json.dumps(test_data)
        mock_redis.publish.assert_called_once_with("channel", expected_json)

    @pytest.mark.asyncio
    async def test_subscribe_to_channel(self, redis_service):
        """Test subscribing to channel"""
        service, mock_redis = redis_service
        mock_pubsub = AsyncMock()
        mock_redis.pubsub.return_value = mock_pubsub
        
        result = await service.subscribe("channel")
        
        assert result == mock_pubsub
        mock_redis.pubsub.assert_called_once()
        mock_pubsub.subscribe.assert_called_once_with("channel")

    @pytest.mark.asyncio
    async def test_cache_with_ttl_hit(self, redis_service):
        """Test cache hit with TTL"""
        service, mock_redis = redis_service
        cached_data = {"cached": True}
        mock_redis.get.return_value = json.dumps(cached_data).encode()
        
        async def expensive_operation():
            return {"computed": True}
        
        result = await service.cache_with_ttl(
            "cache_key", expensive_operation, ttl=3600
        )
        
        assert result == cached_data
        mock_redis.get.assert_called_once_with("cache_key")
        # set should not be called on cache hit
        mock_redis.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_with_ttl_miss(self, redis_service):
        """Test cache miss with TTL"""
        service, mock_redis = redis_service
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        
        computed_data = {"computed": True}
        
        async def expensive_operation():
            return computed_data
        
        result = await service.cache_with_ttl(
            "cache_key", expensive_operation, ttl=3600
        )
        
        assert result == computed_data
        mock_redis.get.assert_called_once_with("cache_key")
        expected_json = json.dumps(computed_data)
        mock_redis.set.assert_called_once_with("cache_key", expected_json, ex=3600)

    @pytest.mark.asyncio
    async def test_rate_limit_allowed(self, redis_service):
        """Test rate limiting when allowed"""
        service, mock_redis = redis_service
        mock_redis.get.return_value = b"5"  # Current count
        mock_redis.incr.return_value = 6
        mock_redis.expire.return_value = True
        
        result = await service.rate_limit("user123", limit=10, window=60)
        
        assert result is True
        mock_redis.get.assert_called_once_with("rate_limit:user123")
        mock_redis.incr.assert_called_once_with("rate_limit:user123")

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, redis_service):
        """Test rate limiting when exceeded"""
        service, mock_redis = redis_service
        mock_redis.get.return_value = b"10"  # At limit
        
        result = await service.rate_limit("user123", limit=10, window=60)
        
        assert result is False
        mock_redis.get.assert_called_once_with("rate_limit:user123")
        # incr should not be called when limit exceeded
        mock_redis.incr.assert_not_called()

    @pytest.mark.asyncio
    async def test_rate_limit_first_request(self, redis_service):
        """Test rate limiting for first request"""
        service, mock_redis = redis_service
        mock_redis.get.return_value = None  # No existing count
        mock_redis.incr.return_value = 1
        mock_redis.expire.return_value = True
        
        result = await service.rate_limit("user123", limit=10, window=60)
        
        assert result is True
        mock_redis.get.assert_called_once_with("rate_limit:user123")
        mock_redis.incr.assert_called_once_with("rate_limit:user123")
        mock_redis.expire.assert_called_once_with("rate_limit:user123", 60)

    @pytest.mark.asyncio
    async def test_get_rate_limit_info(self, redis_service):
        """Test getting rate limit information"""
        service, mock_redis = redis_service
        mock_redis.get.return_value = b"7"
        mock_redis.ttl.return_value = 45
        
        current, remaining, reset_time = await service.get_rate_limit_info(
            "user123", limit=10
        )
        
        assert current == 7
        assert remaining == 3
        assert reset_time == 45

    @pytest.mark.asyncio
    async def test_connection_error_handling(self, redis_service):
        """Test handling of connection errors"""
        service, mock_redis = redis_service
        mock_redis.get.side_effect = Exception("Connection failed")
        
        with pytest.raises(InternalServerErrorException):
            await service.get("test_key")

    @pytest.mark.asyncio
    async def test_cleanup_expired_keys(self, redis_service):
        """Test cleanup of expired keys"""
        service, mock_redis = redis_service
        mock_redis.scan.return_value = (0, [b"expired_key1", b"expired_key2"])
        mock_redis.delete.return_value = 2
        
        result = await service.cleanup_expired_keys("pattern:*")
        
        assert result == 2
        mock_redis.scan.assert_called_once_with(match="pattern:*")
        mock_redis.delete.assert_called_once_with("expired_key1", "expired_key2")

    @pytest.mark.asyncio
    async def test_health_check_success(self, redis_service):
        """Test successful health check"""
        service, mock_redis = redis_service
        mock_redis.ping.return_value = True
        
        result = await service.health_check()
        
        assert result is True
        mock_redis.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_failure(self, redis_service):
        """Test failed health check"""
        service, mock_redis = redis_service
        mock_redis.ping.side_effect = Exception("Connection failed")
        
        result = await service.health_check()
        
        assert result is False

    @pytest.mark.asyncio
    async def test_batch_operations(self, redis_service):
        """Test batch operations using pipeline"""
        service, mock_redis = redis_service
        mock_pipeline = AsyncMock()
        mock_redis.pipeline.return_value = mock_pipeline
        mock_pipeline.execute.return_value = [True, True, "value"]
        
        operations = [
            ("set", "key1", "value1"),
            ("set", "key2", "value2"),
            ("get", "key3")
        ]
        
        results = await service.batch_operations(operations)
        
        assert results == [True, True, "value"]
        mock_redis.pipeline.assert_called_once()
        mock_pipeline.execute.assert_called_once()