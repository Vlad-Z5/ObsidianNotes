# Architecture High-Performance

## Performance Optimization

High-performance architecture requires systematic optimization across multiple layers including caching strategies, database optimization, application performance tuning, and comprehensive monitoring. This guide provides production-ready implementations for building ultra-fast, scalable systems.

### Performance Patterns

Modern high-performance systems require layered optimization strategies that address bottlenecks at every level of the application stack.

#### Multi-Tier Caching Strategy Implementation

```python
import asyncio
import redis
import memcache
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
import zlib
import pickle
import aiohttp
import asyncpg

class CacheLevel(Enum):
    L1_APPLICATION = "L1_APPLICATION"
    L2_REDIS = "L2_REDIS"
    L3_MEMCACHED = "L3_MEMCACHED"
    L4_DATABASE = "L4_DATABASE"

class EvictionPolicy(Enum):
    LRU = "LRU"
    LFU = "LFU"
    FIFO = "FIFO"
    TTL = "TTL"

@dataclass
class CacheEntry:
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl_seconds: Optional[int] = None
    size_bytes: int = 0

@dataclass
class CacheMetrics:
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_requests: int = 0
    avg_response_time_ms: float = 0.0
    memory_usage_bytes: int = 0

class HighPerformanceCacheManager:
    """Multi-tier caching system with intelligent cache promotion and eviction"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # L1 Cache - In-memory application cache
        self.l1_cache: Dict[str, CacheEntry] = {}
        self.l1_max_size = config.get('l1_max_size', 1000)
        self.l1_max_memory = config.get('l1_max_memory_mb', 100) * 1024 * 1024
        
        # L2 Cache - Redis distributed cache
        self.redis_client = redis.Redis(
            host=config.get('redis_host', 'localhost'),
            port=config.get('redis_port', 6379),
            db=config.get('redis_db', 0),
            decode_responses=True
        )
        
        # L3 Cache - Memcached
        self.memcached_client = memcache.Client(
            config.get('memcached_servers', ['127.0.0.1:11211'])
        )
        
        # Cache metrics
        self.metrics: Dict[CacheLevel, CacheMetrics] = {
            level: CacheMetrics() for level in CacheLevel
        }
        
        # Background tasks
        self.cleanup_task = None
        self.promotion_task = None
        
    async def get(self, key: str, fetch_function: Optional[Callable] = None) -> Optional[Any]:
        """Get value from cache with automatic cache promotion"""
        start_time = time.perf_counter()
        
        try:
            # Try L1 cache first
            value = await self._get_from_l1(key)
            if value is not None:
                self.metrics[CacheLevel.L1_APPLICATION].hits += 1
                return value
            
            self.metrics[CacheLevel.L1_APPLICATION].misses += 1
            
            # Try L2 cache (Redis)
            value = await self._get_from_l2(key)
            if value is not None:
                self.metrics[CacheLevel.L2_REDIS].hits += 1
                # Promote to L1
                await self._set_to_l1(key, value)
                return value
            
            self.metrics[CacheLevel.L2_REDIS].misses += 1
            
            # Try L3 cache (Memcached)
            value = await self._get_from_l3(key)
            if value is not None:
                self.metrics[CacheLevel.L3_MEMCACHED].hits += 1
                # Promote to L2 and L1
                await self._set_to_l2(key, value)
                await self._set_to_l1(key, value)
                return value
            
            self.metrics[CacheLevel.L3_MEMCACHED].misses += 1
            
            # Cache miss - fetch from source if function provided
            if fetch_function:
                value = await fetch_function(key)
                if value is not None:
                    # Store in all cache levels
                    await self.set(key, value)
                return value
            
            return None
            
        finally:
            # Update response time metrics
            end_time = time.perf_counter()
            response_time_ms = (end_time - start_time) * 1000
            
            for level in CacheLevel:
                metrics = self.metrics[level]
                metrics.total_requests += 1
                # Update rolling average
                metrics.avg_response_time_ms = (
                    (metrics.avg_response_time_ms * (metrics.total_requests - 1) + response_time_ms) 
                    / metrics.total_requests
                )
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl_seconds: Optional[int] = None,
        cache_levels: Optional[List[CacheLevel]] = None
    ) -> bool:
        """Set value in specified cache levels"""
        
        if cache_levels is None:
            cache_levels = [CacheLevel.L1_APPLICATION, CacheLevel.L2_REDIS, CacheLevel.L3_MEMCACHED]
        
        success = True
        
        for level in cache_levels:
            try:
                if level == CacheLevel.L1_APPLICATION:
                    await self._set_to_l1(key, value, ttl_seconds)
                elif level == CacheLevel.L2_REDIS:
                    await self._set_to_l2(key, value, ttl_seconds)
                elif level == CacheLevel.L3_MEMCACHED:
                    await self._set_to_l3(key, value, ttl_seconds)
            except Exception as e:
                print(f"Error setting cache level {level}: {e}")
                success = False
        
        return success
    
    async def _get_from_l1(self, key: str) -> Optional[Any]:
        """Get from L1 in-memory cache"""
        if key not in self.l1_cache:
            return None
        
        entry = self.l1_cache[key]
        
        # Check TTL
        if entry.ttl_seconds and (datetime.utcnow() - entry.created_at).seconds > entry.ttl_seconds:
            del self.l1_cache[key]
            return None
        
        # Update access statistics
        entry.last_accessed = datetime.utcnow()
        entry.access_count += 1
        
        return entry.value
    
    async def _set_to_l1(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Set to L1 in-memory cache with eviction policy"""
        
        # Calculate size
        size_bytes = len(pickle.dumps(value))
        
        # Check if we need to evict
        if len(self.l1_cache) >= self.l1_max_size or self._get_l1_memory_usage() + size_bytes > self.l1_max_memory:
            await self._evict_from_l1()
        
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            ttl_seconds=ttl_seconds,
            size_bytes=size_bytes
        )
        
        self.l1_cache[key] = entry
    
    async def _get_from_l2(self, key: str) -> Optional[Any]:
        """Get from L2 Redis cache"""
        try:
            serialized_value = self.redis_client.get(key)
            if serialized_value:
                # Decompress if needed
                if serialized_value.startswith(b'compressed:'):
                    compressed_data = serialized_value[11:]  # Remove 'compressed:' prefix
                    decompressed_data = zlib.decompress(compressed_data)
                    return pickle.loads(decompressed_data)
                else:
                    return pickle.loads(serialized_value)
            return None
        except Exception as e:
            print(f"Error getting from Redis: {e}")
            return None
    
    async def _set_to_l2(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Set to L2 Redis cache with compression"""
        try:
            serialized_value = pickle.dumps(value)
            
            # Compress large values
            if len(serialized_value) > 1024:  # Compress if larger than 1KB
                compressed_value = zlib.compress(serialized_value)
                if len(compressed_value) < len(serialized_value):
                    serialized_value = b'compressed:' + compressed_value
            
            if ttl_seconds:
                self.redis_client.setex(key, ttl_seconds, serialized_value)
            else:
                self.redis_client.set(key, serialized_value)
                
        except Exception as e:
            print(f"Error setting to Redis: {e}")
    
    async def _evict_from_l1(self) -> None:
        """Evict entries from L1 cache using LRU policy"""
        if not self.l1_cache:
            return
        
        # Sort by last accessed time (LRU)
        sorted_entries = sorted(
            self.l1_cache.items(),
            key=lambda x: x[1].last_accessed
        )
        
        # Remove oldest 25% of entries
        evict_count = max(1, len(sorted_entries) // 4)
        
        for i in range(evict_count):
            key, _ = sorted_entries[i]
            del self.l1_cache[key]
            self.metrics[CacheLevel.L1_APPLICATION].evictions += 1
    
    def _get_l1_memory_usage(self) -> int:
        """Calculate total memory usage of L1 cache"""
        return sum(entry.size_bytes for entry in self.l1_cache.values())
    
    async def start_background_tasks(self) -> None:
        """Start background maintenance tasks"""
        self.cleanup_task = asyncio.create_task(self._periodic_cleanup())
        self.promotion_task = asyncio.create_task(self._cache_promotion_analyzer())
    
    async def _periodic_cleanup(self) -> None:
        """Periodic cleanup of expired entries"""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                
                current_time = datetime.utcnow()
                expired_keys = []
                
                for key, entry in self.l1_cache.items():
                    if entry.ttl_seconds and (current_time - entry.created_at).seconds > entry.ttl_seconds:
                        expired_keys.append(key)
                
                for key in expired_keys:
                    del self.l1_cache[key]
                    
            except Exception as e:
                print(f"Error in periodic cleanup: {e}")
```

