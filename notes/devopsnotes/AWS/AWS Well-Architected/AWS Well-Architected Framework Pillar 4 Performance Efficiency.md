# AWS Well-Architected Framework - Pillar 4: Performance Efficiency

## Strategic Context

Performance efficiency directly impacts user experience, conversion rates, and operational costs. A 100ms improvement in page load times can increase conversion rates by 1-2%, while poor performance can drive customer churn and competitive disadvantage.

### Business Impact of Performance Efficiency
- **Revenue Impact**: 1-second delay reduces conversions by 7%
- **User Experience**: 53% of mobile users abandon sites that take >3 seconds to load
- **Cost Optimization**: Efficient resource usage reduces infrastructure costs by 30-50%
- **Competitive Advantage**: Superior performance becomes key differentiator
- **SEO Benefits**: Site speed directly impacts search rankings

### Performance Efficiency Design Principles
1. **Democratize advanced technologies**: Use managed services to reduce complexity
2. **Go global in minutes**: Deploy systems closer to users worldwide
3. **Use serverless architectures**: Eliminate operational overhead
4. **Experiment more often**: Compare different approaches with A/B testing
5. **Consider mechanical sympathy**: Understand how hardware impacts performance

## Core Principles and Best Practices

### Resource Optimization

**Right-Sizing and Auto-Scaling**
Implement intelligent resource allocation based on actual usage patterns rather than peak capacity planning. Use auto-scaling groups and serverless architectures to optimize resource utilization.

```yaml
# Example: Kubernetes Vertical Pod Autoscaler
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: web-app-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: web-app
      maxAllowed:
        cpu: 2
        memory: 4Gi
      minAllowed:
        cpu: 100m
        memory: 128Mi
      controlledResources: ["cpu", "memory"]
      controlledValues: RequestsAndLimits
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app
  minReplicas: 2
  maxReplicas: 100
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: requests_per_second
      target:
        type: AverageValue
        averageValue: "100"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 30
```

**Caching Strategies**
Implement multi-layer caching including application caches, database query caches, and content delivery network caching. Use cache invalidation strategies to maintain data consistency.

