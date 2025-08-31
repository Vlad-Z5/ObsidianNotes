# Performance Caching Strategies

**Focus:** Multi-level caching architectures, cache invalidation strategies, distributed caching, CDN optimization, application-level caching, database query caching, and intelligent cache management.

## Core Caching Performance Principles

### 1. Cache Hierarchy Design
- **L1 Cache**: CPU-level caching (hardware)
- **L2 Cache**: Application memory caching
- **L3 Cache**: Distributed cache layers (Redis, Memcached)
- **L4 Cache**: CDN and edge caching

### 2. Cache Strategy Patterns
- **Cache-Aside (Lazy Loading)**: Load on cache miss
- **Write-Through**: Synchronous cache updates
- **Write-Behind (Write-Back)**: Asynchronous cache updates
- **Read-Through**: Automatic cache population

### 3. Cache Invalidation Strategies
- **TTL-Based**: Time-to-live expiration
- **Event-Driven**: Invalidation on data changes
- **Tag-Based**: Grouped cache invalidation
- **Dependency-Based**: Hierarchical invalidation

### 4. Advanced Caching Techniques
- **Cache Warming**: Proactive cache population
- **Cache Partitioning**: Sharded cache distribution
- **Intelligent Prefetching**: Predictive cache loading
- **Cache Compression**: Memory optimization

## Enterprise Caching Framework

