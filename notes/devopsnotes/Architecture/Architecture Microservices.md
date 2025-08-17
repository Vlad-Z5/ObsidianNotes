# Architecture Microservices

## Core Concepts

Microservices architecture is an approach to building software systems as a collection of small, independent, and loosely coupled services that communicate over well-defined APIs. Each service is responsible for a specific business capability and can be developed, deployed, and scaled independently.

### Service Decomposition

#### Domain-Driven Design (DDD) Approach
**Definition:** Breaking down the system based on business domains and bounded contexts rather than technical layers.

**Example - E-commerce Platform Decomposition:**
```python
# Bounded Context: User Management
class UserDomain:
    """
    Responsible for user registration, authentication, and profile management
    Business Capability: Managing user lifecycle and authentication
    """
    
    class User:
        def __init__(self, email, password, profile_data):
            self.user_id = self._generate_id()
            self.email = email
            self.password_hash = self._hash_password(password)
            self.profile = UserProfile(profile_data)
            self.status = UserStatus.PENDING_VERIFICATION
            self.created_at = datetime.utcnow()
        
        def verify_email(self, verification_token):
            if self._is_valid_token(verification_token):
                self.status = UserStatus.ACTIVE
                return UserVerifiedEvent(self.user_id, self.email)
            raise InvalidTokenError()
        
        def update_profile(self, profile_updates):
            old_profile = self.profile.copy()
            self.profile.update(profile_updates)
            return ProfileUpdatedEvent(self.user_id, old_profile, self.profile)

    class UserService:
        def __init__(self, user_repository, email_service, event_publisher):
            self.user_repository = user_repository
            self.email_service = email_service
            self.event_publisher = event_publisher
        
        def register_user(self, registration_request):
            # Domain validation
            if self.user_repository.email_exists(registration_request.email):
                raise UserAlreadyExistsError()
            
            # Create domain entity
            user = User(
                registration_request.email,
                registration_request.password,
                registration_request.profile_data
            )
            
            # Persist
            saved_user = self.user_repository.save(user)
            
            # Domain events
            self.event_publisher.publish(
                UserRegisteredEvent(saved_user.user_id, saved_user.email)
            )
            
            # External communication
            self.email_service.send_verification_email(saved_user)
            
            return saved_user

# Bounded Context: Order Management
class OrderDomain:
    """
    Responsible for order processing, payment coordination, and fulfillment
    Business Capability: Managing the order lifecycle
    """
    
    class Order:
        def __init__(self, customer_id, items, shipping_address):
            self.order_id = self._generate_id()
            self.customer_id = customer_id
            self.items = items
            self.shipping_address = shipping_address
            self.status = OrderStatus.PENDING
            self.total_amount = self._calculate_total(items)
            self.created_at = datetime.utcnow()
        
        def add_item(self, item):
            if self.status != OrderStatus.PENDING:
                raise InvalidOrderStateError("Cannot modify confirmed order")
            
            self.items.append(item)
            self.total_amount = self._calculate_total(self.items)
            return ItemAddedEvent(self.order_id, item)
        
        def confirm(self):
            if not self.items:
                raise EmptyOrderError("Cannot confirm empty order")
            
            self.status = OrderStatus.CONFIRMED
            self.confirmed_at = datetime.utcnow()
            return OrderConfirmedEvent(self.order_id, self.total_amount, self.items)

    class OrderService:
        def __init__(self, order_repository, inventory_client, payment_client, event_publisher):
            self.order_repository = order_repository
            self.inventory_client = inventory_client
            self.payment_client = payment_client
            self.event_publisher = event_publisher
        
        async def process_order(self, order_request):
            # Create order entity
            order = Order(
                order_request.customer_id,
                order_request.items,
                order_request.shipping_address
            )
            
            # Check inventory availability (external service call)
            inventory_check = await self.inventory_client.check_availability(order.items)
            if not inventory_check.all_available:
                raise InsufficientInventoryError(inventory_check.unavailable_items)
            
            # Reserve inventory
            reservation = await self.inventory_client.reserve_items(
                order.items, 
                reservation_timeout=300  # 5 minutes
            )
            
            try:
                # Process payment (external service call)
                payment_result = await self.payment_client.charge_customer(
                    order.customer_id,
                    order.total_amount,
                    order_request.payment_method
                )
                
                if payment_result.successful:
                    # Confirm order
                    order.confirm()
                    order.payment_id = payment_result.payment_id
                    
                    # Persist
                    saved_order = self.order_repository.save(order)
                    
                    # Publish domain event
                    self.event_publisher.publish(
                        OrderConfirmedEvent(
                            saved_order.order_id,
                            saved_order.customer_id,
                            saved_order.total_amount
                        )
                    )
                    
                    return saved_order
                else:
                    # Release inventory reservation
                    await self.inventory_client.release_reservation(reservation.id)
                    raise PaymentFailedError(payment_result.error_message)
                    
            except Exception as e:
                # Compensating action - release reservation
                await self.inventory_client.release_reservation(reservation.id)
                raise

# Bounded Context: Inventory Management
class InventoryDomain:
    """
    Responsible for product availability, stock management, and reservations
    Business Capability: Managing product inventory and availability
    """
    
    class Product:
        def __init__(self, sku, name, description, price):
            self.sku = sku
            self.name = name
            self.description = description
            self.price = price
            self.quantity_available = 0
            self.reserved_quantity = 0
            self.reorder_level = 10
        
        def adjust_stock(self, quantity, reason):
            old_quantity = self.quantity_available
            self.quantity_available += quantity
            
            if self.quantity_available < 0:
                self.quantity_available = old_quantity
                raise InsufficientStockError()
            
            return StockAdjustedEvent(
                self.sku, 
                old_quantity, 
                self.quantity_available, 
                reason
            )
        
        def reserve(self, quantity):
            if self.quantity_available < quantity:
                raise InsufficientStockError()
            
            self.quantity_available -= quantity
            self.reserved_quantity += quantity
            
            return StockReservedEvent(self.sku, quantity)

    class InventoryService:
        def __init__(self, product_repository, event_publisher):
            self.product_repository = product_repository
            self.event_publisher = event_publisher
        
        def check_availability(self, items):
            """Check if all requested items are available"""
            availability_results = []
            
            for item in items:
                product = self.product_repository.find_by_sku(item.sku)
                
                if not product:
                    availability_results.append(
                        AvailabilityResult(item.sku, False, "Product not found")
                    )
                elif product.quantity_available < item.quantity:
                    availability_results.append(
                        AvailabilityResult(
                            item.sku, 
                            False, 
                            f"Only {product.quantity_available} available"
                        )
                    )
                else:
                    availability_results.append(
                        AvailabilityResult(item.sku, True, "Available")
                    )
            
            return AvailabilityCheckResult(availability_results)
        
        def reserve_items(self, items, reservation_timeout):
            """Reserve items for a specific time period"""
            reservation_id = self._generate_reservation_id()
            reserved_items = []
            
            try:
                for item in items:
                    product = self.product_repository.find_by_sku(item.sku)
                    reservation_event = product.reserve(item.quantity)
                    
                    self.product_repository.save(product)
                    reserved_items.append(ReservedItem(item.sku, item.quantity))
                    
                    # Publish event
                    self.event_publisher.publish(reservation_event)
                
                # Create reservation record with timeout
                reservation = Reservation(
                    reservation_id,
                    reserved_items,
                    expires_at=datetime.utcnow() + timedelta(seconds=reservation_timeout)
                )
                
                # Schedule reservation cleanup
                self._schedule_reservation_cleanup(reservation_id, reservation_timeout)
                
                return reservation
                
            except Exception as e:
                # Rollback any successful reservations
                for reserved_item in reserved_items:
                    self._rollback_reservation(reserved_item)
                raise
```