```python
# Example: Advanced Caching Implementation
import redis
import hashlib
import json
import asyncio
from typing import Any, Optional, Callable
from functools import wraps
from datetime import datetime, timedelta

class AdvancedCacheManager:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.local_cache = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
    
    def generate_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate deterministic cache key"""
        key_data = {
            'function': func_name,
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return f"cache:{hashlib.md5(key_string.encode()).hexdigest()}"
    
    def cache_with_fallback(self, 
                           ttl: int = 3600, 
                           fallback_ttl: int = 300,
                           cache_null: bool = False):
        """Multi-level cache decorator with fallback strategies"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                cache_key = self.generate_cache_key(func.__name__, args, kwargs)
                
                # L1: Check local cache first
                if cache_key in self.local_cache:
                    cache_data = self.local_cache[cache_key]
                    if cache_data['expires'] > datetime.now():
                        self.cache_stats['hits'] += 1
                        return cache_data['value']
                    else:
                        del self.local_cache[cache_key]
                
                # L2: Check Redis cache
                try:
                    cached_data = self.redis_client.get(cache_key)
                    if cached_data:
                        result = json.loads(cached_data)
                        # Update local cache
                        self.local_cache[cache_key] = {
                            'value': result,
                            'expires': datetime.now() + timedelta(seconds=fallback_ttl)
                        }
                        self.cache_stats['hits'] += 1
                        return result
                except redis.ConnectionError:
                    # Redis is down, continue to function execution
                    pass
                
                # Cache miss - execute function
                self.cache_stats['misses'] += 1
                try:
                    result = await func(*args, **kwargs)
                    
                    # Store in both caches if result is not None or cache_null is True
                    if result is not None or cache_null:
                        # Store in Redis
                        try:
                            self.redis_client.setex(
                                cache_key, 
                                ttl, 
                                json.dumps(result, default=str)
                            )
                        except redis.ConnectionError:
                            pass
                        
                        # Store in local cache
                        self.local_cache[cache_key] = {
                            'value': result,
                            'expires': datetime.now() + timedelta(seconds=fallback_ttl)
                        }
                    
                    return result
                except Exception as e:
                    # Function failed, try to return stale cache if available
                    stale_key = f"stale:{cache_key}"
                    try:
                        stale_data = self.redis_client.get(stale_key)
                        if stale_data:
                            return json.loads(stale_data)
                    except redis.ConnectionError:
                        pass
                    
                    raise e
            
            return wrapper
        return decorator
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate cache keys matching pattern"""
        try:
            keys = self.redis_client.keys(f"cache:*{pattern}*")
            if keys:
                self.redis_client.delete(*keys)
                self.cache_stats['evictions'] += len(keys)
        except redis.ConnectionError:
            pass
        
        # Also clear local cache
        keys_to_remove = [k for k in self.local_cache.keys() if pattern in k]
        for key in keys_to_remove:
            del self.local_cache[key]
    
    def get_stats(self) -> dict:
        """Get cache performance statistics"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = self.cache_stats['hits'] / total_requests if total_requests > 0 else 0
        
        return {
            'hit_rate': hit_rate,
            'total_requests': total_requests,
            **self.cache_stats
        }

# Usage Example
cache_manager = AdvancedCacheManager()

@cache_manager.cache_with_fallback(ttl=3600, fallback_ttl=300)
async def get_user_data(user_id: int) -> dict:
    """Simulate expensive database operation"""
    # Expensive database query
    await asyncio.sleep(0.1)  # Simulate DB latency
    return {
        'user_id': user_id,
        'name': f'User {user_id}',
        'last_updated': datetime.now().isoformat()
    }

@cache_manager.cache_with_fallback(ttl=1800)
async def get_product_recommendations(user_id: int, category: str) -> list:
    """Simulate ML model inference"""
    await asyncio.sleep(0.5)  # Simulate ML inference time
    return [f'product_{i}' for i in range(10)]
```

**Database Optimization**
Optimize database performance through proper indexing, query optimization, and database design. Consider read replicas, sharding, and NoSQL solutions for specific use cases.

```sql
-- Example: Advanced Database Optimization Strategies

-- 1. Composite Indexes for Complex Queries
CREATE INDEX CONCURRENTLY idx_orders_user_status_date 
ON orders (user_id, status, created_at DESC) 
WHERE status IN ('pending', 'processing');

-- 2. Partial Indexes for Selective Data
CREATE INDEX CONCURRENTLY idx_products_active_category 
ON products (category_id, price) 
WHERE is_active = true AND stock_quantity > 0;

-- 3. Expression Indexes for Computed Queries
CREATE INDEX CONCURRENTLY idx_users_email_lower 
ON users (LOWER(email));

-- 4. Optimized Query with CTE and Window Functions
WITH user_order_stats AS (
    SELECT 
        user_id,
        COUNT(*) as total_orders,
        SUM(total_amount) as total_spent,
        AVG(total_amount) as avg_order_value,
        ROW_NUMBER() OVER (PARTITION BY DATE_TRUNC('month', created_at) 
                          ORDER BY total_amount DESC) as monthly_rank
    FROM orders 
    WHERE created_at >= NOW() - INTERVAL '12 months'
    GROUP BY user_id, DATE_TRUNC('month', created_at)
),
user_segments AS (
    SELECT 
        user_id,
        CASE 
            WHEN total_spent > 1000 THEN 'premium'
            WHEN total_spent > 500 THEN 'regular'
            ELSE 'basic'
        END as segment,
        total_orders,
        avg_order_value
    FROM user_order_stats
    WHERE monthly_rank <= 100
)
SELECT 
    u.user_id,
    u.email,
    us.segment,
    us.total_orders,
    us.avg_order_value,
    COALESCE(r.recommendation_score, 0) as ml_score
FROM users u
JOIN user_segments us ON u.user_id = us.user_id
LEFT JOIN user_recommendations r ON u.user_id = r.user_id
WHERE u.is_active = true
ORDER BY us.avg_order_value DESC;

-- 5. Database Partitioning for Large Tables
CREATE TABLE orders_partitioned (
    order_id BIGSERIAL,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL,
    total_amount DECIMAL(10,2),
    status VARCHAR(20)
) PARTITION BY RANGE (created_at);

-- Create monthly partitions
CREATE TABLE orders_2024_01 PARTITION OF orders_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE orders_2024_02 PARTITION OF orders_partitioned
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
```

