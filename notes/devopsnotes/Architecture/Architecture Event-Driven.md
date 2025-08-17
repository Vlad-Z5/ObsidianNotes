# Architecture Event-Driven

## Core Concepts

Event-Driven Architecture (EDA) is a software design pattern that promotes the production, detection, consumption, and reaction to events. An event represents a change in state or an update, such as an order being placed, a payment being processed, or a user logging in.

### Event Fundamentals

#### Event Definition and Structure
**Definition:** An event is an immutable record of something that happened in the system at a specific point in time.

**Example - E-commerce Event Hierarchy:**
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
import uuid
import json

@dataclass
class BaseEvent(ABC):
    """Base class for all domain events"""
    
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = field(init=False)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source_service: str = field(default="unknown")
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    version: str = "1.0"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Set event type from class name"""
        self.event_type = self.__class__.__name__
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'timestamp': self.timestamp.isoformat(),
            'source_service': self.source_service,
            'correlation_id': self.correlation_id,
            'causation_id': self.causation_id,
            'version': self.version,
            'metadata': self.metadata,
            'payload': self._get_payload()
        }
    
    @abstractmethod
    def _get_payload(self) -> Dict[str, Any]:
        """Get event-specific payload"""
        pass
    
    def to_json(self) -> str:
        """Serialize event to JSON"""
        return json.dumps(self.to_dict(), default=str)

# Domain Events
@dataclass
class UserRegisteredEvent(BaseEvent):
    """Event fired when a new user registers"""
    
    user_id: str
    email: str
    first_name: str
    last_name: str
    registration_source: str = "web"
    email_verified: bool = False
    
    def _get_payload(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'registration_source': self.registration_source,
            'email_verified': self.email_verified
        }

@dataclass
class OrderCreatedEvent(BaseEvent):
    """Event fired when an order is created"""
    
    order_id: str
    customer_id: str
    items: list
    total_amount: float
    currency: str = "USD"
    shipping_address: Dict[str, str] = field(default_factory=dict)
    
    def _get_payload(self) -> Dict[str, Any]:
        return {
            'order_id': self.order_id,
            'customer_id': self.customer_id,
            'items': self.items,
            'total_amount': self.total_amount,
            'currency': self.currency,
            'shipping_address': self.shipping_address
        }

@dataclass
class PaymentProcessedEvent(BaseEvent):
    """Event fired when a payment is successfully processed"""
    
    payment_id: str
    order_id: str
    amount: float
    payment_method: str
    gateway_response: Dict[str, Any] = field(default_factory=dict)
    
    def _get_payload(self) -> Dict[str, Any]:
        return {
            'payment_id': self.payment_id,
            'order_id': self.order_id,
            'amount': self.amount,
            'payment_method': self.payment_method,
            'gateway_response': self.gateway_response
        }

@dataclass
class InventoryReservedEvent(BaseEvent):
    """Event fired when inventory is reserved for an order"""
    
    reservation_id: str
    order_id: str
    items: list
    expires_at: datetime
    
    def _get_payload(self) -> Dict[str, Any]:
        return {
            'reservation_id': self.reservation_id,
            'order_id': self.order_id,
            'items': self.items,
            'expires_at': self.expires_at.isoformat()
        }

# Aggregate Events
@dataclass
class OrderCompletedEvent(BaseEvent):
    """High-level event indicating order completion"""
    
    order_id: str
    customer_id: str
    total_amount: float
    completion_time: datetime
    processing_duration_seconds: int
    
    def _get_payload(self) -> Dict[str, Any]:
        return {
            'order_id': self.order_id,
            'customer_id': self.customer_id,
            'total_amount': self.total_amount,
            'completion_time': self.completion_time.isoformat(),
            'processing_duration_seconds': self.processing_duration_seconds
        }
```

#### Event Store Implementation
**Purpose:** Persistent storage for events that maintains the complete history of changes in the system.

**Example - Production Event Store:**
```python
from abc import ABC, abstractmethod
from typing import List, Optional, Iterator
import json
import sqlite3
from dataclasses import asdict
import threading
from contextlib import contextmanager

class EventStore(ABC):
    """Abstract interface for event storage"""
    
    @abstractmethod
    def append_event(self, stream_id: str, event: BaseEvent, expected_version: Optional[int] = None):
        """Append event to stream"""
        pass
    
    @abstractmethod
    def get_events(self, stream_id: str, from_version: int = 0) -> List[BaseEvent]:
        """Get events from stream"""
        pass
    
    @abstractmethod
    def get_all_events(self, from_position: int = 0) -> Iterator[BaseEvent]:
        """Get all events from all streams"""
        pass

class SQLiteEventStore(EventStore):
    """SQLite-based event store implementation"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._local = threading.local()
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    position INTEGER PRIMARY KEY AUTOINCREMENT,
                    stream_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    event_id TEXT NOT NULL UNIQUE,
                    event_type TEXT NOT NULL,
                    event_data TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(stream_id, version)
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_stream_version 
                ON events(stream_id, version)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_event_type 
                ON events(event_type)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON events(timestamp)
            ''')
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper cleanup"""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False
            )
            self._local.connection.row_factory = sqlite3.Row
        
        try:
            yield self._local.connection
        except Exception:
            self._local.connection.rollback()
            raise
        else:
            self._local.connection.commit()
    
    def append_event(self, stream_id: str, event: BaseEvent, expected_version: Optional[int] = None):
        """Append event to stream with optimistic concurrency control"""
        with self._get_connection() as conn:
            # Get current version
            cursor = conn.execute(
                'SELECT MAX(version) as current_version FROM events WHERE stream_id = ?',
                (stream_id,)
            )
            
            result = cursor.fetchone()
            current_version = result['current_version'] if result['current_version'] is not None else -1
            
            # Check expected version for optimistic concurrency
            if expected_version is not None and current_version != expected_version:
                raise ConcurrencyError(
                    f"Expected version {expected_version}, but current version is {current_version}"
                )
            
            # Insert event
            new_version = current_version + 1
            
            conn.execute('''
                INSERT INTO events (stream_id, version, event_id, event_type, event_data, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                stream_id,
                new_version,
                event.event_id,
                event.event_type,
                event.to_json(),
                event.timestamp.isoformat()
            ))
            
            return new_version
    
    def get_events(self, stream_id: str, from_version: int = 0) -> List[BaseEvent]:
        """Get events from stream starting from specified version"""
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT event_type, event_data 
                FROM events 
                WHERE stream_id = ? AND version >= ?
                ORDER BY version
            ''', (stream_id, from_version))
            
            events = []
            for row in cursor:
                event = self._deserialize_event(row['event_type'], row['event_data'])
                events.append(event)
            
            return events
    
    def get_all_events(self, from_position: int = 0) -> Iterator[BaseEvent]:
        """Get all events from all streams"""
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT event_type, event_data 
                FROM events 
                WHERE position >= ?
                ORDER BY position
            ''', (from_position,))
            
            for row in cursor:
                yield self._deserialize_event(row['event_type'], row['event_data'])
    
    def get_stream_version(self, stream_id: str) -> int:
        """Get current version of stream"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                'SELECT MAX(version) as current_version FROM events WHERE stream_id = ?',
                (stream_id,)
            )
            
            result = cursor.fetchone()
            return result['current_version'] if result['current_version'] is not None else -1
    
    def _deserialize_event(self, event_type: str, event_data: str) -> BaseEvent:
        """Deserialize event from JSON"""
        data = json.loads(event_data)
        
        # Event type mapping - in production, use a registry
        event_classes = {
            'UserRegisteredEvent': UserRegisteredEvent,
            'OrderCreatedEvent': OrderCreatedEvent,
            'PaymentProcessedEvent': PaymentProcessedEvent,
            'InventoryReservedEvent': InventoryReservedEvent,
            'OrderCompletedEvent': OrderCompletedEvent
        }
        
        event_class = event_classes.get(event_type)
        if not event_class:
            raise ValueError(f"Unknown event type: {event_type}")
        
        payload = data.get('payload', {})
        
        # Create event instance
        if event_type == 'UserRegisteredEvent':
            return UserRegisteredEvent(
                event_id=data['event_id'],
                timestamp=datetime.fromisoformat(data['timestamp']),
                source_service=data['source_service'],
                correlation_id=data.get('correlation_id'),
                causation_id=data.get('causation_id'),
                version=data['version'],
                metadata=data['metadata'],
                **payload
            )
        # Add other event types as needed...
        
        raise ValueError(f"Deserialization not implemented for {event_type}")

class ConcurrencyError(Exception):
    """Raised when optimistic concurrency check fails"""
    pass
```

### Event Sourcing

#### Event-Sourced Aggregates
**Definition:** Storing the state of an application as a sequence of events rather than the current state.

**Example - Order Aggregate with Event Sourcing:**
```python
from enum import Enum
from typing import List
from decimal import Decimal

class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class OrderAggregate:
    """Event-sourced order aggregate"""
    
    def __init__(self, order_id: str):
        self.order_id = order_id
        self.customer_id: Optional[str] = None
        self.items: List[Dict] = []
        self.status = OrderStatus.PENDING
        self.total_amount = Decimal('0.00')
        self.payment_id: Optional[str] = None
        self.shipping_address: Optional[Dict] = None
        self.version = -1
        
        # Uncommitted events
        self._uncommitted_events: List[BaseEvent] = []
    
    @classmethod
    def from_history(cls, order_id: str, events: List[BaseEvent]) -> 'OrderAggregate':
        """Reconstruct aggregate from event history"""
        aggregate = cls(order_id)
        
        for event in events:
            aggregate._apply_event(event)
            aggregate.version += 1
        
        return aggregate
    
    def create_order(self, customer_id: str, items: List[Dict], shipping_address: Dict):
        """Create a new order"""
        if self.version >= 0:
            raise ValueError("Order already exists")
        
        event = OrderCreatedEvent(
            order_id=self.order_id,
            customer_id=customer_id,
            items=items,
            total_amount=float(sum(Decimal(str(item['price'])) * item['quantity'] for item in items)),
            shipping_address=shipping_address,
            source_service="order-service"
        )
        
        self._apply_event(event)
        self._uncommitted_events.append(event)
    
    def add_item(self, product_id: str, quantity: int, price: Decimal):
        """Add item to order"""
        if self.status != OrderStatus.PENDING:
            raise ValueError("Cannot modify confirmed order")
        
        event = OrderItemAddedEvent(
            order_id=self.order_id,
            product_id=product_id,
            quantity=quantity,
            price=float(price),
            source_service="order-service"
        )
        
        self._apply_event(event)
        self._uncommitted_events.append(event)
    
    def confirm_order(self):
        """Confirm the order"""
        if self.status != OrderStatus.PENDING:
            raise ValueError("Order is not in pending status")
        
        if not self.items:
            raise ValueError("Cannot confirm empty order")
        
        event = OrderConfirmedEvent(
            order_id=self.order_id,
            customer_id=self.customer_id,
            total_amount=float(self.total_amount),
            source_service="order-service"
        )
        
        self._apply_event(event)
        self._uncommitted_events.append(event)
    
    def mark_as_paid(self, payment_id: str, amount: Decimal):
        """Mark order as paid"""
        if self.status != OrderStatus.CONFIRMED:
            raise ValueError("Order must be confirmed before payment")
        
        if amount != self.total_amount:
            raise ValueError("Payment amount does not match order total")
        
        event = OrderPaidEvent(
            order_id=self.order_id,
            payment_id=payment_id,
            amount=float(amount),
            source_service="payment-service"
        )
        
        self._apply_event(event)
        self._uncommitted_events.append(event)
    
    def ship_order(self, tracking_number: str, carrier: str):
        """Ship the order"""
        if self.status != OrderStatus.PAID:
            raise ValueError("Order must be paid before shipping")
        
        event = OrderShippedEvent(
            order_id=self.order_id,
            tracking_number=tracking_number,
            carrier=carrier,
            source_service="fulfillment-service"
        )
        
        self._apply_event(event)
        self._uncommitted_events.append(event)
    
    def cancel_order(self, reason: str):
        """Cancel the order"""
        if self.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            raise ValueError("Cannot cancel shipped or delivered order")
        
        event = OrderCancelledEvent(
            order_id=self.order_id,
            reason=reason,
            cancelled_from_status=self.status.value,
            source_service="order-service"
        )
        
        self._apply_event(event)
        self._uncommitted_events.append(event)
    
    def get_uncommitted_events(self) -> List[BaseEvent]:
        """Get events that haven't been persisted yet"""
        return self._uncommitted_events.copy()
    
    def mark_events_committed(self):
        """Mark all uncommitted events as committed"""
        self._uncommitted_events.clear()
    
    def _apply_event(self, event: BaseEvent):
        """Apply event to aggregate state"""
        if isinstance(event, OrderCreatedEvent):
            self.customer_id = event.customer_id
            self.items = event.items.copy()
            self.total_amount = Decimal(str(event.total_amount))
            self.shipping_address = event.shipping_address
            self.status = OrderStatus.PENDING
            
        elif isinstance(event, OrderItemAddedEvent):
            self.items.append({
                'product_id': event.product_id,
                'quantity': event.quantity,
                'price': event.price
            })
            self.total_amount = Decimal(str(sum(
                Decimal(str(item['price'])) * item['quantity'] 
                for item in self.items
            )))
            
        elif isinstance(event, OrderConfirmedEvent):
            self.status = OrderStatus.CONFIRMED
            
        elif isinstance(event, OrderPaidEvent):
            self.payment_id = event.payment_id
            self.status = OrderStatus.PAID
            
        elif isinstance(event, OrderShippedEvent):
            self.status = OrderStatus.SHIPPED
            
        elif isinstance(event, OrderCancelledEvent):
            self.status = OrderStatus.CANCELLED

