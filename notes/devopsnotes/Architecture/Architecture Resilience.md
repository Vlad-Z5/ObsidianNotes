# Architecture Resilience

## Core Concepts

Resilience architecture is the ability of a system to recover quickly from failures and continue to operate or return to operation as soon as possible. It encompasses fault tolerance, graceful degradation, and the ability to handle unexpected loads and failures.

### Fault Tolerance Patterns

#### Circuit Breaker Pattern

**Definition:** A design pattern that prevents an application from repeatedly trying to execute an operation that's likely to fail, allowing it to continue without waiting for the fault to be resolved.

**States:**
- **Closed:** Normal operation, requests pass through
- **Open:** Failing fast, requests immediately return with error
- **Half-Open:** Testing if the service has recovered

**Implementation Example:**
```python
import time
import threading
from enum import Enum
from typing import Callable, Any, Dict
from dataclasses import dataclass
import logging

class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5
    success_threshold: int = 3
    timeout: float = 60.0
    expected_exception: tuple = (Exception,)

class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open"""
    pass

class CircuitBreaker:
    """Production-ready circuit breaker implementation"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator for circuit breaker"""
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        return wrapper
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        with self.lock:
            current_state = self._get_state()
            
            if current_state == CircuitState.OPEN:
                self.logger.warning(f"Circuit breaker OPEN - failing fast for {func.__name__}")
                raise CircuitBreakerError("Circuit breaker is OPEN")
            
            if current_state == CircuitState.HALF_OPEN:
                return self._attempt_reset(func, *args, **kwargs)
            
            # CLOSED state - normal operation
            return self._execute_call(func, *args, **kwargs)
    
    def _get_state(self) -> CircuitState:
        """Get current state, handling transitions"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                self.logger.info("Circuit breaker transitioning to HALF_OPEN")
        
        return self.state
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return False
        
        return (time.time() - self.last_failure_time) >= self.config.timeout
    
    def _attempt_reset(self, func: Callable, *args, **kwargs) -> Any:
        """Attempt to reset circuit breaker in HALF_OPEN state"""
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception as e:
            self._on_failure()
            raise
    
    def _execute_call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function call in CLOSED state"""
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful execution"""
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.logger.info("Circuit breaker RESET to CLOSED")
    
    def _on_failure(self):
        """Handle failed execution"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            self.logger.error(f"Circuit breaker TRIPPED to OPEN after {self.failure_count} failures")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        with self.lock:
            return {
                'state': self.state.value,
                'failure_count': self.failure_count,
                'success_count': self.success_count,
                'last_failure_time': self.last_failure_time,
                'time_since_last_failure': (
                    time.time() - self.last_failure_time 
                    if self.last_failure_time else None
                )
            }

# Service integration example
class ExternalServiceClient:
    """Client with circuit breaker protection"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        
        # Configure circuit breakers for different endpoints
        self.circuit_breakers = {
            'payment': CircuitBreaker(CircuitBreakerConfig(
                failure_threshold=3,
                success_threshold=2,
                timeout=30.0,
                expected_exception=(requests.exceptions.RequestException,)
            )),
            'user': CircuitBreaker(CircuitBreakerConfig(
                failure_threshold=5,
                success_threshold=3,
                timeout=60.0,
                expected_exception=(requests.exceptions.RequestException,)
            ))
        }
    
    def get_user(self, user_id: str):
        """Get user with circuit breaker protection"""
        @self.circuit_breakers['user']
        def _get_user():
            response = self.session.get(
                f"{self.base_url}/users/{user_id}",
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        
        return _get_user()
    
    def process_payment(self, payment_data: dict):
        """Process payment with circuit breaker protection"""
        @self.circuit_breakers['payment']
        def _process_payment():
            response = self.session.post(
                f"{self.base_url}/payments",
                json=payment_data,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        
        return _process_payment()
    
    def get_health_status(self):
        """Get health status of all circuit breakers"""
        return {
            endpoint: breaker.get_stats()
            for endpoint, breaker in self.circuit_breakers.items()
        }
```

#### Retry Pattern with Exponential Backoff

**Definition:** Automatically retry failed operations with increasing delays between attempts to avoid overwhelming failing services.