#### Service Boundaries and Data Ownership
**Principle:** Each microservice owns its data and business logic completely.

**Example - Service Boundary Definition:**
```yaml
# User Service Boundary
user_service:
  owns:
    data:
      - users table
      - user_profiles table
      - user_sessions table
      - email_verification_tokens table
    
    business_logic:
      - User registration and validation
      - Authentication and authorization
      - Profile management
      - Email verification
    
    external_dependencies:
      - Email service (for sending notifications)
      - Audit service (for logging user actions)
    
  exposes:
    apis:
      - POST /users (register user)
      - POST /auth/login (authenticate)
      - GET /users/{id} (get user profile)
      - PUT /users/{id} (update profile)
      - POST /auth/verify-email (verify email)
    
    events:
      - UserRegistered
      - UserVerified
      - ProfileUpdated
      - UserLoggedIn

# Order Service Boundary  
order_service:
  owns:
    data:
      - orders table
      - order_items table
      - order_history table
    
    business_logic:
      - Order creation and validation
      - Order state management
      - Order pricing calculations
      - Order fulfillment coordination
    
    external_dependencies:
      - Inventory service (check availability, reserve items)
      - Payment service (process payments)
      - Shipping service (calculate shipping, create shipments)
      - User service (validate customer)
    
  exposes:
    apis:
      - POST /orders (create order)
      - GET /orders/{id} (get order details)
      - PUT /orders/{id}/cancel (cancel order)
      - GET /customers/{id}/orders (get customer orders)
    
    events:
      - OrderCreated
      - OrderConfirmed
      - OrderCancelled
      - OrderShipped
```

### Communication Patterns

#### Synchronous Communication (HTTP/REST)
**When to Use:** For immediate response requirements, simple request-response patterns, and real-time data needs.

**Example - Order Service calling Inventory Service:**
```python
import httpx
import asyncio
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum

class ServiceDiscovery:
    """Service discovery for finding other microservices"""
    
    def __init__(self, consul_client):
        self.consul = consul_client
    
    async def get_service_url(self, service_name: str) -> str:
        """Get URL for a service from service registry"""
        services = await self.consul.health.service(service_name, passing=True)
        
        if not services:
            raise ServiceUnavailableError(f"Service {service_name} not available")
        
        # Simple round-robin selection
        service = services[0]['Service']
        return f"http://{service['Address']}:{service['Port']}"

class InventoryServiceClient:
    """HTTP client for Inventory Service"""
    
    def __init__(self, service_discovery: ServiceDiscovery):
        self.service_discovery = service_discovery
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),  # 30 second timeout
            limits=httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100
            )
        )
    
    async def check_availability(self, items: List[OrderItem]) -> AvailabilityResult:
        """Check if items are available for order"""
        service_url = await self.service_discovery.get_service_url("inventory-service")
        
        # Prepare request payload
        request_payload = {
            "items": [
                {"sku": item.sku, "quantity": item.quantity}
                for item in items
            ]
        }
        
        try:
            response = await self.client.post(
                f"{service_url}/api/v1/inventory/check-availability",
                json=request_payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "order-service/1.0"
                }
            )
            
            response.raise_for_status()
            result_data = response.json()
            
            return AvailabilityResult.from_dict(result_data)
            
        except httpx.TimeoutException:
            raise ServiceTimeoutError("Inventory service timeout")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ItemNotFoundError("One or more items not found")
            elif e.response.status_code >= 500:
                raise ServiceUnavailableError("Inventory service error")
            else:
                raise ServiceClientError(f"HTTP {e.response.status_code}")
    
    async def reserve_items(self, items: List[OrderItem], timeout_seconds: int) -> ReservationResult:
        """Reserve items for a specific duration"""
        service_url = await self.service_discovery.get_service_url("inventory-service")
        
        request_payload = {
            "items": [
                {"sku": item.sku, "quantity": item.quantity}
                for item in items
            ],
            "timeout_seconds": timeout_seconds,
            "requester": "order-service"
        }
        
        try:
            response = await self.client.post(
                f"{service_url}/api/v1/inventory/reservations",
                json=request_payload
            )
            
            response.raise_for_status()
            result_data = response.json()
            
            return ReservationResult(
                reservation_id=result_data["reservation_id"],
                reserved_items=result_data["reserved_items"],
                expires_at=datetime.fromisoformat(result_data["expires_at"])
            )
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                error_data = e.response.json()
                raise InsufficientInventoryError(error_data["unavailable_items"])
            raise ServiceClientError(f"Reservation failed: HTTP {e.response.status_code}")
    
    async def release_reservation(self, reservation_id: str):
        """Release a previously made reservation"""
        service_url = await self.service_discovery.get_service_url("inventory-service")
        
        try:
            response = await self.client.delete(
                f"{service_url}/api/v1/inventory/reservations/{reservation_id}"
            )
            
            response.raise_for_status()
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Reservation might have already expired - not an error
                pass
            else:
                raise ServiceClientError(f"Failed to release reservation: HTTP {e.response.status_code}")

# Circuit Breaker Pattern for Resilience
class CircuitBreaker:
    """Circuit breaker to prevent cascading failures"""
    
    def __init__(self, failure_threshold: int = 5, timeout_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.timeout_seconds
        )
    
    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

# Usage with Circuit Breaker
class ResilientInventoryClient(InventoryServiceClient):
    """Inventory client with circuit breaker protection"""
    
    def __init__(self, service_discovery: ServiceDiscovery):
        super().__init__(service_discovery)
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, timeout_seconds=30)
    
    async def check_availability(self, items: List[OrderItem]) -> AvailabilityResult:
        """Check availability with circuit breaker protection"""
        return await self.circuit_breaker.call(
            super().check_availability, 
            items
        )
    
    async def reserve_items(self, items: List[OrderItem], timeout_seconds: int) -> ReservationResult:
        """Reserve items with circuit breaker protection"""
        return await self.circuit_breaker.call(
            super().reserve_items,
            items,
            timeout_seconds
        )
```

#### Asynchronous Messaging
**When to Use:** For eventual consistency, decoupling services, handling high volume events, and improving system resilience.