### Architecture Patterns

**Microservices and Service Mesh**
Implement microservices architectures with service mesh for improved scalability and maintainability. Use API gateways and service discovery for efficient service communication.

```yaml
# Example: Istio Service Mesh Configuration
apiVersion: networking.istio.io/v1alpha3
kind: ServiceEntry
metadata:
  name: external-database
spec:
  hosts:
  - database.external.com
  ports:
  - number: 5432
    name: postgres
    protocol: TCP
  location: MESH_EXTERNAL
  resolution: DNS
---
apiVersion: networking.istio.io/v1alpha3
kind: DestinationRule
metadata:
  name: user-service-circuit-breaker
spec:
  host: user-service
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 50
        http2MaxRequests: 100
        maxRequestsPerConnection: 2
        maxRetries: 3
        connectTimeout: 30s
        h2UpgradePolicy: UPGRADE
    loadBalancer:
      simple: LEAST_CONN
    outlierDetection:
      consecutiveGatewayErrors: 3
      consecutive5xxErrors: 3
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
      minHealthPercent: 30
---
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: user-service-routing
spec:
  hosts:
  - user-service
  http:
  - match:
    - headers:
        canary:
          exact: "true"
    route:
    - destination:
        host: user-service
        subset: canary
      weight: 100
  - route:
    - destination:
        host: user-service
        subset: stable
      weight: 90
    - destination:
        host: user-service
        subset: canary
      weight: 10
    timeout: 30s
    retries:
      attempts: 3
      perTryTimeout: 10s
      retryOn: gateway-error,connect-failure,refused-stream
```

**Event-Driven Architecture**
Design systems using event-driven patterns to improve responsiveness and scalability. Implement message queues and event streaming for asynchronous processing.

