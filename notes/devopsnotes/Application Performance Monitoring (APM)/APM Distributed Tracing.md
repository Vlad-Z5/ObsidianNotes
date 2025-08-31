# APM Distributed Tracing

Distributed tracing provides visibility into request flows across microservices and distributed systems, enabling developers and DevOps engineers to understand system behavior, identify performance bottlenecks, and troubleshoot issues in complex architectures. This guide covers distributed tracing concepts, implementation strategies, trace analysis, and enterprise tracing solutions.

## Distributed Tracing Fundamentals

### Core Concepts and Architecture

```python
from typing import Dict, List, Optional, Any
import time
import uuid
import json
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

class SpanKind(Enum):
    CLIENT = "CLIENT"
    SERVER = "SERVER"
    PRODUCER = "PRODUCER"
    CONSUMER = "CONSUMER"
    INTERNAL = "INTERNAL"

class SpanStatus(Enum):
    OK = "OK"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"

@dataclass
class SpanContext:
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    trace_flags: int = 1
    trace_state: str = ""
    baggage: Dict[str, str] = None
    
    def __post_init__(self):
        if self.baggage is None:
            self.baggage = {}

@dataclass
class Span:
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    operation_name: str
    service_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    status: SpanStatus = SpanStatus.OK
    kind: SpanKind = SpanKind.INTERNAL
    tags: Dict[str, Any] = None
    logs: List[Dict[str, Any]] = None
    references: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}
        if self.logs is None:
            self.logs = []
        if self.references is None:
            self.references = []

class DistributedTracer:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.active_spans: Dict[str, Span] = {}
        self.completed_spans: List[Span] = []
        
    def generate_trace_id(self) -> str:
        """Generate a new trace ID"""
        return str(uuid.uuid4()).replace('-', '')[:16]
    
    def generate_span_id(self) -> str:
        """Generate a new span ID"""
        return str(uuid.uuid4()).replace('-', '')[:8]
    
    def start_span(self, operation_name: str, parent_span: Optional[Span] = None, 
                   kind: SpanKind = SpanKind.INTERNAL, tags: Dict[str, Any] = None) -> Span:
        """Start a new span"""
        span_id = self.generate_span_id()
        
        if parent_span:
            trace_id = parent_span.trace_id
            parent_span_id = parent_span.span_id
        else:
            trace_id = self.generate_trace_id()
            parent_span_id = None
        
        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            service_name=self.service_name,
            start_time=datetime.utcnow(),
            kind=kind,
            tags=tags or {}
        )
        
        # Add default tags
        span.tags.update({
            'service.name': self.service_name,
            'span.kind': kind.value,
            'component': 'distributed-tracer'
        })
        
        self.active_spans[span_id] = span
        return span
    
    def finish_span(self, span: Span, status: SpanStatus = SpanStatus.OK, 
                   error: Exception = None) -> None:
        """Finish a span"""
        span.end_time = datetime.utcnow()
        span.duration_ms = (span.end_time - span.start_time).total_seconds() * 1000
        span.status = status
        
        if error:
            span.status = SpanStatus.ERROR
            span.tags['error'] = True
            span.tags['error.kind'] = type(error).__name__
            span.tags['error.object'] = str(error)
            
            # Add error log
            span.logs.append({
                'timestamp': datetime.utcnow().isoformat(),
                'level': 'error',
                'message': str(error),
                'event': 'error'
            })
        
        # Move from active to completed
        if span.span_id in self.active_spans:
            del self.active_spans[span.span_id]
        
        self.completed_spans.append(span)
    
    def add_span_tag(self, span: Span, key: str, value: Any) -> None:
        """Add tag to span"""
        span.tags[key] = value
    
    def add_span_log(self, span: Span, fields: Dict[str, Any]) -> None:
        """Add log entry to span"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            **fields
        }
        span.logs.append(log_entry)
    
    def get_trace_spans(self, trace_id: str) -> List[Span]:
        """Get all spans for a trace"""
        return [span for span in self.completed_spans if span.trace_id == trace_id]
    
    def export_traces(self, format: str = 'jaeger') -> List[Dict]:
        """Export traces in specified format"""
        if format == 'jaeger':
            return self._export_jaeger_format()
        elif format == 'zipkin':
            return self._export_zipkin_format()
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_jaeger_format(self) -> List[Dict]:
        """Export traces in Jaeger format"""
        traces_by_id = {}
        
        for span in self.completed_spans:
            if span.trace_id not in traces_by_id:
                traces_by_id[span.trace_id] = {
                    'traceID': span.trace_id,
                    'spans': [],
                    'processes': {}
                }
            
            # Add process info
            process_id = f"p{len(traces_by_id[span.trace_id]['processes'])}"
            traces_by_id[span.trace_id]['processes'][process_id] = {
                'serviceName': span.service_name,
                'tags': [
                    {'key': 'service.name', 'type': 'string', 'value': span.service_name}
                ]
            }
            
            # Convert span to Jaeger format
            jaeger_span = {
                'traceID': span.trace_id,
                'spanID': span.span_id,
                'parentSpanID': span.parent_span_id,
                'operationName': span.operation_name,
                'startTime': int(span.start_time.timestamp() * 1000000),  # microseconds
                'duration': int(span.duration_ms * 1000) if span.duration_ms else 0,  # microseconds
                'processID': process_id,
                'tags': [
                    {'key': k, 'type': self._get_jaeger_type(v), 'value': v}
                    for k, v in span.tags.items()
                ],
                'logs': [
                    {
                        'timestamp': int(datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')).timestamp() * 1000000),
                        'fields': [
                            {'key': k, 'value': str(v)} for k, v in log.items() if k != 'timestamp'
                        ]
                    }
                    for log in span.logs
                ]
            }
            
            traces_by_id[span.trace_id]['spans'].append(jaeger_span)
        
        return list(traces_by_id.values())
    
    def _export_zipkin_format(self) -> List[Dict]:
        """Export traces in Zipkin format"""
        zipkin_spans = []
        
        for span in self.completed_spans:
            zipkin_span = {
                'traceId': span.trace_id,
                'id': span.span_id,
                'name': span.operation_name,
                'timestamp': int(span.start_time.timestamp() * 1000000),  # microseconds
                'duration': int(span.duration_ms * 1000) if span.duration_ms else 0,  # microseconds
                'localEndpoint': {
                    'serviceName': span.service_name
                },
                'tags': {k: str(v) for k, v in span.tags.items()},
                'annotations': []
            }
            
            if span.parent_span_id:
                zipkin_span['parentId'] = span.parent_span_id
            
            # Add kind-specific annotations
            if span.kind == SpanKind.CLIENT:
                zipkin_span['kind'] = 'CLIENT'
            elif span.kind == SpanKind.SERVER:
                zipkin_span['kind'] = 'SERVER'
            elif span.kind == SpanKind.PRODUCER:
                zipkin_span['kind'] = 'PRODUCER'
            elif span.kind == SpanKind.CONSUMER:
                zipkin_span['kind'] = 'CONSUMER'
            
            # Add logs as annotations
            for log in span.logs:
                zipkin_span['annotations'].append({
                    'timestamp': int(datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')).timestamp() * 1000000),
                    'value': log.get('message', json.dumps(log))
                })
            
            zipkin_spans.append(zipkin_span)
        
        return zipkin_spans
    
    def _get_jaeger_type(self, value: Any) -> str:
        """Get Jaeger type for value"""
        if isinstance(value, bool):
            return 'bool'
        elif isinstance(value, int):
            return 'int64'
        elif isinstance(value, float):
            return 'float64'
        else:
            return 'string'

# Example usage with microservice tracing
class MicroserviceTracer:
    def __init__(self):
        self.services = {
            'api-gateway': DistributedTracer('api-gateway'),
            'user-service': DistributedTracer('user-service'),
            'order-service': DistributedTracer('order-service'),
            'payment-service': DistributedTracer('payment-service'),
            'notification-service': DistributedTracer('notification-service')
        }
    
    def simulate_distributed_request(self):
        """Simulate a distributed request across microservices"""
        
        # 1. API Gateway receives request
        gateway_tracer = self.services['api-gateway']
        root_span = gateway_tracer.start_span(
            'POST /api/orders',
            kind=SpanKind.SERVER,
            tags={
                'http.method': 'POST',
                'http.url': '/api/orders',
                'http.user_agent': 'Mozilla/5.0',
                'user.id': 'user123'
            }
        )
        
        # Add request processing log
        gateway_tracer.add_span_log(root_span, {
            'event': 'request.received',
            'message': 'Processing order creation request'
        })
        
        # 2. Call user service to validate user
        user_tracer = self.services['user-service']
        user_span = user_tracer.start_span(
            'validate_user',
            parent_span=root_span,
            kind=SpanKind.SERVER,
            tags={
                'user.id': 'user123',
                'db.type': 'postgresql',
                'db.instance': 'users_db'
            }
        )
        
        # Simulate user validation
        time.sleep(0.05)  # 50ms
        user_tracer.add_span_log(user_span, {
            'event': 'db.query',
            'query': 'SELECT * FROM users WHERE id = ?'
        })
        
        user_tracer.finish_span(user_span)
        
        # 3. Call order service to create order
        order_tracer = self.services['order-service']
        order_span = order_tracer.start_span(
            'create_order',
            parent_span=root_span,
            kind=SpanKind.SERVER,
            tags={
                'order.items': 3,
                'order.total': 99.99,
                'db.type': 'postgresql',
                'db.instance': 'orders_db'
            }
        )
        
        time.sleep(0.1)  # 100ms
        order_tracer.add_span_log(order_span, {
            'event': 'order.created',
            'order.id': 'order456'
        })
        
        # 4. Call payment service from order service
        payment_tracer = self.services['payment-service']
        payment_span = payment_tracer.start_span(
            'process_payment',
            parent_span=order_span,
            kind=SpanKind.CLIENT,
            tags={
                'payment.method': 'credit_card',
                'payment.amount': 99.99,
                'external.service': 'stripe'
            }
        )
        
        time.sleep(0.2)  # 200ms - external payment processing
        payment_tracer.add_span_log(payment_span, {
            'event': 'payment.processed',
            'transaction.id': 'tx789'
        })
        
        payment_tracer.finish_span(payment_span)
        order_tracer.finish_span(order_span)
        
        # 5. Call notification service asynchronously
        notification_tracer = self.services['notification-service']
        notification_span = notification_tracer.start_span(
            'send_order_confirmation',
            parent_span=root_span,
            kind=SpanKind.PRODUCER,
            tags={
                'notification.type': 'email',
                'notification.template': 'order_confirmation',
                'user.email': 'user123@example.com'
            }
        )
        
        time.sleep(0.03)  # 30ms
        notification_tracer.add_span_log(notification_span, {
            'event': 'notification.sent',
            'message_id': 'msg999'
        })
        
        notification_tracer.finish_span(notification_span)
        
        # Finish root span
        gateway_tracer.add_span_log(root_span, {
            'event': 'request.completed',
            'response.status': 201
        })
        
        gateway_tracer.add_span_tag(root_span, 'http.status_code', 201)
        gateway_tracer.finish_span(root_span)
        
        return root_span.trace_id
    
    def get_trace_summary(self, trace_id: str) -> Dict[str, Any]:
        """Get summary of a trace"""
        all_spans = []
        
        for service_name, tracer in self.services.items():
            spans = tracer.get_trace_spans(trace_id)
            all_spans.extend(spans)
        
        if not all_spans:
            return {'error': 'Trace not found'}
        
        # Calculate trace metrics
        total_duration = max(span.duration_ms for span in all_spans if span.duration_ms)
        service_counts = {}
        operation_counts = {}
        
        for span in all_spans:
            service_counts[span.service_name] = service_counts.get(span.service_name, 0) + 1
            operation_counts[span.operation_name] = operation_counts.get(span.operation_name, 0) + 1
        
        return {
            'trace_id': trace_id,
            'total_spans': len(all_spans),
            'total_duration_ms': total_duration,
            'services_involved': list(service_counts.keys()),
            'service_span_counts': service_counts,
            'operation_counts': operation_counts,
            'spans': [
                {
                    'span_id': span.span_id,
                    'service': span.service_name,
                    'operation': span.operation_name,
                    'duration_ms': span.duration_ms,
                    'status': span.status.value,
                    'tags': span.tags
                }
                for span in all_spans
            ]
        }
    
    def export_all_traces(self, format: str = 'jaeger') -> Dict[str, List[Dict]]:
        """Export all traces from all services"""
        exported_traces = {}
        
        for service_name, tracer in self.services.items():
            if tracer.completed_spans:
                exported_traces[service_name] = tracer.export_traces(format)
        
        return exported_traces

# Demonstration
microservice_tracer = MicroserviceTracer()

print("Simulating distributed request across microservices...")
print("=" * 60)

# Simulate multiple requests
for i in range(3):
    trace_id = microservice_tracer.simulate_distributed_request()
    trace_summary = microservice_tracer.get_trace_summary(trace_id)
    
    print(f"\nTrace {i+1} Summary:")
    print(f"Trace ID: {trace_summary['trace_id']}")
    print(f"Total Duration: {trace_summary['total_duration_ms']:.1f}ms")
    print(f"Total Spans: {trace_summary['total_spans']}")
    print(f"Services Involved: {', '.join(trace_summary['services_involved'])}")
    
    print("\nSpan Details:")
    for span in trace_summary['spans']:
        print(f"  {span['service']:<20} | {span['operation']:<25} | {span['duration_ms']:.1f}ms | {span['status']}")

# Export traces in Jaeger format
print("\n" + "=" * 60)
print("Exporting traces in Jaeger format...")

exported_traces = microservice_tracer.export_all_traces('jaeger')
total_exported = sum(len(traces) for traces in exported_traces.values())
print(f"Exported {total_exported} traces from {len(exported_traces)} services")

for service_name, traces in exported_traces.items():
    print(f"  {service_name}: {len(traces)} traces")
```