**Example - Event-Driven Order Processing:**
```python
import asyncio
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Callable

class EventBus(ABC):
    """Abstract event bus for publishing and subscribing to events"""
    
    @abstractmethod
    async def publish(self, topic: str, event: Dict[str, Any], partition_key: str = None):
        """Publish an event to a topic"""
        pass
    
    @abstractmethod
    async def subscribe(self, topic: str, handler: Callable, consumer_group: str):
        """Subscribe to events from a topic"""
        pass

class KafkaEventBus(EventBus):
    """Kafka-based event bus implementation"""
    
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self.consumers = {}
    
    async def initialize(self):
        """Initialize Kafka producer and consumers"""
        from aiokafka import AIOKafkaProducer
        
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',  # Wait for all replicas to acknowledge
            retries=3,
            enable_idempotence=True
        )
        
        await self.producer.start()
    
    async def publish(self, topic: str, event: Dict[str, Any], partition_key: str = None):
        """Publish event to Kafka topic"""
        try:
            # Add metadata
            enriched_event = {
                **event,
                "timestamp": datetime.utcnow().isoformat(),
                "event_id": str(uuid.uuid4()),
                "source_service": "order-service"
            }
            
            # Send to Kafka
            await self.producer.send(
                topic=topic,
                value=enriched_event,
                key=partition_key
            )
            
            print(f"Published event to {topic}: {event.get('type', 'unknown')}")
            
        except Exception as e:
            print(f"Failed to publish event: {e}")
            raise EventPublishError(f"Failed to publish to {topic}: {e}")
    
    async def subscribe(self, topic: str, handler: Callable, consumer_group: str):
        """Subscribe to Kafka topic"""
        from aiokafka import AIOKafkaConsumer
        
        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=consumer_group,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            enable_auto_commit=False,  # Manual commit for reliability
            auto_offset_reset='earliest'
        )
        
        await consumer.start()
        self.consumers[f"{topic}:{consumer_group}"] = consumer
        
        try:
            async for message in consumer:
                try:
                    # Process event
                    await handler(message.value)
                    
                    # Commit offset after successful processing
                    await consumer.commit()
                    
                except Exception as e:
                    print(f"Error processing event: {e}")
                    # Could implement dead letter queue here
                    
        except Exception as e:
            print(f"Consumer error: {e}")
        finally:
            await consumer.stop()

# Event Definitions
@dataclass
class OrderCreatedEvent:
    order_id: str
    customer_id: str
    items: List[Dict[str, Any]]
    total_amount: float
    created_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "OrderCreated",
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "items": self.items,
            "total_amount": self.total_amount,
            "created_at": self.created_at
        }

@dataclass
class InventoryReservedEvent:
    reservation_id: str
    order_id: str
    items: List[Dict[str, Any]]
    expires_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "InventoryReserved",
            "reservation_id": self.reservation_id,
            "order_id": self.order_id,
            "items": self.items,
            "expires_at": self.expires_at
        }

# Event Handlers
class InventoryEventHandler:
    """Handles inventory-related events"""
    
    def __init__(self, inventory_service, event_bus):
        self.inventory_service = inventory_service
        self.event_bus = event_bus
    
    async def handle_order_created(self, event_data: Dict[str, Any]):
        """Handle OrderCreated event by reserving inventory"""
        try:
            # Parse event
            order_id = event_data["order_id"]
            items = event_data["items"]
            
            print(f"Processing inventory reservation for order {order_id}")
            
            # Reserve inventory
            reservation = await self.inventory_service.reserve_items(
                items, 
                timeout_seconds=300
            )
            
            # Publish success event
            reserved_event = InventoryReservedEvent(
                reservation_id=reservation.id,
                order_id=order_id,
                items=items,
                expires_at=reservation.expires_at.isoformat()
            )
            
            await self.event_bus.publish(
                topic="inventory.reserved",
                event=reserved_event.to_dict(),
                partition_key=order_id
            )
            
        except InsufficientInventoryError as e:
            # Publish failure event
            failure_event = {
                "type": "InventoryReservationFailed",
                "order_id": event_data["order_id"],
                "reason": "insufficient_inventory",
                "unavailable_items": e.unavailable_items
            }
            
            await self.event_bus.publish(
                topic="inventory.reservation_failed",
                event=failure_event,
                partition_key=event_data["order_id"]
            )
            
        except Exception as e:
            print(f"Unexpected error processing order created event: {e}")
            # Could send to dead letter queue

class PaymentEventHandler:
    """Handles payment-related events"""
    
    def __init__(self, payment_service, event_bus):
        self.payment_service = payment_service
        self.event_bus = event_bus
    
    async def handle_inventory_reserved(self, event_data: Dict[str, Any]):
        """Handle InventoryReserved event by processing payment"""
        try:
            order_id = event_data["order_id"]
            
            # Get order details (would typically call order service)
            order = await self._get_order_details(order_id)
            
            # Process payment
            payment_result = await self.payment_service.charge_customer(
                customer_id=order.customer_id,
                amount=order.total_amount,
                payment_method=order.payment_method
            )
            
            if payment_result.successful:
                # Publish payment success
                payment_event = {
                    "type": "PaymentProcessed",
                    "order_id": order_id,
                    "payment_id": payment_result.payment_id,
                    "amount": order.total_amount
                }
                
                await self.event_bus.publish(
                    topic="payment.processed",
                    event=payment_event,
                    partition_key=order_id
                )
            else:
                # Publish payment failure
                failure_event = {
                    "type": "PaymentFailed",
                    "order_id": order_id,
                    "reason": payment_result.error_message
                }
                
                await self.event_bus.publish(
                    topic="payment.failed",
                    event=failure_event,
                    partition_key=order_id
                )
                
        except Exception as e:
            print(f"Error processing inventory reserved event: {e}")

# Event Bus Setup and Subscription
class EventSubscriptionManager:
    """Manages event subscriptions for the service"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.handlers = {}
    
    def register_handler(self, topic: str, handler_class, consumer_group: str):
        """Register an event handler for a topic"""
        self.handlers[topic] = {
            "handler": handler_class,
            "consumer_group": consumer_group
        }
    
    async def start_subscriptions(self):
        """Start all event subscriptions"""
        tasks = []
        
        for topic, config in self.handlers.items():
            task = asyncio.create_task(
                self.event_bus.subscribe(
                    topic=topic,
                    handler=config["handler"],
                    consumer_group=config["consumer_group"]
                )
            )
            tasks.append(task)
        
        # Wait for all subscriptions to start
        await asyncio.gather(*tasks)

# Usage Example
async def setup_inventory_service_events():
    """Setup event handling for inventory service"""
    
    # Initialize event bus
    event_bus = KafkaEventBus("localhost:9092")
    await event_bus.initialize()
    
    # Create handlers
    inventory_handler = InventoryEventHandler(inventory_service, event_bus)
    
    # Setup subscriptions
    subscription_manager = EventSubscriptionManager(event_bus)
    
    subscription_manager.register_handler(
        topic="order.created",
        handler_class=inventory_handler.handle_order_created,
        consumer_group="inventory-service"
    )
    
    # Start processing events
    await subscription_manager.start_subscriptions()
```

#### API Gateway Pattern
**Purpose:** Centralize cross-cutting concerns and provide a single entry point for clients.