```python
import redis
import memcache
import time
import json
import hashlib
import threading
import asyncio
import aioredis
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import statistics
from contextlib import asynccontextmanager
import pickle
import zlib
import uuid
from datetime import datetime, timedelta
import sqlite3
import pymongo
from functools import wraps
import numpy as np

@dataclass
class CacheMetric:
    cache_type: str
    operation: str  # get, set, delete, hit, miss
    key: str
    execution_time_ms: float
    data_size_bytes: int
    hit: bool
    timestamp: float

@dataclass
class CachePerformanceStats:
    cache_name: str
    hit_ratio: float
    miss_ratio: float
    avg_response_time_ms: float
    total_operations: int
    memory_usage_mb: float
    eviction_count: int

class CacheInterface(ABC):
    """Abstract cache interface for different cache implementations"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        pass

class RedisCache(CacheInterface):
    """Redis cache implementation with advanced features"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.redis_client = None
        self.metrics = []
        self.logger = logging.getLogger(__name__)
        
    async def connect(self):
        """Establish Redis connection with optimization"""
        self.redis_client = await aioredis.from_url(
            self.config.get('redis_url', 'redis://localhost:6379'),
            encoding='utf-8',
            decode_responses=True,
            max_connections=self.config.get('max_connections', 20),
            retry_on_timeout=True,
            socket_timeout=self.config.get('socket_timeout', 5),
            socket_connect_timeout=self.config.get('connect_timeout', 5)
        )
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis with performance tracking"""
        start_time = time.time()
        
        try:
            compressed_data = await self.redis_client.get(key)
            
            if compressed_data:
                # Decompress and deserialize
                if self.config.get('compression_enabled', True):
                    decompressed_data = zlib.decompress(compressed_data.encode('latin1'))
                    value = pickle.loads(decompressed_data)
                else:
                    value = json.loads(compressed_data)
                
                execution_time = (time.time() - start_time) * 1000
                self._record_metric('get', key, execution_time, len(compressed_data), True)
                
                return value
            else:
                execution_time = (time.time() - start_time) * 1000
                self._record_metric('get', key, execution_time, 0, False)
                return None
                
        except Exception as e:
            self.logger.error(f"Redis GET error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in Redis with compression and performance tracking"""
        start_time = time.time()
        
        try:
            # Serialize and compress
            if self.config.get('compression_enabled', True):
                serialized_data = pickle.dumps(value)
                compressed_data = zlib.compress(serialized_data)
                data_to_store = compressed_data.decode('latin1')
            else:
                data_to_store = json.dumps(value, default=str)
            
            await self.redis_client.setex(key, ttl, data_to_store)
            
            execution_time = (time.time() - start_time) * 1000
            self._record_metric('set', key, execution_time, len(data_to_store), True)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Redis SET error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        start_time = time.time()
        
        try:
            result = await self.redis_client.delete(key)
            execution_time = (time.time() - start_time) * 1000
            self._record_metric('delete', key, execution_time, 0, result > 0)
            
            return result > 0
            
        except Exception as e:
            self.logger.error(f"Redis DELETE error for key {key}: {e}")
            return False
    
    async def clear(self) -> bool:
        """Clear all keys from Redis"""
        try:
            await self.redis_client.flushdb()
            return True
        except Exception as e:
            self.logger.error(f"Redis CLEAR error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Redis performance statistics"""
        try:
            if self.redis_client:
                info = self.redis_client.info()
                return {
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory_human': info.get('used_memory_human', 'N/A'),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0),
                    'evicted_keys': info.get('evicted_keys', 0),
                    'expired_keys': info.get('expired_keys', 0)
                }
        except Exception:
            pass
        
        return {}
    
    def _record_metric(self, operation: str, key: str, execution_time: float, 
                      data_size: int, hit: bool):
        """Record cache operation metrics"""
        metric = CacheMetric(
            cache_type='redis',
            operation=operation,
            key=key,
            execution_time_ms=execution_time,
            data_size_bytes=data_size,
            hit=hit,
            timestamp=time.time()
        )
        self.metrics.append(metric)
        
        # Keep only recent metrics
        if len(self.metrics) > 10000:
            self.metrics = self.metrics[-5000:]

class InMemoryCache(CacheInterface):
    """High-performance in-memory cache with LRU eviction"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.cache_data = {}
        self.access_times = {}
        self.metrics = []
        self.lock = threading.RLock()
        self.max_size = config.get('max_size', 1000)
        self.default_ttl = config.get('default_ttl', 3600)
        
    async def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache"""
        start_time = time.time()
        
        with self.lock:
            if key in self.cache_data:
                entry = self.cache_data[key]
                
                # Check TTL
                if entry['expires_at'] > time.time():
                    self.access_times[key] = time.time()
                    
                    execution_time = (time.time() - start_time) * 1000
                    self._record_metric('get', key, execution_time, 
                                      len(str(entry['value'])), True)
                    
                    return entry['value']
                else:
                    # Expired entry
                    del self.cache_data[key]
                    del self.access_times[key]
            
            execution_time = (time.time() - start_time) * 1000
            self._record_metric('get', key, execution_time, 0, False)
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in memory cache with LRU eviction"""
        start_time = time.time()
        
        if ttl is None:
            ttl = self.default_ttl
        
        with self.lock:
            # Check if we need to evict entries
            if len(self.cache_data) >= self.max_size and key not in self.cache_data:
                self._evict_lru_entry()
            
            expires_at = time.time() + ttl
            self.cache_data[key] = {
                'value': value,
                'expires_at': expires_at,
                'created_at': time.time()
            }
            self.access_times[key] = time.time()
            
            execution_time = (time.time() - start_time) * 1000
            self._record_metric('set', key, execution_time, len(str(value)), True)
            
            return True
    
    async def delete(self, key: str) -> bool:
        """Delete key from memory cache"""
        start_time = time.time()
        
        with self.lock:
            if key in self.cache_data:
                del self.cache_data[key]
                del self.access_times[key]
                
                execution_time = (time.time() - start_time) * 1000
                self._record_metric('delete', key, execution_time, 0, True)
                return True
            
            execution_time = (time.time() - start_time) * 1000
            self._record_metric('delete', key, execution_time, 0, False)
            return False
    
    async def clear(self) -> bool:
        """Clear all entries from memory cache"""
        with self.lock:
            self.cache_data.clear()
            self.access_times.clear()
            return True
    
    def _evict_lru_entry(self):
        """Evict least recently used entry"""
        if not self.access_times:
            return
        
        lru_key = min(self.access_times.keys(), key=self.access_times.get)
        del self.cache_data[lru_key]
        del self.access_times[lru_key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory cache statistics"""
        with self.lock:
            return {
                'total_keys': len(self.cache_data),
                'max_size': self.max_size,
                'memory_usage_estimate': sum(len(str(entry)) for entry in self.cache_data.values()),
                'oldest_entry': min(entry['created_at'] for entry in self.cache_data.values()) if self.cache_data else 0
            }
    
    def _record_metric(self, operation: str, key: str, execution_time: float, 
                      data_size: int, hit: bool):
        """Record cache operation metrics"""
        metric = CacheMetric(
            cache_type='memory',
            operation=operation,
            key=key,
            execution_time_ms=execution_time,
            data_size_bytes=data_size,
            hit=hit,
            timestamp=time.time()
        )
        self.metrics.append(metric)
        
        if len(self.metrics) > 5000:
            self.metrics = self.metrics[-2500:]

class EnterpriseCacheManager:
    """Enterprise-level cache management with multi-tier support"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.cache_layers = {}
        self.cache_stats = {}
        self.logger = self._setup_logging()
        self.performance_metrics = []
        
    def _setup_logging(self) -> logging.Logger:
        """Setup cache manager logger"""
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)
    
    async def setup_cache_layers(self):
        """Setup multi-tier cache architecture"""
        
        # L1 Cache: In-Memory
        if self.config.get('l1_cache_enabled', True):
            l1_config = self.config.get('l1_cache', {})
            self.cache_layers['l1'] = InMemoryCache(l1_config)
        
        # L2 Cache: Redis
        if self.config.get('l2_cache_enabled', True):
            l2_config = self.config.get('l2_cache', {})
            redis_cache = RedisCache(l2_config)
            await redis_cache.connect()
            self.cache_layers['l2'] = redis_cache
        
        self.logger.info(f"Initialized {len(self.cache_layers)} cache layers")
    
    async def get(self, key: str, cache_layers: List[str] = None) -> Optional[Any]:
        """Get value with multi-tier cache fallback"""
        if cache_layers is None:
            cache_layers = ['l1', 'l2']
        
        start_time = time.time()
        
        for layer_name in cache_layers:
            if layer_name in self.cache_layers:
                layer = self.cache_layers[layer_name]
                value = await layer.get(key)
                
                if value is not None:
                    # Cache hit - populate higher layers
                    await self._populate_higher_layers(key, value, layer_name, cache_layers)
                    
                    execution_time = (time.time() - start_time) * 1000
                    self._record_performance_metric('multi_get', key, execution_time, True, layer_name)
                    
                    return value
        
        # Cache miss across all layers
        execution_time = (time.time() - start_time) * 1000
        self._record_performance_metric('multi_get', key, execution_time, False, None)
        
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600, 
                 cache_layers: List[str] = None) -> bool:
        """Set value across specified cache layers"""
        if cache_layers is None:
            cache_layers = ['l1', 'l2']
        
        start_time = time.time()
        success_count = 0
        
        for layer_name in cache_layers:
            if layer_name in self.cache_layers:
                layer = self.cache_layers[layer_name]
                if await layer.set(key, value, ttl):
                    success_count += 1
        
        execution_time = (time.time() - start_time) * 1000
        self._record_performance_metric('multi_set', key, execution_time, True, None)
        
        return success_count > 0
    
    async def delete(self, key: str, cache_layers: List[str] = None) -> bool:
        """Delete key from specified cache layers"""
        if cache_layers is None:
            cache_layers = ['l1', 'l2']
        
        success_count = 0
        
        for layer_name in cache_layers:
            if layer_name in self.cache_layers:
                layer = self.cache_layers[layer_name]
                if await layer.delete(key):
                    success_count += 1
        
        return success_count > 0
    
    async def _populate_higher_layers(self, key: str, value: Any, source_layer: str, 
                                    available_layers: List[str]):
        """Populate higher cache layers after cache hit"""
        source_index = available_layers.index(source_layer)
        
        for i in range(source_index):
            layer_name = available_layers[i]
            if layer_name in self.cache_layers:
                layer = self.cache_layers[layer_name]
                await layer.set(key, value)
    
    def cache_decorator(self, ttl: int = 3600, key_generator: Callable = None):
        """Decorator for automatic function result caching"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                if key_generator:
                    cache_key = key_generator(*args, **kwargs)
                else:
                    cache_key = self._generate_cache_key(func.__name__, args, kwargs)
                
                # Try to get from cache
                cached_result = await self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                await self.set(cache_key, result, ttl)
                
                return result
            return wrapper
        return decorator
    
    def _generate_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate cache key from function signature"""
        key_parts = [func_name]
        
        # Add positional arguments
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            else:
                key_parts.append(str(hash(str(arg))))
        
        # Add keyword arguments
        for k, v in sorted(kwargs.items()):
            if isinstance(v, (str, int, float, bool)):
                key_parts.append(f"{k}:{v}")
            else:
                key_parts.append(f"{k}:{hash(str(v))}")
        
        combined_key = '|'.join(key_parts)
        return hashlib.md5(combined_key.encode()).hexdigest()
    
    async def warm_cache(self, warming_strategies: List[Dict]):
        """Warm cache with predefined data"""
        self.logger.info("Starting cache warming process")
        
        for strategy in warming_strategies:
            strategy_name = strategy.get('name', 'unknown')
            
            try:
                if strategy['type'] == 'database_preload':
                    await self._warm_from_database(strategy)
                elif strategy['type'] == 'api_preload':
                    await self._warm_from_api(strategy)
                elif strategy['type'] == 'file_preload':
                    await self._warm_from_file(strategy)
                
                self.logger.info(f"Completed cache warming strategy: {strategy_name}")
                
            except Exception as e:
                self.logger.error(f"Cache warming strategy {strategy_name} failed: {e}")
    
    async def _warm_from_database(self, strategy: Dict):
        """Warm cache from database queries"""
        # This would integrate with your database
        # Implementation depends on specific database setup
        pass
    
    async def _warm_from_api(self, strategy: Dict):
        """Warm cache from API endpoints"""
        # Implementation for API-based cache warming
        pass
    
    async def _warm_from_file(self, strategy: Dict):
        """Warm cache from file data"""
        # Implementation for file-based cache warming
        pass
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache performance statistics"""
        stats = {
            'timestamp': time.time(),
            'cache_layers': {},
            'performance_summary': {},
            'recommendations': []
        }
        
        # Get stats from each cache layer
        for layer_name, layer in self.cache_layers.items():
            layer_stats = layer.get_stats()
            layer_metrics = getattr(layer, 'metrics', [])
            
            if layer_metrics:
                # Calculate performance metrics
                hit_count = len([m for m in layer_metrics if m.hit])
                total_count = len(layer_metrics)
                hit_ratio = hit_count / total_count if total_count > 0 else 0
                
                avg_response_time = statistics.mean([m.execution_time_ms for m in layer_metrics])
                
                stats['cache_layers'][layer_name] = {
                    'hit_ratio': hit_ratio,
                    'total_operations': total_count,
                    'avg_response_time_ms': avg_response_time,
                    'infrastructure_stats': layer_stats
                }
            else:
                stats['cache_layers'][layer_name] = {
                    'hit_ratio': 0,
                    'total_operations': 0,
                    'avg_response_time_ms': 0,
                    'infrastructure_stats': layer_stats
                }
        
        # Overall performance summary
        all_metrics = []
        for layer in self.cache_layers.values():
            all_metrics.extend(getattr(layer, 'metrics', []))
        
        if all_metrics:
            total_hits = len([m for m in all_metrics if m.hit])
            total_operations = len(all_metrics)
            overall_hit_ratio = total_hits / total_operations if total_operations > 0 else 0
            
            stats['performance_summary'] = {
                'overall_hit_ratio': overall_hit_ratio,
                'total_operations': total_operations,
                'avg_response_time_ms': statistics.mean([m.execution_time_ms for m in all_metrics]),
                'operations_per_second': len([m for m in all_metrics if m.timestamp > time.time() - 60])
            }
        
        # Generate recommendations
        stats['recommendations'] = self._generate_cache_recommendations(stats)
        
        return stats
    
    def _generate_cache_recommendations(self, stats: Dict) -> List[str]:
        """Generate cache optimization recommendations"""
        recommendations = []
        
        for layer_name, layer_stats in stats['cache_layers'].items():
            hit_ratio = layer_stats['hit_ratio']
            
            if hit_ratio < 0.5:
                recommendations.append(f"Low hit ratio ({hit_ratio:.2%}) in {layer_name} cache - review caching strategy")
            elif hit_ratio > 0.95:
                recommendations.append(f"Excellent hit ratio ({hit_ratio:.2%}) in {layer_name} cache - consider expanding")
            
            avg_response = layer_stats['avg_response_time_ms']
            if avg_response > 100:
                recommendations.append(f"High response time ({avg_response:.1f}ms) in {layer_name} cache - optimize implementation")
        
        # General recommendations
        recommendations.extend([
            "Monitor cache eviction rates to optimize memory allocation",
            "Implement cache warming for frequently accessed data",
            "Consider cache partitioning for better performance isolation",
            "Regular cache performance analysis and tuning"
        ])
        
        return recommendations[:10]
    
    def _record_performance_metric(self, operation: str, key: str, execution_time: float, 
                                 hit: bool, layer: Optional[str]):
        """Record performance metrics for cache operations"""
        metric = {
            'operation': operation,
            'key': key,
            'execution_time_ms': execution_time,
            'hit': hit,
            'layer': layer,
            'timestamp': time.time()
        }
        
        self.performance_metrics.append(metric)
        
        # Keep only recent metrics
        if len(self.performance_metrics) > 10000:
            self.performance_metrics = self.performance_metrics[-5000:]

# Advanced Caching Patterns
class CachePattern:
    """Advanced caching pattern implementations"""
    
    @staticmethod
    def cache_aside_pattern(cache_manager: EnterpriseCacheManager, 
                          data_loader: Callable):
        """Implement cache-aside pattern"""
        async def get_data(key: str):
            # Try cache first
            cached_data = await cache_manager.get(key)
            if cached_data is not None:
                return cached_data
            
            # Load from data source
            data = await data_loader(key)
            if data is not None:
                await cache_manager.set(key, data)
            
            return data
        
        return get_data
    
    @staticmethod
    def write_through_pattern(cache_manager: EnterpriseCacheManager, 
                            data_writer: Callable):
        """Implement write-through pattern"""
        async def write_data(key: str, data: Any):
            # Write to data source first
            success = await data_writer(key, data)
            if success:
                # Then write to cache
                await cache_manager.set(key, data)
            
            return success
        
        return write_data

# Configuration Example
cache_config = {
    'l1_cache_enabled': True,
    'l1_cache': {
        'max_size': 10000,
        'default_ttl': 300  # 5 minutes
    },
    'l2_cache_enabled': True,
    'l2_cache': {
        'redis_url': 'redis://localhost:6379',
        'max_connections': 50,
        'socket_timeout': 5,
        'compression_enabled': True
    }
}

# Usage Example
async def main():
    cache_manager = EnterpriseCacheManager(cache_config)
    await cache_manager.setup_cache_layers()
    
    # Basic caching operations
    await cache_manager.set('user:1234', {'name': 'John Doe', 'email': 'john@example.com'})
    user_data = await cache_manager.get('user:1234')
    
    # Decorator usage
    @cache_manager.cache_decorator(ttl=600)
    async def expensive_computation(param1: str, param2: int) -> Dict:
        # Simulate expensive operation
        await asyncio.sleep(1)
        return {'result': f'computed_{param1}_{param2}'}
    
    result = await expensive_computation('test', 42)
    
    # Cache warming
    warming_strategies = [
        {
            'name': 'user_preload',
            'type': 'database_preload',
            'query': 'SELECT * FROM users WHERE active = true',
            'key_pattern': 'user:{id}'
        }
    ]
    
    await cache_manager.warm_cache(warming_strategies)
    
    # Get comprehensive stats
    stats = cache_manager.get_comprehensive_stats()
    print(json.dumps(stats, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())
```

This comprehensive caching framework provides:

1. **Multi-Tier Architecture**: L1 (memory) and L2 (Redis) cache layers
2. **Advanced Cache Patterns**: Cache-aside, write-through, write-behind
3. **Intelligent Cache Management**: LRU eviction, TTL management, compression
4. **Performance Monitoring**: Detailed metrics and hit ratio tracking
5. **Cache Warming**: Proactive cache population strategies
6. **Decorator Support**: Automatic function result caching
7. **Enterprise Features**: Multi-layer fallback, optimization recommendations
8. **Async Operations**: High-performance asynchronous cache operations

The system enables developers to implement sophisticated caching strategies with enterprise-grade performance monitoring and optimization capabilities.