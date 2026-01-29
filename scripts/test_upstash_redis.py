"""
Test Upstash Redis Connection

Usage:
    python scripts/test_upstash_redis.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.redis_client import redis_client, check_redis_health
from src.api.cache_service import cache_service
from src.utils import logger

def test_basic_oprations():
    """Test basic Redis operations"""
    logger.info("=" * 60)
    logger.info("TEST 1: Basic Redis Operations")
    logger.info("=" * 60)

    try:
        # SET
        logger.info("Testing SET...")
        result = redis_client.set("test:key", "test_value", ex=60)
        assert result, "SET FAILED"
        logger.info("SET successful")

        # GET
        logger.info("Testing GET...")
        value = redis_client.get("test:key")
        assert value == "test_value", f"Expected 'test_value', got '{value}'"
        logger.info(f"GET successful: {value}")

        # EXISTS
        logger.info("Testing EXISTS...")
        exists = redis_client.exists("test:key")
        assert exists == 1, "Key should exist"
        logger.info("EXISTS successful")

        # TIL
        logger.info("Testing TTL...")
        ttl = redis_client.ttl("test:key")
        assert 0 < ttl <= 60, f"TTL should be between 0 and 60, got {ttl}"
        logger.info(f"TTL successful: {ttl} seconds")

        # DELETE
        logger.info("Testing DELETE...")
        deleted = redis_client.delete("test:key")
        assert deleted == 1, "DELETE should return 1"
        logger.info("DELETE successful")

        # Verify deleted
        value_after_delete = redis_client.get("test:key")
        assert value_after_delete is None, "Key should not exist after delete"
        logger.info("Key successfully deleted")

        logger.info("All basic operations passed!")
        return True
    
    except Exception as e:
        logger.error(f"Basic operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
def test_json_opration():
    """Test JSON serialization/deserialization"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: JSON Operations")
    logger.info("=" * 60)

    try:
        test_data = {
            "customer_id":"CUST001",
            "prediction": 1,
            "probability": 0.75,
            "metadata": {
                "model_version": "1.0.0",
                "features": ["tenure", "monthly_charges"]
            }
        }

        logger.info("Testing SET with JSON...")
        redis_client.set("test:json", test_data, ex=120)
        logger.info("JSON SET successful")

        logger.info("Testing GET JSON...")
        retrieved = redis_client.get("test:json")
        assert retrieved == test_data, "Retrieved data doesn't match"
        logger.info(f"JSON GET successful: {retrieved}")

        redis_client.delete("test:json")

        logger.info("All JSON operations passed!")

        return True
    
    except Exception as e:
        logger.error(f"JSON operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cache_service():
    """Test cache service functionality"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Cache Service")
    logger.info("=" * 60)

    try:
        logger.info("Testing prediction cache...")
        test_prediction = {
            "customer_id": "TEST001",
            "prediction": 1,
            "churn_probability": 0.82,
            "no_churn_probability": 0.18
        }

        input_hash = cache_service.hash_input_data({"test": "data"})

        cache_service.set_prediction("TEST001", input_hash, test_prediction)
        logger.info("Prediction cached")

        cached = cache_service.get_prediction("TEST001", input_hash)
        assert cached == test_prediction, "Cached prediction doesn't match"
        logger.info("Prediction retrieved from cache")

        logger.info("Testing analytics cache...")

        analytics_data = {
            "total_predictions": 100,
            "churn_rate": 0.25,
            "timestamp": "2024-01-15T10:00:00"
        }

        cache_service.set_analytics("summary", analytics_data)
        cached_analytics = cache_service.get_analytics("summary")
        assert cached_analytics == analytics_data, "Analytics cache mismatch"
        logger.info("Analytics cache working")

        logger.info("Testing cache invalidation...")
        cache_service.invalidate_predictions("TEST001")
        invalidated = cache_service.get_prediction("TEST001", input_hash)
        assert invalidated is None, "Cache should be invalidated"
        logger.info("Cache invalidation working")

        cache_service.invalidate_analytics()

        logger.info("\nAll cache service tests passed!")
        
        return True
    
    except Exception as e:
        logger.error(f"Cache service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
def test_rate_limiting():
    """Test rate limiting functionality"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 4: Rate Limiting")
    logger.info("=" * 60)

    try:
        from src.api.rate_limit import rate_limiter

        test_key = "test:ratelimit:client123"

        logger.info("Testing rate limit allowance...")
        for i in range(5):
            allowed = rate_limiter.is_allowed(test_key, max_requests=10, window_seconds=60)
            assert allowed, f"Request {i+1} should be allowed"
        logger.info("5 requests allowed (within limit)")

        remaining = rate_limiter.get_remaining(test_key, max_requests=10, window_seconds=60)
        logger.info(f"Remaining requests: {remaining}")
        assert remaining == 5, f"Expected 5 remaining, got {remaining}"

        logger.info("Testing rate limit blocking...")
        for i in range(5):
            rate_limiter.is_allowed(test_key, max_requests=10, window_seconds=60)
        
        blocked = rate_limiter.is_allowed(test_key, max_requests=10, window_seconds=60)
        assert not blocked, "Request should be blocked after limit"
        logger.info("Request blocked after limit reached")

        rate_limiter.reset(test_key)
        logger.info("Rate limit reset")

        logger.info("\nAll rate limiting tests passed!")
        return True
    
    except Exception as e:
        logger.error(f"Rate limiting test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cache_stats():
    """Test cache statistics"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 6: Cache Statistics")
    logger.info("=" * 60)

    try:
        redis_client.set("test:stat1", "value1")
        redis_client.set("test:stat2", "value2")
        redis_client.set("prediction:test", {"pred":1})
        
        stats = cache_service.get_cache_stats()

        logger.info("Cache Statistics:")
        logger.info(f"  Total Keys: {stats['total_keys']}")
        logger.info(f"  By Type: {stats['by_type']}")
        logger.info(f"  Redis Info: {stats.get('redis_info', {})}")

        redis_client.delete("test:stat1", "test:stat2", "prediction:test")

        logger.info("\nCache statistics test passed!")
        return True

    except Exception as e:
        logger.error(f"Cache statistics test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
def test_redis_info():
    """Test Redis connection info"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 5: Redis Info")
    logger.info("=" * 60)

    try:
        info = redis_client.get_info()

        logger.info("Redis Information:")
        for key, value in info.items():
            logger.info(f"  {key}: {value}")
        
        health = check_redis_health()
        logger.info(f"\nHealth Status: {health}")

        assert health["healthy"], "Redis should be healthy"
        logger.info("\nRedis info test passed!")
        return True

    except Exception as e:
        logger.error(f"Redis info test failed: {e}")
        return False
    