**Example - API Gateway Implementation:**
```python
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import time
import asyncio
from typing import Dict, Any, Optional

class APIGateway:
    """API Gateway for microservices"""
    
    def __init__(self):
        self.app = FastAPI(title="E-commerce API Gateway", version="1.0.0")
        self.service_registry = ServiceRegistry()
        self.rate_limiter = RateLimiter()
        self.auth_service = AuthenticationService()
        
        self._setup_middleware()
        self._setup_routes()
    
    def _setup_middleware(self):
        """Setup cross-cutting concerns middleware"""
        
        # CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Request logging
        @self.app.middleware("http")
        async def log_requests(request: Request, call_next):
            start_time = time.time()
            
            # Log request
            print(f"Request: {request.method} {request.url}")
            
            response = await call_next(request)
            
            # Log response
            process_time = time.time() - start_time
            print(f"Response: {response.status_code} in {process_time:.4f}s")
            
            return response
        
        # Rate limiting
        @self.app.middleware("http")
        async def rate_limit_middleware(request: Request, call_next):
            client_ip = request.client.host
            
            if not await self.rate_limiter.allow_request(client_ip):
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded"
                )
            
            return await call_next(request)
    
    def _setup_routes(self):
        """Setup API routes with service routing"""
        
        # User Service Routes
        @self.app.post("/api/v1/users")
        async def create_user(request: Request):
            return await self._route_to_service(
                service_name="user-service",
                path="/api/v1/users",
                method="POST",
                request=request,
                auth_required=False
            )
        
        @self.app.get("/api/v1/users/{user_id}")
        async def get_user(user_id: str, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
            return await self._route_to_service(
                service_name="user-service",
                path=f"/api/v1/users/{user_id}",
                method="GET",
                auth_token=credentials.credentials
            )
        
        # Order Service Routes
        @self.app.post("/api/v1/orders")
        async def create_order(request: Request, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
            return await self._route_to_service(
                service_name="order-service",
                path="/api/v1/orders",
                method="POST",
                request=request,
                auth_token=credentials.credentials
            )
        
        @self.app.get("/api/v1/orders/{order_id}")
        async def get_order(order_id: str, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
            return await self._route_to_service(
                service_name="order-service",
                path=f"/api/v1/orders/{order_id}",
                method="GET",
                auth_token=credentials.credentials
            )
        
        # Inventory Service Routes (Admin only)
        @self.app.get("/api/v1/inventory/{sku}")
        async def get_inventory(sku: str, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
            # Verify admin role
            user_info = await self.auth_service.verify_token(credentials.credentials)
            if not user_info.has_role("admin"):
                raise HTTPException(status_code=403, detail="Admin access required")
            
            return await self._route_to_service(
                service_name="inventory-service",
                path=f"/api/v1/inventory/{sku}",
                method="GET",
                auth_token=credentials.credentials
            )
    
    async def _route_to_service(
        self, 
        service_name: str, 
        path: str, 
        method: str,
        request: Request = None,
        auth_token: str = None,
        auth_required: bool = True
    ):
        """Route request to appropriate microservice"""
        
        try:
            # Get service endpoint
            service_url = await self.service_registry.get_service_url(service_name)
            
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "X-Gateway-Request-ID": str(uuid.uuid4()),
                "X-Forwarded-For": request.client.host if request else "gateway"
            }
            
            # Add authentication
            if auth_token:
                # Verify token
                user_info = await self.auth_service.verify_token(auth_token)
                headers["Authorization"] = f"Bearer {auth_token}"
                headers["X-User-ID"] = user_info.user_id
                headers["X-User-Roles"] = ",".join(user_info.roles)
            elif auth_required:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            # Get request body if present
            body = None
            if request and request.method in ["POST", "PUT", "PATCH"]:
                body = await request.json()
            
            # Make request to service
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method=method,
                    url=f"{service_url}{path}",
                    headers=headers,
                    json=body
                )
            
            # Return response
            return response.json()
            
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail=f"Service {service_name} timeout"
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Service {service_name} error"
            )
        except ServiceUnavailableError:
            raise HTTPException(
                status_code=503,
                detail=f"Service {service_name} unavailable"
            )

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, requests_per_minute: int = 100):
        self.requests_per_minute = requests_per_minute
        self.requests = {}  # client_ip -> list of request timestamps
    
    async def allow_request(self, client_ip: str) -> bool:
        """Check if request is allowed for client"""
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if req_time > minute_ago
            ]
        else:
            self.requests[client_ip] = []
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return False
        
        # Add current request
        self.requests[client_ip].append(now)
        return True

class AuthenticationService:
    """Authentication service for token verification"""
    
    def __init__(self, user_service_url: str):
        self.user_service_url = user_service_url
        self.token_cache = {}  # Simple token cache
    
    async def verify_token(self, token: str) -> UserInfo:
        """Verify JWT token and return user info"""
        
        # Check cache first
        if token in self.token_cache:
            cached_info, cache_time = self.token_cache[token]
            if time.time() - cache_time < 300:  # 5 minute cache
                return cached_info
        
        # Verify with user service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.user_service_url}/api/v1/auth/verify",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                user_data = response.json()
                user_info = UserInfo(
                    user_id=user_data["user_id"],
                    email=user_data["email"],
                    roles=user_data["roles"]
                )
                
                # Cache result
                self.token_cache[token] = (user_info, time.time())
                
                return user_info
            else:
                raise HTTPException(status_code=401, detail="Invalid token")

@dataclass
class UserInfo:
    user_id: str
    email: str
    roles: List[str]
    
    def has_role(self, role: str) -> bool:
        return role in self.roles
```

### Service Discovery and Registration

Dynamic service discovery enables microservices to find and communicate with each other without hardcoded configurations.