## OpenTelemetry Implementation

### Production OpenTelemetry Setup

```python
from opentelemetry import trace, metrics, baggage
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
import logging
import os

class ProductionTracingSetup:
    def __init__(self, service_name: str, service_version: str = "1.0.0"):
        self.service_name = service_name
        self.service_version = service_version
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for tracing"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Reduce noise from tracing libraries
        logging.getLogger("opentelemetry").setLevel(logging.WARNING)
        
    def initialize_tracing(self):
        """Initialize OpenTelemetry tracing"""
        
        # Create resource with service information
        resource = Resource.create({
            ResourceAttributes.SERVICE_NAME: self.service_name,
            ResourceAttributes.SERVICE_VERSION: self.service_version,
            ResourceAttributes.DEPLOYMENT_ENVIRONMENT: os.getenv("ENVIRONMENT", "production"),
            ResourceAttributes.SERVICE_INSTANCE_ID: os.getenv("HOSTNAME", "unknown"),
            ResourceAttributes.K8S_POD_NAME: os.getenv("K8S_POD_NAME"),
            ResourceAttributes.K8S_NAMESPACE_NAME: os.getenv("K8S_NAMESPACE_NAME"),
            ResourceAttributes.K8S_DEPLOYMENT_NAME: os.getenv("K8S_DEPLOYMENT_NAME"),
            ResourceAttributes.CLOUD_PROVIDER: os.getenv("CLOUD_PROVIDER", "aws"),
            ResourceAttributes.CLOUD_REGION: os.getenv("AWS_REGION", "us-east-1"),
        })
        
        # Set up tracer provider
        tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(tracer_provider)
        
        # Configure Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name=os.getenv("JAEGER_AGENT_HOST", "jaeger-agent"),
            agent_port=int(os.getenv("JAEGER_AGENT_PORT", "6831")),
            collector_endpoint=os.getenv("JAEGER_ENDPOINT"),
        )
        
        # Add batch span processor
        span_processor = BatchSpanProcessor(
            jaeger_exporter,
            max_queue_size=2048,
            export_timeout_millis=30000,
            max_export_batch_size=512,
        )
        tracer_provider.add_span_processor(span_processor)
        
        # Set up propagators
        set_global_textmap(B3MultiFormat())
        
        logging.info(f"Tracing initialized for service: {self.service_name}")
        
    def initialize_metrics(self):
        """Initialize OpenTelemetry metrics"""
        
        # Prometheus metric reader
        prometheus_reader = PrometheusMetricReader()
        
        # Create meter provider
        meter_provider = MeterProvider(
            resource=Resource.create({
                ResourceAttributes.SERVICE_NAME: self.service_name,
                ResourceAttributes.SERVICE_VERSION: self.service_version,
            }),
            metric_readers=[prometheus_reader]
        )
        
        metrics.set_meter_provider(meter_provider)
        logging.info("Metrics initialized with Prometheus export")
        
    def instrument_libraries(self):
        """Instrument common libraries"""
        
        # Flask instrumentation
        try:
            FlaskInstrumentor().instrument()
            logging.info("Flask instrumentation enabled")
        except Exception as e:
            logging.warning(f"Flask instrumentation failed: {e}")
        
        # Requests instrumentation
        try:
            RequestsInstrumentor().instrument()
            logging.info("Requests instrumentation enabled")
        except Exception as e:
            logging.warning(f"Requests instrumentation failed: {e}")
        
        # SQLAlchemy instrumentation
        try:
            SQLAlchemyInstrumentor().instrument()
            logging.info("SQLAlchemy instrumentation enabled")
        except Exception as e:
            logging.warning(f"SQLAlchemy instrumentation failed: {e}")
        
        # Redis instrumentation
        try:
            RedisInstrumentor().instrument()
            logging.info("Redis instrumentation enabled")
        except Exception as e:
            logging.warning(f"Redis instrumentation failed: {e}")
    
    def setup_complete(self):
        """Complete OpenTelemetry setup"""
        self.initialize_tracing()
        self.initialize_metrics()
        self.instrument_libraries()
        
        logging.info("OpenTelemetry setup completed successfully")

# Custom tracing decorators and utilities
class TracingUtils:
    
    @staticmethod
    def trace_function(operation_name: str = None, tags: dict = None):
        """Decorator to trace functions"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                tracer = trace.get_tracer(__name__)
                span_name = operation_name or f"{func.__module__}.{func.__name__}"
                
                with tracer.start_as_current_span(span_name) as span:
                    # Add default tags
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)
                    
                    # Add custom tags
                    if tags:
                        for key, value in tags.items():
                            span.set_attribute(key, value)
                    
                    # Add function arguments as tags (be careful with sensitive data)
                    if args:
                        span.set_attribute("function.args.count", len(args))
                    if kwargs:
                        span.set_attribute("function.kwargs.count", len(kwargs))
                        # Only log non-sensitive kwargs
                        safe_kwargs = {k: v for k, v in kwargs.items() 
                                     if not any(sensitive in k.lower() 
                                              for sensitive in ['password', 'token', 'secret', 'key'])}
                        for key, value in safe_kwargs.items():
                            span.set_attribute(f"function.kwargs.{key}", str(value))
                    
                    try:
                        result = func(*args, **kwargs)
                        span.set_status(trace.Status(trace.StatusCode.OK))
                        return result
                    except Exception as e:
                        span.record_exception(e)
                        span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                        raise
            
            return wrapper
        return decorator
    
    @staticmethod
    def trace_database_operation(query: str, database: str = None, table: str = None):
        """Trace database operations"""
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("database.query") as span:
            span.set_attribute("db.statement", query)
            span.set_attribute("db.type", "sql")
            
            if database:
                span.set_attribute("db.name", database)
            if table:
                span.set_attribute("db.sql.table", table)
            
            return span
    
    @staticmethod
    def trace_external_call(service: str, operation: str, url: str = None):
        """Trace external service calls"""
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span(f"external.{service}.{operation}") as span:
            span.set_attribute("external.service", service)
            span.set_attribute("external.operation", operation)
            span.set_attribute("span.kind", "client")
            
            if url:
                span.set_attribute("http.url", url)
            
            return span
    
    @staticmethod
    def add_business_context(user_id: str = None, session_id: str = None, 
                           tenant_id: str = None, custom_attributes: dict = None):
        """Add business context to current span"""
        span = trace.get_current_span()
        
        if span.is_recording():
            if user_id:
                span.set_attribute("user.id", user_id)
            if session_id:
                span.set_attribute("session.id", session_id)
            if tenant_id:
                span.set_attribute("tenant.id", tenant_id)
            
            if custom_attributes:
                for key, value in custom_attributes.items():
                    span.set_attribute(f"business.{key}", str(value))

# Example Flask application with tracing
from flask import Flask, request, jsonify
import requests
import time
import random

# Initialize tracing
tracing_setup = ProductionTracingSetup("ecommerce-api")
tracing_setup.setup_complete()

app = Flask(__name__)

@app.route('/api/products/<int:product_id>')
@TracingUtils.trace_function("get_product", {"api.endpoint": "/api/products"})
def get_product(product_id):
    """Get product details with distributed tracing"""
    
    # Add business context
    user_id = request.headers.get('X-User-ID', 'anonymous')
    TracingUtils.add_business_context(
        user_id=user_id,
        custom_attributes={
            'product.id': product_id,
            'api.version': 'v1',
            'request.source': request.headers.get('User-Agent', 'unknown')
        }
    )
    
    try:
        # Simulate database query
        with TracingUtils.trace_database_operation(
            "SELECT * FROM products WHERE id = ?", 
            database="ecommerce", 
            table="products"
        ) as db_span:
            
            time.sleep(random.uniform(0.01, 0.05))  # Simulate DB latency
            db_span.set_attribute("db.rows_affected", 1)
            
            product_data = {
                'id': product_id,
                'name': f'Product {product_id}',
                'price': round(random.uniform(10.0, 100.0), 2),
                'category': 'electronics'
            }
        
        # Call external service for reviews
        with TracingUtils.trace_external_call(
            "reviews-service", 
            "get_reviews", 
            f"http://reviews-service/api/reviews?product_id={product_id}"
        ) as ext_span:
            
            # Simulate external API call
            time.sleep(random.uniform(0.05, 0.1))
            ext_span.set_attribute("http.status_code", 200)
            ext_span.set_attribute("reviews.count", random.randint(0, 50))
        
        # Add response attributes to main span
        span = trace.get_current_span()
        span.set_attribute("http.response.status_code", 200)
        span.set_attribute("product.price", product_data['price'])
        span.set_attribute("product.category", product_data['category'])
        
        return jsonify({
            'product': product_data,
            'reviews_count': random.randint(0, 50)
        })
        
    except Exception as e:
        span = trace.get_current_span()
        span.record_exception(e)
        span.set_attribute("http.response.status_code", 500)
        
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/orders', methods=['POST'])
@TracingUtils.trace_function("create_order", {"api.endpoint": "/api/orders"})
def create_order():
    """Create order with distributed tracing"""
    
    order_data = request.get_json()
    user_id = request.headers.get('X-User-ID', 'anonymous')
    
    # Add business context
    TracingUtils.add_business_context(
        user_id=user_id,
        custom_attributes={
            'order.items_count': len(order_data.get('items', [])),
            'order.total_amount': order_data.get('total', 0),
            'api.version': 'v1'
        }
    )
    
    try:
        # Validate user
        with TracingUtils.trace_external_call("user-service", "validate_user") as user_span:
            time.sleep(random.uniform(0.02, 0.04))
            user_span.set_attribute("user.validation.result", "valid")
        
        # Process payment
        with TracingUtils.trace_external_call("payment-service", "process_payment") as payment_span:
            time.sleep(random.uniform(0.1, 0.2))
            payment_span.set_attribute("payment.method", "credit_card")
            payment_span.set_attribute("payment.amount", order_data.get('total', 0))
            payment_span.set_attribute("payment.status", "success")
        
        # Create order in database
        with TracingUtils.trace_database_operation(
            "INSERT INTO orders ...", 
            database="ecommerce", 
            table="orders"
        ) as db_span:
            time.sleep(random.uniform(0.01, 0.03))
            order_id = f"order_{random.randint(1000, 9999)}"
            db_span.set_attribute("order.id", order_id)
        
        # Send notification
        with TracingUtils.trace_external_call("notification-service", "send_confirmation") as notif_span:
            time.sleep(random.uniform(0.02, 0.05))
            notif_span.set_attribute("notification.type", "order_confirmation")
            notif_span.set_attribute("notification.channel", "email")
        
        # Success response
        span = trace.get_current_span()
        span.set_attribute("http.response.status_code", 201)
        span.set_attribute("order.created", True)
        
        return jsonify({
            'order_id': order_id,
            'status': 'created',
            'message': 'Order created successfully'
        }), 201
        
    except Exception as e:
        span = trace.get_current_span()
        span.record_exception(e)
        span.set_attribute("http.response.status_code", 500)
        span.set_attribute("order.created", False)
        
        return jsonify({'error': 'Failed to create order'}), 500

@app.route('/health')
def health_check():
    """Health check endpoint (not traced to reduce noise)"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    print("Starting Flask application with distributed tracing...")
    print("Traces will be sent to Jaeger")
    print("Metrics available at /metrics")
    app.run(host='0.0.0.0', port=5000, debug=False)
```