#### Connection Pooling and Resource Management

```python
import asyncio
import asyncpg
import aiohttp
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import threading
import queue
import weakref

@dataclass
class ConnectionStats:
    created_at: datetime
    last_used: datetime
    total_queries: int = 0
    total_time_seconds: float = 0.0
    is_healthy: bool = True

class AsyncConnectionPool:
    """High-performance async connection pool with health monitoring"""
    
    def __init__(
        self,
        database_url: str,
        min_size: int = 5,
        max_size: int = 20,
        max_queries: int = 50000,
        max_inactive_connection_lifetime: int = 300,
        command_timeout: int = 30
    ):
        self.database_url = database_url
        self.min_size = min_size
        self.max_size = max_size
        self.max_queries = max_queries
        self.max_inactive_connection_lifetime = max_inactive_connection_lifetime
        self.command_timeout = command_timeout
        
        self._pool: Optional[asyncpg.Pool] = None
        self._connection_stats: Dict[int, ConnectionStats] = {}
        self._lock = asyncio.Lock()
        self._health_check_task: Optional[asyncio.Task] = None
        
    async def initialize(self) -> None:
        """Initialize the connection pool"""
        self._pool = await asyncpg.create_pool(
            self.database_url,
            min_size=self.min_size,
            max_size=self.max_size,
            max_queries=self.max_queries,
            max_inactive_connection_lifetime=self.max_inactive_connection_lifetime,
            command_timeout=self.command_timeout,
            setup=self._setup_connection,
            init=self._init_connection
        )
        
        # Start health monitoring
        self._health_check_task = asyncio.create_task(self._health_monitor())
    
    async def _setup_connection(self, connection: asyncpg.Connection) -> None:
        """Setup new connection with optimizations"""
        # Set connection-level optimizations
        await connection.execute("SET statement_timeout = '30s'")
        await connection.execute("SET lock_timeout = '10s'")
        await connection.execute("SET idle_in_transaction_session_timeout = '60s'")
        
        # Enable prepared statement cache
        await connection.execute("SET plan_cache_mode = 'force_generic_plan'")
        
        # Record connection stats
        conn_id = id(connection)
        self._connection_stats[conn_id] = ConnectionStats(
            created_at=datetime.utcnow(),
            last_used=datetime.utcnow()
        )
    
    async def _init_connection(self, connection: asyncpg.Connection) -> None:
        """Initialize connection with custom types and extensions"""
        # Add custom JSON encoder/decoder if needed
        await connection.set_type_codec(
            'json',
            encoder=json.dumps,
            decoder=json.loads,
            schema='pg_catalog'
        )
        
        # Enable extensions if needed
        try:
            await connection.execute("CREATE EXTENSION IF NOT EXISTS pg_stat_statements")
        except Exception:
            pass  # Extension might not be available
    
    async def acquire_connection(self):
        """Acquire connection from pool with stats tracking"""
        if not self._pool:
            await self.initialize()
        
        connection = await self._pool.acquire()
        
        # Update stats
        conn_id = id(connection)
        if conn_id in self._connection_stats:
            self._connection_stats[conn_id].last_used = datetime.utcnow()
        
        return ConnectionWrapper(connection, self._connection_stats.get(conn_id))
    
    async def execute_query(self, query: str, *args) -> List[Dict]:
        """Execute query with automatic connection management"""
        async with self.acquire_connection() as conn:
            return await conn.fetch(query, *args)
    
    async def execute_transaction(self, transaction_func, *args, **kwargs):
        """Execute function within a transaction"""
        async with self.acquire_connection() as conn:
            async with conn.transaction():
                return await transaction_func(conn, *args, **kwargs)
    
    async def _health_monitor(self) -> None:
        """Monitor connection health and replace unhealthy connections"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                if not self._pool:
                    continue
                
                # Check connection health
                unhealthy_connections = []
                
                for conn_id, stats in self._connection_stats.items():
                    # Check if connection is stale
                    if (datetime.utcnow() - stats.last_used).seconds > self.max_inactive_connection_lifetime:
                        unhealthy_connections.append(conn_id)
                    
                    # Check query performance
                    if stats.total_queries > 0:
                        avg_query_time = stats.total_time_seconds / stats.total_queries
                        if avg_query_time > 1.0:  # Avg query time > 1 second
                            unhealthy_connections.append(conn_id)
                
                # Mark unhealthy connections
                for conn_id in unhealthy_connections:
                    if conn_id in self._connection_stats:
                        self._connection_stats[conn_id].is_healthy = False
                        
            except Exception as e:
                print(f"Error in health monitor: {e}")
    
    async def get_pool_stats(self) -> Dict[str, Any]:
        """Get comprehensive pool statistics"""
        if not self._pool:
            return {}
        
        total_connections = len(self._connection_stats)
        healthy_connections = sum(
            1 for stats in self._connection_stats.values() 
            if stats.is_healthy
        )
        
        return {
            'pool_size': self._pool.get_size(),
            'pool_min_size': self._pool.get_min_size(),
            'pool_max_size': self._pool.get_max_size(),
            'total_connections': total_connections,
            'healthy_connections': healthy_connections,
            'average_query_time': self._calculate_avg_query_time(),
            'total_queries': sum(stats.total_queries for stats in self._connection_stats.values())
        }
    
    def _calculate_avg_query_time(self) -> float:
        """Calculate average query time across all connections"""
        total_time = sum(stats.total_time_seconds for stats in self._connection_stats.values())
        total_queries = sum(stats.total_queries for stats in self._connection_stats.values())
        
        return total_time / total_queries if total_queries > 0 else 0.0

class ConnectionWrapper:
    """Wrapper for database connection with stats tracking"""
    
    def __init__(self, connection: asyncpg.Connection, stats: Optional[ConnectionStats]):
        self.connection = connection
        self.stats = stats
        self._pool_reference = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Return connection to pool
        if hasattr(self.connection, '_pool') and self.connection._pool:
            self.connection._pool.release(self.connection)
    
    async def fetch(self, query: str, *args) -> List[Dict]:
        """Execute fetch with timing"""
        start_time = time.perf_counter()
        try:
            result = await self.connection.fetch(query, *args)
            return [dict(row) for row in result]
        finally:
            if self.stats:
                elapsed = time.perf_counter() - start_time
                self.stats.total_queries += 1
                self.stats.total_time_seconds += elapsed
                self.stats.last_used = datetime.utcnow()
    
    async def execute(self, query: str, *args) -> str:
        """Execute command with timing"""
        start_time = time.perf_counter()
        try:
            return await self.connection.execute(query, *args)
        finally:
            if self.stats:
                elapsed = time.perf_counter() - start_time
                self.stats.total_queries += 1
                self.stats.total_time_seconds += elapsed
                self.stats.last_used = datetime.utcnow()
    
    async def transaction(self):
        """Start transaction"""
        return self.connection.transaction()
```