```python
# Example: High-Performance Event Processing
import asyncio
import aioredis
import json
from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from datetime import datetime
import logging

@dataclass
class Event:
    event_type: str
    data: dict
    timestamp: datetime
    correlation_id: str
    source: str

class HighPerformanceEventProcessor:
    def __init__(self, redis_url: str, batch_size: int = 100, max_wait_time: int = 1):
        self.redis_url = redis_url
        self.batch_size = batch_size
        self.max_wait_time = max_wait_time
        self.handlers: Dict[str, List[Callable]] = {}
        self.redis_pool = None
        self.processing_stats = {
            'processed': 0,
            'errors': 0,
            'batches': 0
        }
    
    async def initialize(self):
        """Initialize Redis connection pool"""
        self.redis_pool = aioredis.ConnectionPool.from_url(
            self.redis_url,
            max_connections=20,
            retry_on_timeout=True
        )
    
    def register_handler(self, event_type: str, handler: Callable):
        """Register event handler for specific event type"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
    
    async def publish_event(self, event: Event):
        """Publish event to Redis stream"""
        redis = aioredis.Redis(connection_pool=self.redis_pool)
        
        event_data = {
            'event_type': event.event_type,
            'data': json.dumps(event.data),
            'timestamp': event.timestamp.isoformat(),
            'correlation_id': event.correlation_id,
            'source': event.source
        }
        
        await redis.xadd(f"events:{event.event_type}", event_data)
    
    async def process_events_batch(self, events: List[Event]) -> List[dict]:
        """Process a batch of events concurrently"""
        tasks = []
        
        for event in events:
            if event.event_type in self.handlers:
                for handler in self.handlers[event.event_type]:
                    task = asyncio.create_task(self._safe_handler_call(handler, event))
                    tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results
        return []
    
    async def _safe_handler_call(self, handler: Callable, event: Event) -> dict:
        """Safely call event handler with error handling"""
        try:
            start_time = datetime.now()
            result = await handler(event)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'status': 'success',
                'handler': handler.__name__,
                'event_type': event.event_type,
                'processing_time': processing_time,
                'result': result
            }
        except Exception as e:
            logging.error(f"Handler {handler.__name__} failed for event {event.event_type}: {e}")
            self.processing_stats['errors'] += 1
            
            return {
                'status': 'error',
                'handler': handler.__name__,
                'event_type': event.event_type,
                'error': str(e)
            }
    
    async def start_consumer(self, consumer_group: str = "default"):
        """Start consuming events from Redis streams"""
        redis = aioredis.Redis(connection_pool=self.redis_pool)
        
        # Create consumer groups for each event type
        for event_type in self.handlers.keys():
            stream_name = f"events:{event_type}"
            try:
                await redis.xgroup_create(stream_name, consumer_group, id='0', mkstream=True)
            except aioredis.ResponseError:
                # Group already exists
                pass
        
        while True:
            try:
                events_batch = []
                batch_start_time = datetime.now()
                
                # Collect events for batch processing
                for event_type in self.handlers.keys():
                    stream_name = f"events:{event_type}"
                    
                    messages = await redis.xreadgroup(
                        consumer_group,
                        'consumer-1',
                        {stream_name: '>'},
                        count=self.batch_size // len(self.handlers),
                        block=self.max_wait_time * 1000
                    )
                    
                    for stream, msgs in messages:
                        for msg_id, fields in msgs:
                            event = Event(
                                event_type=fields['event_type'],
                                data=json.loads(fields['data']),
                                timestamp=datetime.fromisoformat(fields['timestamp']),
                                correlation_id=fields['correlation_id'],
                                source=fields['source']
                            )
                            events_batch.append((event, stream.decode(), msg_id.decode()))
                
                if events_batch:
                    # Process batch
                    events_only = [event for event, _, _ in events_batch]
                    results = await self.process_events_batch(events_only)
                    
                    # Acknowledge processed messages
                    for (event, stream_name, msg_id), result in zip(events_batch, results):
                        if result and result.get('status') == 'success':
                            await redis.xack(stream_name, consumer_group, msg_id)
                    
                    self.processing_stats['processed'] += len(events_batch)
                    self.processing_stats['batches'] += 1
                    
                    batch_time = (datetime.now() - batch_start_time).total_seconds()
                    logging.info(f"Processed batch of {len(events_batch)} events in {batch_time:.2f}s")
                
                # Brief pause to prevent tight loop
                await asyncio.sleep(0.01)
                
            except Exception as e:
                logging.error(f"Error in event consumer: {e}")
                await asyncio.sleep(1)

# Usage Example
async def user_created_handler(event: Event):
    """Handle user creation events"""
    user_data = event.data
    
    # Send welcome email (simulated)
    await asyncio.sleep(0.1)
    
    # Update analytics
    await asyncio.sleep(0.05)
    
    return {'email_sent': True, 'analytics_updated': True}

async def order_placed_handler(event: Event):
    """Handle order placement events"""
    order_data = event.data
    
    # Process payment (simulated)
    await asyncio.sleep(0.2)
    
    # Update inventory
    await asyncio.sleep(0.1)
    
    # Send confirmation
    await asyncio.sleep(0.05)
    
    return {'payment_processed': True, 'inventory_updated': True}

# Initialize processor
processor = HighPerformanceEventProcessor("redis://localhost:6379")
await processor.initialize()

# Register handlers
processor.register_handler('user.created', user_created_handler)
processor.register_handler('order.placed', order_placed_handler)

# Start processing
await processor.start_consumer()
```