## Trace Analysis and Visualization

### Jaeger Query and Analysis Tools

```python
import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

class JaegerAnalyzer:
    def __init__(self, jaeger_endpoint: str = "http://jaeger-query:16686"):
        self.jaeger_endpoint = jaeger_endpoint.rstrip('/')
        self.api_endpoint = f"{self.jaeger_endpoint}/api"
        
    def get_services(self) -> List[str]:
        """Get list of services"""
        try:
            response = requests.get(f"{self.api_endpoint}/services")
            response.raise_for_status()
            return response.json().get('data', [])
        except Exception as e:
            print(f"Error fetching services: {e}")
            return []
    
    def get_operations(self, service: str) -> List[str]:
        """Get operations for a service"""
        try:
            response = requests.get(f"{self.api_endpoint}/operations", params={'service': service})
            response.raise_for_status()
            return [op['operationName'] for op in response.json().get('data', [])]
        except Exception as e:
            print(f"Error fetching operations: {e}")
            return []
    
    def search_traces(self, service: str, operation: str = None, 
                     lookback: str = "1h", limit: int = 100,
                     min_duration: str = None, max_duration: str = None,
                     tags: Dict[str, str] = None) -> List[Dict]:
        """Search for traces"""
        params = {
            'service': service,
            'lookback': lookback,
            'limit': limit
        }
        
        if operation:
            params['operation'] = operation
        if min_duration:
            params['minDuration'] = min_duration
        if max_duration:
            params['maxDuration'] = max_duration
        if tags:
            for key, value in tags.items():
                params[f'tag'] = f"{key}:{value}"
        
        try:
            response = requests.get(f"{self.api_endpoint}/traces", params=params)
            response.raise_for_status()
            return response.json().get('data', [])
        except Exception as e:
            print(f"Error searching traces: {e}")
            return []
    
    def get_trace_detail(self, trace_id: str) -> Optional[Dict]:
        """Get detailed trace information"""
        try:
            response = requests.get(f"{self.api_endpoint}/traces/{trace_id}")
            response.raise_for_status()
            traces = response.json().get('data', [])
            return traces[0] if traces else None
        except Exception as e:
            print(f"Error fetching trace detail: {e}")
            return None
    
    def analyze_service_performance(self, service: str, lookback: str = "1h") -> Dict[str, Any]:
        """Analyze service performance metrics"""
        traces = self.search_traces(service, lookback=lookback, limit=1000)
        
        if not traces:
            return {"error": "No traces found"}
        
        # Extract metrics from traces
        durations = []
        error_count = 0
        operation_stats = {}
        
        for trace in traces:
            if 'spans' not in trace:
                continue
                
            trace_duration = trace.get('spans', [{}])[0].get('duration', 0) / 1000  # Convert to ms
            durations.append(trace_duration)
            
            # Check for errors
            has_error = any(
                any(tag.get('key') == 'error' and tag.get('value') == True 
                    for tag in span.get('tags', []))
                for span in trace.get('spans', [])
            )
            if has_error:
                error_count += 1
            
            # Operation statistics
            for span in trace.get('spans', []):
                if span.get('process', {}).get('serviceName') == service:
                    op_name = span.get('operationName', 'unknown')
                    if op_name not in operation_stats:
                        operation_stats[op_name] = {
                            'count': 0,
                            'total_duration': 0,
                            'min_duration': float('inf'),
                            'max_duration': 0,
                            'errors': 0
                        }
                    
                    span_duration = span.get('duration', 0) / 1000  # Convert to ms
                    stats = operation_stats[op_name]
                    stats['count'] += 1
                    stats['total_duration'] += span_duration
                    stats['min_duration'] = min(stats['min_duration'], span_duration)
                    stats['max_duration'] = max(stats['max_duration'], span_duration)
                    
                    # Check for span errors
                    if any(tag.get('key') == 'error' and tag.get('value') == True 
                           for tag in span.get('tags', [])):
                        stats['errors'] += 1
        
        # Calculate percentiles
        durations.sort()
        total_traces = len(durations)
        
        analysis = {
            'service': service,
            'lookback': lookback,
            'total_traces': total_traces,
            'error_rate': (error_count / total_traces) * 100 if total_traces > 0 else 0,
            'duration_stats': {
                'min_ms': min(durations) if durations else 0,
                'max_ms': max(durations) if durations else 0,
                'avg_ms': sum(durations) / len(durations) if durations else 0,
                'p50_ms': durations[int(0.5 * len(durations))] if durations else 0,
                'p95_ms': durations[int(0.95 * len(durations))] if durations else 0,
                'p99_ms': durations[int(0.99 * len(durations))] if durations else 0,
            },
            'operations': {}
        }
        
        # Calculate operation averages
        for op_name, stats in operation_stats.items():
            if stats['count'] > 0:
                analysis['operations'][op_name] = {
                    'count': stats['count'],
                    'avg_duration_ms': stats['total_duration'] / stats['count'],
                    'min_duration_ms': stats['min_duration'],
                    'max_duration_ms': stats['max_duration'],
                    'error_rate': (stats['errors'] / stats['count']) * 100,
                }
        
        return analysis
    
    def find_slow_traces(self, service: str, threshold_ms: float = 1000, 
                        lookback: str = "1h", limit: int = 50) -> List[Dict]:
        """Find traces slower than threshold"""
        traces = self.search_traces(
            service, 
            lookback=lookback, 
            limit=limit,
            min_duration=f"{threshold_ms}ms"
        )
        
        slow_traces = []
        for trace in traces:
            if 'spans' not in trace:
                continue
                
            root_span = trace.get('spans', [{}])[0]
            duration_ms = root_span.get('duration', 0) / 1000
            
            slow_traces.append({
                'trace_id': trace.get('traceID'),
                'duration_ms': duration_ms,
                'operation': root_span.get('operationName'),
                'start_time': root_span.get('startTime', 0) / 1000000,  # Convert to seconds
                'span_count': len(trace.get('spans', [])),
                'services': list(set(
                    span.get('process', {}).get('serviceName', 'unknown')
                    for span in trace.get('spans', [])
                ))
            })
        
        return sorted(slow_traces, key=lambda x: x['duration_ms'], reverse=True)
    
    def find_error_traces(self, service: str, lookback: str = "1h", 
                         limit: int = 100) -> List[Dict]:
        """Find traces with errors"""
        traces = self.search_traces(service, lookback=lookback, limit=limit)
        
        error_traces = []
        for trace in traces:
            if 'spans' not in trace:
                continue
                
            # Check for errors in spans
            errors = []
            for span in trace.get('spans', []):
                span_errors = []
                for tag in span.get('tags', []):
                    if tag.get('key') == 'error' and tag.get('value') == True:
                        span_errors.append({
                            'span_id': span.get('spanID'),
                            'operation': span.get('operationName'),
                            'service': span.get('process', {}).get('serviceName')
                        })
                
                # Check logs for error messages
                for log in span.get('logs', []):
                    for field in log.get('fields', []):
                        if field.get('key') in ['error', 'error.kind', 'message']:
                            span_errors.append({
                                'span_id': span.get('spanID'),
                                'operation': span.get('operationName'),
                                'service': span.get('process', {}).get('serviceName'),
                                'error_message': field.get('value')
                            })
                
                errors.extend(span_errors)
            
            if errors:
                root_span = trace.get('spans', [{}])[0]
                error_traces.append({
                    'trace_id': trace.get('traceID'),
                    'duration_ms': root_span.get('duration', 0) / 1000,
                    'operation': root_span.get('operationName'),
                    'start_time': root_span.get('startTime', 0) / 1000000,
                    'errors': errors
                })
        
        return error_traces
    
    def analyze_service_dependencies(self, service: str, lookback: str = "1h") -> Dict[str, Any]:
        """Analyze service dependencies"""
        traces = self.search_traces(service, lookback=lookback, limit=500)
        
        dependencies = {}
        for trace in traces:
            if 'spans' not in trace:
                continue
                
            service_spans = {}
            
            # Group spans by service
            for span in trace.get('spans', []):
                span_service = span.get('process', {}).get('serviceName', 'unknown')
                if span_service not in service_spans:
                    service_spans[span_service] = []
                service_spans[span_service].append(span)
            
            # Analyze dependencies for the target service
            if service in service_spans:
                for span in service_spans[service]:
                    # Look for client spans that call other services
                    for tag in span.get('tags', []):
                        if tag.get('key') == 'span.kind' and tag.get('value') == 'client':
                            # Try to identify target service from tags or operation name
                            target_service = None
                            for other_tag in span.get('tags', []):
                                if other_tag.get('key') in ['external.service', 'peer.service']:
                                    target_service = other_tag.get('value')
                                    break
                            
                            if not target_service:
                                # Infer from operation name
                                op_name = span.get('operationName', '')
                                if 'external.' in op_name:
                                    target_service = op_name.split('.')[1]
                            
                            if target_service:
                                if target_service not in dependencies:
                                    dependencies[target_service] = {
                                        'call_count': 0,
                                        'total_duration': 0,
                                        'error_count': 0,
                                        'operations': set()
                                    }
                                
                                dep = dependencies[target_service]
                                dep['call_count'] += 1
                                dep['total_duration'] += span.get('duration', 0) / 1000
                                dep['operations'].add(span.get('operationName'))
                                
                                # Check for errors
                                if any(tag.get('key') == 'error' and tag.get('value') == True 
                                       for tag in span.get('tags', [])):
                                    dep['error_count'] += 1
        
        # Calculate averages and convert sets to lists
        for dep_name, dep_info in dependencies.items():
            if dep_info['call_count'] > 0:
                dep_info['avg_duration_ms'] = dep_info['total_duration'] / dep_info['call_count']
                dep_info['error_rate'] = (dep_info['error_count'] / dep_info['call_count']) * 100
            dep_info['operations'] = list(dep_info['operations'])
        
        return {
            'service': service,
            'dependencies': dependencies,
            'total_dependencies': len(dependencies)
        }
    
    def generate_performance_report(self, services: List[str], lookback: str = "1h") -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'lookback': lookback,
            'services': {}
        }
        
        for service in services:
            print(f"Analyzing service: {service}")
            
            # Get performance metrics
            perf_analysis = self.analyze_service_performance(service, lookback)
            
            # Get slow traces
            slow_traces = self.find_slow_traces(service, lookback=lookback)
            
            # Get error traces
            error_traces = self.find_error_traces(service, lookback=lookback)
            
            # Get dependencies
            dependencies = self.analyze_service_dependencies(service, lookback)
            
            report['services'][service] = {
                'performance': perf_analysis,
                'slow_traces': slow_traces[:10],  # Top 10 slowest
                'error_traces': error_traces[:10],  # Top 10 with errors
                'dependencies': dependencies['dependencies'],
                'health_score': self._calculate_health_score(perf_analysis, slow_traces, error_traces)
            }
        
        return report
    
    def _calculate_health_score(self, perf_analysis: Dict, slow_traces: List, error_traces: List) -> float:
        """Calculate service health score (0-100)"""
        score = 100.0
        
        # Deduct for high error rate
        error_rate = perf_analysis.get('error_rate', 0)
        if error_rate > 5:
            score -= min(20, error_rate * 2)
        elif error_rate > 1:
            score -= error_rate * 5
        
        # Deduct for high latency
        p95_latency = perf_analysis.get('duration_stats', {}).get('p95_ms', 0)
        if p95_latency > 2000:  # 2 seconds
            score -= min(30, (p95_latency - 2000) / 100)
        elif p95_latency > 1000:  # 1 second
            score -= (p95_latency - 1000) / 100
        
        # Deduct for slow traces
        slow_trace_count = len(slow_traces)
        if slow_trace_count > 10:
            score -= min(20, slow_trace_count - 10)
        
        # Deduct for error traces
        error_trace_count = len(error_traces)
        if error_trace_count > 5:
            score -= min(15, (error_trace_count - 5) * 2)
        
        return max(0.0, score)

# Example usage
if __name__ == "__main__":
    analyzer = JaegerAnalyzer("http://localhost:16686")
    
    # Get available services
    services = analyzer.get_services()
    print(f"Available services: {services}")
    
    if services:
        # Analyze first service
        service_name = services[0]
        print(f"\nAnalyzing service: {service_name}")
        
        # Performance analysis
        perf_analysis = analyzer.analyze_service_performance(service_name)
        print(f"\nPerformance Analysis:")
        print(f"Total traces: {perf_analysis.get('total_traces')}")
        print(f"Error rate: {perf_analysis.get('error_rate'):.2f}%")
        print(f"P95 latency: {perf_analysis.get('duration_stats', {}).get('p95_ms', 0):.1f}ms")
        
        # Find slow traces
        slow_traces = analyzer.find_slow_traces(service_name, threshold_ms=500)
        print(f"\nFound {len(slow_traces)} slow traces (>500ms)")
        
        for trace in slow_traces[:5]:
            print(f"  Trace {trace['trace_id']}: {trace['duration_ms']:.1f}ms - {trace['operation']}")
        
        # Find error traces
        error_traces = analyzer.find_error_traces(service_name)
        print(f"\nFound {len(error_traces)} error traces")
        
        # Service dependencies
        dependencies = analyzer.analyze_service_dependencies(service_name)
        print(f"\nService dependencies:")
        for dep_name, dep_info in dependencies['dependencies'].items():
            print(f"  {dep_name}: {dep_info['call_count']} calls, {dep_info['avg_duration_ms']:.1f}ms avg, {dep_info['error_rate']:.1f}% error rate")
```

This comprehensive distributed tracing guide provides the foundation for implementing, managing, and analyzing traces in production environments, essential for maintaining observability in modern distributed systems.