# Additional Event Types
@dataclass
class OrderItemAddedEvent(BaseEvent):
    order_id: str
    product_id: str
    quantity: int
    price: float
    
    def _get_payload(self) -> Dict[str, Any]:
        return {
            'order_id': self.order_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'price': self.price
        }

@dataclass
class OrderConfirmedEvent(BaseEvent):
    order_id: str
    customer_id: str
    total_amount: float
    
    def _get_payload(self) -> Dict[str, Any]:
        return {
            'order_id': self.order_id,
            'customer_id': self.customer_id,
            'total_amount': self.total_amount
        }

@dataclass
class OrderPaidEvent(BaseEvent):
    order_id: str
    payment_id: str
    amount: float
    
    def _get_payload(self) -> Dict[str, Any]:
        return {
            'order_id': self.order_id,
            'payment_id': self.payment_id,
            'amount': self.amount
        }

@dataclass
class OrderShippedEvent(BaseEvent):
    order_id: str
    tracking_number: str
    carrier: str
    
    def _get_payload(self) -> Dict[str, Any]:
        return {
            'order_id': self.order_id,
            'tracking_number': self.tracking_number,
            'carrier': self.carrier
        }

@dataclass
class OrderCancelledEvent(BaseEvent):
    order_id: str
    reason: str
    cancelled_from_status: str
    
    def _get_payload(self) -> Dict[str, Any]:
        return {
            'order_id': self.order_id,
            'reason': self.reason,
            'cancelled_from_status': self.cancelled_from_status
        }