def main():
    """Run all tests"""
    logger.info("UPSTASH REDIS CONNECTION TEST")
    logger.info("=" * 60)

    redis_url = os.getenv("UPSTASH_REDIS_URL")
    if not redis_url:
        logger.error("UPSTASH_REDIS_URL not set in environment!")
        logger.info("Set it in .env file or export it:")
        logger.info('  export UPSTASH_REDIS_URL="rediss://..."')
        return 1
    
    logger.error(f"Redis URL: {redis_url[:30]}...")

    tests = [
        ("Basic Operations", test_basic_oprations),
        ("JSON Operations", test_json_opration),
        ("Cache Service", test_cache_service),
        ("Rate Limiting", test_rate_limiting),
        ("Redis Info", test_redis_info),
        ("Cache Statistics", test_cache_stats)
    ]

    results = []

    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            logger.error(f"Test '{name}' crashed: {e}")
            results.append((name, False))


    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        logger.info(f"{name:25s}: {status}")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    logger.info("=" * 60)
    logger.info(f"Results: {passed}/{total} tests passed")
    logger.info("=" * 60)

    if passed == total:
        logger.info("\nALL TESTS PASSED!")
        logger.info("Your Upstash Redis setup is working perfectly!")
        return 0
    
    else:
        logger.error("\nSOME TESTS FAILED!")
        logger.error("Please check the errors above and fix them.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
