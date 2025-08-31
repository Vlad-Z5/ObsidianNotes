# APM Custom Instrumentation

Custom instrumentation enables detailed monitoring of specific application components, business logic, and custom workflows that aren't covered by automatic instrumentation. This guide covers manual instrumentation techniques, custom metrics creation, business transaction tracking, and enterprise-grade instrumentation patterns for various programming languages and frameworks.

## Custom Instrumentation Framework

### Multi-Language Instrumentation Library

```python
import time
import threading
import functools
import logging
import json
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from contextlib import contextmanager
from abc import ABC, abstractmethod
import uuid
import inspect

@dataclass
class CustomSpan:
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    operation_name: str
    service_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "ok"
    error: Optional[str] = None

@dataclass
class CustomMetric:
    name: str
    value: Union[int, float]
    metric_type: str  # counter, gauge, histogram, timer
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    unit: str = ""

class InstrumentationContext:
    """Thread-local context for tracking active spans"""
    
    def __init__(self):
        self._local = threading.local()
    
    def get_active_span(self) -> Optional[CustomSpan]:
        """Get currently active span"""
        return getattr(self._local, 'active_span', None)
    
    def set_active_span(self, span: Optional[CustomSpan]):
        """Set active span"""
        self._local.active_span = span
    
    def get_trace_id(self) -> Optional[str]:
        """Get current trace ID"""
        active_span = self.get_active_span()
        return active_span.trace_id if active_span else None

class CustomInstrumentationCollector:
    """Collect and manage custom instrumentation data"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.context = InstrumentationContext()
        self.spans_buffer = deque(maxlen=10000)
        self.metrics_buffer = deque(maxlen=50000)
        self.counters = defaultdict(int)
        self.gauges = {}
        self.timers = defaultdict(list)
        self.lock = threading.Lock()
        self.logger = logging.getLogger(f"custom_instrumentation_{service_name}")
        
        # Business transaction tracking
        self.business_transactions = {}
        self.user_journeys = defaultdict(list)
        
    def start_span(self, operation_name: str, parent_span: Optional[CustomSpan] = None,
                   tags: Dict[str, Any] = None) -> CustomSpan:
        """Start a new custom span"""
        
        # Generate IDs
        span_id = str(uuid.uuid4())[:8]
        
        if parent_span:
            trace_id = parent_span.trace_id
            parent_span_id = parent_span.span_id
        else:
            # Check for active span
            active_span = self.context.get_active_span()
            if active_span:
                trace_id = active_span.trace_id
                parent_span_id = active_span.span_id
            else:
                trace_id = str(uuid.uuid4())[:16]
                parent_span_id = None
        
        span = CustomSpan(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            service_name=self.service_name,
            start_time=datetime.utcnow(),
            tags=tags or {}
        )
        
        # Set as active span
        self.context.set_active_span(span)
        
        return span
    
    def finish_span(self, span: CustomSpan, error: Exception = None):
        """Finish a custom span"""
        
        span.end_time = datetime.utcnow()
        span.duration_ms = (span.end_time - span.start_time).total_seconds() * 1000
        
        if error:
            span.status = "error"
            span.error = str(error)
            span.tags['error'] = True
            span.tags['error.kind'] = type(error).__name__
            
            # Add error log
            span.logs.append({
                'timestamp': datetime.utcnow().isoformat(),
                'level': 'error',
                'message': str(error),
                'event': 'error'
            })
        
        # Add to buffer
        with self.lock:
            self.spans_buffer.append(span)
        
        # Reset active span if this was the active one
        if self.context.get_active_span() == span:
            # Find parent span to set as active
            parent_span = None
            if span.parent_span_id:
                # In a real implementation, you'd track the span stack
                parent_span = None
            self.context.set_active_span(parent_span)
    
    def add_span_tag(self, span: CustomSpan, key: str, value: Any):
        """Add tag to span"""
        span.tags[key] = value
    
    def add_span_log(self, span: CustomSpan, message: str, level: str = "info", **kwargs):
        """Add log entry to span"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,
            'message': message,
            **kwargs
        }
        span.logs.append(log_entry)
    
    @contextmanager
    def trace(self, operation_name: str, tags: Dict[str, Any] = None):
        """Context manager for tracing operations"""
        
        span = self.start_span(operation_name, tags=tags)
        try:
            yield span
        except Exception as e:
            self.finish_span(span, error=e)
            raise
        else:
            self.finish_span(span)
    
    def increment_counter(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        """Increment a custom counter"""
        
        metric = CustomMetric(
            name=name,
            value=value,
            metric_type="counter",
            tags=tags or {}
        )
        
        with self.lock:
            self.counters[name] += value
            self.metrics_buffer.append(metric)
    
    def set_gauge(self, name: str, value: Union[int, float], tags: Dict[str, str] = None):
        """Set a gauge value"""
        
        metric = CustomMetric(
            name=name,
            value=value,
            metric_type="gauge",
            tags=tags or {}
        )
        
        with self.lock:
            self.gauges[name] = value
            self.metrics_buffer.append(metric)
    
    def record_timer(self, name: str, duration_ms: float, tags: Dict[str, str] = None):
        """Record a timing measurement"""
        
        metric = CustomMetric(
            name=name,
            value=duration_ms,
            metric_type="timer",
            tags=tags or {},
            unit="milliseconds"
        )
        
        with self.lock:
            self.timers[name].append(duration_ms)
            # Keep only recent 1000 measurements
            if len(self.timers[name]) > 1000:
                self.timers[name] = self.timers[name][-1000:]
            self.metrics_buffer.append(metric)
    
    def record_histogram(self, name: str, value: Union[int, float], tags: Dict[str, str] = None):
        """Record a histogram value"""
        
        metric = CustomMetric(
            name=name,
            value=value,
            metric_type="histogram",
            tags=tags or {}
        )
        
        with self.lock:
            self.metrics_buffer.append(metric)
    
    @contextmanager
    def time_operation(self, operation_name: str, tags: Dict[str, str] = None):
        """Time an operation and record as metric"""
        
        start_time = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.record_timer(f"{operation_name}_duration", duration_ms, tags)
    
    def track_business_transaction(self, transaction_type: str, transaction_id: str,
                                 user_id: str = None, amount: float = None, 
                                 currency: str = "USD", **kwargs):
        """Track business transaction"""
        
        transaction = {
            'transaction_id': transaction_id,
            'transaction_type': transaction_type,
            'user_id': user_id,
            'amount': amount,
            'currency': currency,
            'timestamp': datetime.utcnow().isoformat(),
            'trace_id': self.context.get_trace_id(),
            'custom_attributes': kwargs
        }
        
        self.business_transactions[transaction_id] = transaction
        
        # Record as metrics
        self.increment_counter(
            f"business_transaction_{transaction_type}",
            tags={'currency': currency, 'user_id': user_id}
        )
        
        if amount:
            self.record_histogram(
                f"business_transaction_amount_{transaction_type}",
                amount,
                tags={'currency': currency}
            )
    
    def track_user_journey_step(self, user_id: str, step_name: str, step_data: Dict[str, Any] = None):
        """Track user journey step"""
        
        journey_step = {
            'step_name': step_name,
            'timestamp': datetime.utcnow().isoformat(),
            'trace_id': self.context.get_trace_id(),
            'data': step_data or {}
        }
        
        self.user_journeys[user_id].append(journey_step)
        
        # Keep only recent 50 steps per user
        if len(self.user_journeys[user_id]) > 50:
            self.user_journeys[user_id] = self.user_journeys[user_id][-50:]
        
        # Record metric
        self.increment_counter(
            f"user_journey_step_{step_name}",
            tags={'user_id': user_id}
        )

# Decorators for Easy Instrumentation
class InstrumentationDecorators:
    """Decorators for easy custom instrumentation"""
    
    def __init__(self, collector: CustomInstrumentationCollector):
        self.collector = collector
    
    def trace_method(self, operation_name: str = None, tags: Dict[str, Any] = None):
        """Decorator to trace method execution"""
        
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Generate operation name if not provided
                op_name = operation_name or f"{func.__module__}.{func.__name__}"
                
                # Add function metadata as tags
                method_tags = {
                    'function.name': func.__name__,
                    'function.module': func.__module__,
                    **(tags or {})
                }
                
                with self.collector.trace(op_name, method_tags) as span:
                    # Add function arguments as tags (be careful with sensitive data)
                    if args:
                        span.tags['function.args_count'] = len(args)
                    
                    if kwargs:
                        # Only add non-sensitive kwargs
                        safe_kwargs = {
                            k: v for k, v in kwargs.items()
                            if not any(sensitive in k.lower() 
                                     for sensitive in ['password', 'token', 'secret', 'key'])
                        }
                        for key, value in safe_kwargs.items():
                            span.tags[f'function.kwarg.{key}'] = str(value)[:100]  # Limit length
                    
                    try:
                        result = func(*args, **kwargs)
                        span.tags['function.success'] = True
                        return result
                    except Exception as e:
                        span.tags['function.success'] = False
                        span.tags['function.error'] = str(e)
                        raise
            
            return wrapper
        return decorator
    
    def time_method(self, metric_name: str = None, tags: Dict[str, str] = None):
        """Decorator to time method execution"""
        
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Generate metric name if not provided
                timer_name = metric_name or f"{func.__module__}.{func.__name__}"
                
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    success = True
                    return result
                except Exception as e:
                    success = False
                    raise
                finally:
                    duration_ms = (time.time() - start_time) * 1000
                    method_tags = {
                        'function': func.__name__,
                        'module': func.__module__,
                        'success': str(success),
                        **(tags or {})
                    }
                    self.collector.record_timer(timer_name, duration_ms, method_tags)
            
            return wrapper
        return decorator
    
    def count_calls(self, counter_name: str = None, tags: Dict[str, str] = None):
        """Decorator to count method calls"""
        
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Generate counter name if not provided
                count_name = counter_name or f"{func.__module__}.{func.__name__}_calls"
                
                method_tags = {
                    'function': func.__name__,
                    'module': func.__module__,
                    **(tags or {})
                }
                
                try:
                    result = func(*args, **kwargs)
                    method_tags['success'] = 'true'
                    self.collector.increment_counter(count_name, tags=method_tags)
                    return result
                except Exception as e:
                    method_tags['success'] = 'false'
                    method_tags['error_type'] = type(e).__name__
                    self.collector.increment_counter(count_name, tags=method_tags)
                    raise
            
            return wrapper
        return decorator
    
    def track_business_method(self, transaction_type: str, extract_id: Callable = None,
                            extract_amount: Callable = None, extract_user: Callable = None):
        """Decorator to track business transactions"""
        
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Extract business transaction details
                transaction_id = extract_id(*args, **kwargs) if extract_id else str(uuid.uuid4())[:8]
                amount = extract_amount(*args, **kwargs) if extract_amount else None
                user_id = extract_user(*args, **kwargs) if extract_user else None
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Track business transaction
                self.collector.track_business_transaction(
                    transaction_type=transaction_type,
                    transaction_id=transaction_id,
                    user_id=user_id,
                    amount=amount,
                    function=func.__name__,
                    module=func.__module__
                )
                
                return result
            
            return wrapper
        return decorator

# Framework-Specific Instrumentation
class FlaskInstrumentation:
    """Custom instrumentation for Flask applications"""
    
    def __init__(self, app, collector: CustomInstrumentationCollector):
        self.app = app
        self.collector = collector
        self.setup_instrumentation()
    
    def setup_instrumentation(self):
        """Setup Flask-specific instrumentation"""
        
        @self.app.before_request
        def before_request():
            from flask import request, g
            
            # Start request span
            operation_name = f"{request.method} {request.endpoint or request.path}"
            
            tags = {
                'http.method': request.method,
                'http.url': request.url,
                'http.path': request.path,
                'http.endpoint': request.endpoint,
                'http.remote_addr': request.remote_addr,
                'http.user_agent': request.headers.get('User-Agent', ''),
                'component': 'flask'
            }
            
            span = self.collector.start_span(operation_name, tags=tags)
            g.request_span = span
            g.request_start_time = time.time()
        
        @self.app.after_request
        def after_request(response):
            from flask import g
            
            if hasattr(g, 'request_span'):
                # Add response information
                g.request_span.tags['http.status_code'] = response.status_code
                g.request_span.tags['http.status_class'] = f"{response.status_code // 100}xx"
                
                # Calculate and record response time
                if hasattr(g, 'request_start_time'):
                    response_time_ms = (time.time() - g.request_start_time) * 1000
                    g.request_span.tags['http.response_time_ms'] = response_time_ms
                    
                    # Record as metric
                    self.collector.record_timer(
                        'http_request_duration',
                        response_time_ms,
                        tags={
                            'method': g.request_span.tags['http.method'],
                            'endpoint': g.request_span.tags['http.endpoint'] or 'unknown',
                            'status_class': g.request_span.tags['http.status_class']
                        }
                    )
                
                # Finish span
                if response.status_code >= 400:
                    error = Exception(f"HTTP {response.status_code}")
                    self.collector.finish_span(g.request_span, error=error)
                else:
                    self.collector.finish_span(g.request_span)
            
            return response
        
        @self.app.errorhandler(Exception)
        def handle_exception(e):
            from flask import g
            
            if hasattr(g, 'request_span'):
                self.collector.finish_span(g.request_span, error=e)
            
            # Re-raise the exception
            raise e

class DatabaseInstrumentation:
    """Custom database operation instrumentation"""
    
    def __init__(self, collector: CustomInstrumentationCollector):
        self.collector = collector
    
    def instrument_query(self, query: str, database: str, table: str = None,
                        operation: str = None, connection_name: str = "default"):
        """Instrument database query execution"""
        
        @contextmanager
        def query_span():
            # Determine operation type if not provided
            if not operation:
                query_upper = query.strip().upper()
                if query_upper.startswith('SELECT'):
                    operation = 'SELECT'
                elif query_upper.startswith('INSERT'):
                    operation = 'INSERT'
                elif query_upper.startswith('UPDATE'):
                    operation = 'UPDATE'
                elif query_upper.startswith('DELETE'):
                    operation = 'DELETE'
                else:
                    operation = 'OTHER'
            
            # Sanitize query for logging (remove sensitive data)
            sanitized_query = self._sanitize_query(query)
            
            tags = {
                'db.type': 'sql',
                'db.instance': database,
                'db.operation': operation,
                'db.connection': connection_name,
                'component': 'database'
            }
            
            if table:
                tags['db.table'] = table
            
            operation_name = f"db.{operation.lower()}"
            if table:
                operation_name += f".{table}"
            
            with self.collector.trace(operation_name, tags) as span:
                # Add query as log (truncated for safety)
                span.logs.append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'event': 'query',
                    'query': sanitized_query[:500]  # Limit query length
                })
                
                yield span
        
        return query_span()
    
    def _sanitize_query(self, query: str) -> str:
        """Sanitize SQL query by removing potential sensitive data"""
        import re
        
        # Remove string literals (potential sensitive data)
        sanitized = re.sub(r"'[^']*'", "'?'", query)
        # Remove numeric literals
        sanitized = re.sub(r'\b\d+\b', '?', sanitized)
        # Clean up whitespace
        sanitized = ' '.join(sanitized.split())
        
        return sanitized

class ExternalServiceInstrumentation:
    """Instrumentation for external service calls"""
    
    def __init__(self, collector: CustomInstrumentationCollector):
        self.collector = collector
    
    def instrument_http_call(self, url: str, method: str = "GET", service_name: str = None):
        """Instrument HTTP call to external service"""
        
        @contextmanager
        def http_span():
            # Extract service name from URL if not provided
            if not service_name:
                from urllib.parse import urlparse
                parsed_url = urlparse(url)
                service_name = parsed_url.hostname or 'unknown'
            
            tags = {
                'http.method': method,
                'http.url': url,
                'external.service': service_name,
                'component': 'http-client',
                'span.kind': 'client'
            }
            
            operation_name = f"http.{method.lower()}.{service_name}"
            
            with self.collector.trace(operation_name, tags) as span:
                yield span
        
        return http_span()
    
    def instrument_message_queue(self, queue_name: str, operation: str, 
                               message_id: str = None, broker: str = "rabbitmq"):
        """Instrument message queue operations"""
        
        @contextmanager  
        def mq_span():
            tags = {
                'mq.broker': broker,
                'mq.queue': queue_name,
                'mq.operation': operation,
                'component': 'message-queue'
            }
            
            if message_id:
                tags['mq.message_id'] = message_id
            
            if operation.lower() in ['send', 'publish']:
                tags['span.kind'] = 'producer'
            elif operation.lower() in ['receive', 'consume']:
                tags['span.kind'] = 'consumer'
            
            operation_name = f"mq.{operation.lower()}.{queue_name}"
            
            with self.collector.trace(operation_name, tags) as span:
                yield span
        
        return mq_span()

# Usage Example and Demonstration
def demonstrate_custom_instrumentation():
    """Demonstrate custom instrumentation capabilities"""
    
    print("🔧 Custom Instrumentation Demo")
    print("=" * 35)
    
    # Initialize collector
    collector = CustomInstrumentationCollector("ecommerce-api")
    decorators = InstrumentationDecorators(collector)
    
    print("📊 Setting up custom instrumentation...")
    
    # Example 1: Method instrumentation with decorators
    @decorators.trace_method("user_service.get_user")
    @decorators.time_method("user_lookup_time")
    @decorators.count_calls("user_service_calls")
    def get_user(user_id: int, include_profile: bool = True):
        """Get user information"""
        time.sleep(0.05)  # Simulate database query
        
        if user_id == 404:
            raise ValueError("User not found")
        
        return {
            'user_id': user_id,
            'username': f'user_{user_id}',
            'profile': {'plan': 'premium'} if include_profile else None
        }
    
    # Example 2: Business transaction tracking
    @decorators.track_business_method(
        "purchase",
        extract_id=lambda *args, **kwargs: kwargs.get('order_id'),
        extract_amount=lambda *args, **kwargs: kwargs.get('total'),
        extract_user=lambda *args, **kwargs: kwargs.get('user_id')
    )
    def process_purchase(user_id: int, order_id: str, total: float, items: list):
        """Process purchase transaction"""
        time.sleep(0.1)  # Simulate payment processing
        
        if total < 0:
            raise ValueError("Invalid purchase amount")
        
        return {'order_id': order_id, 'status': 'completed'}
    
    # Example 3: Database instrumentation
    db_instrumentation = DatabaseInstrumentation(collector)
    
    def fetch_user_orders(user_id: int):
        """Fetch user orders from database"""
        query = f"SELECT * FROM orders WHERE user_id = {user_id} ORDER BY created_at DESC"
        
        with db_instrumentation.instrument_query(
            query=query,
            database="ecommerce",
            table="orders",
            operation="SELECT"
        ) as span:
            # Simulate database execution
            time.sleep(0.03)
            span.tags['db.rows_affected'] = 5
            
            return [
                {'order_id': f'order_{i}', 'total': i * 25.99}
                for i in range(1, 6)
            ]
    
    # Example 4: External service instrumentation
    external_instrumentation = ExternalServiceInstrumentation(collector)
    
    def call_payment_service(amount: float, card_token: str):
        """Call external payment service"""
        
        with external_instrumentation.instrument_http_call(
            url="https://payment-gateway.example.com/charge",
            method="POST",
            service_name="payment-gateway"
        ) as span:
            # Simulate HTTP call
            time.sleep(0.08)
            span.tags['payment.amount'] = amount
            span.tags['payment.currency'] = 'USD'
            span.tags['http.status_code'] = 200
            
            return {'transaction_id': 'tx_12345', 'status': 'success'}
    
    # Example 5: Message queue instrumentation
    def send_order_notification(order_id: str, user_id: int):
        """Send order notification via message queue"""
        
        with external_instrumentation.instrument_message_queue(
            queue_name="order-notifications",
            operation="publish",
            message_id=f"msg_{order_id}"
        ) as span:
            # Simulate message publishing
            time.sleep(0.01)
            span.tags['notification.type'] = 'order_confirmation'
            span.tags['notification.user_id'] = user_id
    
    # Execute instrumented operations
    print("\n🚀 Executing instrumented operations...")
    
    try:
        # Test user operations
        user = get_user(123, include_profile=True)
        print(f"✅ Retrieved user: {user['username']}")
        
        # Test error handling
        try:
            get_user(404)
        except ValueError as e:
            print(f"⚠️  Handled error: {e}")
        
        # Test business transaction
        purchase_result = process_purchase(
            user_id=123,
            order_id="order_789",
            total=99.99,
            items=["laptop", "mouse"]
        )
        print(f"✅ Processed purchase: {purchase_result['order_id']}")
        
        # Test database operations
        orders = fetch_user_orders(123)
        print(f"✅ Fetched {len(orders)} orders")
        
        # Test external service
        payment_result = call_payment_service(99.99, "card_token_123")
        print(f"✅ Payment processed: {payment_result['transaction_id']}")
        
        # Test message queue
        send_order_notification("order_789", 123)
        print("✅ Notification sent")
        
        # Track user journey
        collector.track_user_journey_step(
            user_id="123",
            step_name="purchase_completed",
            step_data={"order_id": "order_789", "amount": 99.99}
        )
        print("✅ User journey tracked")
        
    except Exception as e:
        print(f"❌ Operation failed: {e}")
    
    # Display collected instrumentation data
    print(f"\n📈 Instrumentation Data Collected:")
    print("-" * 40)
    
    with collector.lock:
        print(f"Spans: {len(collector.spans_buffer)}")
        print(f"Metrics: {len(collector.metrics_buffer)}")
        print(f"Business Transactions: {len(collector.business_transactions)}")
        print(f"User Journeys: {len(collector.user_journeys)}")
    
    # Show sample spans
    if collector.spans_buffer:
        print(f"\nSample Spans:")
        for span in list(collector.spans_buffer)[-3:]:
            print(f"  • {span.operation_name} ({span.duration_ms:.1f}ms)")
            print(f"    Status: {span.status}, Tags: {len(span.tags)}")
    
    # Show sample metrics
    if collector.metrics_buffer:
        print(f"\nSample Metrics:")
        recent_metrics = list(collector.metrics_buffer)[-5:]
        for metric in recent_metrics:
            print(f"  • {metric.name}: {metric.value} ({metric.metric_type})")
    
    # Show business transactions
    if collector.business_transactions:
        print(f"\nBusiness Transactions:")
        for tx_id, tx in collector.business_transactions.items():
            print(f"  • {tx['transaction_type']}: {tx_id} - ${tx['amount']}")
    
    print(f"\n💡 Custom Instrumentation Benefits:")
    print("  • Detailed application-specific monitoring")
    print("  • Business transaction visibility")
    print("  • Custom performance metrics")
    print("  • Enhanced debugging and troubleshooting")
    print("  • User journey tracking and analysis")

if __name__ == "__main__":
    demonstrate_custom_instrumentation()
```

This comprehensive custom instrumentation framework provides enterprise-grade capabilities for detailed application monitoring, business transaction tracking, and custom metrics collection essential for deep visibility into application behavior and performance.