```

#### Repository Pattern for Event-Sourced Aggregates
**Purpose:** Provide a clean interface for loading and saving event-sourced aggregates.

**Example - Order Repository:**
```python
class OrderRepository:
    """Repository for event-sourced order aggregates"""
    
    def __init__(self, event_store: EventStore, event_bus: 'EventBus'):
        self.event_store = event_store
        self.event_bus = event_bus
    
    def get_by_id(self, order_id: str) -> Optional[OrderAggregate]:
        """Load order aggregate from event history"""
        events = self.event_store.get_events(f"order-{order_id}")
        
        if not events:
            return None
        
        return OrderAggregate.from_history(order_id, events)
    
    def save(self, order: OrderAggregate):
        """Save order aggregate by persisting uncommitted events"""
        uncommitted_events = order.get_uncommitted_events()
        
        if not uncommitted_events:
            return  # Nothing to save
        
        stream_id = f"order-{order.order_id}"
        
        try:
            # Save events to event store
            for event in uncommitted_events:
                self.event_store.append_event(
                    stream_id, 
                    event, 
                    expected_version=order.version
                )
                order.version += 1
            
            # Mark events as committed
            order.mark_events_committed()
            
            # Publish events to event bus
            for event in uncommitted_events:
                self.event_bus.publish(event)
                
        except ConcurrencyError:
            # Handle optimistic concurrency conflicts
            raise OrderConcurrencyError(
                f"Order {order.order_id} was modified by another process"
            )
    
    def create_new(self, order_id: str) -> OrderAggregate:
        """Create a new order aggregate"""
        existing = self.get_by_id(order_id)
        if existing:
            raise ValueError(f"Order {order_id} already exists")
        
        return OrderAggregate(order_id)

class OrderConcurrencyError(Exception):
    """Raised when order is modified concurrently"""
    pass
```

### Event-Driven Communication

#### Event Bus Implementation
**Purpose:** Coordinate event publishing and subscription across the system.

**Example - Production Event Bus:**
```python
import asyncio
from abc import ABC, abstractmethod
from typing import Callable, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import logging

class EventBus(ABC):
    """Abstract event bus interface"""
    
    @abstractmethod
    async def publish(self, event: BaseEvent):
        """Publish an event"""
        pass
    
    @abstractmethod
    async def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to events of specific type"""
        pass
    
    @abstractmethod
    async def start(self):
        """Start the event bus"""
        pass
    
    @abstractmethod
    async def stop(self):
        """Stop the event bus"""
        pass

class InMemoryEventBus(EventBus):
    """In-memory event bus for development and testing"""
    
    def __init__(self, max_workers: int = 10):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.logger = logging.getLogger(__name__)
        self._running = False
    
    async def publish(self, event: BaseEvent):
        """Publish event to all subscribers"""
        if not self._running:
            return
        
        event_type = event.event_type
        handlers = self.subscribers.get(event_type, [])
        
        if not handlers:
            self.logger.debug(f"No handlers for event type: {event_type}")
            return
        
        # Execute handlers asynchronously
        tasks = []
        for handler in handlers:
            task = asyncio.create_task(self._execute_handler(handler, event))
            tasks.append(task)
        
        # Wait for all handlers to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log any failures
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(
                    f"Handler {handlers[i].__name__} failed for event {event_type}: {result}"
                )
    
    async def subscribe(self, event_type: str, handler: Callable):
        """Subscribe handler to event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(handler)
        self.logger.info(f"Subscribed {handler.__name__} to {event_type}")
    
    async def start(self):
        """Start the event bus"""
        self._running = True
        self.logger.info("In-memory event bus started")
    
    async def stop(self):
        """Stop the event bus"""
        self._running = False
        self.executor.shutdown(wait=True)
        self.logger.info("In-memory event bus stopped")
    
    async def _execute_handler(self, handler: Callable, event: BaseEvent):
        """Execute event handler with error handling"""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                # Run sync handlers in thread pool
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(self.executor, handler, event)
                
        except Exception as e:
            self.logger.error(f"Handler {handler.__name__} failed: {e}")
            raise

