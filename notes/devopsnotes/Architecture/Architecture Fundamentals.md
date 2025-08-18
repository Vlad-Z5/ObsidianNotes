# Architecture Fundamentals

## Core Concepts

Architecture fundamentals form the foundation of all software system design. These principles, patterns, and practices guide architects in creating robust, maintainable, and scalable systems.

### Architectural Principles

#### Separation of Concerns (SoC)
**Definition:** Dividing a system into distinct sections where each section addresses a separate concern or responsibility.

**Example:** In a web application:
```
├── Presentation Layer (UI concerns)
│   ├── Controllers (HTTP request handling)
│   ├── Views (Data presentation)
│   └── Web Assets (CSS, JS, images)
├── Business Logic Layer (Domain concerns)
│   ├── Services (Business rules)
│   ├── Domain Models (Business entities)
│   └── Workflows (Business processes)
└── Data Access Layer (Persistence concerns)
    ├── Repositories (Data access patterns)
    ├── Data Models (Database entities)
    └── Database Scripts (Schema, migrations)
```

**Benefits:**
- Reduces complexity by isolating different aspects
- Enables parallel development by different teams
- Improves maintainability and testability
- Facilitates technology changes in isolated layers

#### Single Responsibility Principle (SRP)
**Definition:** Every module, class, or function should have one reason to change - one responsibility.

**Example - Bad Design:**
```python
class UserManager:
    def save_user(self, user):
        # Validates user data
        if not user.email or '@' not in user.email:
            raise ValueError("Invalid email")
        
        # Saves to database
        db.save(user)
        
        # Sends welcome email
        email_service.send_welcome_email(user.email)
        
        # Logs the action
        logger.log(f"User {user.id} created")
```

**Good Design:**
```python
class UserValidator:
    def validate(self, user):
        if not user.email or '@' not in user.email:
            raise ValueError("Invalid email")

class UserRepository:
    def save(self, user):
        return db.save(user)

class EmailService:
    def send_welcome_email(self, email):
        # Send welcome email logic

class UserManager:
    def __init__(self, validator, repository, email_service, logger):
        self.validator = validator
        self.repository = repository
        self.email_service = email_service
        self.logger = logger
    
    def create_user(self, user):
        self.validator.validate(user)
        saved_user = self.repository.save(user)
        self.email_service.send_welcome_email(user.email)
        self.logger.log(f"User {saved_user.id} created")
        return saved_user
```

#### Open/Closed Principle (OCP)
**Definition:** Software entities should be open for extension but closed for modification.

**Example - Payment Processing:**
```python
# Base abstraction
class PaymentProcessor:
    def process_payment(self, amount, payment_details):
        raise NotImplementedError

# Concrete implementations
class CreditCardProcessor(PaymentProcessor):
    def process_payment(self, amount, payment_details):
        # Credit card specific logic
        return self._charge_credit_card(amount, payment_details)

class PayPalProcessor(PaymentProcessor):
    def process_payment(self, amount, payment_details):
        # PayPal specific logic
        return self._charge_paypal(amount, payment_details)

class BitcoinProcessor(PaymentProcessor):  # New payment method - extension
    def process_payment(self, amount, payment_details):
        # Bitcoin specific logic
        return self._charge_bitcoin(amount, payment_details)

# Payment service doesn't need modification for new payment types
class PaymentService:
    def __init__(self, processors: List[PaymentProcessor]):
        self.processors = {p.__class__.__name__: p for p in processors}
    
    def process(self, payment_type, amount, details):
        processor = self.processors.get(f"{payment_type}Processor")
        if processor:
            return processor.process_payment(amount, details)
        raise ValueError(f"Unsupported payment type: {payment_type}")
```

#### Dependency Inversion Principle (DIP)
**Definition:** High-level modules should not depend on low-level modules. Both should depend on abstractions.

**Example - Order Processing:**
```python
# Bad: High-level module depends on low-level modules
class OrderService:
    def __init__(self):
        self.email_sender = SMTPEmailSender()  # Concrete dependency
        self.payment_gateway = StripePaymentGateway()  # Concrete dependency
        self.inventory = MySQLInventory()  # Concrete dependency

# Good: Dependency inversion with abstractions
class EmailSender(ABC):
    @abstractmethod
    def send_email(self, to, subject, body): pass

class PaymentGateway(ABC):
    @abstractmethod
    def charge(self, amount, card_token): pass

class InventoryService(ABC):
    @abstractmethod
    def reserve_items(self, items): pass

class OrderService:
    def __init__(self, email_sender: EmailSender, 
                 payment_gateway: PaymentGateway,
                 inventory_service: InventoryService):
        self.email_sender = email_sender
        self.payment_gateway = payment_gateway
        self.inventory_service = inventory_service
    
    def process_order(self, order):
        # Business logic remains the same regardless of implementations
        self.inventory_service.reserve_items(order.items)
        self.payment_gateway.charge(order.total, order.payment_info)
        self.email_sender.send_email(order.customer_email, 
                                   "Order Confirmation", 
                                   order.confirmation_details)
```

#### Interface Segregation Principle (ISP)
**Definition:** No client should be forced to depend on methods it does not use.