**Serverless Computing**
Leverage serverless architectures for event-driven workloads and variable traffic patterns. Use function-as-a-service platforms for optimal resource utilization.

```typescript
// Example: High-Performance Serverless Function
import { APIGatewayProxyEvent, APIGatewayProxyResult, Context } from 'aws-lambda';
import { DynamoDB } from 'aws-sdk';
import { createHash } from 'crypto';

// Connection reuse outside handler
const dynamodb = new DynamoDB.DocumentClient({
  region: process.env.AWS_REGION,
  maxRetries: 3,
  retryDelayOptions: {
    customBackoff: function(retryCount: number) {
      return Math.pow(2, retryCount) * 100;
    }
  }
});

// Cached data (persists across invocations)
let cachedConfig: any = null;
let cacheExpiry: number = 0;

interface UserProfile {
  userId: string;
  preferences: any;
  lastUpdated: string;
}

export const handler = async (
  event: APIGatewayProxyEvent,
  context: Context
): Promise<APIGatewayProxyResult> => {
  
  // Performance optimization: reduce timeout for faster cold starts
  context.callbackWaitsForEmptyEventLoop = false;
  
  const startTime = Date.now();
  
  try {
    // Input validation and parsing
    const userId = event.pathParameters?.userId;
    if (!userId) {
      return {
        statusCode: 400,
        headers: getCORSHeaders(),
        body: JSON.stringify({ error: 'User ID is required' })
      };
    }
    
    // Get cached configuration if available
    const config = await getCachedConfig();
    
    // Parallel data fetching
    const [userProfile, userAnalytics] = await Promise.all([
      getUserProfile(userId),
      getUserAnalytics(userId, config.analyticsRetentionDays)
    ]);
    
    if (!userProfile) {
      return {
        statusCode: 404,
        headers: getCORSHeaders(),
        body: JSON.stringify({ error: 'User not found' })
      };
    }
    
    // Generate ETag for caching
    const responseData = {
      profile: userProfile,
      analytics: userAnalytics,
      generatedAt: new Date().toISOString()
    };
    
    const etag = generateETag(responseData);
    
    // Check if client has cached version
    if (event.headers['If-None-Match'] === etag) {
      return {
        statusCode: 304,
        headers: {
          ...getCORSHeaders(),
          'ETag': etag,
          'Cache-Control': 'public, max-age=300'
        },
        body: ''
      };
    }
    
    const processingTime = Date.now() - startTime;
    
    return {
      statusCode: 200,
      headers: {
        ...getCORSHeaders(),
        'ETag': etag,
        'Cache-Control': 'public, max-age=300',
        'X-Processing-Time': processingTime.toString()
      },
      body: JSON.stringify(responseData)
    };
    
  } catch (error) {
    console.error('Handler error:', error);
    
    const processingTime = Date.now() - startTime;
    
    return {
      statusCode: 500,
      headers: {
        ...getCORSHeaders(),
        'X-Processing-Time': processingTime.toString()
      },
      body: JSON.stringify({ 
        error: 'Internal server error',
        requestId: context.awsRequestId
      })
    };
  }
};

async function getCachedConfig(): Promise<any> {
  const now = Date.now();
  
  if (cachedConfig && now < cacheExpiry) {
    return cachedConfig;
  }
  
  try {
    const result = await dynamodb.get({
      TableName: process.env.CONFIG_TABLE!,
      Key: { configKey: 'app-settings' }
    }).promise();
    
    cachedConfig = result.Item?.config || {};
    cacheExpiry = now + (5 * 60 * 1000); // Cache for 5 minutes
    
    return cachedConfig;
  } catch (error) {
    console.error('Failed to fetch config:', error);
    return {};
  }
}

async function getUserProfile(userId: string): Promise<UserProfile | null> {
  try {
    const result = await dynamodb.get({
      TableName: process.env.USERS_TABLE!,
      Key: { userId },
      ProjectionExpression: 'userId, preferences, lastUpdated'
    }).promise();
    
    return result.Item as UserProfile || null;
  } catch (error) {
    console.error('Failed to fetch user profile:', error);
    throw error;
  }
}

async function getUserAnalytics(userId: string, retentionDays: number = 30): Promise<any> {
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - retentionDays);
  
  try {
    const result = await dynamodb.query({
      TableName: process.env.ANALYTICS_TABLE!,
      KeyConditionExpression: 'userId = :userId AND #timestamp >= :cutoff',
      ExpressionAttributeNames: {
        '#timestamp': 'timestamp'
      },
      ExpressionAttributeValues: {
        ':userId': userId,
        ':cutoff': cutoffDate.toISOString()
      },
      ScanIndexForward: false,
      Limit: 100
    }).promise();
    
    return {
      events: result.Items || [],
      count: result.Count || 0
    };
  } catch (error) {
    console.error('Failed to fetch user analytics:', error);
    return { events: [], count: 0 };
  }
}

function generateETag(data: any): string {
  const hash = createHash('md5');
  hash.update(JSON.stringify(data));
  return `"${hash.digest('hex')}"`;
}

function getCORSHeaders(): Record<string, string> {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,If-None-Match',
    'Access-Control-Allow-Methods': 'GET,OPTIONS',
    'Content-Type': 'application/json'
  };
}
```