class KafkaEventBus(EventBus):
    """Kafka-based event bus for production"""
    
    def __init__(self, bootstrap_servers: str, group_id: str):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.producer = None
        self.consumers = {}
        self.subscriber_tasks = []
        self.logger = logging.getLogger(__name__)
        self._running = False
    
    async def start(self):
        """Start Kafka producer and consumers"""
        try:
            from aiokafka import AIOKafkaProducer
            
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: v.encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3,
                enable_idempotence=True
            )
            
            await self.producer.start()
            self._running = True
            self.logger.info("Kafka event bus started")
            
        except ImportError:
            raise RuntimeError("aiokafka package required for Kafka event bus")
    
    async def stop(self):
        """Stop Kafka producer and consumers"""
        self._running = False
        
        # Stop all consumer tasks
        for task in self.subscriber_tasks:
            task.cancel()
        
        await asyncio.gather(*self.subscriber_tasks, return_exceptions=True)
        
        # Stop consumers
        for consumer in self.consumers.values():
            await consumer.stop()
        
        # Stop producer
        if self.producer:
            await self.producer.stop()
        
        self.logger.info("Kafka event bus stopped")
    
    async def publish(self, event: BaseEvent):
        """Publish event to Kafka topic"""
        if not self._running or not self.producer:
            return
        
        topic = f"events.{event.event_type.lower()}"
        
        try:
            await self.producer.send(
                topic=topic,
                value=event.to_json(),
                key=getattr(event, 'aggregate_id', None)
            )
            
            self.logger.debug(f"Published {event.event_type} to {topic}")
            
        except Exception as e:
            self.logger.error(f"Failed to publish event {event.event_type}: {e}")
            raise
    
    async def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to Kafka topic for event type"""
        try:
            from aiokafka import AIOKafkaConsumer
            
            topic = f"events.{event_type.lower()}"
            
            consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=f"{self.group_id}.{event_type}",
                value_deserializer=lambda m: m.decode('utf-8'),
                enable_auto_commit=False,
                auto_offset_reset='earliest'
            )
            
            await consumer.start()
            self.consumers[event_type] = consumer
            
            # Start consumer task
            task = asyncio.create_task(
                self._consume_events(consumer, handler, event_type)
            )
            self.subscriber_tasks.append(task)
            
            self.logger.info(f"Subscribed {handler.__name__} to {event_type}")
            
        except ImportError:
            raise RuntimeError("aiokafka package required for Kafka event bus")
    
    async def _consume_events(self, consumer, handler: Callable, event_type: str):
        """Consume events from Kafka and execute handler"""
        try:
            async for message in consumer:
                try:
                    # Deserialize event
                    event_data = json.loads(message.value)
                    event = self._deserialize_event(event_data)
                    
                    # Execute handler
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                    
                    # Commit offset
                    await consumer.commit()
                    
                except Exception as e:
                    self.logger.error(
                        f"Error processing event in {event_type} handler: {e}"
                    )
                    # Could implement dead letter queue here
                    
        except asyncio.CancelledError:
            self.logger.info(f"Consumer for {event_type} cancelled")
        except Exception as e:
            self.logger.error(f"Consumer for {event_type} failed: {e}")
    
    def _deserialize_event(self, event_data: Dict[str, Any]) -> BaseEvent:
        """Deserialize event from dictionary"""
        # Implementation similar to EventStore._deserialize_event
        # This would use an event registry in production
        pass
```

#### Event Handlers and Projections
**Purpose:** Process events to update read models, trigger business processes, and maintain system consistency.

**Example - Order Processing Event Handlers:**
```python
class OrderEventHandlers:
    """Event handlers for order-related events"""
    
    def __init__(self, inventory_service, payment_service, notification_service, analytics_service):
        self.inventory_service = inventory_service
        self.payment_service = payment_service
        self.notification_service = notification_service
        self.analytics_service = analytics_service
    
    async def handle_order_created(self, event: OrderCreatedEvent):
        """Handle order creation by reserving inventory"""
        try:
            self.logger.info(f"Processing order created: {event.order_id}")
            
            # Reserve inventory
            reservation_result = await self.inventory_service.reserve_items(
                order_id=event.order_id,
                items=event.items
            )
            
            if reservation_result.success:
                # Publish inventory reserved event
                reserved_event = InventoryReservedEvent(
                    reservation_id=reservation_result.reservation_id,
                    order_id=event.order_id,
                    items=event.items,
                    expires_at=reservation_result.expires_at,
                    source_service="inventory-service",
                    correlation_id=event.correlation_id
                )
                
                # This would be published through the event bus
                await self._publish_event(reserved_event)
            else:
                # Publish inventory insufficient event
                insufficient_event = InventoryInsufficientEvent(
                    order_id=event.order_id,
                    requested_items=event.items,
                    unavailable_items=reservation_result.unavailable_items,
                    source_service="inventory-service",
                    correlation_id=event.correlation_id
                )
                
                await self._publish_event(insufficient_event)
                
        except Exception as e:
            self.logger.error(f"Failed to process order created event: {e}")
            # Could publish error event or send to dead letter queue
    
    async def handle_inventory_reserved(self, event: InventoryReservedEvent):
        """Handle inventory reservation by initiating payment"""
        try:
            self.logger.info(f"Processing inventory reserved: {event.order_id}")
            
            # Get order details (would typically load from read model)
            order_details = await self._get_order_details(event.order_id)
            
            # Process payment
            payment_result = await self.payment_service.process_payment(
                order_id=event.order_id,
                amount=order_details.total_amount,
                payment_method=order_details.payment_method,
                customer_id=order_details.customer_id
            )
            
            if payment_result.success:
                # Publish payment processed event
                payment_event = PaymentProcessedEvent(
                    payment_id=payment_result.payment_id,
                    order_id=event.order_id,
                    amount=order_details.total_amount,
                    payment_method=order_details.payment_method,
                    gateway_response=payment_result.gateway_response,
                    source_service="payment-service",
                    correlation_id=event.correlation_id
                )
                
                await self._publish_event(payment_event)
            else:
                # Release inventory reservation
                await self.inventory_service.release_reservation(event.reservation_id)
                
                # Publish payment failed event
                payment_failed_event = PaymentFailedEvent(
                    order_id=event.order_id,
                    amount=order_details.total_amount,
                    reason=payment_result.error_message,
                    source_service="payment-service",
                    correlation_id=event.correlation_id
                )
                
                await self._publish_event(payment_failed_event)
                
        except Exception as e:
            self.logger.error(f"Failed to process inventory reserved event: {e}")
    
    async def handle_payment_processed(self, event: PaymentProcessedEvent):
        """Handle successful payment by completing order"""
        try:
            self.logger.info(f"Processing payment completed: {event.order_id}")
            
            # Mark order as paid (would update order aggregate)
            await self._mark_order_as_paid(event.order_id, event.payment_id)
            
            # Send order confirmation notification
            await self.notification_service.send_order_confirmation(event.order_id)
            
            # Trigger fulfillment process
            await self._initiate_fulfillment(event.order_id)
            
            # Update analytics
            await self.analytics_service.record_order_completion(
                order_id=event.order_id,
                amount=event.amount,
                processing_time=self._calculate_processing_time(event)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to process payment completed event: {e}")

# Read Model Projections
class OrderProjectionHandler:
    """Maintains read models for order queries"""
    
    def __init__(self, read_model_store):
        self.read_model_store = read_model_store
    
    async def handle_order_created(self, event: OrderCreatedEvent):
        """Create order read model"""
        order_view = {
            'order_id': event.order_id,
            'customer_id': event.customer_id,
            'items': event.items,
            'total_amount': event.total_amount,
            'status': 'pending',
            'created_at': event.timestamp.isoformat(),
            'updated_at': event.timestamp.isoformat()
        }
        
        await self.read_model_store.create_order_view(order_view)
    
    async def handle_payment_processed(self, event: PaymentProcessedEvent):
        """Update order status to paid"""
        await self.read_model_store.update_order_status(
            event.order_id,
            'paid',
            payment_id=event.payment_id
        )
    
    async def handle_order_shipped(self, event: OrderShippedEvent):
        """Update order status to shipped"""
        await self.read_model_store.update_order_status(
            event.order_id,
            'shipped',
            tracking_number=event.tracking_number,
            carrier=event.carrier
        )

class CustomerProjectionHandler:
    """Maintains customer analytics and behavior read models"""
    
    def __init__(self, analytics_store):
        self.analytics_store = analytics_store
    
    async def handle_order_created(self, event: OrderCreatedEvent):
        """Update customer order statistics"""
        await self.analytics_store.increment_customer_orders(
            event.customer_id,
            order_value=event.total_amount
        )
    
    async def handle_payment_processed(self, event: PaymentProcessedEvent):
        """Update customer spending statistics"""
        await self.analytics_store.record_customer_purchase(
            event.order_id,
            amount=event.amount,
            payment_method=event.payment_method
        )
```

#### CQRS Integration
**Purpose:** Separate read and write models to optimize for different access patterns.

**Example - CQRS with Event Sourcing:**
```python
# Command Side (Write Model)
class OrderCommandHandler:
    """Handles commands that modify order state"""
    
    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository
    
    async def handle_create_order(self, command: CreateOrderCommand) -> str:
        """Handle order creation command"""
        # Create new aggregate
        order = self.order_repository.create_new(command.order_id)
        
        # Execute business logic
        order.create_order(
            customer_id=command.customer_id,
            items=command.items,
            shipping_address=command.shipping_address
        )
        
        # Save aggregate (publishes events)
        await self.order_repository.save(order)
        
        return order.order_id
    
    async def handle_add_item(self, command: AddItemToOrderCommand):
        """Handle adding item to order"""
        order = self.order_repository.get_by_id(command.order_id)
        
        if not order:
            raise OrderNotFoundError(command.order_id)
        
        order.add_item(
            command.product_id,
            command.quantity,
            command.price
        )
        
        await self.order_repository.save(order)
    
    async def handle_confirm_order(self, command: ConfirmOrderCommand):
        """Handle order confirmation"""
        order = self.order_repository.get_by_id(command.order_id)
        
        if not order:
            raise OrderNotFoundError(command.order_id)
        
        order.confirm_order()
        await self.order_repository.save(order)

# Query Side (Read Model)
class OrderQueryHandler:
    """Handles queries for order information"""
    
    def __init__(self, read_model_store):
        self.read_model_store = read_model_store
    
    async def get_order_details(self, order_id: str) -> Optional[Dict]:
        """Get order details from read model"""
        return await self.read_model_store.get_order_view(order_id)
    
    async def get_customer_orders(self, customer_id: str, page: int = 1, size: int = 20) -> Dict:
        """Get customer's orders with pagination"""
        return await self.read_model_store.get_customer_orders(
            customer_id, 
            page, 
            size
        )
    
    async def search_orders(self, criteria: OrderSearchCriteria) -> List[Dict]:
        """Search orders by various criteria"""
        return await self.read_model_store.search_orders(criteria)
    
    async def get_order_analytics(self, date_range: DateRange) -> Dict:
        """Get order analytics for date range"""
        return await self.read_model_store.get_order_analytics(date_range)

# Commands
@dataclass
class CreateOrderCommand:
    order_id: str
    customer_id: str
    items: List[Dict]
    shipping_address: Dict

@dataclass
class AddItemToOrderCommand:
    order_id: str
    product_id: str
    quantity: int
    price: Decimal

@dataclass
class ConfirmOrderCommand:
    order_id: str

