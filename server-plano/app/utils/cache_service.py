"""
Caching service for pattern matching and template data.
Provides Redis-based caching with fallback to in-memory storage.
"""
import json
import pickle
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import asdict
import logging

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from ..models.core import EventContext
from ..models.enums import EventType, CulturalRequirement, VenueType, BudgetTier


logger = logging.getLogger(__name__)


class CacheService:
    """
    Centralized caching service for event planning data.
    Uses Redis when available, falls back to in-memory storage.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379", 
                 default_ttl: int = 3600, use_redis: bool = True):
        """
        Initialize cache service.
        
        Args:
            redis_url: Redis connection URL
            default_ttl: Default time-to-live in seconds
            use_redis: Whether to use Redis (falls back to memory if False or unavailable)
        """
        self.default_ttl = default_ttl
        self.use_redis = use_redis and REDIS_AVAILABLE
        self.redis_client = None
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        
        if self.use_redis:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=False)
                # Test connection
                self.redis_client.ping()
                logger.info("Redis cache initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Falling back to memory cache.")
                self.use_redis = False
                self.redis_client = None
        
        if not self.use_redis:
            logger.info("Using in-memory cache")
    
    def _generate_key(self, prefix: str, identifier: Union[str, Dict, Any]) -> str:
        """Generate a cache key from prefix and identifier"""
        if isinstance(identifier, str):
            key_data = identifier
        elif isinstance(identifier, dict):
            # Sort dict for consistent hashing
            key_data = json.dumps(identifier, sort_keys=True)
        else:
            # For complex objects, use string representation
            key_data = str(identifier)
        
        # Create hash for consistent key length
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            if self.use_redis and self.redis_client:
                data = self.redis_client.get(key)
                if data:
                    return pickle.loads(data)
            else:
                # Memory cache
                if key in self._memory_cache:
                    entry = self._memory_cache[key]
                    # Check expiration
                    if entry['expires_at'] > datetime.now():
                        return entry['data']
                    else:
                        # Remove expired entry
                        del self._memory_cache[key]
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        try:
            ttl = ttl or self.default_ttl
            
            if self.use_redis and self.redis_client:
                serialized = pickle.dumps(value)
                return self.redis_client.setex(key, ttl, serialized)
            else:
                # Memory cache
                expires_at = datetime.now() + timedelta(seconds=ttl)
                self._memory_cache[key] = {
                    'data': value,
                    'expires_at': expires_at
                }
                return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            if self.use_redis and self.redis_client:
                return bool(self.redis_client.delete(key))
            else:
                # Memory cache
                if key in self._memory_cache:
                    del self._memory_cache[key]
                    return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
        
        return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        deleted_count = 0
        try:
            if self.use_redis and self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    deleted_count = self.redis_client.delete(*keys)
            else:
                # Memory cache - simple pattern matching
                keys_to_delete = []
                pattern_clean = pattern.replace('*', '')
                for key in self._memory_cache:
                    if pattern_clean in key:
                        keys_to_delete.append(key)
                
                for key in keys_to_delete:
                    del self._memory_cache[key]
                    deleted_count += 1
        except Exception as e:
            logger.error(f"Cache delete pattern error for pattern {pattern}: {e}")
        
        return deleted_count
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            if self.use_redis and self.redis_client:
                return bool(self.redis_client.exists(key))
            else:
                # Memory cache
                if key in self._memory_cache:
                    entry = self._memory_cache[key]
                    if entry['expires_at'] > datetime.now():
                        return True
                    else:
                        del self._memory_cache[key]
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
        
        return False
    
    def clear_all(self) -> bool:
        """Clear all cache entries"""
        try:
            if self.use_redis and self.redis_client:
                return self.redis_client.flushdb()
            else:
                self._memory_cache.clear()
                return True
        except Exception as e:
            logger.error(f"Cache clear all error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = {
            'cache_type': 'redis' if self.use_redis else 'memory',
            'default_ttl': self.default_ttl
        }
        
        try:
            if self.use_redis and self.redis_client:
                info = self.redis_client.info()
                stats.update({
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory': info.get('used_memory_human', 'N/A'),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0)
                })
            else:
                # Memory cache stats
                active_entries = 0
                expired_entries = 0
                now = datetime.now()
                
                for entry in self._memory_cache.values():
                    if entry['expires_at'] > now:
                        active_entries += 1
                    else:
                        expired_entries += 1
                
                stats.update({
                    'active_entries': active_entries,
                    'expired_entries': expired_entries,
                    'total_entries': len(self._memory_cache)
                })
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            stats['error'] = str(e)
        
        return stats


class PatternCacheService:
    """Specialized caching service for event patterns and templates"""
    
    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
        self.pattern_ttl = 7200  # 2 hours for patterns
        self.template_ttl = 86400  # 24 hours for templates
        self.similarity_ttl = 1800  # 30 minutes for similarity calculations
    
    def cache_event_pattern(self, pattern_id: str, pattern: Any) -> bool:
        """Cache an event pattern"""
        key = self.cache._generate_key("pattern", pattern_id)
        return self.cache.set(key, pattern, self.pattern_ttl)
    
    def get_event_pattern(self, pattern_id: str) -> Optional[Any]:
        """Get cached event pattern"""
        key = self.cache._generate_key("pattern", pattern_id)
        return self.cache.get(key)
    
    def cache_similar_events(self, context_hash: str, similar_events: List[Any]) -> bool:
        """Cache similar events for a context"""
        key = self.cache._generate_key("similar", context_hash)
        return self.cache.set(key, similar_events, self.similarity_ttl)
    
    def get_similar_events(self, context_hash: str) -> Optional[List[Any]]:
        """Get cached similar events"""
        key = self.cache._generate_key("similar", context_hash)
        return self.cache.get(key)
    
    def cache_ceremony_templates(self, event_type: EventType, 
                               cultural_req: CulturalRequirement, 
                               templates: List[Any]) -> bool:
        """Cache ceremony templates for specific criteria"""
        cache_key = f"{event_type.value}_{cultural_req.value}"
        key = self.cache._generate_key("ceremony", cache_key)
        return self.cache.set(key, templates, self.template_ttl)
    
    def get_ceremony_templates(self, event_type: EventType, 
                             cultural_req: CulturalRequirement) -> Optional[List[Any]]:
        """Get cached ceremony templates"""
        cache_key = f"{event_type.value}_{cultural_req.value}"
        key = self.cache._generate_key("ceremony", cache_key)
        return self.cache.get(key)
    
    def cache_activity_templates(self, template_type: str, templates: Dict[str, Any]) -> bool:
        """Cache activity templates by type"""
        key = self.cache._generate_key("activity", template_type)
        return self.cache.set(key, templates, self.template_ttl)
    
    def get_activity_templates(self, template_type: str) -> Optional[Dict[str, Any]]:
        """Get cached activity templates"""
        key = self.cache._generate_key("activity", template_type)
        return self.cache.get(key)
    
    def cache_success_patterns(self, event_type: EventType, patterns: List[Any]) -> bool:
        """Cache success patterns for event type"""
        key = self.cache._generate_key("success", event_type.value)
        return self.cache.set(key, patterns, self.pattern_ttl)
    
    def get_success_patterns(self, event_type: EventType) -> Optional[List[Any]]:
        """Get cached success patterns"""
        key = self.cache._generate_key("success", event_type.value)
        return self.cache.get(key)
    
    def invalidate_patterns(self, pattern_prefix: str = "pattern") -> int:
        """Invalidate all cached patterns"""
        return self.cache.delete_pattern(f"{pattern_prefix}:*")
    
    def invalidate_templates(self) -> int:
        """Invalidate all cached templates"""
        ceremony_count = self.cache.delete_pattern("ceremony:*")
        activity_count = self.cache.delete_pattern("activity:*")
        return ceremony_count + activity_count
    
    def generate_context_hash(self, context: EventContext) -> str:
        """Generate a hash for event context for caching purposes"""
        # Create a simplified context for hashing
        context_data = {
            'event_type': context.event_type.value,
            'guest_count_range': self._get_guest_count_range(context.guest_count),
            'venue_type': context.venue_type.value,
            'cultural_requirements': sorted([req.value for req in context.cultural_requirements]),
            'budget_tier': context.budget_tier.value,
            'season': context.season.value,
            'duration_days': context.duration_days
        }
        
        # Generate hash
        context_str = json.dumps(context_data, sort_keys=True)
        return hashlib.md5(context_str.encode()).hexdigest()
    
    def _get_guest_count_range(self, guest_count: int) -> str:
        """Get guest count range for caching consistency"""
        if guest_count <= 50:
            return "small"
        elif guest_count <= 150:
            return "medium"
        elif guest_count <= 300:
            return "large"
        else:
            return "very_large"


# Global cache service instance
_cache_service = None
_pattern_cache_service = None


def get_cache_service() -> CacheService:
    """Get global cache service instance"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def get_pattern_cache_service() -> PatternCacheService:
    """Get global pattern cache service instance"""
    global _pattern_cache_service
    if _pattern_cache_service is None:
        _pattern_cache_service = PatternCacheService(get_cache_service())
    return _pattern_cache_service