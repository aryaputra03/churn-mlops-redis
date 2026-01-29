"""
Caching Service for MLOps API

Implements intelligent caching for:
- Model predictions
- User data
- Analytics results
- Model metadata
"""

from typing import Optional, Any, Dict
from datetime import timedelta
import hashlib
import json
from src.api.redis_client import redis_client, cache_result, invalidate_cache
from src.utils import logger

class CacheService:
    """
    Centralized caching service for the application
    """

    TTL_PREDICTION = 600
    TTL_USER_DATA = 300
    TTL_ANALYTICS = 900
    TTL_MODEL_INFO = 3600
    TTL_HISTORY = 180

    def __init__(self):
        """Initialize cache service"""
        self.redis = redis_client
    
    def get_prediction(self, customer_id: str, input_hash: str) -> Optional[Dict]:
        """
        Get cached prediction result
        
        Args:
            customer_id: Customer identifier
            input_hash: Hash of input data
            
        Returns:
            Cached prediction or None
        """
        cache_key = f"prediction:{customer_id}:{input_hash}"
        return self.redis.get(cache_key)
    
    def set_prediction(
            self,
            customer_id: str,
            input_hash: str,
            prediction_result: Dict
    ):
        """
        Cache prediction result
        
        Args:
            customer_id: Customer identifier
            input_hash: Hash of input data
            prediction_result: Prediction to cache
        """
        cache_key = f"prediction:{customer_id}:{input_hash}"
        self.redis.set(cache_key, prediction_result, ex=self.TTL_PREDICTION)
        logger.debug(f"Cached prediction: {cache_key}")

    @staticmethod
    def hash_input_data(data: Dict) -> str:
        """
        Create hash of input data for caching
        
        Args:
            data: Input data dictionary
            
        Returns:
            MD5 hash of input data
        """
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def invalidate_predictions(self, customer_id: Optional[str] = None):
        """
        Invalidate prediction cache
        
        Args:
            customer_id: Optional customer ID to invalidate specific customer
        """
        if customer_id:
            pattern = f"prediction:{customer_id}:*"
        else:
            pattern = "prediction:*"
        
        invalidate_cache(pattern)

    # ==========================================
    # User Data Caching
    # ==========================================

    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get cached user data"""
        cache_key = f"user:{user_id}"
        return self.redis.get(cache_key)
    
    def set_user(self, user_id: int, user_data: Dict):
        """Cache user data"""
        cache_key = f"user:{user_id}"
        self.redis.set(cache_key, user_data, ex=self.TTL_USER_DATA)
    
    def invalidate_user(self, user_id: int):
        """Invalidate user cache"""
        cache_key = f"user:{user_id}"
        self.redis.delete(cache_key)

    # ==========================================
    # Analytics Caching
    # ==========================================

    def get_analytics(self, analytics_type: str) -> Optional[Dict]:
        """
        Get cached analytics
        
        Args:
            analytics_type: Type of analytics (summary, daily, etc.)
            
        Returns:
            Cached analytics or None
        """
        cache_key = f"analytics:{analytics_type}"
        return self.redis.get(cache_key)
    
    def set_analytics(self, analytics_type: str, data: Dict):
        """
        Cache analytics data
        
        Args:
            analytics_type: Type of analytics
            data: Analytics data to cache
        """
        cache_key = f"analytics:{analytics_type}"
        self.redis.set(cache_key, data, ex=self.TTL_ANALYTICS)
    
    def invalidate_analytics(self):
        """Invalidate all analytics cache"""
        invalidate_cache("analytics:*")

    # ==========================================
    # History Caching
    # ==========================================

    def get_history(self, user_id: int, limit: int) -> Optional[list]:
        """Get cached prediction history"""
        cache_key = f"history:{user_id}:{limit}"
        return self.redis.get(cache_key)
    
    def set_history(self, user_id: int, limit: int, history: list):
        """Get cached prediction history"""
        cache_key = f"history:{user_id}:{limit}"
        return self.redis.set(cache_key, history, ex=self.TTL_HISTORY)
    
    def invalidate_history(self, user_id: Optional[int] = None):
        """Invalidate history cache"""
        if user_id:
            pattern = f"history:{user_id}:*"
        else:
            pattern = "history:*"
        invalidate_cache(pattern)
    
    # ==========================================
    # Batch Operations
    # ==========================================

    def invalidate_all(self):
        """Invalidate all cache (use with caution!)"""
        logger.warning("Invalidating ALL cache")
        self.redis.flushdb()
    
    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        try:
            all_keys = self.redis.keys("*")

            stats = {
                "total_keys" : len(all_keys),
                "by_type":{
                    "predictions" : len([k for k in all_keys if k.startswith("prediction:")]),
                    "users": len([k for k in all_keys if k.startswith("user:")]),
                    "analytics": len([k for k in all_keys if k.startswith("analytics:")]),
                    "history": len([k for k in all_keys if k.startswith("history:")]),
                    "ratelimit": len([k for k in all_keys if k.startswith("ratelimit:")]),
                    "other": len([k for k in all_keys if not any(k.startswith(p) for p in ["prediction:", "user:", "analytics:", "history:", "ratelimit:"])])
                },
                "redis_info": self.redis.get_info()
            }
            return stats
        
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}
        
    # ==========================================
    # Model Info Caching
    # ==========================================

    def get_model_info(self) -> Optional[Dict]:
        """Get cached model info"""
        cache_key = "model:info"
        return self.redis.get(cache_key)

    def set_model_info(self, info: Dict):
        """Cache model info"""
        cache_key = "model:info"
        self.redis.set(cache_key, info, ex=self.TTL_MODEL_INFO)

    def invalidate_model_info(self):
        """Invalidate model info cache"""
        self.redis.delete("model:info")

cache_service = CacheService()