**Implementation Example:**
```python
import time
import random
import logging
from typing import Callable, Any, List, Type
from dataclasses import dataclass
from functools import wraps

@dataclass
class RetryConfig:
    """Configuration for retry mechanism"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_multiplier: float = 2.0
    jitter: bool = True
    retryable_exceptions: tuple = (Exception,)

class RetryExhaustedError(Exception):
    """Raised when all retry attempts are exhausted"""
    def __init__(self, attempts: int, last_exception: Exception):
        self.attempts = attempts
        self.last_exception = last_exception
        super().__init__(f"Retry exhausted after {attempts} attempts. Last error: {last_exception}")

class RetryHandler:
    """Advanced retry handler with exponential backoff and jitter"""
    
    def __init__(self, config: RetryConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator for retry functionality"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.execute(func, *args, **kwargs)
        return wrapper
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic"""
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                self.logger.debug(f"Attempting {func.__name__} (attempt {attempt}/{self.config.max_attempts})")
                result = func(*args, **kwargs)
                
                if attempt > 1:
                    self.logger.info(f"{func.__name__} succeeded on attempt {attempt}")
                
                return result
                
            except self.config.retryable_exceptions as e:
                last_exception = e
                
                if attempt == self.config.max_attempts:
                    self.logger.error(f"{func.__name__} failed after {attempt} attempts: {e}")
                    break
                
                delay = self._calculate_delay(attempt)
                self.logger.warning(f"{func.__name__} failed on attempt {attempt}: {e}. Retrying in {delay:.2f}s")
                time.sleep(delay)
            
            except Exception as e:
                # Non-retryable exception
                self.logger.error(f"{func.__name__} failed with non-retryable exception: {e}")
                raise
        
        raise RetryExhaustedError(self.config.max_attempts, last_exception)
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and optional jitter"""
        delay = self.config.base_delay * (self.config.exponential_multiplier ** (attempt - 1))
        delay = min(delay, self.config.max_delay)
        
        if self.config.jitter:
            # Add random jitter to prevent thundering herd
            jitter_range = delay * 0.1
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)

# Combine retry with circuit breaker
class ResilientServiceClient:
    """Service client with both retry and circuit breaker"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        
        # Configure retry handlers
        self.retry_handlers = {
            'critical': RetryHandler(RetryConfig(
                max_attempts=5,
                base_delay=0.5,
                max_delay=30.0,
                exponential_multiplier=2.0,
                jitter=True,
                retryable_exceptions=(
                    requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout,
                    requests.exceptions.HTTPError
                )
            )),
            'normal': RetryHandler(RetryConfig(
                max_attempts=3,
                base_delay=1.0,
                max_delay=10.0,
                exponential_multiplier=2.0,
                jitter=True,
                retryable_exceptions=(
                    requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout
                )
            ))
        }
        
        # Circuit breaker from previous example
        self.circuit_breaker = CircuitBreaker(CircuitBreakerConfig(
            failure_threshold=5,
            success_threshold=3,
            timeout=60.0
        ))
    
    def get_critical_data(self, data_id: str):
        """Get critical data with aggressive retry and circuit breaker"""
        @self.circuit_breaker
        @self.retry_handlers['critical']
        def _get_data():
            response = self.session.get(
                f"{self.base_url}/critical-data/{data_id}",
                timeout=5
            )
            if response.status_code >= 500:
                raise requests.exceptions.HTTPError(f"Server error: {response.status_code}")
            response.raise_for_status()
            return response.json()
        
        return _get_data()
    
    def get_user_preferences(self, user_id: str):
        """Get user preferences with normal retry policy"""
        @self.circuit_breaker
        @self.retry_handlers['normal']
        def _get_preferences():
            response = self.session.get(
                f"{self.base_url}/users/{user_id}/preferences",
                timeout=3
            )
            response.raise_for_status()
            return response.json()
        
        return _get_preferences()
```

#### Bulkhead Pattern

**Definition:** Isolate critical resources to prevent failures in one part of the system from cascading to other parts.

