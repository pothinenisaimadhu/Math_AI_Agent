import json
import hashlib
import time
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ResponseCache:
    """Simple in-memory cache for responses"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.ttl = ttl  # Time to live in seconds
    
    def _generate_key(self, query: str, context: str = "", model: str = "") -> str:
        """Generate cache key from query and context"""
        key_data = f"{query}_{context}_{model}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, query: str, context: str = "", model: str = "") -> Optional[Dict[str, Any]]:
        """Get cached response"""
        key = self._generate_key(query, context, model)
        
        if key in self.cache:
            # Check if expired
            if time.time() - self.cache[key]["timestamp"] > self.ttl:
                del self.cache[key]
                if key in self.access_times:
                    del self.access_times[key]
                return None
            
            # Update access time
            self.access_times[key] = time.time()
            logger.info(f"Cache hit for query: {query[:50]}...")
            return self.cache[key]["response"]
        
        return None
    
    def set(self, query: str, response: Dict[str, Any], context: str = "", model: str = ""):
        """Cache response"""
        key = self._generate_key(query, context, model)
        
        # Clean cache if at max size
        if len(self.cache) >= self.max_size:
            self._evict_oldest()
        
        self.cache[key] = {
            "response": response,
            "timestamp": time.time()
        }
        self.access_times[key] = time.time()
        
        logger.info(f"Cached response for query: {query[:50]}...")
    
    def _evict_oldest(self):
        """Evict least recently used item"""
        if not self.access_times:
            return
        
        oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        del self.cache[oldest_key]
        del self.access_times[oldest_key]
        logger.info("Evicted oldest cache entry")
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.access_times.clear()
        logger.info("Cache cleared")
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl": self.ttl,
            "oldest_entry": min(self.access_times.values()) if self.access_times else None
        }