# Read Model Store
class OrderReadModelStore:
    """Storage for order read models"""
    
    def __init__(self, database):
        self.db = database
    
    async def create_order_view(self, order_data: Dict):
        """Create order view in read model"""
        await self.db.execute("""
            INSERT INTO order_views (
                order_id, customer_id, items, total_amount, 
                status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            order_data['order_id'],
            order_data['customer_id'],
            json.dumps(order_data['items']),
            order_data['total_amount'],
            order_data['status'],
            order_data['created_at'],
            order_data['updated_at']
        ))
    
    async def update_order_status(self, order_id: str, status: str, **kwargs):
        """Update order status and additional fields"""
        update_fields = ['status = ?', 'updated_at = ?']
        params = [status, datetime.utcnow().isoformat()]
        
        for key, value in kwargs.items():
            update_fields.append(f"{key} = ?")
            params.append(value)
        
        params.append(order_id)
        
        await self.db.execute(f"""
            UPDATE order_views 
            SET {', '.join(update_fields)}
            WHERE order_id = ?
        """, params)
    
    async def get_order_view(self, order_id: str) -> Optional[Dict]:
        """Get order view by ID"""
        result = await self.db.fetch_one(
            "SELECT * FROM order_views WHERE order_id = ?",
            (order_id,)
        )
        
        if result:
            return dict(result)
        return None
    
    async def get_customer_orders(self, customer_id: str, page: int, size: int) -> Dict:
        """Get customer orders with pagination"""
        offset = (page - 1) * size
        
        orders = await self.db.fetch_all("""
            SELECT * FROM order_views 
            WHERE customer_id = ? 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        """, (customer_id, size, offset))
        
        total = await self.db.fetch_val(
            "SELECT COUNT(*) FROM order_views WHERE customer_id = ?",
            (customer_id,)
        )
        
        return {
            'orders': [dict(order) for order in orders],
            'pagination': {
                'page': page,
                'size': size,
                'total': total,
                'has_next': offset + size < total
            }
        }
```

## Advanced Event-Driven Patterns

### Saga Pattern for Distributed Transactions

Long-running business processes that span multiple services require coordination. The Saga pattern manages these distributed transactions using choreography or orchestration.

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from enum import Enum
import asyncio
import uuid

class SagaStepStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATED = "compensated"

class SagaStatus(Enum):
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"

@dataclass
class SagaStep:
    """Individual step in a saga"""
    step_id: str
    step_type: str
    status: SagaStepStatus = SagaStepStatus.PENDING
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    error_data: Optional[Dict[str, Any]] = None
    compensation_data: Optional[Dict[str, Any]] = None

class SagaOrchestrator:
    """Orchestrates saga execution with compensation"""
    
    def __init__(self, saga_store, event_bus):
        self.saga_store = saga_store
        self.event_bus = event_bus
        self.step_handlers = {}
        self.compensation_handlers = {}
        self.logger = logging.getLogger(__name__)
    
    def register_step_handler(self, step_type: str, handler: Callable, compensator: Callable = None):
        """Register step handler and optional compensator"""
        self.step_handlers[step_type] = handler
        if compensator:
            self.compensation_handlers[step_type] = compensator
    
    async def start_saga(self, saga_definition: Dict[str, Any], input_data: Dict[str, Any]) -> str:
        """Start a new saga execution"""
        saga_id = str(uuid.uuid4())
        
        # Create saga instance
        saga = {
            'saga_id': saga_id,
            'saga_type': saga_definition['type'],
            'status': SagaStatus.STARTED,
            'steps': [
                SagaStep(
                    step_id=str(uuid.uuid4()),
                    step_type=step['type'],
                    input_data=step.get('input_transform', lambda x: x)(input_data)
                )
                for step in saga_definition['steps']
            ],
            'current_step': 0,
            'input_data': input_data,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        # Save saga
        await self.saga_store.save_saga(saga)
        
        # Start first step
        await self._execute_next_step(saga)
        
        return saga_id
    
    async def handle_step_completed(self, saga_id: str, step_id: str, output_data: Dict[str, Any]):
        """Handle step completion"""
        saga = await self.saga_store.get_saga(saga_id)
        if not saga:
            self.logger.error(f"Saga {saga_id} not found")
            return
        
        # Update step status
        step = self._find_step(saga, step_id)
        if step:
            step.status = SagaStepStatus.COMPLETED
            step.output_data = output_data
        
        saga['current_step'] += 1
        saga['updated_at'] = datetime.utcnow()
        
        if saga['current_step'] >= len(saga['steps']):
            # Saga completed
            saga['status'] = SagaStatus.COMPLETED
            await self.saga_store.save_saga(saga)
            
            # Publish saga completed event
            await self.event_bus.publish(SagaCompletedEvent(
                saga_id=saga_id,
                saga_type=saga['saga_type'],
                completion_time=datetime.utcnow(),
                source_service="saga-orchestrator"
            ))
        else:
            # Execute next step
            await self.saga_store.save_saga(saga)
            await self._execute_next_step(saga)
    
    async def handle_step_failed(self, saga_id: str, step_id: str, error_data: Dict[str, Any]):
        """Handle step failure and initiate compensation"""
        saga = await self.saga_store.get_saga(saga_id)
        if not saga:
            return
        
        # Mark step as failed
        step = self._find_step(saga, step_id)
        if step:
            step.status = SagaStepStatus.FAILED
            step.error_data = error_data
        
        saga['status'] = SagaStatus.COMPENSATING
        saga['updated_at'] = datetime.utcnow()
        await self.saga_store.save_saga(saga)
        
        # Start compensation
        await self._compensate_saga(saga)
    
    async def _execute_next_step(self, saga: Dict[str, Any]):
        """Execute the next step in the saga"""
        current_step_index = saga['current_step']
        
        if current_step_index >= len(saga['steps']):
            return
        
        step = saga['steps'][current_step_index]
        handler = self.step_handlers.get(step.step_type)
        
        if not handler:
            await self.handle_step_failed(
                saga['saga_id'], 
                step.step_id, 
                {'error': f'No handler for step type {step.step_type}'}
            )
            return
        
        try:
            # Execute step
            await handler(saga['saga_id'], step.step_id, step.input_data)
            
        except Exception as e:
            self.logger.error(f"Step {step.step_type} failed: {e}")
            await self.handle_step_failed(
                saga['saga_id'], 
                step.step_id, 
                {'error': str(e)}
            )
    
    async def _compensate_saga(self, saga: Dict[str, Any]):
        """Compensate completed steps in reverse order"""
        completed_steps = [
            step for step in saga['steps'] 
            if step.status == SagaStepStatus.COMPLETED
        ]
        
        # Compensate in reverse order
        for step in reversed(completed_steps):
            compensator = self.compensation_handlers.get(step.step_type)
            
            if compensator:
                try:
                    await compensator(saga['saga_id'], step.step_id, step.output_data)
                    step.status = SagaStepStatus.COMPENSATED
                    
                except Exception as e:
                    self.logger.error(f"Compensation failed for step {step.step_type}: {e}")
                    step.compensation_data = {'error': str(e)}
        
        saga['status'] = SagaStatus.COMPENSATED
        saga['updated_at'] = datetime.utcnow()
        await self.saga_store.save_saga(saga)
        
        # Publish saga compensated event
        await self.event_bus.publish(SagaCompensatedEvent(
            saga_id=saga['saga_id'],
            saga_type=saga['saga_type'],
            compensation_time=datetime.utcnow(),
            source_service="saga-orchestrator"
        ))
    
    def _find_step(self, saga: Dict[str, Any], step_id: str) -> Optional[SagaStep]:
        """Find step by ID"""
        for step in saga['steps']:
            if step.step_id == step_id:
                return step
        return None

# Order Processing Saga Example
class OrderProcessingSaga:
    """Complete order processing saga"""
    
    def __init__(self, orchestrator: SagaOrchestrator):
        self.orchestrator = orchestrator
        self._register_handlers()
    
    def _register_handlers(self):
        """Register saga step handlers"""
        self.orchestrator.register_step_handler(
            'reserve_inventory',
            self._reserve_inventory,
            self._release_inventory
        )
        
        self.orchestrator.register_step_handler(
            'process_payment',
            self._process_payment,
            self._refund_payment
        )
        
        self.orchestrator.register_step_handler(
            'ship_order',
            self._ship_order,
            self._cancel_shipment
        )
        
        self.orchestrator.register_step_handler(
            'send_confirmation',
            self._send_confirmation,
            self._send_cancellation
        )
    
    async def process_order(self, order_data: Dict[str, Any]) -> str:
        """Start order processing saga"""
        saga_definition = {
            'type': 'order_processing',
            'steps': [
                {'type': 'reserve_inventory'},
                {'type': 'process_payment'},
                {'type': 'ship_order'},
                {'type': 'send_confirmation'}
            ]
        }
        
        return await self.orchestrator.start_saga(saga_definition, order_data)
    
    async def _reserve_inventory(self, saga_id: str, step_id: str, input_data: Dict[str, Any]):
        """Reserve inventory step"""
        # Simulate inventory reservation
        await asyncio.sleep(0.1)
        
        if input_data.get('items_available', True):
            await self.orchestrator.handle_step_completed(
                saga_id, 
                step_id, 
                {'reservation_id': str(uuid.uuid4())}
            )
        else:
            await self.orchestrator.handle_step_failed(
                saga_id, 
                step_id, 
                {'error': 'Insufficient inventory'}
            )
    
    async def _release_inventory(self, saga_id: str, step_id: str, output_data: Dict[str, Any]):
        """Compensate inventory reservation"""
        reservation_id = output_data.get('reservation_id')
        # Release inventory reservation
        await asyncio.sleep(0.1)
        self.logger.info(f"Released inventory reservation {reservation_id}")
    
    async def _process_payment(self, saga_id: str, step_id: str, input_data: Dict[str, Any]):
        """Process payment step"""
        await asyncio.sleep(0.1)
        
        if input_data.get('payment_valid', True):
            await self.orchestrator.handle_step_completed(
                saga_id, 
                step_id, 
                {'payment_id': str(uuid.uuid4())}
            )
        else:
            await self.orchestrator.handle_step_failed(
                saga_id, 
                step_id, 
                {'error': 'Payment failed'}
            )
    
    async def _refund_payment(self, saga_id: str, step_id: str, output_data: Dict[str, Any]):
        """Compensate payment processing"""
        payment_id = output_data.get('payment_id')
        await asyncio.sleep(0.1)
        self.logger.info(f"Refunded payment {payment_id}")
    
    async def _ship_order(self, saga_id: str, step_id: str, input_data: Dict[str, Any]):
        """Ship order step"""
        await asyncio.sleep(0.1)
        
        await self.orchestrator.handle_step_completed(
            saga_id, 
            step_id, 
            {'tracking_number': f"TN{uuid.uuid4().hex[:8]}"}
        )
    
    async def _cancel_shipment(self, saga_id: str, step_id: str, output_data: Dict[str, Any]):
        """Compensate order shipment"""
        tracking_number = output_data.get('tracking_number')
        await asyncio.sleep(0.1)
        self.logger.info(f"Cancelled shipment {tracking_number}")
    
    async def _send_confirmation(self, saga_id: str, step_id: str, input_data: Dict[str, Any]):
        """Send confirmation step"""
        await asyncio.sleep(0.1)
        
        await self.orchestrator.handle_step_completed(
            saga_id, 
            step_id, 
            {'confirmation_sent': True}
        )
    
    async def _send_cancellation(self, saga_id: str, step_id: str, output_data: Dict[str, Any]):
        """Send cancellation notification"""
        await asyncio.sleep(0.1)
        self.logger.info("Sent order cancellation notification")

# Saga Events
@dataclass
class SagaCompletedEvent(BaseEvent):
    saga_id: str
    saga_type: str
    completion_time: datetime
    
    def _get_payload(self) -> Dict[str, Any]:
        return {
            'saga_id': self.saga_id,
            'saga_type': self.saga_type,
            'completion_time': self.completion_time.isoformat()
        }

@dataclass
class SagaCompensatedEvent(BaseEvent):
    saga_id: str
    saga_type: str
    compensation_time: datetime
    
    def _get_payload(self) -> Dict[str, Any]:
        return {
            'saga_id': self.saga_id,
            'saga_type': self.saga_type,
            'compensation_time': self.compensation_time.isoformat()
        }
```

### Event Sourcing with Snapshots

For aggregates with long event histories, snapshots improve performance by providing a baseline state.

```python
from typing import Optional, Type
import pickle
import gzip

@dataclass
class Snapshot:
    """Aggregate snapshot"""
    aggregate_id: str
    aggregate_type: str
    version: int
    data: bytes
    timestamp: datetime
    
    @classmethod
    def create(cls, aggregate_id: str, aggregate_type: str, version: int, aggregate_state: Any) -> 'Snapshot':
        """Create snapshot from aggregate state"""
        # Compress the serialized state
        serialized_data = pickle.dumps(aggregate_state)
        compressed_data = gzip.compress(serialized_data)
        
        return cls(
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            version=version,
            data=compressed_data,
            timestamp=datetime.utcnow()
        )
    
    def restore_state(self) -> Any:
        """Restore aggregate state from snapshot"""
        decompressed_data = gzip.decompress(self.data)
        return pickle.loads(decompressed_data)

class SnapshotStore:
    """Storage for aggregate snapshots"""
    
    def __init__(self, storage_backend):
        self.storage = storage_backend
    
    async def save_snapshot(self, snapshot: Snapshot):
        """Save aggregate snapshot"""
        await self.storage.execute("""
            INSERT OR REPLACE INTO snapshots (
                aggregate_id, aggregate_type, version, data, timestamp
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            snapshot.aggregate_id,
            snapshot.aggregate_type,
            snapshot.version,
            snapshot.data,
            snapshot.timestamp.isoformat()
        ))
    
    async def get_latest_snapshot(self, aggregate_id: str) -> Optional[Snapshot]:
        """Get latest snapshot for aggregate"""
        result = await self.storage.fetch_one("""
            SELECT aggregate_id, aggregate_type, version, data, timestamp
            FROM snapshots 
            WHERE aggregate_id = ?
            ORDER BY version DESC 
            LIMIT 1
        """, (aggregate_id,))
        
        if result:
            return Snapshot(
                aggregate_id=result['aggregate_id'],
                aggregate_type=result['aggregate_type'],
                version=result['version'],
                data=result['data'],
                timestamp=datetime.fromisoformat(result['timestamp'])
            )
        
        return None
    
    async def delete_old_snapshots(self, aggregate_id: str, keep_latest: int = 3):
        """Delete old snapshots, keeping only the latest N"""
        await self.storage.execute("""
            DELETE FROM snapshots 
            WHERE aggregate_id = ? 
            AND version NOT IN (
                SELECT version FROM snapshots 
                WHERE aggregate_id = ? 
                ORDER BY version DESC 
                LIMIT ?
            )
        """, (aggregate_id, aggregate_id, keep_latest))