**Example - Document Processing:**
```python
# Bad: Fat interface
class DocumentProcessor:
    def read_pdf(self, file): pass
    def read_word(self, file): pass
    def read_excel(self, file): pass
    def write_pdf(self, data): pass
    def write_word(self, data): pass
    def write_excel(self, data): pass
    def print_document(self, doc): pass
    def email_document(self, doc): pass

# Good: Segregated interfaces
class DocumentReader:
    def read(self, file): pass

class DocumentWriter:
    def write(self, data): pass

class DocumentPrinter:
    def print(self, document): pass

class DocumentEmailer:
    def email(self, document, recipient): pass

# Specific implementations only implement what they need
class PDFReader(DocumentReader):
    def read(self, file):
        # PDF reading logic
        pass

class EmailService(DocumentEmailer):
    def email(self, document, recipient):
        # Email logic - doesn't need to know about reading/writing
        pass
```

#### Don't Repeat Yourself (DRY)
**Definition:** Every piece of knowledge should have a single, unambiguous representation within a system.

**Example - Configuration Management:**
```python
# Bad: Repeated validation logic
class UserController:
    def create_user(self, user_data):
        if not user_data.get('email') or '@' not in user_data['email']:
            raise ValueError("Invalid email")
        if len(user_data.get('password', '')) < 8:
            raise ValueError("Password too short")
        # ... create user logic

class PasswordResetController:
    def reset_password(self, email, new_password):
        if not email or '@' not in email:
            raise ValueError("Invalid email")
        if len(new_password) < 8:
            raise ValueError("Password too short")
        # ... reset logic

# Good: Centralized validation
class ValidationService:
    @staticmethod
    def validate_email(email):
        if not email or '@' not in email:
            raise ValueError("Invalid email")
        return True
    
    @staticmethod
    def validate_password(password):
        if len(password) < 8:
            raise ValueError("Password too short")
        return True

class UserController:
    def create_user(self, user_data):
        ValidationService.validate_email(user_data.get('email'))
        ValidationService.validate_password(user_data.get('password'))
        # ... create user logic

class PasswordResetController:
    def reset_password(self, email, new_password):
        ValidationService.validate_email(email)
        ValidationService.validate_password(new_password)
        # ... reset logic
```

### Quality Attributes (Non-Functional Requirements)

#### Performance
**Definition:** How fast the system responds to requests and processes data.

**Measurement Metrics:**
- Response Time: Time to complete a single request
- Throughput: Number of requests processed per unit time
- Latency: Time delay in processing

**Example - Database Query Optimization:**
```sql
-- Bad: N+1 Query Problem
SELECT * FROM users WHERE active = 1;  -- 1 query
-- For each user, fetch their orders
SELECT * FROM orders WHERE user_id = 1;  -- N queries
SELECT * FROM orders WHERE user_id = 2;
-- ... continues for each user

-- Good: Single Query with JOIN
SELECT u.*, o.* 
FROM users u 
LEFT JOIN orders o ON u.id = o.user_id 
WHERE u.active = 1;  -- 1 query total
```

**Performance Optimization Strategies:**
- Caching (Redis, Memcached)
- Database indexing
- Connection pooling
- Asynchronous processing
- Content delivery networks (CDNs)

#### Scalability
**Definition:** The system's ability to handle increased load by adding resources.

**Types:**
1. **Vertical Scaling (Scale Up):** Adding more power to existing machines
2. **Horizontal Scaling (Scale Out):** Adding more machines to the pool

**Example - Microservices Scaling:**
```yaml
# Kubernetes deployment with horizontal scaling
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
spec:
  replicas: 3  # Start with 3 instances
  selector:
    matchLabels:
      app: user-service
  template:
    metadata:
      labels:
        app: user-service
    spec:
      containers:
      - name: user-service
        image: user-service:latest
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
---
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
```

#### Reliability
**Definition:** The system's ability to perform its required functions under stated conditions for a specified period.

**Reliability Patterns:**
1. **Retry Pattern:** Automatically retry failed operations
2. **Circuit Breaker:** Prevent cascading failures
3. **Bulkhead:** Isolate critical resources

**Example - Circuit Breaker Implementation:**
```python
import time
from enum import Enum

class CircuitState(Enum):
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Failing, reject requests
    HALF_OPEN = "HALF_OPEN"  # Testing if service recovered

class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise e
    
    def on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

# Usage
def unreliable_service_call():
    # Simulate service that might fail
    import random
    if random.random() < 0.3:  # 30% failure rate
        raise Exception("Service unavailable")
    return "Success"

circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=30)

# Protected service call
try:
    result = circuit_breaker.call(unreliable_service_call)
    print(f"Result: {result}")
except Exception as e:
    print(f"Failed: {e}")
```

#### Availability
**Definition:** The degree to which a system is operational and accessible when required.

**Availability Levels:**
- 99% (3.65 days downtime/year)
- 99.9% (8.76 hours downtime/year)
- 99.99% (52.56 minutes downtime/year)
- 99.999% (5.26 minutes downtime/year)