## Key Tools and Implementation

### Performance Monitoring and Optimization
- **APM Solutions**: New Relic, AppDynamics, or cloud-native application monitoring
- **Database Monitoring**: DataDog Database Monitoring, SolarWinds, or database-specific tools
- **Content Optimization**: ImageOptim, WebP conversion, or content optimization services
- **Performance Testing**: JMeter, LoadRunner, or cloud-native load testing services

### Caching and Content Delivery
- **Application Caches**: Redis, Memcached, or cloud-native caching services
- **Database Caches**: Query result caching, connection pooling
- **CDN Services**: CloudFront, CloudFlare, or content delivery networks
- **Edge Computing**: Lambda@Edge, CloudFlare Workers, or edge computing platforms

### Load Testing and Optimization
- **K6**: Modern load testing tool with JavaScript
- **Artillery**: Modern, powerful toolkit for load testing
- **Gatling**: High-performance load testing framework
- **AWS Load Testing Solution**: Cloud-native load testing

## Performance Anti-Patterns and Solutions

### Anti-Pattern: Premature Optimization
**Problem**: Optimizing for theoretical performance scenarios rather than actual usage patterns
**Solution**: Data-driven optimization based on real metrics

```python
# Example: Performance Profiling and Optimization
import cProfile
import pstats
import time
from functools import wraps
from typing import Dict, List
import asyncio

class PerformanceProfiler:
    def __init__(self):
        self.profiles: Dict[str, List[float]] = {}
        self.slow_queries: List[dict] = []
    
    def profile_function(self, threshold_ms: float = 100):
        """Decorator to profile function performance"""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                
                # Profile the function
                profiler = cProfile.Profile()
                profiler.enable()
                
                try:
                    result = await func(*args, **kwargs)
                finally:
                    profiler.disable()
                
                end_time = time.perf_counter()
                duration_ms = (end_time - start_time) * 1000
                
                # Record performance data
                func_name = f"{func.__module__}.{func.__name__}"
                if func_name not in self.profiles:
                    self.profiles[func_name] = []
                
                self.profiles[func_name].append(duration_ms)
                
                # Log slow operations
                if duration_ms > threshold_ms:
                    stats = pstats.Stats(profiler)
                    stats.sort_stats('cumulative')
                    
                    self.slow_queries.append({
                        'function': func_name,
                        'duration_ms': duration_ms,
                        'timestamp': time.time(),
                        'args_size': len(str(args)),
                        'kwargs_size': len(str(kwargs))
                    })
                
                return result
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                
                profiler = cProfile.Profile()
                profiler.enable()
                
                try:
                    result = func(*args, **kwargs)
                finally:
                    profiler.disable()
                
                end_time = time.perf_counter()
                duration_ms = (end_time - start_time) * 1000
                
                func_name = f"{func.__module__}.{func.__name__}"
                if func_name not in self.profiles:
                    self.profiles[func_name] = []
                
                self.profiles[func_name].append(duration_ms)
                
                if duration_ms > threshold_ms:
                    self.slow_queries.append({
                        'function': func_name,
                        'duration_ms': duration_ms,
                        'timestamp': time.time()
                    })
                
                return result
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator
    
    def get_performance_report(self) -> dict:
        """Generate performance report"""
        report = {}
        
        for func_name, times in self.profiles.items():
            if times:
                report[func_name] = {
                    'call_count': len(times),
                    'avg_duration_ms': sum(times) / len(times),
                    'min_duration_ms': min(times),
                    'max_duration_ms': max(times),
                    'p95_duration_ms': self._percentile(times, 95),
                    'p99_duration_ms': self._percentile(times, 99)
                }
        
        return {
            'function_stats': report,
            'slow_queries': sorted(self.slow_queries, 
                                 key=lambda x: x['duration_ms'], 
                                 reverse=True)[:10]
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data"""
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]

# Usage
profiler = PerformanceProfiler()

@profiler.profile_function(threshold_ms=50)
async def expensive_database_operation(query: str, params: dict):
    # Simulate database operation
    await asyncio.sleep(0.1)
    return {"result": "data"}

@profiler.profile_function(threshold_ms=10)
def cpu_intensive_operation(data_size: int):
    # Simulate CPU-intensive work
    result = sum(i * i for i in range(data_size))
    return result
```