```python
import consul
import asyncio
import httpx
from typing import List, Dict, Optional
import random
import logging

class ServiceRegistry:
    """Service registry using Consul"""
    
    def __init__(self, consul_host: str = "localhost", consul_port: int = 8500):
        self.consul = consul.Consul(host=consul_host, port=consul_port)
        self.logger = logging.getLogger(__name__)
    
    async def register_service(
        self, 
        service_name: str, 
        service_id: str, 
        address: str, 
        port: int,
        health_check_url: str,
        tags: List[str] = None
    ):
        """Register a service with health check"""
        
        service_definition = {
            'name': service_name,
            'id': service_id,
            'address': address,
            'port': port,
            'tags': tags or [],
            'check': {
                'http': health_check_url,
                'interval': '10s',
                'timeout': '5s',
                'deregister_critical_service_after': '30s'
            }
        }
        
        try:
            self.consul.agent.service.register(**service_definition)
            self.logger.info(f"Registered service {service_name} at {address}:{port}")
            
        except Exception as e:
            self.logger.error(f"Failed to register service {service_name}: {e}")
            raise ServiceRegistrationError(f"Registration failed: {e}")
    
    async def deregister_service(self, service_id: str):
        """Deregister a service"""
        try:
            self.consul.agent.service.deregister(service_id)
            self.logger.info(f"Deregistered service {service_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to deregister service {service_id}: {e}")
    
    async def discover_service(self, service_name: str) -> List[ServiceInstance]:
        """Discover healthy instances of a service"""
        try:
            # Get only healthy services
            index, services = self.consul.health.service(service_name, passing=True)
            
            instances = []
            for service_info in services:
                service = service_info['Service']
                instances.append(ServiceInstance(
                    service_id=service['ID'],
                    service_name=service['Service'],
                    address=service['Address'],
                    port=service['Port'],
                    tags=service.get('Tags', [])
                ))
            
            return instances
            
        except Exception as e:
            self.logger.error(f"Service discovery failed for {service_name}: {e}")
            return []
    
    async def get_service_url(self, service_name: str, load_balance: bool = True) -> str:
        """Get service URL with optional load balancing"""
        instances = await self.discover_service(service_name)
        
        if not instances:
            raise ServiceUnavailableError(f"No healthy instances of {service_name}")
        
        # Load balancing
        if load_balance:
            instance = random.choice(instances)
        else:
            instance = instances[0]
        
        return f"http://{instance.address}:{instance.port}"

@dataclass
class ServiceInstance:
    service_id: str
    service_name: str
    address: str
    port: int
    tags: List[str]

class ServiceHealthCheck:
    """Health check implementation for services"""
    
    def __init__(self, dependencies: Dict[str, Callable]):
        self.dependencies = dependencies
        self.logger = logging.getLogger(__name__)
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }
        
        overall_healthy = True
        
        # Check each dependency
        for name, check_func in self.dependencies.items():
            try:
                check_result = await self._run_check(check_func)
                health_status["checks"][name] = {
                    "status": "healthy" if check_result else "unhealthy",
                    "details": check_result
                }
                
                if not check_result:
                    overall_healthy = False
                    
            except Exception as e:
                health_status["checks"][name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                overall_healthy = False
        
        health_status["status"] = "healthy" if overall_healthy else "unhealthy"
        return health_status
    
    async def _run_check(self, check_func: Callable) -> bool:
        """Run individual health check with timeout"""
        try:
            if asyncio.iscoroutinefunction(check_func):
                return await asyncio.wait_for(check_func(), timeout=5.0)
            else:
                return check_func()
        except asyncio.TimeoutError:
            return False

# Usage example
async def setup_service_discovery():
    """Setup service discovery for inventory service"""
    
    service_registry = ServiceRegistry()
    
    # Health check dependencies
    async def database_check():
        # Check database connectivity
        try:
            # Perform simple query
            await database.execute("SELECT 1")
            return True
        except:
            return False
    
    def memory_check():
        # Check memory usage
        import psutil
        memory_percent = psutil.virtual_memory().percent
        return memory_percent < 90  # Less than 90% memory usage
    
    health_checker = ServiceHealthCheck({
        "database": database_check,
        "memory": memory_check
    })
    
    # Register service
    await service_registry.register_service(
        service_name="inventory-service",
        service_id="inventory-service-1",
        address="10.0.1.100",
        port=8080,
        health_check_url="http://10.0.1.100:8080/health",
        tags=["v1.0", "production"]
    )
    
    return service_registry, health_checker
```

### Data Management Patterns

#### Database per Service
Each microservice owns its data and database schema completely.

```python
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import asyncpg
import motor.motor_asyncio

# User Service Database (PostgreSQL)
class UserServiceDatabase:
    """PostgreSQL database for user service"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.Base = declarative_base()
        self._define_models()
    
    def _define_models(self):
        """Define user service models"""
        
        class User(self.Base):
            __tablename__ = "users"
            
            user_id = Column(String, primary_key=True)
            email = Column(String, unique=True, nullable=False)
            password_hash = Column(String, nullable=False)
            first_name = Column(String)
            last_name = Column(String)
            is_verified = Column(Boolean, default=False)
            created_at = Column(DateTime)
            updated_at = Column(DateTime)
        
        class UserSession(self.Base):
            __tablename__ = "user_sessions"
            
            session_id = Column(String, primary_key=True)
            user_id = Column(String, nullable=False)
            expires_at = Column(DateTime, nullable=False)
            created_at = Column(DateTime)
        
        self.User = User
        self.UserSession = UserSession
    
    def create_tables(self):
        """Create database tables"""
        self.Base.metadata.create_all(bind=self.engine)

# Order Service Database (PostgreSQL with different schema)
class OrderServiceDatabase:
    """PostgreSQL database for order service"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.Base = declarative_base()
        self._define_models()
    
    def _define_models(self):
        """Define order service models"""
        
        class Order(self.Base):
            __tablename__ = "orders"
            
            order_id = Column(String, primary_key=True)
            customer_id = Column(String, nullable=False)  # Reference to user, not foreign key
            status = Column(String, nullable=False)
            total_amount = Column(Integer)  # Store as cents
            shipping_address = Column(Text)
            created_at = Column(DateTime)
            updated_at = Column(DateTime)
        
        class OrderItem(self.Base):
            __tablename__ = "order_items"
            
            item_id = Column(String, primary_key=True)
            order_id = Column(String, nullable=False)
            product_sku = Column(String, nullable=False)  # Reference to product, not foreign key
            quantity = Column(Integer, nullable=False)
            unit_price = Column(Integer, nullable=False)  # Store as cents
        
        self.Order = Order
        self.OrderItem = OrderItem

# Product Catalog Service Database (MongoDB)
class ProductCatalogDatabase:
    """MongoDB database for product catalog service"""
    
    def __init__(self, connection_string: str, database_name: str):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(connection_string)
        self.database = self.client[database_name]
        self.products = self.database.products
        self.categories = self.database.categories
    
    async def create_indexes(self):
        """Create database indexes"""
        await self.products.create_index("sku", unique=True)
        await self.products.create_index("category_id")
        await self.products.create_index([("name", "text"), ("description", "text")])
        await self.categories.create_index("name", unique=True)
    
    async def create_product(self, product_data: Dict[str, Any]) -> str:
        """Create new product"""
        result = await self.products.insert_one(product_data)
        return str(result.inserted_id)
    
    async def find_product_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        """Find product by SKU"""
        return await self.products.find_one({"sku": sku})
    
    async def search_products(self, query: str, category_id: str = None) -> List[Dict[str, Any]]:
        """Search products with text search"""
        search_filter = {"$text": {"$search": query}}
        
        if category_id:
            search_filter["category_id"] = category_id
        
        cursor = self.products.find(search_filter)
        return await cursor.to_list(length=100)

# Inventory Service Database (Redis for fast access)
class InventoryServiceDatabase:
    """Redis database for inventory service"""
    
    def __init__(self, redis_url: str):
        import redis.asyncio as redis
        self.redis = redis.from_url(redis_url)
    
    async def get_stock_level(self, sku: str) -> int:
        """Get current stock level"""
        stock = await self.redis.get(f"stock:{sku}")
        return int(stock) if stock else 0
    
    async def update_stock_level(self, sku: str, quantity: int) -> bool:
        """Update stock level atomically"""
        # Use Lua script for atomic update
        lua_script = """
        local current = redis.call('GET', KEYS[1])
        if current == false then
            current = 0
        else
            current = tonumber(current)
        end
        
        local new_quantity = current + tonumber(ARGV[1])
        if new_quantity < 0 then
            return -1  -- Insufficient stock
        end
        
        redis.call('SET', KEYS[1], new_quantity)
        return new_quantity
        """
        
        result = await self.redis.eval(lua_script, 1, f"stock:{sku}", quantity)
        return result >= 0
    
    async def reserve_stock(self, sku: str, quantity: int, reservation_id: str, ttl: int = 300) -> bool:
        """Reserve stock with expiration"""
        pipe = self.redis.pipeline()
        
        # Check and decrement available stock
        available_key = f"stock:{sku}"
        reserved_key = f"reserved:{sku}:{reservation_id}"
        
        # Use transaction
        async with pipe:
            pipe.watch(available_key)
            
            current_stock = await self.redis.get(available_key)
            current_stock = int(current_stock) if current_stock else 0
            
            if current_stock < quantity:
                return False
            
            pipe.multi()
            pipe.decrby(available_key, quantity)
            pipe.setex(reserved_key, ttl, quantity)
            
            await pipe.execute()
            return True
```