**High Availability Strategies:**
```yaml
# Example: Redis High Availability with Sentinel
# Master-Slave replication with automatic failover
version: '3.8'
services:
  redis-master:
    image: redis:6.2
    ports:
      - "6379:6379"
    volumes:
      - redis-master-data:/data
    command: redis-server --appendonly yes
  
  redis-slave:
    image: redis:6.2
    ports:
      - "6380:6379"
    volumes:
      - redis-slave-data:/data
    command: redis-server --slaveof redis-master 6379 --appendonly yes
    depends_on:
      - redis-master
  
  redis-sentinel:
    image: redis:6.2
    ports:
      - "26379:26379"
    volumes:
      - ./sentinel.conf:/usr/local/etc/redis/sentinel.conf
    command: redis-sentinel /usr/local/etc/redis/sentinel.conf
    depends_on:
      - redis-master
      - redis-slave

volumes:
  redis-master-data:
  redis-slave-data:
```

#### Security
**Definition:** Protection of system resources from unauthorized access, use, disclosure, disruption, modification, or destruction.

**Security Principles:**
1. **Least Privilege:** Users get minimum necessary permissions
2. **Defense in Depth:** Multiple layers of security
3. **Fail Secure:** Systems fail to a secure state

**Example - JWT Authentication with Role-Based Access:**
```python
import jwt
from functools import wraps
from flask import request, jsonify, current_app

class SecurityService:
    @staticmethod
    def generate_token(user_id, roles):
        payload = {
            'user_id': user_id,
            'roles': roles,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
    
    @staticmethod
    def verify_token(token):
        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

def require_auth(required_roles=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({'error': 'No token provided'}), 401
            
            # Remove 'Bearer ' prefix
            if token.startswith('Bearer '):
                token = token[7:]
            
            payload = SecurityService.verify_token(token)
            if not payload:
                return jsonify({'error': 'Invalid token'}), 401
            
            # Check roles if required
            if required_roles:
                user_roles = payload.get('roles', [])
                if not any(role in user_roles for role in required_roles):
                    return jsonify({'error': 'Insufficient permissions'}), 403
            
            request.current_user = payload
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Usage
@app.route('/admin/users')
@require_auth(required_roles=['admin', 'super_admin'])
def get_all_users():
    # Only admins can access this endpoint
    return jsonify({'users': User.get_all()})

@app.route('/profile')
@require_auth()
def get_profile():
    # Any authenticated user can access
    user_id = request.current_user['user_id']
    return jsonify({'profile': User.get_by_id(user_id)})
```

### Architecture Documentation

#### Architecture Diagrams
**Purpose:** Visual representation of system structure and relationships.

**Types:**
1. **Context Diagram:** System boundaries and external entities
2. **Container Diagram:** High-level technology choices
3. **Component Diagram:** Internal structure of containers
4. **Code Diagram:** Class relationships and interactions

**Example - C4 Model Documentation:**
```
System Context Diagram:
┌─────────────────────────────────────────────────────────┐
│                    E-commerce System                     │
│  ┌─────────────┐     ┌─────────────┐     ┌───────────┐  │
│  │   Customer  │────▶│  Web Store  │────▶│  Payment  │  │
│  │             │     │             │     │  Gateway  │  │
│  └─────────────┘     └─────────────┘     └───────────┘  │
│                              │                           │
│                              ▼                           │
│                      ┌─────────────┐                     │
│                      │ Inventory   │                     │
│                      │ Management  │                     │
│                      └─────────────┘                     │
└─────────────────────────────────────────────────────────┘

Container Diagram:
┌─────────────────────────────────────────────────────────┐
│                    Web Store Container                   │
│  ┌─────────────┐     ┌─────────────┐     ┌───────────┐  │
│  │   React     │────▶│   Node.js   │────▶│ PostgreSQL│  │
│  │    SPA      │     │  API Server │     │ Database  │  │
│  └─────────────┘     └─────────────┘     └───────────┘  │
│                              │                           │
│                              ▼                           │
│                      ┌─────────────┐                     │
│                      │    Redis    │                     │
│                      │    Cache    │                     │
│                      └─────────────┘                     │
└─────────────────────────────────────────────────────────┘
```

#### Interface Specifications
**Purpose:** Define contracts between system components.

**Example - API Contract (OpenAPI/Swagger):**
```yaml
openapi: 3.0.0
info:
  title: User Management API
  version: 1.0.0
  description: API for managing user accounts

paths:
  /users:
    post:
      summary: Create a new user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - email
                - password
                - firstName
                - lastName
              properties:
                email:
                  type: string
                  format: email
                  example: "john.doe@example.com"
                password:
                  type: string
                  minLength: 8
                  example: "securePassword123"
                firstName:
                  type: string
                  example: "John"
                lastName:
                  type: string
                  example: "Doe"
      responses:
        '201':
          description: User created successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  id:
                    type: integer
                    example: 12345
                  email:
                    type: string
                    example: "john.doe@example.com"
                  firstName:
                    type: string
                    example: "John"
                  lastName:
                    type: string
                    example: "Doe"
                  createdAt:
                    type: string
                    format: date-time
        '400':
          description: Invalid input data
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    type: string
                    example: "Invalid email format"
                  code:
                    type: string
                    example: "VALIDATION_ERROR"
```