**Implementation Example:**
```python
import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor, Future, TimeoutError
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass
from enum import Enum

class BulkheadType(Enum):
    THREAD_POOL = "thread_pool"
    SEMAPHORE = "semaphore"
    RATE_LIMIT = "rate_limit"

@dataclass
class BulkheadConfig:
    """Configuration for bulkhead isolation"""
    max_concurrent: int = 10
    queue_size: int = 100
    timeout: float = 30.0
    bulkhead_type: BulkheadType = BulkheadType.THREAD_POOL

class BulkheadRejectedError(Exception):
    """Raised when bulkhead rejects execution"""
    pass

class ThreadPoolBulkhead:
    """Thread pool-based bulkhead for compute isolation"""
    
    def __init__(self, config: BulkheadConfig):
        self.config = config
        self.executor = ThreadPoolExecutor(
            max_workers=config.max_concurrent,
            thread_name_prefix="bulkhead"
        )
        self.active_tasks = 0
        self.rejected_tasks = 0
        self.completed_tasks = 0
        self.lock = threading.Lock()
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function in isolated thread pool"""
        with self.lock:
            if self.active_tasks >= self.config.max_concurrent:
                self.rejected_tasks += 1
                raise BulkheadRejectedError("Thread pool bulkhead at capacity")
            
            self.active_tasks += 1
        
        try:
            future = self.executor.submit(func, *args, **kwargs)
            result = future.result(timeout=self.config.timeout)
            
            with self.lock:
                self.completed_tasks += 1
            
            return result
            
        except TimeoutError:
            future.cancel()
            raise TimeoutError(f"Execution timed out after {self.config.timeout}s")
        
        finally:
            with self.lock:
                self.active_tasks -= 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get bulkhead statistics"""
        with self.lock:
            return {
                'max_concurrent': self.config.max_concurrent,
                'active_tasks': self.active_tasks,
                'completed_tasks': self.completed_tasks,
                'rejected_tasks': self.rejected_tasks,
                'utilization': self.active_tasks / self.config.max_concurrent
            }
    
    def shutdown(self):
        """Shutdown the bulkhead"""
        self.executor.shutdown(wait=True)

class SemaphoreBulkhead:
    """Semaphore-based bulkhead for resource limiting"""
    
    def __init__(self, config: BulkheadConfig):
        self.config = config
        self.semaphore = threading.Semaphore(config.max_concurrent)
        self.active_count = 0
        self.total_acquired = 0
        self.total_rejected = 0
        self.lock = threading.Lock()
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with semaphore protection"""
        acquired = self.semaphore.acquire(blocking=False)
        
        if not acquired:
            with self.lock:
                self.total_rejected += 1
            raise BulkheadRejectedError("Semaphore bulkhead at capacity")
        
        try:
            with self.lock:
                self.active_count += 1
                self.total_acquired += 1
            
            return func(*args, **kwargs)
            
        finally:
            with self.lock:
                self.active_count -= 1
            self.semaphore.release()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get semaphore statistics"""
        with self.lock:
            return {
                'max_concurrent': self.config.max_concurrent,
                'active_count': self.active_count,
                'total_acquired': self.total_acquired,
                'total_rejected': self.total_rejected,
                'available_permits': self.semaphore._value
            }

class RateLimitBulkhead:
    """Rate limiting bulkhead for throughput control"""
    
    def __init__(self, config: BulkheadConfig):
        self.config = config
        self.requests = []
        self.window_size = 60.0  # 1 minute window
        self.lock = threading.Lock()
        self.total_requests = 0
        self.rejected_requests = 0
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with rate limiting"""
        current_time = time.time()
        
        with self.lock:
            # Clean old requests outside window
            self.requests = [req_time for req_time in self.requests 
                           if current_time - req_time < self.window_size]
            
            if len(self.requests) >= self.config.max_concurrent:
                self.rejected_requests += 1
                raise BulkheadRejectedError("Rate limit bulkhead exceeded")
            
            self.requests.append(current_time)
            self.total_requests += 1
        
        return func(*args, **kwargs)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limit statistics"""
        current_time = time.time()
        
        with self.lock:
            # Clean old requests for accurate stats
            self.requests = [req_time for req_time in self.requests 
                           if current_time - req_time < self.window_size]
            
            return {
                'max_rate': self.config.max_concurrent,
                'current_rate': len(self.requests),
                'window_size': self.window_size,
                'total_requests': self.total_requests,
                'rejected_requests': self.rejected_requests,
                'utilization': len(self.requests) / self.config.max_concurrent
            }

class BulkheadManager:
    """Manager for multiple bulkheads"""
    
    def __init__(self):
        self.bulkheads: Dict[str, Any] = {}
    
    def create_bulkhead(self, name: str, config: BulkheadConfig):
        """Create a new bulkhead"""
        if config.bulkhead_type == BulkheadType.THREAD_POOL:
            bulkhead = ThreadPoolBulkhead(config)
        elif config.bulkhead_type == BulkheadType.SEMAPHORE:
            bulkhead = SemaphoreBulkhead(config)
        elif config.bulkhead_type == BulkheadType.RATE_LIMIT:
            bulkhead = RateLimitBulkhead(config)
        else:
            raise ValueError(f"Unknown bulkhead type: {config.bulkhead_type}")
        
        self.bulkheads[name] = bulkhead
        return bulkhead
    
    def get_bulkhead(self, name: str):
        """Get bulkhead by name"""
        return self.bulkheads.get(name)
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all bulkheads"""
        return {
            name: bulkhead.get_stats()
            for name, bulkhead in self.bulkheads.items()
        }
    
    def shutdown_all(self):
        """Shutdown all bulkheads"""
        for bulkhead in self.bulkheads.values():
            if hasattr(bulkhead, 'shutdown'):
                bulkhead.shutdown()

# Service with bulkhead isolation
class IsolatedServiceClient:
    """Service client with bulkhead isolation"""
    
    def __init__(self):
        self.manager = BulkheadManager()
        
        # Create different bulkheads for different operations
        self.manager.create_bulkhead('database', BulkheadConfig(
            max_concurrent=20,
            timeout=30.0,
            bulkhead_type=BulkheadType.THREAD_POOL
        ))
        
        self.manager.create_bulkhead('external_api', BulkheadConfig(
            max_concurrent=10,
            timeout=15.0,
            bulkhead_type=BulkheadType.SEMAPHORE
        ))
        
        self.manager.create_bulkhead('file_upload', BulkheadConfig(
            max_concurrent=5,
            bulkhead_type=BulkheadType.RATE_LIMIT
        ))
    
    def database_operation(self, query: str):
        """Database operation with thread pool isolation"""
        bulkhead = self.manager.get_bulkhead('database')
        
        def _execute_query():
            # Simulate database operation
            time.sleep(0.1)
            return f"Query result for: {query}"
        
        return bulkhead.execute(_execute_query)
    
    def external_api_call(self, endpoint: str):
        """External API call with semaphore isolation"""
        bulkhead = self.manager.get_bulkhead('external_api')
        
        def _api_call():
            # Simulate API call
            time.sleep(0.5)
            return f"API response from: {endpoint}"
        
        return bulkhead.execute(_api_call)
    
    def upload_file(self, file_data: bytes):
        """File upload with rate limiting"""
        bulkhead = self.manager.get_bulkhead('file_upload')
        
        def _upload():
            # Simulate file upload
            time.sleep(1.0)
            return f"Uploaded {len(file_data)} bytes"
        
        return bulkhead.execute(_upload)
    
    def get_health_status(self):
        """Get health status of all bulkheads"""
        return self.manager.get_all_stats()
```

