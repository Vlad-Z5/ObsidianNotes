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

This comprehensive coverage of Architecture Fundamentals provides the foundation for understanding all other architectural concepts. Each principle is explained with concrete examples and real-world applications, demonstrating how these fundamentals apply in practice.