### Design Thinking Process

#### Problem Identification
**Process:** Understanding the real problem before jumping to solutions.

**Example - E-commerce Performance Problem:**
```
Problem Statement: "Our e-commerce site is slow"

Root Cause Analysis:
1. Symptoms:
   - Page load times > 5 seconds
   - High bounce rate (60%)
   - Customer complaints about slowness

2. Investigation:
   - Database queries taking 2-3 seconds
   - Images not optimized (5MB+ sizes)
   - No caching implemented
   - Synchronous processing for all operations

3. Root Causes Identified:
   - Missing database indexes on frequently queried columns
   - No image compression pipeline
   - No CDN for static assets
   - Blocking operations in main request thread

4. Prioritized Solutions:
   High Impact, Low Effort:
   - Add database indexes
   - Implement Redis caching
   
   High Impact, High Effort:
   - Implement CDN
   - Asynchronous processing for non-critical operations
   
   Low Impact, Low Effort:
   - Image compression
   - Code optimization
```

#### Requirements Analysis
**Process:** Gathering and analyzing functional and non-functional requirements.

**Example - Online Banking System:**
```
Functional Requirements:
1. Account Management
   - Users can view account balances
   - Users can view transaction history
   - Users can transfer money between accounts

2. Security Features
   - Multi-factor authentication required
   - Transaction limits based on user verification level
   - Automatic logout after inactivity

Non-Functional Requirements:
1. Performance
   - Response time < 2 seconds for all operations
   - Support 10,000 concurrent users
   - 99.9% uptime requirement

2. Security
   - All data encrypted at rest and in transit
   - Compliance with PCI DSS standards
   - Audit trail for all transactions

3. Scalability
   - System must handle 100% increase in users within 6 months
   - Auto-scaling based on load

Requirements Traceability Matrix:
┌─────────────────┬──────────────────┬─────────────────┬──────────────┐
│ Requirement ID  │ Description      │ Component       │ Test Case    │
├─────────────────┼──────────────────┼─────────────────┼──────────────┤
│ FR-001          │ View Balance     │ Account Service │ TC-001       │
│ FR-002          │ Transfer Money   │ Transfer Service│ TC-002       │
│ NFR-001         │ Response < 2s    │ All Services    │ TC-003       │
│ NFR-002         │ 99.9% Uptime     │ Infrastructure  │ TC-004       │
└─────────────────┴──────────────────┴─────────────────┴──────────────┘
```

#### Trade-off Analysis
**Process:** Evaluating different architectural options and their implications.

**Example - Database Choice for Analytics Platform:**
```
Option 1: PostgreSQL (Relational)
Pros:
+ ACID compliance
+ Mature ecosystem
+ Good for complex queries
+ Team expertise exists

Cons:
- Limited horizontal scaling
- Performance issues with very large datasets
- Complex sharding implementation

Option 2: MongoDB (Document)
Pros:
+ Flexible schema
+ Good horizontal scaling
+ Better performance for simple queries
+ Built-in sharding

Cons:
- Eventual consistency model
- Limited join capabilities
- Less mature for analytics workloads

Option 3: ClickHouse (Columnar)
Pros:
+ Excellent for analytics workloads
+ Very high performance for aggregations
+ Good compression ratios
+ Built for time-series data

Cons:
- Limited update/delete capabilities
- Smaller ecosystem
- Learning curve for team

Decision Matrix:
┌─────────────────┬─────────────┬─────────────┬─────────────┐
│ Criteria        │ PostgreSQL  │ MongoDB     │ ClickHouse  │
├─────────────────┼─────────────┼─────────────┼─────────────┤
│ Performance     │ 3/5         │ 4/5         │ 5/5         │
│ Scalability     │ 2/5         │ 4/5         │ 5/5         │
│ Team Expertise  │ 5/5         │ 2/5         │ 1/5         │
│ Ecosystem       │ 5/5         │ 4/5         │ 3/5         │
│ Maintenance     │ 4/5         │ 3/5         │ 2/5         │
├─────────────────┼─────────────┼─────────────┼─────────────┤
│ Total Score     │ 19/25       │ 17/25       │ 16/25       │
└─────────────────┴─────────────┴─────────────┴─────────────┘

Recommendation: PostgreSQL for initial implementation due to team expertise 
and ecosystem maturity, with migration path to ClickHouse for analytics 
workloads as the platform scales.
```

### Advanced Architectural Concepts

#### Domain-Driven Design (DDD) Fundamentals

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import uuid
from datetime import datetime

# Value Objects - Immutable objects defined by their attributes
@dataclass(frozen=True)
class Money:
    amount: float
    currency: str
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
        if not self.currency or len(self.currency) != 3:
            raise ValueError("Currency must be 3-letter code")
    
    def add(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)

@dataclass(frozen=True)
class EmailAddress:
    value: str
    
    def __post_init__(self):
        if not self._is_valid_email(self.value):
            raise ValueError("Invalid email address")
    
    def _is_valid_email(self, email: str) -> bool:
        return "@" in email and "." in email.split("@")[1]