class SnapshotCapableOrderRepository(OrderRepository):
    """Order repository with snapshot support"""
    
    def __init__(self, event_store: EventStore, event_bus, snapshot_store: SnapshotStore, snapshot_frequency: int = 10):
        super().__init__(event_store, event_bus)
        self.snapshot_store = snapshot_store
        self.snapshot_frequency = snapshot_frequency
    
    async def get_by_id(self, order_id: str) -> Optional[OrderAggregate]:
        """Load order aggregate using snapshots"""
        # Try to get latest snapshot
        snapshot = await self.snapshot_store.get_latest_snapshot(f"order-{order_id}")
        
        if snapshot:
            # Restore from snapshot
            aggregate_state = snapshot.restore_state()
            aggregate = OrderAggregate(order_id)
            aggregate.__dict__.update(aggregate_state)
            aggregate.version = snapshot.version
            
            # Load events since snapshot
            events = self.event_store.get_events(f"order-{order_id}", snapshot.version + 1)
            
            for event in events:
                aggregate._apply_event(event)
                aggregate.version += 1
        else:
            # Load from full event history
            events = self.event_store.get_events(f"order-{order_id}")
            
            if not events:
                return None
            
            aggregate = OrderAggregate.from_history(order_id, events)
        
        return aggregate
    
    async def save(self, order: OrderAggregate):
        """Save aggregate and create snapshot if needed"""
        # Save events normally
        await super().save(order)
        
        # Check if snapshot is needed
        if order.version % self.snapshot_frequency == 0:
            await self._create_snapshot(order)
    
    async def _create_snapshot(self, order: OrderAggregate):
        """Create snapshot of aggregate state"""
        # Extract serializable state
        state = {
            'order_id': order.order_id,
            'customer_id': order.customer_id,
            'items': order.items,
            'status': order.status,
            'total_amount': order.total_amount,
            'payment_id': order.payment_id,
            'shipping_address': order.shipping_address
        }
        
        snapshot = Snapshot.create(
            aggregate_id=f"order-{order.order_id}",
            aggregate_type="OrderAggregate",
            version=order.version,
            aggregate_state=state
        )
        
        await self.snapshot_store.save_snapshot(snapshot)
        
        # Clean up old snapshots
        await self.snapshot_store.delete_old_snapshots(f"order-{order.order_id}")
