import redis
import json
import hashlib
import logging
from typing import Optional, Dict
from config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_CACHE_TTL

logger = logging.getLogger(__name__)

class RedisCache:
    def __init__(self):
        try:
            self.client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                decode_responses=True
            )
            self.client.ping()
            self.ttl = REDIS_CACHE_TTL
            logger.info(f"✅ Redis FAQ cache connected: {REDIS_HOST}:{REDIS_PORT}")
        except Exception as e:
            logger.warning(f"⚠️ Redis FAQ cache unavailable: {e}")
            self.client = None
    
    def _get_key(self, query: str) -> str:
        """Generate cache key from query"""
        hash_key = hashlib.md5(query.lower().strip().encode()).hexdigest()
        full_key = f"faq:{hash_key}"
        logger.info(f"🔑 Cache key: {full_key} for '{query[:50]}...'")
        return full_key
    
    def get(self, query: str) -> Optional[Dict]:
        """Get cached answer for query"""
        if not self.client:
            logger.warning("⚠️ Redis client unavailable - skip cache check")
            return None
        try:
            logger.info(f"🔍 Checking cache for: '{query[:50]}...'")
            key = self._get_key(query)
            data = self.client.get(key)
            if data:
                logger.info(f"✅ CACHE HIT! Returning cached answer")
                return json.loads(data)
            else:
                logger.info(f"❌ CACHE MISS - No cached answer")
        except Exception as e:
            logger.error(f"❌ Redis get error: {e}")
        return None
    
    def set(self, query: str, answer: Dict):
        """Cache answer for query"""
        if not self.client:
            logger.warning("⚠️ Redis client unavailable - skip cache storage")
            return
        try:
            key = self._get_key(query)
            self.client.setex(key, self.ttl, json.dumps(answer))
            logger.info(f"💾 CACHED: '{query[:50]}...' (TTL: {self.ttl}s)")
        except Exception as e:
            logger.error(f"❌ Redis set error: {e}")
    
    def increment_count(self, query: str):
        """Track query frequency"""
        if not self.client:
            return
        try:
            count_key = f"count:{self._get_key(query)}"
            new_count = self.client.incr(count_key)
            logger.info(f"📊 Query count: {new_count} for '{query[:50]}...'")
        except Exception as e:
            logger.error(f"❌ Redis incr error: {e}")
    
    def get_popular_queries(self, limit: int = 10) -> list:
        """Get most asked questions"""
        if not self.client:
            return []
        try:
            keys = self.client.keys("count:faq:*")
            queries = []
            for key in keys:
                count = int(self.client.get(key) or 0)
                queries.append((key, count))
            queries.sort(key=lambda x: x[1], reverse=True)
            return queries[:limit]
        except Exception as e:
            logger.error(f"❌ Redis popular queries error: {e}")
            return []

# Global cache instance
redis_cache = RedisCache()