## Performance Maturity Assessment

### Level 1: Basic Performance (Reactive)
- Basic monitoring and alerting
- Manual performance testing
- Single-region deployment
- Limited caching strategies

### Level 2: Managed Performance (Proactive)
- Automated performance testing in CI/CD
- Multi-tier caching implementation
- Basic auto-scaling capabilities
- Performance budgets and SLOs

### Level 3: Advanced Performance (Optimized)
- Real-time performance optimization
- Advanced caching and CDN strategies
- Predictive scaling and capacity planning
- Comprehensive performance monitoring

### Level 4: Expert Performance (Predictive)
- AI-driven performance optimization
- Self-tuning systems and algorithms
- Global performance optimization
- Continuous performance innovation

## Implementation Strategy

Begin with basic performance monitoring and caching, then progressively implement advanced optimization techniques and architectural patterns.

### Phase 1: Foundation (Months 1-3)
1. **Performance Monitoring**: Implement APM and basic metrics
2. **Caching Layer**: Add Redis/Memcached for application caching
3. **Database Optimization**: Basic indexing and query optimization
4. **CDN Implementation**: Set up content delivery network

### Phase 2: Enhancement (Months 4-6)
1. **Auto-scaling**: Implement horizontal and vertical scaling
2. **Load Balancing**: Advanced load balancing strategies
3. **Performance Testing**: Automated performance testing in CI/CD
4. **Edge Computing**: Deploy edge functions and optimization

### Phase 3: Optimization (Months 7-12)
1. **Advanced Caching**: Multi-tier caching with invalidation strategies
2. **Microservices**: Service mesh and advanced routing
3. **Predictive Scaling**: ML-based capacity planning
4. **Global Optimization**: Multi-region performance optimization

### Success Metrics
- **Response Time**: P95 and P99 latency measurements
- **Throughput**: Requests per second and transaction volume
- **Resource Utilization**: CPU, memory, and network efficiency
- **User Experience**: Core Web Vitals and user satisfaction scores
- **Cost Efficiency**: Performance per dollar spent