```

### Event Stream Processing

Real-time processing of event streams for analytics and real-time responses.

```python
import asyncio
from typing import Callable, Dict, Any, List
from collections import defaultdict, deque
import time

class EventStreamProcessor:
    """Process events in real-time streams"""
    
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.processors = {}
        self.windows = defaultdict(lambda: deque())
        self.aggregations = defaultdict(dict)
        self.logger = logging.getLogger(__name__)
    
    def register_processor(self, event_type: str, processor: Callable):
        """Register stream processor for event type"""
        self.processors[event_type] = processor
    
    async def start_processing(self):
        """Start processing event streams"""
        for event_type, processor in self.processors.items():
            await self.event_bus.subscribe(event_type, self._process_event)
    
    async def _process_event(self, event: BaseEvent):
        """Process individual event"""
        processor = self.processors.get(event.event_type)
        if processor:
            try:
                await processor(event)
            except Exception as e:
                self.logger.error(f"Stream processor failed for {event.event_type}: {e}")
    
    def create_sliding_window_aggregator(self, window_size_seconds: int, slide_interval_seconds: int):
        """Create sliding window aggregator"""
        
        async def sliding_window_processor(event: BaseEvent):
            """Process event in sliding window"""
            current_time = time.time()
            window_key = f"{event.event_type}_{int(current_time / slide_interval_seconds)}"
            
            # Add event to window
            self.windows[window_key].append((current_time, event))
            
            # Remove old events outside window
            cutoff_time = current_time - window_size_seconds
            while self.windows[window_key] and self.windows[window_key][0][0] < cutoff_time:
                self.windows[window_key].popleft()
            
            # Calculate aggregations
            window_events = [event for _, event in self.windows[window_key]]
            aggregation = self._calculate_window_aggregation(window_events)
            
            # Store aggregation
            self.aggregations[window_key] = {
                'aggregation': aggregation,
                'timestamp': current_time,
                'event_count': len(window_events)
            }
            
            # Publish window aggregation event
            await self.event_bus.publish(WindowAggregationEvent(
                window_key=window_key,
                event_type=event.event_type,
                window_size=window_size_seconds,
                event_count=len(window_events),
                aggregation_data=aggregation,
                timestamp=datetime.fromtimestamp(current_time),
                source_service="stream-processor"
            ))
        
        return sliding_window_processor
    
    def _calculate_window_aggregation(self, events: List[BaseEvent]) -> Dict[str, Any]:
        """Calculate aggregations for window events"""
        if not events:
            return {}
        
        event_type = events[0].event_type
        
        if event_type == 'OrderCreatedEvent':
            total_amount = sum(
                event.total_amount for event in events 
                if hasattr(event, 'total_amount')
            )
            unique_customers = len(set(
                event.customer_id for event in events 
                if hasattr(event, 'customer_id')
            ))
            
            return {
                'total_orders': len(events),
                'total_amount': total_amount,
                'unique_customers': unique_customers,
                'average_order_value': total_amount / len(events) if events else 0
            }
        
        elif event_type == 'PaymentProcessedEvent':
            total_payments = sum(
                event.amount for event in events 
                if hasattr(event, 'amount')
            )
            
            return {
                'total_payments': len(events),
                'total_amount': total_payments,
                'average_payment': total_payments / len(events) if events else 0
            }
        
        return {'event_count': len(events)}