### Caching Implementations

Advanced caching strategies require intelligent cache warming, invalidation, and consistency management across distributed systems.

#### Intelligent Cache Warming System

```python
import asyncio
import aiohttp
from typing import Dict, List, Set, Callable, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import heapq
import json
import logging

class CacheWarmingStrategy(Enum):
    PREDICTIVE = "PREDICTIVE"
    SCHEDULED = "SCHEDULED"
    ON_DEMAND = "ON_DEMAND"
    ADAPTIVE = "ADAPTIVE"

@dataclass
class CacheWarmingJob:
    key: str
    priority: int
    strategy: CacheWarmingStrategy
    fetch_function: Callable
    scheduled_time: datetime
    estimated_duration_seconds: float = 0.0
    retry_count: int = 0
    max_retries: int = 3
    
    def __lt__(self, other):
        return self.priority < other.priority

@dataclass 
class AccessPattern:
    key: str
    access_times: List[datetime] = field(default_factory=list)
    access_frequency: float = 0.0
    last_access: Optional[datetime] = None
    avg_response_time: float = 0.0

class IntelligentCacheWarmer:
    """AI-driven cache warming system that predicts and preloads cache entries"""
    
    def __init__(self, cache_manager: 'HighPerformanceCacheManager'):
        self.cache_manager = cache_manager
        self.warming_queue: List[CacheWarmingJob] = []
        self.access_patterns: Dict[str, AccessPattern] = {}
        self.warming_workers: List[asyncio.Task] = []
        self.pattern_analyzer_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        # Configuration
        self.max_workers = 5
        self.analysis_window_hours = 24
        self.prediction_lookahead_minutes = 30
        self.min_frequency_threshold = 0.1  # Accesses per hour
        
        self.logger = logging.getLogger(__name__)
    
    async def start(self) -> None:
        """Start cache warming system"""
        self.is_running = True
        
        # Start warming workers
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._warming_worker(f"worker-{i}"))
            self.warming_workers.append(worker)
        
        # Start pattern analyzer
        self.pattern_analyzer_task = asyncio.create_task(self._pattern_analyzer())
        
        self.logger.info(f"Started cache warming system with {self.max_workers} workers")
    
    async def stop(self) -> None:
        """Stop cache warming system"""
        self.is_running = False
        
        # Cancel all workers
        for worker in self.warming_workers:
            worker.cancel()
        
        if self.pattern_analyzer_task:
            self.pattern_analyzer_task.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.warming_workers, return_exceptions=True)
        
        self.logger.info("Stopped cache warming system")
    
    async def record_access(self, key: str, response_time_ms: float) -> None:
        """Record cache access for pattern analysis"""
        now = datetime.utcnow()
        
        if key not in self.access_patterns:
            self.access_patterns[key] = AccessPattern(key=key)
        
        pattern = self.access_patterns[key]
        pattern.access_times.append(now)
        pattern.last_access = now
        
        # Update rolling average response time
        if pattern.avg_response_time == 0:
            pattern.avg_response_time = response_time_ms
        else:
            pattern.avg_response_time = (pattern.avg_response_time * 0.9) + (response_time_ms * 0.1)
        
        # Keep only recent access times
        cutoff_time = now - timedelta(hours=self.analysis_window_hours)
        pattern.access_times = [t for t in pattern.access_times if t > cutoff_time]
        
        # Calculate frequency (accesses per hour)
        pattern.access_frequency = len(pattern.access_times) / self.analysis_window_hours
    
    async def schedule_warming(
        self,
        key: str,
        fetch_function: Callable,
        strategy: CacheWarmingStrategy = CacheWarmingStrategy.ON_DEMAND,
        priority: int = 5,
        scheduled_time: Optional[datetime] = None
    ) -> None:
        """Schedule a cache warming job"""
        
        if scheduled_time is None:
            scheduled_time = datetime.utcnow()
        
        job = CacheWarmingJob(
            key=key,
            priority=priority,
            strategy=strategy,
            fetch_function=fetch_function,
            scheduled_time=scheduled_time
        )
        
        heapq.heappush(self.warming_queue, job)
        self.logger.debug(f"Scheduled warming job for key: {key}, strategy: {strategy}")
    
    async def _warming_worker(self, worker_id: str) -> None:
        """Worker that processes cache warming jobs"""
        self.logger.debug(f"Started warming worker: {worker_id}")
        
        while self.is_running:
            try:
                # Get next job
                if not self.warming_queue:
                    await asyncio.sleep(1)
                    continue
                
                job = heapq.heappop(self.warming_queue)
                
                # Check if it's time to process the job
                if datetime.utcnow() < job.scheduled_time:
                    # Put job back and wait
                    heapq.heappush(self.warming_queue, job)
                    await asyncio.sleep(1)
                    continue
                
                # Process the warming job
                await self._process_warming_job(job, worker_id)
                
            except Exception as e:
                self.logger.error(f"Error in warming worker {worker_id}: {e}")
                await asyncio.sleep(1)
    
    async def _process_warming_job(self, job: CacheWarmingJob, worker_id: str) -> None:
        """Process a single cache warming job"""
        start_time = time.perf_counter()
        
        try:
            self.logger.debug(f"Worker {worker_id} processing warming job for key: {job.key}")
            
            # Fetch the data
            data = await job.fetch_function(job.key)
            
            if data is not None:
                # Store in cache
                await self.cache_manager.set(job.key, data)
                
                # Record success
                elapsed = time.perf_counter() - start_time
                job.estimated_duration_seconds = elapsed
                
                self.logger.debug(f"Successfully warmed cache for key: {job.key} in {elapsed:.3f}s")
            else:
                self.logger.warning(f"Warming job returned None for key: {job.key}")
                
        except Exception as e:
            self.logger.error(f"Error warming cache for key {job.key}: {e}")
            
            # Retry logic
            job.retry_count += 1
            if job.retry_count < job.max_retries:
                # Reschedule with exponential backoff
                delay_seconds = 2 ** job.retry_count
                job.scheduled_time = datetime.utcnow() + timedelta(seconds=delay_seconds)
                heapq.heappush(self.warming_queue, job)
                
                self.logger.debug(f"Rescheduled warming job for key: {job.key}, retry: {job.retry_count}")
    
    async def _pattern_analyzer(self) -> None:
        """Analyze access patterns and schedule predictive warming"""
        self.logger.debug("Started pattern analyzer")
        
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Analyze every minute
                
                # Analyze patterns and predict future accesses
                predictions = await self._predict_future_accesses()
                
                # Schedule warming jobs for predictions
                for prediction in predictions:
                    # Check if already cached
                    cached_value = await self.cache_manager.get(prediction['key'])
                    
                    if cached_value is None:
                        # Schedule predictive warming
                        await self.schedule_warming(
                            key=prediction['key'],
                            fetch_function=prediction['fetch_function'],
                            strategy=CacheWarmingStrategy.PREDICTIVE,
                            priority=prediction['priority'],
                            scheduled_time=prediction['predicted_time']
                        )
                
            except Exception as e:
                self.logger.error(f"Error in pattern analyzer: {e}")
    
    async def _predict_future_accesses(self) -> List[Dict[str, Any]]:
        """Predict future cache accesses based on historical patterns"""
        predictions = []
        now = datetime.utcnow()
        
        for key, pattern in self.access_patterns.items():
            # Only predict for frequently accessed keys
            if pattern.access_frequency < self.min_frequency_threshold:
                continue
            
            # Analyze temporal patterns
            if len(pattern.access_times) < 3:
                continue
            
            # Simple prediction: look for regular intervals
            intervals = []
            sorted_times = sorted(pattern.access_times)
            
            for i in range(1, len(sorted_times)):
                interval = (sorted_times[i] - sorted_times[i-1]).total_seconds()
                intervals.append(interval)
            
            if intervals:
                # Use median interval for prediction
                median_interval = sorted(intervals)[len(intervals) // 2]
                
                # Predict next access time
                predicted_time = pattern.last_access + timedelta(seconds=median_interval)
                
                # Only predict if within lookahead window
                if predicted_time <= now + timedelta(minutes=self.prediction_lookahead_minutes):
                    # Calculate priority based on frequency and response time
                    priority = int(pattern.access_frequency * 10) + int(pattern.avg_response_time / 100)
                    
                    predictions.append({
                        'key': key,
                        'predicted_time': predicted_time,
                        'priority': min(priority, 10),  # Cap at 10
                        'confidence': self._calculate_prediction_confidence(pattern),
                        'fetch_function': self._get_fetch_function_for_key(key)
                    })
        
        return sorted(predictions, key=lambda x: x['priority'], reverse=True)
    
    def _calculate_prediction_confidence(self, pattern: AccessPattern) -> float:
        """Calculate confidence score for prediction"""
        # Simple confidence based on regularity of access pattern
        if len(pattern.access_times) < 3:
            return 0.0
        
        # Calculate coefficient of variation for intervals
        intervals = []
        sorted_times = sorted(pattern.access_times)
        
        for i in range(1, len(sorted_times)):
            interval = (sorted_times[i] - sorted_times[i-1]).total_seconds()
            intervals.append(interval)
        
        if not intervals:
            return 0.0
        
        mean_interval = sum(intervals) / len(intervals)
        variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
        std_dev = variance ** 0.5
        
        # Lower coefficient of variation = higher confidence
        cv = std_dev / mean_interval if mean_interval > 0 else float('inf')
        confidence = max(0.0, min(1.0, 1.0 - cv))
        
        return confidence
    
    def _get_fetch_function_for_key(self, key: str) -> Callable:
        """Get appropriate fetch function for a cache key"""
        # This would be configured based on your application's needs
        # For now, return a placeholder function
        async def default_fetch(cache_key: str):
            # Implement your data fetching logic here
            return f"data_for_{cache_key}"
        
        return default_fetch
    
    async def get_warming_stats(self) -> Dict[str, Any]:
        """Get cache warming statistics"""
        queue_size = len(self.warming_queue)
        patterns_tracked = len(self.access_patterns)
        
        # Calculate average frequency
        total_frequency = sum(p.access_frequency for p in self.access_patterns.values())
        avg_frequency = total_frequency / patterns_tracked if patterns_tracked > 0 else 0
        
        return {
            'queue_size': queue_size,
            'patterns_tracked': patterns_tracked,
            'average_access_frequency': avg_frequency,
            'workers_active': len([w for w in self.warming_workers if not w.done()]),
            'is_running': self.is_running
        }
```