# Entities - Objects with identity that persists over time
class Customer:
    def __init__(self, customer_id: str, email: EmailAddress, name: str):
        self.id = customer_id
        self.email = email
        self.name = name
        self.created_at = datetime.now()
        self.version = 1
        self._domain_events: List[DomainEvent] = []
    
    def change_email(self, new_email: EmailAddress) -> None:
        if self.email != new_email:
            old_email = self.email
            self.email = new_email
            self.version += 1
            
            # Raise domain event
            self._domain_events.append(
                CustomerEmailChangedEvent(self.id, old_email, new_email)
            )
    
    def get_domain_events(self) -> List['DomainEvent']:
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events

# Aggregates - Consistency boundaries
class Order:
    def __init__(self, order_id: str, customer_id: str):
        self.id = order_id
        self.customer_id = customer_id
        self.items: List[OrderItem] = []
        self.status = OrderStatus.PENDING
        self.total = Money(0.0, "USD")
        self.version = 1
        self._domain_events: List[DomainEvent] = []
    
    def add_item(self, product_id: str, quantity: int, unit_price: Money) -> None:
        if self.status != OrderStatus.PENDING:
            raise DomainException("Cannot modify confirmed order")
        
        # Check business rules
        if quantity <= 0:
            raise DomainException("Quantity must be positive")
        
        # Add item
        item = OrderItem(product_id, quantity, unit_price)
        self.items.append(item)
        
        # Recalculate total
        self._recalculate_total()
        self.version += 1
    
    def confirm(self) -> None:
        if not self.items:
            raise DomainException("Cannot confirm empty order")
        
        if self.status != OrderStatus.PENDING:
            raise DomainException("Order already confirmed")
        
        self.status = OrderStatus.CONFIRMED
        self.version += 1
        
        # Raise domain event
        self._domain_events.append(
            OrderConfirmedEvent(self.id, self.customer_id, self.total)
        )
    
    def _recalculate_total(self) -> None:
        total_amount = sum(item.subtotal().amount for item in self.items)
        self.total = Money(total_amount, "USD")

# Domain Events
@dataclass(frozen=True)
class DomainEvent:
    event_id: str
    occurred_at: datetime
    aggregate_id: str

@dataclass(frozen=True)
class OrderConfirmedEvent(DomainEvent):
    customer_id: str
    total: Money
    
    def __init__(self, order_id: str, customer_id: str, total: Money):
        super().__init__(
            event_id=str(uuid.uuid4()),
            occurred_at=datetime.now(),
            aggregate_id=order_id
        )
        object.__setattr__(self, 'customer_id', customer_id)
        object.__setattr__(self, 'total', total)

# Domain Services - Stateless operations that don't belong to entities
class OrderPricingService:
    def __init__(self, pricing_repository: 'PricingRepository'):
        self.pricing_repository = pricing_repository
    
    def calculate_order_total(self, order: Order) -> Money:
        """Calculate order total with applied discounts and taxes"""
        subtotal = sum(item.subtotal().amount for item in order.items)
        
        # Apply customer-specific discounts
        discount = self._calculate_discount(order.customer_id, subtotal)
        
        # Apply taxes
        tax = self._calculate_tax(subtotal - discount)
        
        return Money(subtotal - discount + tax, "USD")
    
    def _calculate_discount(self, customer_id: str, subtotal: float) -> float:
        # Complex discount calculation logic
        customer_tier = self.pricing_repository.get_customer_tier(customer_id)
        return subtotal * customer_tier.discount_rate
    
    def _calculate_tax(self, amount: float) -> float:
        # Tax calculation based on business rules
        return amount * 0.08  # 8% tax rate

# Repositories - Persistence abstraction
class OrderRepository(ABC):
    @abstractmethod
    def find_by_id(self, order_id: str) -> Optional[Order]:
        pass
    
    @abstractmethod
    def save(self, order: Order) -> None:
        pass
    
    @abstractmethod
    def find_by_customer(self, customer_id: str) -> List[Order]:
        pass

class InMemoryOrderRepository(OrderRepository):
    def __init__(self):
        self._orders: Dict[str, Order] = {}
    
    def find_by_id(self, order_id: str) -> Optional[Order]:
        return self._orders.get(order_id)
    
    def save(self, order: Order) -> None:
        self._orders[order.id] = order
    
    def find_by_customer(self, customer_id: str) -> List[Order]:
        return [order for order in self._orders.values() 
                if order.customer_id == customer_id]

# Application Services - Orchestrate domain operations
class OrderApplicationService:
    def __init__(self, order_repository: OrderRepository, 
                 pricing_service: OrderPricingService,
                 event_publisher: 'EventPublisher'):
        self.order_repository = order_repository
        self.pricing_service = pricing_service
        self.event_publisher = event_publisher
    
    def create_order(self, command: 'CreateOrderCommand') -> str:
        """Create new order from command"""
        order_id = str(uuid.uuid4())
        order = Order(order_id, command.customer_id)
        
        # Add items
        for item_data in command.items:
            order.add_item(
                item_data.product_id,
                item_data.quantity,
                Money(item_data.unit_price, "USD")
            )
        
        # Save order
        self.order_repository.save(order)
        
        # Publish domain events
        events = order.get_domain_events()
        for event in events:
            self.event_publisher.publish(event)
        
        return order_id
    
    def confirm_order(self, order_id: str) -> None:
        """Confirm existing order"""
        order = self.order_repository.find_by_id(order_id)
        if not order:
            raise ApplicationException(f"Order {order_id} not found")
        
        # Domain operation
        order.confirm()
        
        # Persist changes
        self.order_repository.save(order)
        
        # Publish events
        events = order.get_domain_events()
        for event in events:
            self.event_publisher.publish(event)