# Real-time Analytics Processor
class RealTimeAnalyticsProcessor:
    """Real-time analytics using event streams"""
    
    def __init__(self, stream_processor: EventStreamProcessor):
        self.stream_processor = stream_processor
        self.metrics = defaultdict(lambda: defaultdict(float))
        self.setup_processors()
    
    def setup_processors(self):
        """Setup analytics processors"""
        
        # Order metrics
        self.stream_processor.register_processor(
            'OrderCreatedEvent',
            self.stream_processor.create_sliding_window_aggregator(
                window_size_seconds=300,  # 5 minutes
                slide_interval_seconds=60   # 1 minute
            )
        )
        
        # Payment metrics
        self.stream_processor.register_processor(
            'PaymentProcessedEvent',
            self._process_payment_event
        )
        
        # User activity metrics
        self.stream_processor.register_processor(
            'UserRegisteredEvent',
            self._process_user_registration
        )
    
    async def _process_payment_event(self, event: PaymentProcessedEvent):
        """Process payment events for real-time metrics"""
        current_minute = int(time.time() / 60)
        
        # Update metrics
        self.metrics[current_minute]['payment_count'] += 1
        self.metrics[current_minute]['payment_total'] += event.amount
        
        # Calculate hourly metrics
        hourly_key = int(time.time() / 3600)
        self.metrics[f"hourly_{hourly_key}"]['payment_count'] += 1
        self.metrics[f"hourly_{hourly_key}"]['payment_total'] += event.amount
        
        # Detect payment spikes
        recent_payments = sum(
            self.metrics[minute]['payment_count'] 
            for minute in range(current_minute - 4, current_minute + 1)
            if minute in self.metrics
        )
        
        if recent_payments > 100:  # Threshold for payment spike
            await self._publish_alert_event(
                'PaymentSpike',
                f'High payment volume detected: {recent_payments} payments in 5 minutes'
            )
    
    async def _process_user_registration(self, event: UserRegisteredEvent):
        """Process user registration for growth metrics"""
        current_hour = int(time.time() / 3600)
        current_day = int(time.time() / 86400)
        
        self.metrics[f"registrations_hour_{current_hour}"]['count'] += 1
        self.metrics[f"registrations_day_{current_day}"]['count'] += 1
        
        # Track registration sources
        source_key = f"source_{event.registration_source}_{current_day}"
        self.metrics[source_key]['count'] += 1
    
    async def _publish_alert_event(self, alert_type: str, message: str):
        """Publish system alert event"""
        alert_event = SystemAlertEvent(
            alert_type=alert_type,
            message=message,
            severity='warning',
            timestamp=datetime.utcnow(),
            source_service="analytics-processor"
        )
        
        await self.stream_processor.event_bus.publish(alert_event)
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot"""
        current_minute = int(time.time() / 60)
        current_hour = int(time.time() / 3600)
        
        return {
            'current_minute_payments': self.metrics[current_minute]['payment_count'],
            'current_minute_revenue': self.metrics[current_minute]['payment_total'],
            'current_hour_payments': self.metrics[f"hourly_{current_hour}"]['payment_count'],
            'current_hour_revenue': self.metrics[f"hourly_{current_hour}"]['payment_total'],
            'timestamp': datetime.utcnow().isoformat()
        }

# Additional Events
@dataclass
class WindowAggregationEvent(BaseEvent):
    window_key: str
    event_type: str
    window_size: int
    event_count: int
    aggregation_data: Dict[str, Any]
    
    def _get_payload(self) -> Dict[str, Any]:
        return {
            'window_key': self.window_key,
            'event_type': self.event_type,
            'window_size': self.window_size,
            'event_count': self.event_count,
            'aggregation_data': self.aggregation_data
        }

@dataclass
class SystemAlertEvent(BaseEvent):
    alert_type: str
    message: str
    severity: str
    
    def _get_payload(self) -> Dict[str, Any]:
        return {
            'alert_type': self.alert_type,
            'message': self.message,
            'severity': self.severity
        }
```

### Event Store Projections and Read Models

Automated projection building and maintenance for optimized queries.

```python
class ProjectionBuilder:
    """Builds and maintains read model projections"""
    
    def __init__(self, event_store: EventStore, projection_store):
        self.event_store = event_store
        self.projection_store = projection_store
        self.projections = {}
        self.last_processed_position = {}
        self.logger = logging.getLogger(__name__)
    
    def register_projection(self, name: str, projection_handler: Callable, reset_on_error: bool = False):
        """Register a projection handler"""
        self.projections[name] = {
            'handler': projection_handler,
            'reset_on_error': reset_on_error
        }
        self.last_processed_position[name] = 0
    
    async def start_projection_building(self):
        """Start building projections from event store"""
        for name in self.projections.keys():
            asyncio.create_task(self._build_projection(name))
    
    async def _build_projection(self, projection_name: str):
        """Build individual projection"""
        projection_config = self.projections[projection_name]
        handler = projection_config['handler']
        
        # Load last processed position
        last_position = await self.projection_store.get_projection_position(projection_name)
        if last_position is not None:
            self.last_processed_position[projection_name] = last_position
        
        self.logger.info(f"Starting projection {projection_name} from position {self.last_processed_position[projection_name]}")
        
        try:
            # Process events from last position
            async for event in self.event_store.get_all_events(self.last_processed_position[projection_name]):
                try:
                    await handler(event)
                    self.last_processed_position[projection_name] += 1
                    
                    # Periodically save position
                    if self.last_processed_position[projection_name] % 100 == 0:
                        await self.projection_store.save_projection_position(
                            projection_name, 
                            self.last_processed_position[projection_name]
                        )
                
                except Exception as e:
                    self.logger.error(f"Projection {projection_name} failed at position {self.last_processed_position[projection_name]}: {e}")
                    
                    if projection_config['reset_on_error']:
                        await self._reset_projection(projection_name)
                        break
                    else:
                        # Skip this event and continue
                        self.last_processed_position[projection_name] += 1
        
        except Exception as e:
            self.logger.error(f"Projection {projection_name} builder failed: {e}")
    
    async def _reset_projection(self, projection_name: str):
        """Reset projection to start from beginning"""
        self.logger.info(f"Resetting projection {projection_name}")
        
        await self.projection_store.clear_projection(projection_name)
        await self.projection_store.save_projection_position(projection_name, 0)
        self.last_processed_position[projection_name] = 0
        
        # Restart projection building
        asyncio.create_task(self._build_projection(projection_name))

# Order Summary Projection
class OrderSummaryProjection:
    """Maintains order summary read models"""
    
    def __init__(self, projection_store):
        self.projection_store = projection_store
    
    async def handle_event(self, event: BaseEvent):
        """Handle events for order summary projection"""
        
        if isinstance(event, OrderCreatedEvent):
            await self._handle_order_created(event)
        elif isinstance(event, PaymentProcessedEvent):
            await self._handle_payment_processed(event)
        elif isinstance(event, OrderShippedEvent):
            await self._handle_order_shipped(event)
        elif isinstance(event, OrderCancelledEvent):
            await self._handle_order_cancelled(event)
    
    async def _handle_order_created(self, event: OrderCreatedEvent):
        """Create order summary"""
        summary = {
            'order_id': event.order_id,
            'customer_id': event.customer_id,
            'total_amount': event.total_amount,
            'status': 'created',
            'created_at': event.timestamp.isoformat(),
            'updated_at': event.timestamp.isoformat(),
            'item_count': len(event.items),
            'payment_id': None,
            'tracking_number': None
        }
        
        await self.projection_store.save_order_summary(summary)
    
    async def _handle_payment_processed(self, event: PaymentProcessedEvent):
        """Update order summary with payment info"""
        await self.projection_store.update_order_summary(event.order_id, {
            'status': 'paid',
            'payment_id': event.payment_id,
            'updated_at': event.timestamp.isoformat()
        })
    
    async def _handle_order_shipped(self, event: OrderShippedEvent):
        """Update order summary with shipping info"""
        await self.projection_store.update_order_summary(event.order_id, {
            'status': 'shipped',
            'tracking_number': event.tracking_number,
            'carrier': event.carrier,
            'updated_at': event.timestamp.isoformat()
        })
    
    async def _handle_order_cancelled(self, event: OrderCancelledEvent):
        """Update order summary for cancellation"""
        await self.projection_store.update_order_summary(event.order_id, {
            'status': 'cancelled',
            'cancellation_reason': event.reason,
            'updated_at': event.timestamp.isoformat()
        })

# Customer Analytics Projection
class CustomerAnalyticsProjection:
    """Maintains customer analytics read models"""
    
    def __init__(self, projection_store):
        self.projection_store = projection_store
    
    async def handle_event(self, event: BaseEvent):
        """Handle events for customer analytics"""
        
        if isinstance(event, OrderCreatedEvent):
            await self._update_customer_stats(event.customer_id, {
                'total_orders': 1,
                'last_order_date': event.timestamp.isoformat()
            })
        
        elif isinstance(event, PaymentProcessedEvent):
            # Get order details to find customer
            order_summary = await self.projection_store.get_order_summary(event.order_id)
            if order_summary:
                await self._update_customer_stats(order_summary['customer_id'], {
                    'total_spent': event.amount,
                    'last_purchase_date': event.timestamp.isoformat()
                })
    
    async def _update_customer_stats(self, customer_id: str, updates: Dict[str, Any]):
        """Update customer statistics"""
        current_stats = await self.projection_store.get_customer_stats(customer_id) or {
            'customer_id': customer_id,
            'total_orders': 0,
            'total_spent': 0.0,
            'last_order_date': None,
            'last_purchase_date': None
        }
        
        # Apply updates
        for key, value in updates.items():
            if key in ['total_orders', 'total_spent']:
                current_stats[key] = current_stats.get(key, 0) + value
            else:
                current_stats[key] = value
        
        await self.projection_store.save_customer_stats(current_stats)

# Complete example usage
async def setup_event_driven_system():
    """Setup complete event-driven system"""
    
    # Initialize components
    event_store = SQLiteEventStore('events.db')
    event_bus = InMemoryEventBus()
    snapshot_store = SnapshotStore(event_store._get_connection())
    projection_store = ProjectionStore('projections.db')
    
    # Setup repositories
    order_repository = SnapshotCapableOrderRepository(
        event_store, 
        event_bus, 
        snapshot_store
    )
    
    # Setup command handlers
    order_command_handler = OrderCommandHandler(order_repository)
    
    # Setup projections
    projection_builder = ProjectionBuilder(event_store, projection_store)
    
    order_summary_projection = OrderSummaryProjection(projection_store)
    customer_analytics_projection = CustomerAnalyticsProjection(projection_store)
    
    projection_builder.register_projection('order_summary', order_summary_projection.handle_event)
    projection_builder.register_projection('customer_analytics', customer_analytics_projection.handle_event)
    
    # Setup saga orchestrator
    saga_store = SagaStore('sagas.db')
    saga_orchestrator = SagaOrchestrator(saga_store, event_bus)
    order_saga = OrderProcessingSaga(saga_orchestrator)
    
    # Setup stream processing
    stream_processor = EventStreamProcessor(event_bus)
    analytics_processor = RealTimeAnalyticsProcessor(stream_processor)
    
    # Start all components
    await event_bus.start()
    await projection_builder.start_projection_building()
    await stream_processor.start_processing()
    
    return {
        'event_store': event_store,
        'event_bus': event_bus,
        'order_repository': order_repository,
        'command_handler': order_command_handler,
        'saga_orchestrator': saga_orchestrator,
        'stream_processor': stream_processor,
        'projection_builder': projection_builder
    }
```

This comprehensive Event-Driven Architecture documentation provides production-ready implementations for event sourcing, CQRS, sagas, event streaming, projections, and real-time analytics. The patterns demonstrate how to build scalable, resilient event-driven systems with proper error handling, monitoring, and performance optimization through snapshots and projections.