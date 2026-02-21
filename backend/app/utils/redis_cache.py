"""
Redis Cache Manager for embeddings and API responses
Implements 24-hour TTL caching with efficient serialization
"""

import redis
import pickle
import hashlib
import logging
from typing import Optional, Any, Dict
import numpy as np
from datetime import timedelta
import os

logger = logging.getLogger(__name__)


class RedisCacheManager:
    """
    Production-grade Redis cache for embeddings and responses
    """
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        db: int = 0,
        password: str = None,
        default_ttl: int = 86400  # 24 hours
    ):
        """
        Initialize Redis connection
        
        Args:
            host: Redis host (defaults to env var REDIS_HOST or 'localhost')
            port: Redis port (defaults to env var REDIS_PORT or 6379)
            db: Redis database number
            password: Redis password
            default_ttl: Default TTL in seconds (24 hours)
        """
        self.host = host or os.getenv('REDIS_HOST', 'localhost')
        self.port = int(port or os.getenv('REDIS_PORT', 6379))
        self.db = db
        self.password = password or os.getenv('REDIS_PASSWORD')
        self.default_ttl = default_ttl
        
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=False,  # We'll handle binary data
                socket_timeout=5,
                socket_connect_timeout=5
            )
            # Test connection
            self.client.ping()
            logger.info(f"Redis connected: {self.host}:{self.port}")
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection failed: {e}. Cache disabled.")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if Redis is available"""
        if self.client is None:
            return False
        try:
            self.client.ping()
            return True
        except:
            return False
    
    def _generate_key(self, prefix: str, identifier: str) -> str:
        """Generate cache key with namespace"""
        hash_val = hashlib.md5(identifier.encode()).hexdigest()
        return f"cmrs:{prefix}:{hash_val}"
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: int = None
    ) -> bool:
        """
        Set value in Redis with TTL
        
        Args:
            key: Cache key
            value: Value to cache (will be pickled)
            ttl: Time-to-live in seconds (None = default_ttl)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            serialized = pickle.dumps(value)
            ttl = ttl or self.default_ttl
            self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from Redis
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None
        """
        if not self.is_available():
            return None
        
        try:
            data = self.client.get(key)
            if data is None:
                return None
            return pickle.loads(data)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        if not self.is_available():
            return False
        
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    def cache_embedding(
        self,
        content: str,
        content_type: str,  # 'text' or 'image'
        embedding: np.ndarray,
        ttl: int = None
    ) -> bool:
        """
        Cache CLIP embedding
        
        Args:
            content: Text query or image URL/hash
            content_type: 'text' or 'image'
            embedding: Embedding vector (512-dim)
            ttl: Custom TTL in seconds
        
        Returns:
            True if cached successfully
        """
        key = self._generate_key(f"embedding:{content_type}", content)
        
        # Store embedding with metadata
        cache_data = {
            'embedding': embedding.tobytes(),
            'shape': embedding.shape,
            'dtype': str(embedding.dtype)
        }
        
        return self.set(key, cache_data, ttl)
    
    def get_cached_embedding(
        self,
        content: str,
        content_type: str
    ) -> Optional[np.ndarray]:
        """
        Retrieve cached embedding
        
        Args:
            content: Text query or image URL/hash
            content_type: 'text' or 'image'
        
        Returns:
            Embedding array or None
        """
        key = self._generate_key(f"embedding:{content_type}", content)
        cache_data = self.get(key)
        
        if cache_data is None:
            return None
        
        try:
            # Reconstruct numpy array
            embedding = np.frombuffer(
                cache_data['embedding'],
                dtype=cache_data['dtype']
            ).reshape(cache_data['shape'])
            return embedding
        except Exception as e:
            logger.error(f"Error reconstructing embedding: {e}")
            return None
    
    def cache_search_results(
        self,
        query_hash: str,
        results: list,
        ttl: int = 3600  # 1 hour for search results
    ) -> bool:
        """
        Cache search results
        
        Args:
            query_hash: Hash of query parameters
            results: List of product results
            ttl: TTL in seconds (default 1 hour)
        
        Returns:
            True if cached
        """
        key = self._generate_key("search", query_hash)
        return self.set(key, results, ttl)
    
    def get_cached_search_results(self, query_hash: str) -> Optional[list]:
        """Retrieve cached search results"""
        key = self._generate_key("search", query_hash)
        return self.get(key)
    
    def cache_product(
        self,
        product_id: str,
        product_data: Dict,
        ttl: int = None
    ) -> bool:
        """Cache product metadata"""
        key = self._generate_key("product", product_id)
        return self.set(key, product_data, ttl)
    
    def get_cached_product(self, product_id: str) -> Optional[Dict]:
        """Retrieve cached product"""
        key = self._generate_key("product", product_id)
        return self.get(key)
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern
        
        Args:
            pattern: Redis pattern (e.g., 'cmrs:embedding:*')
        
        Returns:
            Number of keys deleted
        """
        if not self.is_available():
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Pattern invalidation error: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.is_available():
            return {"status": "unavailable"}
        
        try:
            info = self.client.info()
            return {
                "status": "connected",
                "used_memory": info.get('used_memory_human', 'N/A'),
                "total_keys": self.client.dbsize(),
                "hits": info.get('keyspace_hits', 0),
                "misses": info.get('keyspace_misses', 0),
                "hit_rate": self._calculate_hit_rate(info)
            }
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {"status": "error", "message": str(e)}
    
    def _calculate_hit_rate(self, info: Dict) -> float:
        """Calculate cache hit rate"""
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)


# Global cache instance
_cache_instance: Optional[RedisCacheManager] = None


def get_cache() -> RedisCacheManager:
    """Get global cache instance (singleton pattern)"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCacheManager()
    return _cache_instance