### Database Performance

Database optimization requires query optimization, intelligent indexing strategies, and connection pooling for maximum throughput.

#### Advanced Query Optimization Engine

```python
import asyncio
import re
import time
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import sqlparse
from sqlparse import sql, tokens as T
import asyncpg

class QueryType(Enum):
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    DDL = "DDL"

class OptimizationLevel(Enum):
    BASIC = "BASIC"
    MODERATE = "MODERATE"
    AGGRESSIVE = "AGGRESSIVE"

@dataclass
class QueryAnalysis:
    original_query: str
    query_type: QueryType
    estimated_cost: float
    execution_time_ms: float
    row_count: int
    tables_accessed: List[str]
    indexes_used: List[str]
    missing_indexes: List[str]
    optimization_suggestions: List[str]
    optimized_query: Optional[str] = None

@dataclass
class QueryPerformanceMetrics:
    query_hash: str
    execution_count: int = 0
    total_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    min_time_ms: float = float('inf')
    max_time_ms: float = 0.0
    last_executed: Optional[datetime] = None
    error_count: int = 0

class DatabaseQueryOptimizer:
    """Advanced database query optimization and performance monitoring"""
    
    def __init__(self, connection_pool: AsyncConnectionPool):
        self.connection_pool = connection_pool
        self.query_metrics: Dict[str, QueryPerformanceMetrics] = {}
        self.slow_query_threshold_ms = 1000  # 1 second
        self.optimization_cache: Dict[str, QueryAnalysis] = {}
        
    async def analyze_query(
        self, 
        query: str, 
        optimization_level: OptimizationLevel = OptimizationLevel.MODERATE
    ) -> QueryAnalysis:
        """Comprehensive query analysis and optimization"""
        
        # Generate query hash for caching
        query_hash = hashlib.md5(query.encode()).hexdigest()
        
        # Check optimization cache
        if query_hash in self.optimization_cache:
            return self.optimization_cache[query_hash]
        
        # Parse query
        parsed = sqlparse.parse(query)[0]
        query_type = self._determine_query_type(parsed)
        tables = self._extract_tables(parsed)
        
        # Get execution plan
        execution_plan = await self._get_execution_plan(query)
        
        # Analyze performance
        analysis = QueryAnalysis(
            original_query=query,
            query_type=query_type,
            estimated_cost=execution_plan.get('total_cost', 0),
            execution_time_ms=0,  # Will be set during execution
            row_count=execution_plan.get('plan_rows', 0),
            tables_accessed=tables,
            indexes_used=self._extract_indexes_from_plan(execution_plan),
            missing_indexes=[],
            optimization_suggestions=[]
        )
        
        # Generate optimization suggestions
        await self._generate_optimization_suggestions(analysis, optimization_level)
        
        # Generate optimized query if possible
        if optimization_level in [OptimizationLevel.MODERATE, OptimizationLevel.AGGRESSIVE]:
            analysis.optimized_query = await self._optimize_query(query, analysis)
        
        # Cache the analysis
        self.optimization_cache[query_hash] = analysis
        
        return analysis
    
    async def execute_optimized_query(
        self, 
        query: str, 
        params: Optional[List] = None,
        optimization_level: OptimizationLevel = OptimizationLevel.MODERATE
    ) -> Tuple[List[Dict], QueryAnalysis]:
        """Execute query with automatic optimization and performance tracking"""
        
        start_time = time.perf_counter()
        query_hash = hashlib.md5(query.encode()).hexdigest()
        
        try:
            # Analyze and potentially optimize the query
            analysis = await self.analyze_query(query, optimization_level)
            
            # Use optimized query if available and beneficial
            execution_query = analysis.optimized_query if analysis.optimized_query else query
            
            # Execute the query
            async with self.connection_pool.acquire_connection() as conn:
                if params:
                    result = await conn.fetch(execution_query, *params)
                else:
                    result = await conn.fetch(execution_query)
            
            # Calculate execution time
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            analysis.execution_time_ms = execution_time_ms
            
            # Update performance metrics
            await self._update_query_metrics(query_hash, execution_time_ms, success=True)
            
            # Log slow queries
            if execution_time_ms > self.slow_query_threshold_ms:
                await self._log_slow_query(query, execution_time_ms, analysis)
            
            return result, analysis
            
        except Exception as e:
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            await self._update_query_metrics(query_hash, execution_time_ms, success=False)
            raise e
    
    async def _get_execution_plan(self, query: str) -> Dict[str, Any]:
        """Get query execution plan from database"""
        
        explain_query = f"EXPLAIN (FORMAT JSON, ANALYZE, BUFFERS) {query}"
        
        try:
            async with self.connection_pool.acquire_connection() as conn:
                result = await conn.fetch(explain_query)
                
                if result and len(result) > 0:
                    plan_data = result[0]['QUERY PLAN']
                    if isinstance(plan_data, str):
                        plan_data = json.loads(plan_data)
                    
                    return plan_data[0]['Plan'] if isinstance(plan_data, list) else plan_data['Plan']
                
        except Exception as e:
            print(f"Error getting execution plan: {e}")
        
        return {}
    
    def _determine_query_type(self, parsed_query) -> QueryType:
        """Determine the type of SQL query"""
        
        for token in parsed_query.flatten():
            if token.ttype is T.Keyword.DML:
                token_value = token.value.upper()
                if token_value in ['SELECT']:
                    return QueryType.SELECT
                elif token_value in ['INSERT']:
                    return QueryType.INSERT
                elif token_value in ['UPDATE']:
                    return QueryType.UPDATE
                elif token_value in ['DELETE']:
                    return QueryType.DELETE
            elif token.ttype is T.Keyword.DDL:
                return QueryType.DDL
        
        return QueryType.SELECT  # Default
    
    def _extract_tables(self, parsed_query) -> List[str]:
        """Extract table names from parsed query"""
        tables = []
        
        def extract_from_token(token):
            if isinstance(token, sql.IdentifierList):
                for identifier in token.get_identifiers():
                    tables.append(str(identifier))
            elif isinstance(token, sql.Identifier):
                tables.append(str(token))
            elif token.ttype is None:
                for sub_token in token.tokens:
                    extract_from_token(sub_token)
        
        in_from_clause = False
        for token in parsed_query.tokens:
            if isinstance(token, sql.Token) and token.ttype is T.Keyword and token.value.upper() == 'FROM':
                in_from_clause = True
            elif in_from_clause and not (isinstance(token, sql.Token) and token.ttype is T.Whitespace):
                if isinstance(token, sql.Token) and token.ttype is T.Keyword:
                    break
                extract_from_token(token)
                break
        
        return [table.strip('`"[]') for table in tables]
    
    def _extract_indexes_from_plan(self, execution_plan: Dict) -> List[str]:
        """Extract indexes used from execution plan"""
        indexes = []
        
        def extract_indexes_recursive(plan_node):
            if isinstance(plan_node, dict):
                # Check for index scan
                node_type = plan_node.get('Node Type', '')
                if 'Index' in node_type:
                    index_name = plan_node.get('Index Name')
                    if index_name:
                        indexes.append(index_name)
                
                # Recursively check child plans
                if 'Plans' in plan_node:
                    for child_plan in plan_node['Plans']:
                        extract_indexes_recursive(child_plan)
        
        extract_indexes_recursive(execution_plan)
        return indexes
    
    async def _generate_optimization_suggestions(
        self, 
        analysis: QueryAnalysis, 
        optimization_level: OptimizationLevel
    ) -> None:
        """Generate optimization suggestions based on query analysis"""
        
        suggestions = []
        
        # Check for missing indexes
        if analysis.query_type == QueryType.SELECT:
            missing_indexes = await self._identify_missing_indexes(analysis)
            analysis.missing_indexes = missing_indexes
            
            for index in missing_indexes:
                suggestions.append(f"Consider adding index: {index}")
        
        # Check for full table scans
        if analysis.estimated_cost > 1000:  # High cost threshold
            suggestions.append("Query performs expensive operations - consider optimization")
        
        # Check for SELECT *
        if 'SELECT *' in analysis.original_query.upper():
            suggestions.append("Avoid SELECT * - specify only needed columns")
        
        # Check for missing WHERE clause on large tables
        if not re.search(r'\bWHERE\b', analysis.original_query, re.IGNORECASE):
            if analysis.tables_accessed:
                table_sizes = await self._get_table_sizes(analysis.tables_accessed)
                large_tables = [table for table, size in table_sizes.items() if size > 100000]
                if large_tables:
                    suggestions.append(f"Consider adding WHERE clause for large tables: {', '.join(large_tables)}")
        
        # Check for inefficient JOINs
        join_suggestions = await self._analyze_joins(analysis.original_query)
        suggestions.extend(join_suggestions)
        
        analysis.optimization_suggestions = suggestions
    
    async def _identify_missing_indexes(self, analysis: QueryAnalysis) -> List[str]:
        """Identify potentially missing indexes based on WHERE clauses"""
        missing_indexes = []
        
        # Extract WHERE conditions
        where_conditions = self._extract_where_conditions(analysis.original_query)
        
        for table in analysis.tables_accessed:
            # Get existing indexes for table
            existing_indexes = await self._get_table_indexes(table)
            
            # Check if WHERE conditions have supporting indexes
            for condition in where_conditions:
                column = condition.get('column')
                if column and not self._has_supporting_index(column, existing_indexes):
                    missing_indexes.append(f"CREATE INDEX idx_{table}_{column} ON {table} ({column})")
        
        return missing_indexes
    
    def _extract_where_conditions(self, query: str) -> List[Dict[str, str]]:
        """Extract WHERE clause conditions"""
        conditions = []
        
        # Simple regex-based extraction (could be improved with proper SQL parsing)
        where_pattern = r'WHERE\s+(.+?)(?:\s+ORDER\s+BY|\s+GROUP\s+BY|\s+HAVING|\s+LIMIT|$)'
        where_match = re.search(where_pattern, query, re.IGNORECASE | re.DOTALL)
        
        if where_match:
            where_clause = where_match.group(1)
            
            # Extract column = value patterns
            condition_pattern = r'(\w+)\s*[=<>]\s*'
            for match in re.finditer(condition_pattern, where_clause):
                conditions.append({'column': match.group(1)})
        
        return conditions
    
    async def _get_table_indexes(self, table_name: str) -> List[str]:
        """Get existing indexes for a table"""
        query = """
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = $1
        """
        
        try:
            async with self.connection_pool.acquire_connection() as conn:
                result = await conn.fetch(query, table_name)
                return [row['indexname'] for row in result]
        except Exception:
            return []
    
    def _has_supporting_index(self, column: str, existing_indexes: List[str]) -> bool:
        """Check if column has a supporting index"""
        # Simple check - in practice, this would be more sophisticated
        return any(column.lower() in index.lower() for index in existing_indexes)
    
    async def _get_table_sizes(self, table_names: List[str]) -> Dict[str, int]:
        """Get approximate row counts for tables"""
        sizes = {}
        
        for table in table_names:
            query = """
                SELECT n_tup_ins + n_tup_upd + n_tup_del as row_count
                FROM pg_stat_user_tables 
                WHERE relname = $1
            """
            
            try:
                async with self.connection_pool.acquire_connection() as conn:
                    result = await conn.fetch(query, table)
                    if result:
                        sizes[table] = result[0]['row_count'] or 0
                    else:
                        sizes[table] = 0
            except Exception:
                sizes[table] = 0
        
        return sizes
    
    async def _analyze_joins(self, query: str) -> List[str]:
        """Analyze JOIN operations for optimization opportunities"""
        suggestions = []
        
        # Check for Cartesian products (JOINs without ON clauses)
        join_pattern = r'JOIN\s+\w+(?:\s+\w+)?\s*(?!ON)'
        if re.search(join_pattern, query, re.IGNORECASE):
            suggestions.append("Potential Cartesian product detected - ensure all JOINs have ON clauses")
        
        # Check for inefficient JOIN order (large tables first)
        # This would require more sophisticated analysis in practice
        
        return suggestions
    
    async def _optimize_query(self, query: str, analysis: QueryAnalysis) -> Optional[str]:
        """Generate optimized version of query"""
        optimized = query
        
        # Apply basic optimizations
        
        # 1. Replace SELECT * with specific columns (if we can determine them)
        if 'SELECT *' in query.upper() and analysis.query_type == QueryType.SELECT:
            # In practice, you'd need to determine which columns are actually needed
            # This is a simplified example
            pass
        
        # 2. Add LIMIT clause for potentially large result sets
        if not re.search(r'\bLIMIT\b', query, re.IGNORECASE) and analysis.row_count > 10000:
            optimized += " LIMIT 1000"
        
        # 3. Rewrite inefficient subqueries as JOINs
        # This would require sophisticated query rewriting
        
        # Return optimized query only if it's different and potentially better
        return optimized if optimized != query else None
    
    async def _update_query_metrics(
        self, 
        query_hash: str, 
        execution_time_ms: float, 
        success: bool = True
    ) -> None:
        """Update query performance metrics"""
        
        if query_hash not in self.query_metrics:
            self.query_metrics[query_hash] = QueryPerformanceMetrics(query_hash=query_hash)
        
        metrics = self.query_metrics[query_hash]
        metrics.execution_count += 1
        metrics.last_executed = datetime.utcnow()
        
        if success:
            metrics.total_time_ms += execution_time_ms
            metrics.avg_time_ms = metrics.total_time_ms / metrics.execution_count
            metrics.min_time_ms = min(metrics.min_time_ms, execution_time_ms)
            metrics.max_time_ms = max(metrics.max_time_ms, execution_time_ms)
        else:
            metrics.error_count += 1
    
    async def _log_slow_query(
        self, 
        query: str, 
        execution_time_ms: float, 
        analysis: QueryAnalysis
    ) -> None:
        """Log slow query for analysis"""
        
        slow_query_info = {
            'query': query,
            'execution_time_ms': execution_time_ms,
            'estimated_cost': analysis.estimated_cost,
            'tables_accessed': analysis.tables_accessed,
            'suggestions': analysis.optimization_suggestions,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # In practice, you'd log this to a dedicated slow query log
        print(f"SLOW QUERY DETECTED: {json.dumps(slow_query_info, indent=2)}")
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        
        total_queries = len(self.query_metrics)
        if total_queries == 0:
            return {"message": "No queries executed yet"}
        
        # Calculate aggregate statistics
        all_avg_times = [m.avg_time_ms for m in self.query_metrics.values() if m.avg_time_ms > 0]
        all_execution_counts = [m.execution_count for m in self.query_metrics.values()]
        
        slowest_queries = sorted(
            self.query_metrics.values(),
            key=lambda x: x.avg_time_ms,
            reverse=True
        )[:10]
        
        most_frequent_queries = sorted(
            self.query_metrics.values(),
            key=lambda x: x.execution_count,
            reverse=True
        )[:10]
        
        return {
            'total_unique_queries': total_queries,
            'average_execution_time_ms': sum(all_avg_times) / len(all_avg_times) if all_avg_times else 0,
            'total_executions': sum(all_execution_counts),
            'slowest_queries': [
                {
                    'query_hash': q.query_hash,
                    'avg_time_ms': q.avg_time_ms,
                    'execution_count': q.execution_count,
                    'error_count': q.error_count
                }
                for q in slowest_queries
            ],
            'most_frequent_queries': [
                {
                    'query_hash': q.query_hash,
                    'execution_count': q.execution_count,
                    'avg_time_ms': q.avg_time_ms,
                    'total_time_ms': q.total_time_ms
                }
                for q in most_frequent_queries
            ],
            'optimization_cache_size': len(self.optimization_cache)
        }
```

This comprehensive High-Performance Architecture guide provides production-ready implementations for caching strategies, connection pooling, database optimization, and performance monitoring. Each component is designed for maximum throughput, minimal latency, and intelligent resource utilization.