```

#### Architectural Decision Framework

```python
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

class DecisionStatus(Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"

@dataclass
class ArchitecturalDecision:
    id: str
    title: str
    status: DecisionStatus
    date: datetime
    context: str
    decision: str
    consequences: List[str]
    alternatives: List[str]
    related_decisions: List[str]
    authors: List[str]
    
class ArchitecturalDecisionRecord:
    """ADR (Architecture Decision Record) implementation"""
    
    def __init__(self):
        self.decisions: Dict[str, ArchitecturalDecision] = {}
        self.decision_counter = 0
    
    def propose_decision(self, title: str, context: str, 
                        alternatives: List[str], 
                        recommended_decision: str,
                        consequences: List[str],
                        authors: List[str]) -> str:
        """Propose new architectural decision"""
        self.decision_counter += 1
        decision_id = f"ADR-{self.decision_counter:04d}"
        
        decision = ArchitecturalDecision(
            id=decision_id,
            title=title,
            status=DecisionStatus.PROPOSED,
            date=datetime.now(),
            context=context,
            decision=recommended_decision,
            consequences=consequences,
            alternatives=alternatives,
            related_decisions=[],
            authors=authors
        )
        
        self.decisions[decision_id] = decision
        return decision_id
    
    def accept_decision(self, decision_id: str) -> None:
        """Accept proposed decision"""
        if decision_id not in self.decisions:
            raise ValueError(f"Decision {decision_id} not found")
        
        decision = self.decisions[decision_id]
        if decision.status != DecisionStatus.PROPOSED:
            raise ValueError(f"Can only accept proposed decisions")
        
        decision.status = DecisionStatus.ACCEPTED
    
    def supersede_decision(self, old_decision_id: str, 
                          new_decision_id: str) -> None:
        """Mark decision as superseded by another"""
        if old_decision_id not in self.decisions:
            raise ValueError(f"Decision {old_decision_id} not found")
        
        old_decision = self.decisions[old_decision_id]
        old_decision.status = DecisionStatus.SUPERSEDED
        
        if new_decision_id in self.decisions:
            new_decision = self.decisions[new_decision_id]
            new_decision.related_decisions.append(old_decision_id)
    
    def generate_adr_document(self, decision_id: str) -> str:
        """Generate ADR document in markdown format"""
        decision = self.decisions.get(decision_id)
        if not decision:
            raise ValueError(f"Decision {decision_id} not found")
        
        return f"""# {decision.id}: {decision.title}

## Status
{decision.status.value.upper()}

## Context
{decision.context}

## Decision
{decision.decision}

## Alternatives Considered
{chr(10).join(f"- {alt}" for alt in decision.alternatives)}

## Consequences
{chr(10).join(f"- {cons}" for cons in decision.consequences)}

## Related Decisions
{chr(10).join(f"- {rel}" for rel in decision.related_decisions)}

---
**Authors:** {", ".join(decision.authors)}
**Date:** {decision.date.strftime("%Y-%m-%d")}
"""

class DecisionGovernanceFramework:
    """Framework for architectural decision governance"""
    
    def __init__(self):
        self.decision_criteria = {
            'performance': {'weight': 0.25, 'threshold': 7.0},
            'maintainability': {'weight': 0.20, 'threshold': 6.0},
            'scalability': {'weight': 0.20, 'threshold': 6.0},
            'security': {'weight': 0.15, 'threshold': 8.0},
            'cost': {'weight': 0.10, 'threshold': 6.0},
            'team_expertise': {'weight': 0.10, 'threshold': 5.0}
        }
        self.reviewers = []
        self.approval_thresholds = {
            'low_impact': 1,    # 1 reviewer
            'medium_impact': 2, # 2 reviewers
            'high_impact': 3    # 3 reviewers
        }
    
    def evaluate_decision(self, decision_options: List[Dict]) -> Dict:
        """Evaluate decision options using multi-criteria analysis"""
        evaluation_results = []
        
        for option in decision_options:
            scores = option.get('scores', {})
            weighted_score = 0
            
            for criterion, config in self.decision_criteria.items():
                score = scores.get(criterion, 0)
                weight = config['weight']
                weighted_score += score * weight
            
            # Check threshold compliance
            threshold_violations = []
            for criterion, config in self.decision_criteria.items():
                score = scores.get(criterion, 0)
                if score < config['threshold']:
                    threshold_violations.append(criterion)
            
            evaluation_results.append({
                'option': option['name'],
                'weighted_score': weighted_score,
                'threshold_violations': threshold_violations,
                'compliant': len(threshold_violations) == 0
            })
        
        # Sort by weighted score
        evaluation_results.sort(key=lambda x: x['weighted_score'], reverse=True)
        
        return {
            'recommendations': evaluation_results,
            'best_option': evaluation_results[0] if evaluation_results else None
        }
    
    def calculate_decision_impact(self, decision: ArchitecturalDecision) -> str:
        """Calculate decision impact level"""
        impact_factors = [
            'affects multiple systems',
            'requires significant investment',
            'changes core architecture',
            'impacts security posture',
            'affects team structure'
        ]
        
        # Count impact factors mentioned in context/consequences
        decision_text = f"{decision.context} {' '.join(decision.consequences)}".lower()
        impact_count = sum(1 for factor in impact_factors if factor in decision_text)
        
        if impact_count >= 3:
            return 'high_impact'
        elif impact_count >= 1:
            return 'medium_impact'
        else:
            return 'low_impact'
```

#### Quality Attribute Scenarios (QAS)

```python
from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum

class QualityAttribute(Enum):
    PERFORMANCE = "performance"
    AVAILABILITY = "availability"
    SECURITY = "security"
    USABILITY = "usability"
    MODIFIABILITY = "modifiability"
    TESTABILITY = "testability"
    INTEROPERABILITY = "interoperability"

@dataclass
class QualityScenario:
    id: str
    quality_attribute: QualityAttribute
    source: str           # Source of stimulus
    stimulus: str         # What triggers the scenario
    artifact: str         # What is affected
    environment: str      # Under what conditions
    response: str         # What the system should do
    response_measure: str # How we measure success

class QualityAttributeWorkshop:
    """QAW (Quality Attribute Workshop) implementation"""
    
    def __init__(self):
        self.scenarios: List[QualityScenario] = []
        self.prioritized_scenarios: List[tuple] = []
    
    def add_scenario(self, scenario: QualityScenario) -> None:
        """Add quality scenario"""
        self.scenarios.append(scenario)
    
    def prioritize_scenarios(self, stakeholder_votes: Dict[str, int]) -> None:
        """Prioritize scenarios based on stakeholder voting"""
        scenario_scores = []
        
        for scenario in self.scenarios:
            score = stakeholder_votes.get(scenario.id, 0)
            scenario_scores.append((scenario, score))
        
        # Sort by score (highest first)
        self.prioritized_scenarios = sorted(
            scenario_scores, 
            key=lambda x: x[1], 
            reverse=True
        )
    
    def generate_scenario_template(self, quality_attribute: QualityAttribute) -> str:
        """Generate scenario template for specific quality attribute"""
        templates = {
            QualityAttribute.PERFORMANCE: {
                'source': 'User/System',
                'stimulus': 'initiates transactions',
                'artifact': 'System',
                'environment': 'under normal/peak load',
                'response': 'processes transactions',
                'response_measure': 'within X seconds'
            },
            QualityAttribute.AVAILABILITY: {
                'source': 'Internal/External fault',
                'stimulus': 'causes system failure',
                'artifact': 'System/Component',
                'environment': 'during normal operation',
                'response': 'continues to operate/recovers',
                'response_measure': 'within X time with Y% availability'
            },
            QualityAttribute.SECURITY: {
                'source': 'Attacker',
                'stimulus': 'attempts unauthorized access',
                'artifact': 'System/Data',
                'environment': 'during operation',
                'response': 'detects and prevents access',
                'response_measure': 'with X% success rate'
            }
        }
        
        template = templates.get(quality_attribute, {})
        return f"""
Source: {template.get('source', '[SOURCE]')}
Stimulus: {template.get('stimulus', '[STIMULUS]')}
Artifact: {template.get('artifact', '[ARTIFACT]')}
Environment: {template.get('environment', '[ENVIRONMENT]')}
Response: {template.get('response', '[RESPONSE]')}
Response Measure: {template.get('response_measure', '[RESPONSE_MEASURE]')}
"""

# Example Quality Scenarios
performance_scenarios = [
    QualityScenario(
        id="PERF-001",
        quality_attribute=QualityAttribute.PERFORMANCE,
        source="User",
        stimulus="initiates search query",
        artifact="Search Service",
        environment="under normal load (1000 concurrent users)",
        response="returns search results",
        response_measure="within 200ms for 95% of requests"
    ),
    QualityScenario(
        id="PERF-002",
        quality_attribute=QualityAttribute.PERFORMANCE,
        source="Batch process",
        stimulus="processes daily transaction report",
        artifact="Analytics System",
        environment="during off-peak hours",
        response="generates complete report",
        response_measure="within 30 minutes for 10M transactions"
    )
]

availability_scenarios = [
    QualityScenario(
        id="AVAIL-001",
        quality_attribute=QualityAttribute.AVAILABILITY,
        source="Hardware failure",
        stimulus="causes database server failure",
        artifact="Database cluster",
        environment="during peak business hours",
        response="switches to backup server and continues operation",
        response_measure="within 5 seconds with no data loss"
    ),
    QualityScenario(
        id="AVAIL-002",
        quality_attribute=QualityAttribute.AVAILABILITY,
        source="Software defect",
        stimulus="causes application crash",
        artifact="Web application",
        environment="during normal operation",
        response="restarts automatically and logs incident",
        response_measure="within 30 seconds with 99.9% uptime"
    )
]
```

#### Architecture Evaluation Methods

```python
class ArchitectureEvaluationMethod:
    """Base class for architecture evaluation methods"""
    
    def __init__(self, name: str):
        self.name = name
        self.scenarios: List[QualityScenario] = []
        self.architectural_views = []
        self.evaluation_results = {}
    
    def evaluate(self, architecture_description: Dict) -> Dict:
        """Evaluate architecture against quality scenarios"""
        raise NotImplementedError

class ATAMEvaluation(ArchitectureEvaluationMethod):
    """ATAM (Architecture Tradeoff Analysis Method) implementation"""
    
    def __init__(self):
        super().__init__("ATAM")
        self.utility_tree = {}
        self.sensitivity_points = []
        self.tradeoff_points = []
        self.risks = []
        self.non_risks = []
    
    def build_utility_tree(self, quality_attributes: List[QualityAttribute]) -> Dict:
        """Build utility tree for quality attributes"""
        utility_tree = {}
        
        for qa in quality_attributes:
            utility_tree[qa.value] = {
                'importance': 'high',  # Would be determined by stakeholders
                'scenarios': [],
                'tactics': []
            }
        
        return utility_tree
    
    def identify_sensitivity_points(self, architecture: Dict, 
                                  scenarios: List[QualityScenario]) -> List[Dict]:
        """Identify architectural elements that affect quality scenarios"""
        sensitivity_points = []
        
        for scenario in scenarios:
            # Analyze which architectural elements affect this scenario
            affected_elements = self._analyze_scenario_impact(scenario, architecture)
            
            for element in affected_elements:
                sensitivity_points.append({
                    'element': element,
                    'scenario': scenario.id,
                    'quality_attribute': scenario.quality_attribute.value,
                    'sensitivity_reason': f"Changes to {element} directly impact {scenario.response_measure}"
                })
        
        return sensitivity_points
    
    def identify_tradeoff_points(self, sensitivity_points: List[Dict]) -> List[Dict]:
        """Identify points where multiple quality attributes trade off"""
        tradeoff_points = []
        
        # Group sensitivity points by architectural element
        element_impacts = {}
        for sp in sensitivity_points:
            element = sp['element']
            if element not in element_impacts:
                element_impacts[element] = []
            element_impacts[element].append(sp)
        
        # Find elements that affect multiple quality attributes
        for element, impacts in element_impacts.items():
            quality_attributes = set(impact['quality_attribute'] for impact in impacts)
            
            if len(quality_attributes) > 1:
                tradeoff_points.append({
                    'element': element,
                    'affected_qualities': list(quality_attributes),
                    'tradeoff_description': f"{element} affects {', '.join(quality_attributes)}"
                })
        
        return tradeoff_points
    
    def _analyze_scenario_impact(self, scenario: QualityScenario, 
                               architecture: Dict) -> List[str]:
        """Analyze which architectural elements are impacted by scenario"""
        # This would involve detailed architectural analysis
        # For this example, we'll use simplified logic
        affected_elements = []
        
        if scenario.quality_attribute == QualityAttribute.PERFORMANCE:
            affected_elements.extend(['Database', 'Caching Layer', 'Load Balancer'])
        elif scenario.quality_attribute == QualityAttribute.AVAILABILITY:
            affected_elements.extend(['Redundancy Components', 'Failover Mechanisms'])
        elif scenario.quality_attribute == QualityAttribute.SECURITY:
            affected_elements.extend(['Authentication Service', 'Authorization Components'])
        
        return affected_elements

class CBAMEvaluation(ArchitectureEvaluationMethod):
    """CBAM (Cost Benefit Analysis Method) implementation"""
    
    def __init__(self):
        super().__init__("CBAM")
        self.architectural_strategies = []
        self.cost_estimates = {}
        self.benefit_estimates = {}
    
    def calculate_roi(self, strategy: Dict) -> float:
        """Calculate return on investment for architectural strategy"""
        costs = self.cost_estimates.get(strategy['id'], 0)
        benefits = self.benefit_estimates.get(strategy['id'], 0)
        
        if costs == 0:
            return float('inf') if benefits > 0 else 0
        
        return (benefits - costs) / costs
    
    def prioritize_strategies(self, strategies: List[Dict]) -> List[Dict]:
        """Prioritize architectural strategies by ROI"""
        strategy_roi = []
        
        for strategy in strategies:
            roi = self.calculate_roi(strategy)
            strategy_roi.append({
                'strategy': strategy,
                'roi': roi,
                'cost': self.cost_estimates.get(strategy['id'], 0),
                'benefit': self.benefit_estimates.get(strategy['id'], 0)
            })
        
        # Sort by ROI (highest first)
        return sorted(strategy_roi, key=lambda x: x['roi'], reverse=True)
```

This comprehensive coverage of Architecture Fundamentals provides the foundation for understanding all other architectural concepts. Each principle is explained with concrete examples and real-world applications, demonstrating how these fundamentals apply in practice through advanced domain-driven design, architectural decision frameworks, quality attribute workshops, and systematic evaluation methods.