### Graceful Degradation

**Definition:** The ability of a system to maintain limited functionality when part of the system fails, rather than failing completely.

**Implementation Example:**
```python
from typing import Any, Optional, Callable, Dict, List
from dataclasses import dataclass
from enum import Enum
import logging
import time
import json

class ServiceLevel(Enum):
    FULL = "full"
    DEGRADED = "degraded"
    MINIMAL = "minimal"
    UNAVAILABLE = "unavailable"

@dataclass
class FeatureFlag:
    """Configuration for feature toggles"""
    name: str
    enabled: bool = True
    service_level: ServiceLevel = ServiceLevel.FULL
    fallback_value: Any = None
    health_check: Optional[Callable] = None

class DegradationManager:
    """Manages graceful degradation of services"""
    
    def __init__(self):
        self.features: Dict[str, FeatureFlag] = {}
        self.service_health: Dict[str, ServiceLevel] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_feature(self, feature: FeatureFlag):
        """Register a feature for degradation management"""
        self.features[feature.name] = feature
        self.service_health[feature.name] = ServiceLevel.FULL
    
    def check_service_health(self, service_name: str) -> ServiceLevel:
        """Check health of a specific service"""
        feature = self.features.get(service_name)
        
        if not feature or not feature.enabled:
            return ServiceLevel.UNAVAILABLE
        
        if feature.health_check:
            try:
                health_result = feature.health_check()
                if health_result:
                    self.service_health[service_name] = ServiceLevel.FULL
                    return ServiceLevel.FULL
                else:
                    self.service_health[service_name] = ServiceLevel.DEGRADED
                    return ServiceLevel.DEGRADED
            except Exception as e:
                self.logger.warning(f"Health check failed for {service_name}: {e}")
                self.service_health[service_name] = ServiceLevel.MINIMAL
                return ServiceLevel.MINIMAL
        
        return self.service_health.get(service_name, ServiceLevel.FULL)
    
    def execute_with_degradation(self, service_name: str, primary_func: Callable, 
                                fallback_func: Optional[Callable] = None, 
                                default_value: Any = None) -> Any:
        """Execute function with graceful degradation"""
        health_level = self.check_service_health(service_name)
        feature = self.features.get(service_name)
        
        if health_level == ServiceLevel.UNAVAILABLE:
            self.logger.warning(f"Service {service_name} unavailable, using default")
            return default_value or (feature.fallback_value if feature else None)
        
        if health_level == ServiceLevel.FULL:
            try:
                return primary_func()
            except Exception as e:
                self.logger.error(f"Primary function failed for {service_name}: {e}")
                self.service_health[service_name] = ServiceLevel.DEGRADED
                health_level = ServiceLevel.DEGRADED
        
        if health_level in [ServiceLevel.DEGRADED, ServiceLevel.MINIMAL]:
            if fallback_func:
                try:
                    self.logger.info(f"Using fallback for {service_name}")
                    return fallback_func()
                except Exception as e:
                    self.logger.error(f"Fallback failed for {service_name}: {e}")
            
            self.logger.warning(f"Returning default value for {service_name}")
            return default_value or (feature.fallback_value if feature else None)

class ECommerceService:
    """E-commerce service with graceful degradation"""
    
    def __init__(self):
        self.degradation_manager = DegradationManager()
        self.cache = {}
        self._setup_features()
    
    def _setup_features(self):
        """Setup feature flags and health checks"""
        
        # Recommendation service
        self.degradation_manager.register_feature(FeatureFlag(
            name="recommendations",
            enabled=True,
            service_level=ServiceLevel.FULL,
            fallback_value=[],
            health_check=self._check_recommendation_service
        ))
        
        # Payment service
        self.degradation_manager.register_feature(FeatureFlag(
            name="payment",
            enabled=True,
            service_level=ServiceLevel.FULL,
            fallback_value=None,
            health_check=self._check_payment_service
        ))
        
        # Inventory service
        self.degradation_manager.register_feature(FeatureFlag(
            name="inventory",
            enabled=True,
            service_level=ServiceLevel.FULL,
            fallback_value={"available": False, "stock": 0},
            health_check=self._check_inventory_service
        ))
        
        # Search service
        self.degradation_manager.register_feature(FeatureFlag(
            name="search",
            enabled=True,
            service_level=ServiceLevel.FULL,
            fallback_value=[],
            health_check=self._check_search_service
        ))
    
    def _check_recommendation_service(self) -> bool:
        """Health check for recommendation service"""
        try:
            # Simulate health check
            import random
            return random.random() > 0.3  # 70% healthy
        except:
            return False
    
    def _check_payment_service(self) -> bool:
        """Health check for payment service"""
        try:
            # Critical service - should be more reliable
            import random
            return random.random() > 0.1  # 90% healthy
        except:
            return False
    
    def _check_inventory_service(self) -> bool:
        """Health check for inventory service"""
        try:
            import random
            return random.random() > 0.2  # 80% healthy
        except:
            return False
    
    def _check_search_service(self) -> bool:
        """Health check for search service"""
        try:
            import random
            return random.random() > 0.4  # 60% healthy
        except:
            return False
    
    def get_product_recommendations(self, user_id: str, product_id: str) -> List[Dict]:
        """Get product recommendations with graceful degradation"""
        
        def primary_recommendations():
            # Simulate ML-based recommendations
            return [
                {"id": "rec1", "title": "Smart Watch", "score": 0.95},
                {"id": "rec2", "title": "Wireless Headphones", "score": 0.87},
                {"id": "rec3", "title": "Phone Case", "score": 0.76}
            ]
        
        def fallback_recommendations():
            # Simple rule-based recommendations
            return [
                {"id": "pop1", "title": "Popular Item 1", "score": 0.6},
                {"id": "pop2", "title": "Popular Item 2", "score": 0.5}
            ]
        
        return self.degradation_manager.execute_with_degradation(
            service_name="recommendations",
            primary_func=primary_recommendations,
            fallback_func=fallback_recommendations,
            default_value=[]
        )
    
    def process_payment(self, payment_data: Dict) -> Dict:
        """Process payment with graceful degradation"""
        
        def primary_payment():
            # Full payment processing
            return {
                "status": "success",
                "transaction_id": "txn_123456",
                "method": "credit_card"
            }
        
        def fallback_payment():
            # Queue payment for later processing
            return {
                "status": "queued",
                "message": "Payment queued for processing",
                "queue_id": "queue_789"
            }
        
        result = self.degradation_manager.execute_with_degradation(
            service_name="payment",
            primary_func=primary_payment,
            fallback_func=fallback_payment,
            default_value={"status": "failed", "message": "Payment service unavailable"}
        )
        
        return result
    
    def check_inventory(self, product_id: str) -> Dict:
        """Check inventory with graceful degradation"""
        
        def primary_inventory():
            # Real-time inventory check
            return {
                "available": True,
                "stock": 15,
                "last_updated": time.time()
            }
        
        def fallback_inventory():
            # Cached inventory (may be stale)
            cached_data = self.cache.get(f"inventory_{product_id}")
            if cached_data:
                cached_data["source"] = "cache"
                return cached_data
            
            return {
                "available": True,  # Optimistic assumption
                "stock": 1,
                "source": "estimated"
            }
        
        return self.degradation_manager.execute_with_degradation(
            service_name="inventory",
            primary_func=primary_inventory,
            fallback_func=fallback_inventory,
            default_value={"available": False, "stock": 0, "source": "unavailable"}
        )
    
    def search_products(self, query: str) -> List[Dict]:
        """Search products with graceful degradation"""
        
        def primary_search():
            # Elasticsearch-based search
            return [
                {"id": "search1", "title": f"Best match for {query}", "relevance": 0.95},
                {"id": "search2", "title": f"Good match for {query}", "relevance": 0.78}
            ]
        
        def fallback_search():
            # Simple text matching from cache
            return [
                {"id": "simple1", "title": f"Simple match: {query}", "relevance": 0.5}
            ]
        
        return self.degradation_manager.execute_with_degradation(
            service_name="search",
            primary_func=primary_search,
            fallback_func=fallback_search,
            default_value=[]
        )
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get overall service status"""
        status = {}
        
        for service_name in self.degradation_manager.features.keys():
            health_level = self.degradation_manager.check_service_health(service_name)
            status[service_name] = {
                "health": health_level.value,
                "enabled": self.degradation_manager.features[service_name].enabled
            }
        
        # Overall system health
        all_levels = [
            self.degradation_manager.service_health[service] 
            for service in self.degradation_manager.service_health
        ]
        
        if all(level == ServiceLevel.FULL for level in all_levels):
            overall_status = "healthy"
        elif any(level == ServiceLevel.UNAVAILABLE for level in all_levels):
            overall_status = "degraded"
        else:
            overall_status = "partial"
        
        return {
            "overall_status": overall_status,
            "services": status,
            "timestamp": time.time()
        }

# Usage example
if __name__ == "__main__":
    service = ECommerceService()
    
    # Test graceful degradation
    print("=== Product Recommendations ===")
    recommendations = service.get_product_recommendations("user123", "product456")
    print(json.dumps(recommendations, indent=2))
    
    print("\n=== Payment Processing ===")
    payment_result = service.process_payment({"amount": 99.99, "currency": "USD"})
    print(json.dumps(payment_result, indent=2))
    
    print("\n=== Inventory Check ===")
    inventory = service.check_inventory("product456")
    print(json.dumps(inventory, indent=2))
    
    print("\n=== Product Search ===")
    search_results = service.search_products("wireless headphones")
    print(json.dumps(search_results, indent=2))
    
    print("\n=== Service Status ===")
    status = service.get_service_status()
    print(json.dumps(status, indent=2))
```