#### Saga Pattern for Data Consistency
Distributed transaction management across multiple services.

```python
import asyncio
from enum import Enum
from typing import Dict, Any, List, Optional, Callable
import uuid
import json

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
    step_id: str
    step_name: str
    service_name: str
    action: str
    compensation_action: str
    input_data: Dict[str, Any]
    status: SagaStepStatus = SagaStepStatus.PENDING
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class SagaOrchestrator:
    """Orchestrates distributed transactions using saga pattern"""
    
    def __init__(self, event_bus, saga_store):
        self.event_bus = event_bus
        self.saga_store = saga_store
        self.step_handlers = {}
        self.compensation_handlers = {}
        self.logger = logging.getLogger(__name__)
    
    def register_step_handler(self, service_name: str, action: str, handler: Callable):
        """Register handler for saga step"""
        key = f"{service_name}.{action}"
        self.step_handlers[key] = handler
    
    def register_compensation_handler(self, service_name: str, action: str, handler: Callable):
        """Register compensation handler for saga step"""
        key = f"{service_name}.{action}"
        self.compensation_handlers[key] = handler
    
    async def start_saga(self, saga_type: str, steps: List[Dict[str, Any]], input_data: Dict[str, Any]) -> str:
        """Start a new saga"""
        saga_id = str(uuid.uuid4())
        
        saga_steps = []
        for i, step_def in enumerate(steps):
            step = SagaStep(
                step_id=str(uuid.uuid4()),
                step_name=step_def["name"],
                service_name=step_def["service"],
                action=step_def["action"],
                compensation_action=step_def.get("compensation", ""),
                input_data=step_def.get("input_transform", lambda x: x)(input_data)
            )
            saga_steps.append(step)
        
        saga = {
            "saga_id": saga_id,
            "saga_type": saga_type,
            "status": SagaStatus.STARTED,
            "steps": saga_steps,
            "current_step": 0,
            "input_data": input_data,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await self.saga_store.save_saga(saga)
        
        # Start executing first step
        asyncio.create_task(self._execute_saga_step(saga_id, 0))
        
        return saga_id
    
    async def handle_step_completion(self, saga_id: str, step_id: str, output_data: Dict[str, Any]):
        """Handle successful step completion"""
        saga = await self.saga_store.get_saga(saga_id)
        if not saga:
            return
        
        # Update step status
        step = self._find_step(saga, step_id)
        if step:
            step.status = SagaStepStatus.COMPLETED
            step.output_data = output_data
        
        saga["current_step"] += 1
        saga["updated_at"] = datetime.utcnow()
        
        if saga["current_step"] >= len(saga["steps"]):
            # Saga completed successfully
            saga["status"] = SagaStatus.COMPLETED
            await self.saga_store.save_saga(saga)
            
            await self.event_bus.publish("saga.completed", {
                "saga_id": saga_id,
                "saga_type": saga["saga_type"]
            })
        else:
            # Execute next step
            await self.saga_store.save_saga(saga)
            asyncio.create_task(self._execute_saga_step(saga_id, saga["current_step"]))
    
    async def handle_step_failure(self, saga_id: str, step_id: str, error_message: str):
        """Handle step failure and start compensation"""
        saga = await self.saga_store.get_saga(saga_id)
        if not saga:
            return
        
        # Update step status
        step = self._find_step(saga, step_id)
        if step:
            step.status = SagaStepStatus.FAILED
            step.error_message = error_message
        
        saga["status"] = SagaStatus.COMPENSATING
        saga["updated_at"] = datetime.utcnow()
        await self.saga_store.save_saga(saga)
        
        # Start compensation process
        asyncio.create_task(self._compensate_saga(saga_id))
    
    async def _execute_saga_step(self, saga_id: str, step_index: int):
        """Execute individual saga step"""
        saga = await self.saga_store.get_saga(saga_id)
        if not saga or step_index >= len(saga["steps"]):
            return
        
        step = saga["steps"][step_index]
        handler_key = f"{step.service_name}.{step.action}"
        handler = self.step_handlers.get(handler_key)
        
        if not handler:
            await self.handle_step_failure(
                saga_id, 
                step.step_id, 
                f"No handler found for {handler_key}"
            )
            return
        
        try:
            await handler(saga_id, step.step_id, step.input_data)
            
        except Exception as e:
            self.logger.error(f"Saga step failed: {e}")
            await self.handle_step_failure(saga_id, step.step_id, str(e))
    
    async def _compensate_saga(self, saga_id: str):
        """Execute compensation actions in reverse order"""
        saga = await self.saga_store.get_saga(saga_id)
        if not saga:
            return
        
        # Get completed steps in reverse order
        completed_steps = [
            step for step in saga["steps"]
            if step.status == SagaStepStatus.COMPLETED
        ]
        
        for step in reversed(completed_steps):
            if step.compensation_action:
                handler_key = f"{step.service_name}.{step.compensation_action}"
                compensation_handler = self.compensation_handlers.get(handler_key)
                
                if compensation_handler:
                    try:
                        await compensation_handler(saga_id, step.step_id, step.output_data)
                        step.status = SagaStepStatus.COMPENSATED
                        
                    except Exception as e:
                        self.logger.error(f"Compensation failed for step {step.step_name}: {e}")
        
        saga["status"] = SagaStatus.COMPENSATED
        saga["updated_at"] = datetime.utcnow()
        await self.saga_store.save_saga(saga)
        
        await self.event_bus.publish("saga.compensated", {
            "saga_id": saga_id,
            "saga_type": saga["saga_type"]
        })
    
    def _find_step(self, saga: Dict[str, Any], step_id: str) -> Optional[SagaStep]:
        """Find step by ID"""
        for step in saga["steps"]:
            if step.step_id == step_id:
                return step
        return None

# Order Processing Saga Implementation
class OrderProcessingSaga:
    """Saga for order processing across multiple services"""
    
    def __init__(self, saga_orchestrator: SagaOrchestrator):
        self.orchestrator = saga_orchestrator
        self._register_handlers()
    
    def _register_handlers(self):
        """Register saga step and compensation handlers"""
        
        # Inventory service handlers
        self.orchestrator.register_step_handler(
            "inventory", "reserve", self._reserve_inventory
        )
        self.orchestrator.register_compensation_handler(
            "inventory", "release", self._release_inventory
        )
        
        # Payment service handlers
        self.orchestrator.register_step_handler(
            "payment", "charge", self._charge_payment
        )
        self.orchestrator.register_compensation_handler(
            "payment", "refund", self._refund_payment
        )
        
        # Shipping service handlers
        self.orchestrator.register_step_handler(
            "shipping", "create_shipment", self._create_shipment
        )
        self.orchestrator.register_compensation_handler(
            "shipping", "cancel_shipment", self._cancel_shipment
        )
    
    async def process_order(self, order_data: Dict[str, Any]) -> str:
        """Start order processing saga"""
        
        saga_steps = [
            {
                "name": "Reserve Inventory",
                "service": "inventory",
                "action": "reserve",
                "compensation": "release",
                "input_transform": lambda data: {
                    "items": data["items"],
                    "order_id": data["order_id"]
                }
            },
            {
                "name": "Process Payment",
                "service": "payment", 
                "action": "charge",
                "compensation": "refund",
                "input_transform": lambda data: {
                    "customer_id": data["customer_id"],
                    "amount": data["total_amount"],
                    "payment_method": data["payment_method"]
                }
            },
            {
                "name": "Create Shipment",
                "service": "shipping",
                "action": "create_shipment",
                "compensation": "cancel_shipment",
                "input_transform": lambda data: {
                    "order_id": data["order_id"],
                    "shipping_address": data["shipping_address"],
                    "items": data["items"]
                }
            }
        ]
        
        return await self.orchestrator.start_saga(
            saga_type="order_processing",
            steps=saga_steps,
            input_data=order_data
        )
    
    async def _reserve_inventory(self, saga_id: str, step_id: str, input_data: Dict[str, Any]):
        """Reserve inventory step"""
        # Simulate inventory service call
        await asyncio.sleep(0.1)
        
        # In real implementation, this would call inventory service
        reservation_id = str(uuid.uuid4())
        
        await self.orchestrator.handle_step_completion(saga_id, step_id, {
            "reservation_id": reservation_id,
            "reserved_items": input_data["items"]
        })
    
    async def _release_inventory(self, saga_id: str, step_id: str, output_data: Dict[str, Any]):
        """Release inventory compensation"""
        reservation_id = output_data.get("reservation_id")
        await asyncio.sleep(0.1)
        self.logger.info(f"Released inventory reservation {reservation_id}")
    
    async def _charge_payment(self, saga_id: str, step_id: str, input_data: Dict[str, Any]):
        """Charge payment step"""
        await asyncio.sleep(0.1)
        
        # Simulate payment processing
        payment_id = str(uuid.uuid4())
        
        await self.orchestrator.handle_step_completion(saga_id, step_id, {
            "payment_id": payment_id,
            "amount_charged": input_data["amount"]
        })
    
    async def _refund_payment(self, saga_id: str, step_id: str, output_data: Dict[str, Any]):
        """Refund payment compensation"""
        payment_id = output_data.get("payment_id")
        await asyncio.sleep(0.1)
        self.logger.info(f"Refunded payment {payment_id}")
    
    async def _create_shipment(self, saga_id: str, step_id: str, input_data: Dict[str, Any]):
        """Create shipment step"""
        await asyncio.sleep(0.1)
        
        tracking_number = f"TN{uuid.uuid4().hex[:8].upper()}"
        
        await self.orchestrator.handle_step_completion(saga_id, step_id, {
            "tracking_number": tracking_number,
            "shipment_id": str(uuid.uuid4())
        })
    
    async def _cancel_shipment(self, saga_id: str, step_id: str, output_data: Dict[str, Any]):
        """Cancel shipment compensation"""
        shipment_id = output_data.get("shipment_id")
        await asyncio.sleep(0.1)
        self.logger.info(f"Cancelled shipment {shipment_id}")
```

### Deployment and Scaling Patterns

#### Container Orchestration with Kubernetes
Production-ready Kubernetes deployments for microservices.

```yaml
# User Service Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
  labels:
    app: user-service
    version: v1
spec:
  replicas: 3
  selector:
    matchLabels:
      app: user-service
      version: v1
  template:
    metadata:
      labels:
        app: user-service
        version: v1
    spec:
      containers:
      - name: user-service
        image: user-service:1.0.0
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: user-service-secrets
              key: database-url
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: user-service-secrets
              key: jwt-secret
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: config-volume
          mountPath: /app/config
      volumes:
      - name: config-volume
        configMap:
          name: user-service-config

---
# User Service Service
apiVersion: v1
kind: Service
metadata:
  name: user-service
  labels:
    app: user-service
spec:
  selector:
    app: user-service
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
  type: ClusterIP

---
# User Service ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: user-service-config
data:
  application.yml: |
    server:
      port: 8080
    logging:
      level:
        com.example: INFO
    features:
      email_verification: true
      password_reset: true

---
# User Service Secrets
apiVersion: v1
kind: Secret
metadata:
  name: user-service-secrets
type: Opaque
data:
  database-url: cG9zdGdyZXNxbDovL3VzZXI6cGFzc0BkYi11c2VyOjU0MzIvdXNlcmRi
  jwt-secret: bXlfc3VwZXJfc2VjcmV0X2tleQ==

---
# User Service HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: user-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: user-service
  minReplicas: 3
  maxReplicas: 10
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

---
# Order Service Deployment with Redis Sidecar
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
  labels:
    app: order-service
    version: v1
spec:
  replicas: 5
  selector:
    matchLabels:
      app: order-service
      version: v1
  template:
    metadata:
      labels:
        app: order-service
        version: v1
    spec:
      containers:
      - name: order-service
        image: order-service:1.0.0
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: order-service-secrets
              key: database-url
        - name: REDIS_URL
          value: "redis://localhost:6379"
        - name: KAFKA_BROKERS
          value: "kafka:9092"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
      - name: redis-cache
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"

---
# Service Mesh with Istio
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: user-service-vs
spec:
  hosts:
  - user-service
  http:
  - match:
    - headers:
        version:
          exact: v2
    route:
    - destination:
        host: user-service
        subset: v2
      weight: 100
  - route:
    - destination:
        host: user-service
        subset: v1
      weight: 100

---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: user-service-dr
spec:
  host: user-service
  trafficPolicy:
    circuitBreaker:
      consecutiveErrors: 3
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 50
        maxRequestsPerConnection: 10
  subsets:
  - name: v1
    labels:
      version: v1
  - name: v2
    labels:
      version: v2
```

#### Blue-Green Deployment Strategy
Zero-downtime deployment implementation.