### Chaos Engineering

**Definition:** The discipline of experimenting on a system to build confidence in the system's capability to withstand turbulent conditions in production.

**Implementation Example:**
```python
import random
import time
import threading
import logging
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass
from enum import Enum
import psutil
import os

class ChaosType(Enum):
    NETWORK_LATENCY = "network_latency"
    NETWORK_FAILURE = "network_failure"
    CPU_STRESS = "cpu_stress"
    MEMORY_STRESS = "memory_stress"
    DISK_STRESS = "disk_stress"
    SERVICE_FAILURE = "service_failure"
    DATABASE_SLOWDOWN = "database_slowdown"

@dataclass
class ChaosExperiment:
    """Configuration for a chaos experiment"""
    name: str
    chaos_type: ChaosType
    probability: float = 0.1  # 10% chance
    duration: float = 60.0  # 60 seconds
    intensity: float = 0.5  # 50% intensity
    target_services: List[str] = None
    enabled: bool = True

class ChaosMonkey:
    """Chaos engineering implementation"""
    
    def __init__(self):
        self.experiments: Dict[str, ChaosExperiment] = {}
        self.active_chaos: Dict[str, Dict] = {}
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
    
    def register_experiment(self, experiment: ChaosExperiment):
        """Register a chaos experiment"""
        self.experiments[experiment.name] = experiment
        self.logger.info(f"Registered chaos experiment: {experiment.name}")
    
    def start_chaos_monkey(self, interval: float = 30.0):
        """Start the chaos monkey"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(
            target=self._chaos_loop,
            args=(interval,),
            daemon=True
        )
        self.thread.start()
        self.logger.info("Chaos Monkey started")
    
    def stop_chaos_monkey(self):
        """Stop the chaos monkey"""
        self.running = False
        if self.thread:
            self.thread.join()
        self._cleanup_all_chaos()
        self.logger.info("Chaos Monkey stopped")
    
    def _chaos_loop(self, interval: float):
        """Main chaos monkey loop"""
        while self.running:
            try:
                self._execute_chaos_experiments()
                time.sleep(interval)
            except Exception as e:
                self.logger.error(f"Error in chaos loop: {e}")
    
    def _execute_chaos_experiments(self):
        """Execute chaos experiments based on probability"""
        for experiment in self.experiments.values():
            if not experiment.enabled:
                continue
            
            if random.random() < experiment.probability:
                self._trigger_chaos(experiment)
    
    def _trigger_chaos(self, experiment: ChaosExperiment):
        """Trigger a specific chaos experiment"""
        with self.lock:
            if experiment.name in self.active_chaos:
                return  # Already running
            
            self.logger.warning(f"Triggering chaos experiment: {experiment.name}")
            
            chaos_info = {
                'experiment': experiment,
                'start_time': time.time(),
                'cleanup_func': None
            }
            
            if experiment.chaos_type == ChaosType.NETWORK_LATENCY:
                cleanup_func = self._inject_network_latency(experiment)
            elif experiment.chaos_type == ChaosType.NETWORK_FAILURE:
                cleanup_func = self._inject_network_failure(experiment)
            elif experiment.chaos_type == ChaosType.CPU_STRESS:
                cleanup_func = self._inject_cpu_stress(experiment)
            elif experiment.chaos_type == ChaosType.MEMORY_STRESS:
                cleanup_func = self._inject_memory_stress(experiment)
            elif experiment.chaos_type == ChaosType.SERVICE_FAILURE:
                cleanup_func = self._inject_service_failure(experiment)
            elif experiment.chaos_type == ChaosType.DATABASE_SLOWDOWN:
                cleanup_func = self._inject_database_slowdown(experiment)
            
            chaos_info['cleanup_func'] = cleanup_func
            self.active_chaos[experiment.name] = chaos_info
            
            # Schedule cleanup
            cleanup_timer = threading.Timer(
                experiment.duration,
                self._cleanup_chaos,
                args=(experiment.name,)
            )
            cleanup_timer.start()
    
    def _inject_network_latency(self, experiment: ChaosExperiment) -> Callable:
        """Inject network latency"""
        original_delay = getattr(NetworkSimulator, 'delay', 0)
        NetworkSimulator.delay = experiment.intensity * 2.0  # Up to 2 seconds
        
        self.logger.warning(f"Injected network latency: {NetworkSimulator.delay}s")
        
        def cleanup():
            NetworkSimulator.delay = original_delay
            self.logger.info("Network latency chaos cleaned up")
        
        return cleanup
    
    def _inject_network_failure(self, experiment: ChaosExperiment) -> Callable:
        """Inject network failures"""
        original_failure_rate = getattr(NetworkSimulator, 'failure_rate', 0)
        NetworkSimulator.failure_rate = experiment.intensity
        
        self.logger.warning(f"Injected network failures: {NetworkSimulator.failure_rate * 100}%")
        
        def cleanup():
            NetworkSimulator.failure_rate = original_failure_rate
            self.logger.info("Network failure chaos cleaned up")
        
        return cleanup
    
    def _inject_cpu_stress(self, experiment: ChaosExperiment) -> Callable:
        """Inject CPU stress"""
        stress_threads = []
        num_threads = int(psutil.cpu_count() * experiment.intensity)
        
        def cpu_stress():
            end_time = time.time() + experiment.duration
            while time.time() < end_time:
                # Burn CPU cycles
                sum(i * i for i in range(1000))
        
        for _ in range(num_threads):
            thread = threading.Thread(target=cpu_stress, daemon=True)
            thread.start()
            stress_threads.append(thread)
        
        self.logger.warning(f"Injected CPU stress with {num_threads} threads")
        
        def cleanup():
            # Threads will naturally die when the function ends
            self.logger.info("CPU stress chaos cleaned up")
        
        return cleanup
    
    def _inject_memory_stress(self, experiment: ChaosExperiment) -> Callable:
        """Inject memory stress"""
        memory_hogs = []
        
        # Allocate memory based on intensity
        available_memory = psutil.virtual_memory().available
        memory_to_allocate = int(available_memory * experiment.intensity * 0.1)  # 10% of intensity
        chunk_size = 1024 * 1024  # 1MB chunks
        
        try:
            for _ in range(memory_to_allocate // chunk_size):
                memory_hogs.append(bytearray(chunk_size))
        except MemoryError:
            self.logger.warning("Memory allocation failed - system protection kicked in")
        
        self.logger.warning(f"Injected memory stress: ~{len(memory_hogs)}MB allocated")
        
        def cleanup():
            memory_hogs.clear()
            self.logger.info("Memory stress chaos cleaned up")
        
        return cleanup
    
    def _inject_service_failure(self, experiment: ChaosExperiment) -> Callable:
        """Inject service failures"""
        if experiment.target_services:
            for service_name in experiment.target_services:
                ServiceFailureSimulator.set_failure_rate(service_name, experiment.intensity)
        
        self.logger.warning(f"Injected service failures for: {experiment.target_services}")
        
        def cleanup():
            if experiment.target_services:
                for service_name in experiment.target_services:
                    ServiceFailureSimulator.set_failure_rate(service_name, 0.0)
            self.logger.info("Service failure chaos cleaned up")
        
        return cleanup
    
    def _inject_database_slowdown(self, experiment: ChaosExperiment) -> Callable:
        """Inject database slowdown"""
        original_delay = getattr(DatabaseSimulator, 'query_delay', 0)
        DatabaseSimulator.query_delay = experiment.intensity * 5.0  # Up to 5 seconds
        
        self.logger.warning(f"Injected database slowdown: {DatabaseSimulator.query_delay}s")
        
        def cleanup():
            DatabaseSimulator.query_delay = original_delay
            self.logger.info("Database slowdown chaos cleaned up")
        
        return cleanup
    
    def _cleanup_chaos(self, experiment_name: str):
        """Cleanup specific chaos experiment"""
        with self.lock:
            if experiment_name in self.active_chaos:
                chaos_info = self.active_chaos[experiment_name]
                if chaos_info['cleanup_func']:
                    chaos_info['cleanup_func']()
                
                del self.active_chaos[experiment_name]
                self.logger.info(f"Cleaned up chaos experiment: {experiment_name}")
    
    def _cleanup_all_chaos(self):
        """Cleanup all active chaos experiments"""
        with self.lock:
            for experiment_name in list(self.active_chaos.keys()):
                self._cleanup_chaos(experiment_name)
    
    def get_active_experiments(self) -> Dict[str, Dict]:
        """Get currently active chaos experiments"""
        with self.lock:
            return {
                name: {
                    'experiment_name': chaos_info['experiment'].name,
                    'chaos_type': chaos_info['experiment'].chaos_type.value,
                    'start_time': chaos_info['start_time'],
                    'duration': chaos_info['experiment'].duration,
                    'elapsed': time.time() - chaos_info['start_time']
                }
                for name, chaos_info in self.active_chaos.items()
            }

# Simulator classes for chaos injection
class NetworkSimulator:
    """Simulates network conditions"""
    delay = 0.0
    failure_rate = 0.0
    
    @classmethod
    def simulate_request(cls, func: Callable, *args, **kwargs):
        """Simulate network request with chaos"""
        if random.random() < cls.failure_rate:
            raise ConnectionError("Simulated network failure")
        
        if cls.delay > 0:
            time.sleep(cls.delay)
        
        return func(*args, **kwargs)

class ServiceFailureSimulator:
    """Simulates service failures"""
    failure_rates: Dict[str, float] = {}
    
    @classmethod
    def set_failure_rate(cls, service_name: str, failure_rate: float):
        """Set failure rate for a service"""
        cls.failure_rates[service_name] = failure_rate
    
    @classmethod
    def simulate_service_call(cls, service_name: str, func: Callable, *args, **kwargs):
        """Simulate service call with potential failure"""
        failure_rate = cls.failure_rates.get(service_name, 0.0)
        
        if random.random() < failure_rate:
            raise Exception(f"Simulated failure in {service_name}")
        
        return func(*args, **kwargs)

class DatabaseSimulator:
    """Simulates database conditions"""
    query_delay = 0.0
    
    @classmethod
    def simulate_query(cls, func: Callable, *args, **kwargs):
        """Simulate database query with chaos"""
        if cls.query_delay > 0:
            time.sleep(cls.query_delay)
        
        return func(*args, **kwargs)

# Example usage
if __name__ == "__main__":
    # Setup chaos monkey
    chaos_monkey = ChaosMonkey()
    
    # Register experiments
    chaos_monkey.register_experiment(ChaosExperiment(
        name="network_latency_test",
        chaos_type=ChaosType.NETWORK_LATENCY,
        probability=0.3,
        duration=30.0,
        intensity=0.5
    ))
    
    chaos_monkey.register_experiment(ChaosExperiment(
        name="service_failure_test",
        chaos_type=ChaosType.SERVICE_FAILURE,
        probability=0.2,
        duration=45.0,
        intensity=0.1,
        target_services=["payment", "inventory"]
    ))
    
    chaos_monkey.register_experiment(ChaosExperiment(
        name="cpu_stress_test",
        chaos_type=ChaosType.CPU_STRESS,
        probability=0.1,
        duration=60.0,
        intensity=0.3
    ))
    
    # Start chaos monkey
    chaos_monkey.start_chaos_monkey(interval=20.0)
    
    try:
        # Let it run for a while
        time.sleep(300)  # 5 minutes
    finally:
        chaos_monkey.stop_chaos_monkey()
```

This comprehensive Architecture Resilience guide covers fault tolerance patterns (Circuit Breaker, Retry with Exponential Backoff, Bulkhead), graceful degradation strategies, and chaos engineering practices with production-ready code examples that demonstrate how to build resilient systems capable of handling failures gracefully.

Now proceeding with Architecture Security-First.md to continue the comprehensive architecture documentation...