```python
import asyncio
import httpx
from typing import Dict, List, Optional
import time

class BlueGreenDeployment:
    """Blue-green deployment orchestrator"""
    
    def __init__(self, kubernetes_client, service_registry):
        self.k8s = kubernetes_client
        self.service_registry = service_registry
        self.logger = logging.getLogger(__name__)
    
    async def deploy_new_version(
        self, 
        service_name: str, 
        new_image: str, 
        health_check_path: str = "/health",
        validation_tests: List[Callable] = None
    ) -> bool:
        """Execute blue-green deployment"""
        
        try:
            # Step 1: Deploy green environment
            green_deployment = await self._deploy_green_environment(
                service_name, new_image
            )
            
            # Step 2: Wait for green environment to be ready
            await self._wait_for_deployment_ready(green_deployment, health_check_path)
            
            # Step 3: Run validation tests
            if validation_tests:
                validation_passed = await self._run_validation_tests(
                    green_deployment, validation_tests
                )
                if not validation_passed:
                    await self._cleanup_green_environment(green_deployment)
                    return False
            
            # Step 4: Switch traffic to green
            await self._switch_traffic_to_green(service_name, green_deployment)
            
            # Step 5: Monitor for issues
            await self._monitor_post_deployment(service_name, green_deployment)
            
            # Step 6: Cleanup old blue environment
            await self._cleanup_blue_environment(service_name)
            
            self.logger.info(f"Successfully deployed {service_name} with image {new_image}")
            return True
            
        except Exception as e:
            self.logger.error(f"Deployment failed: {e}")
            # Rollback if possible
            await self._rollback_deployment(service_name)
            return False
    
    async def _deploy_green_environment(self, service_name: str, new_image: str) -> str:
        """Deploy new version to green environment"""
        
        green_name = f"{service_name}-green"
        
        # Get current deployment spec
        current_deployment = await self.k8s.read_namespaced_deployment(
            name=service_name,
            namespace="default"
        )
        
        # Create green deployment spec
        green_spec = current_deployment.spec.copy()
        green_spec.template.spec.containers[0].image = new_image
        green_spec.selector.match_labels["version"] = "green"
        green_spec.template.metadata.labels["version"] = "green"
        
        green_deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": green_name,
                "labels": {
                    "app": service_name,
                    "version": "green"
                }
            },
            "spec": green_spec
        }
        
        # Deploy green environment
        await self.k8s.create_namespaced_deployment(
            namespace="default",
            body=green_deployment
        )
        
        return green_name
    
    async def _wait_for_deployment_ready(self, deployment_name: str, health_check_path: str):
        """Wait for deployment to be ready"""
        
        max_wait_time = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            # Check deployment status
            deployment = await self.k8s.read_namespaced_deployment(
                name=deployment_name,
                namespace="default"
            )
            
            if (deployment.status.ready_replicas and 
                deployment.status.ready_replicas == deployment.spec.replicas):
                
                # Additional health check
                if await self._health_check_pods(deployment_name, health_check_path):
                    return
            
            await asyncio.sleep(10)
        
        raise TimeoutError(f"Deployment {deployment_name} not ready within {max_wait_time}s")
    
    async def _health_check_pods(self, deployment_name: str, health_check_path: str) -> bool:
        """Perform health check on all pods"""
        
        # Get pods for deployment
        pods = await self.k8s.list_namespaced_pod(
            namespace="default",
            label_selector=f"app={deployment_name.replace('-green', '')},version=green"
        )
        
        for pod in pods.items:
            if pod.status.phase != "Running":
                return False
            
            # Port forward and health check
            pod_ip = pod.status.pod_ip
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"http://{pod_ip}:8080{health_check_path}")
                    if response.status_code != 200:
                        return False
            except:
                return False
        
        return True
    
    async def _run_validation_tests(self, deployment_name: str, tests: List[Callable]) -> bool:
        """Run validation tests against green environment"""
        
        for test in tests:
            try:
                result = await test(deployment_name)
                if not result:
                    self.logger.error(f"Validation test {test.__name__} failed")
                    return False
            except Exception as e:
                self.logger.error(f"Validation test {test.__name__} error: {e}")
                return False
        
        return True
    
    async def _switch_traffic_to_green(self, service_name: str, green_deployment: str):
        """Switch service traffic to green deployment"""
        
        # Update service selector to point to green
        service = await self.k8s.read_namespaced_service(
            name=service_name,
            namespace="default"
        )
        
        service.spec.selector["version"] = "green"
        
        await self.k8s.patch_namespaced_service(
            name=service_name,
            namespace="default",
            body=service
        )
        
        # Update service registry
        await self._update_service_registry(service_name, "green")
    
    async def _monitor_post_deployment(self, service_name: str, green_deployment: str):
        """Monitor deployment after traffic switch"""
        
        monitor_duration = 120  # 2 minutes
        start_time = time.time()
        
        while time.time() - start_time < monitor_duration:
            # Check error rates, response times, etc.
            metrics = await self._get_service_metrics(service_name)
            
            if (metrics.get("error_rate", 0) > 0.05 or  # 5% error rate threshold
                metrics.get("avg_response_time", 0) > 2000):  # 2s response time threshold
                
                self.logger.warning("High error rate or slow response detected, rolling back")
                await self._rollback_deployment(service_name)
                raise Exception("Deployment monitoring failed")
            
            await asyncio.sleep(10)
    
    async def _rollback_deployment(self, service_name: str):
        """Rollback to previous version"""
        
        # Switch service back to blue
        service = await self.k8s.read_namespaced_service(
            name=service_name,
            namespace="default"
        )
        
        service.spec.selector["version"] = "blue"
        
        await self.k8s.patch_namespaced_service(
            name=service_name,
            namespace="default",
            body=service
        )
        
        # Cleanup green deployment
        await self._cleanup_green_environment(f"{service_name}-green")

# Example validation tests
async def validate_api_endpoints(deployment_name: str) -> bool:
    """Validate that API endpoints are working"""
    
    service_url = await get_service_url_for_deployment(deployment_name)
    
    test_cases = [
        {"method": "GET", "path": "/health", "expected_status": 200},
        {"method": "GET", "path": "/api/v1/users/test", "expected_status": 404},
        {"method": "POST", "path": "/api/v1/auth/login", "expected_status": 400}
    ]
    
    async with httpx.AsyncClient() as client:
        for test_case in test_cases:
            try:
                response = await client.request(
                    method=test_case["method"],
                    url=f"{service_url}{test_case['path']}"
                )
                
                if response.status_code != test_case["expected_status"]:
                    return False
                    
            except Exception:
                return False
    
    return True

async def validate_database_connectivity(deployment_name: str) -> bool:
    """Validate database connectivity"""
    
    # This would check if the service can connect to its database
    # Implementation depends on your specific setup
    return True
```

This comprehensive microservices architecture documentation provides production-ready implementations for service discovery, data management patterns, saga orchestration, Kubernetes deployments, and blue-green deployment strategies. Each pattern includes detailed code examples with proper error handling, monitoring, and best practices for building scalable microservices systems.