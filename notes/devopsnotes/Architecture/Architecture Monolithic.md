# Architecture Monolithic

## Monolithic Design

Monolithic architecture is a software design pattern where all components of an application are interconnected and deployed as a single unit. While often contrasted with microservices, well-designed monoliths can be highly effective, especially when built with modular principles.

### Modular Monolith

#### Clear Module Boundaries
**Definition:** Organizing a monolithic application into well-defined modules that maintain clear boundaries and responsibilities.

**Example - E-commerce Modular Monolith:**
```python
# Module structure for an e-commerce application
"""
ecommerce/
├── __init__.py
├── main.py                 # Application entry point
├── config/
│   ├── __init__.py
│   ├── settings.py         # Configuration management
│   └── database.py         # Database setup
├── shared/                 # Shared utilities and common code
│   ├── __init__.py
│   ├── exceptions.py       # Common exceptions
│   ├── models.py          # Base models
│   ├── utils.py           # Utility functions
│   └── events.py          # Internal event system
├── user/                  # User Management Module
│   ├── __init__.py
│   ├── models.py          # User data models
│   ├── services.py        # User business logic
│   ├── repositories.py    # User data access
│   ├── api.py            # User API endpoints
│   └── events.py         # User domain events
├── catalog/               # Product Catalog Module
│   ├── __init__.py
│   ├── models.py          # Product models
│   ├── services.py        # Catalog business logic
│   ├── repositories.py    # Catalog data access
│   ├── api.py            # Catalog API endpoints
│   └── search.py         # Product search functionality
├── orders/                # Order Management Module
│   ├── __init__.py
│   ├── models.py          # Order models
│   ├── services.py        # Order business logic
│   ├── repositories.py    # Order data access
│   ├── api.py            # Order API endpoints
│   └── workflows.py      # Order processing workflows
├── inventory/             # Inventory Management Module
│   ├── __init__.py
│   ├── models.py          # Inventory models
│   ├── services.py        # Inventory business logic
│   ├── repositories.py    # Inventory data access
│   └── api.py            # Inventory API endpoints
└── payments/              # Payment Processing Module
    ├── __init__.py
    ├── models.py          # Payment models
    ├── services.py        # Payment business logic
    ├── processors.py      # Payment gateway integrations
    └── api.py            # Payment API endpoints
"""

# Shared base classes and utilities
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import uuid

# shared/events.py - Internal event system for modules
class DomainEvent:
    """Base class for domain events within the monolith"""
    
    def __init__(self, event_type: str, payload: Dict[str, Any]):
        self.event_id = str(uuid.uuid4())
        self.event_type = event_type
        self.payload = payload
        self.timestamp = datetime.utcnow()
        self.source_module = self.__class__.__module__.split('.')[0]

class EventBus:
    """Simple in-process event bus for module communication"""
    
    def __init__(self):
        self._handlers = {}
    
    def subscribe(self, event_type: str, handler):
        """Subscribe a handler to an event type"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def publish(self, event: DomainEvent):
        """Publish an event to all subscribed handlers"""
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                # Log error but don't fail the entire operation
                print(f"Event handler error: {e}")

# Global event bus instance
event_bus = EventBus()

# shared/models.py - Base models
class BaseEntity:
    """Base entity class with common fields"""
    
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def update_timestamp(self):
        self.updated_at = datetime.utcnow()

class BaseRepository(ABC):
    """Base repository interface"""
    
    @abstractmethod
    def save(self, entity) -> Any:
        pass
    
    @abstractmethod
    def find_by_id(self, entity_id: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        pass

# User Module Implementation
# user/models.py
class User(BaseEntity):
    """User domain entity"""
    
    def __init__(self, email: str, password_hash: str, profile_data: Dict[str, Any]):
        super().__init__()
        self.email = email
        self.password_hash = password_hash
        self.first_name = profile_data.get('first_name', '')
        self.last_name = profile_data.get('last_name', '')
        self.phone = profile_data.get('phone', '')
        self.is_active = True
        self.email_verified = False
    
    def verify_email(self):
        """Mark email as verified"""
        if not self.email_verified:
            self.email_verified = True
            self.update_timestamp()
            
            # Publish internal event
            event = DomainEvent(
                event_type="user.email_verified",
                payload={
                    "user_id": self.id,
                    "email": self.email
                }
            )
            event_bus.publish(event)
    
    def update_profile(self, profile_updates: Dict[str, Any]):
        """Update user profile information"""
        old_data = {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone": self.phone
        }
        
        self.first_name = profile_updates.get('first_name', self.first_name)
        self.last_name = profile_updates.get('last_name', self.last_name)
        self.phone = profile_updates.get('phone', self.phone)
        self.update_timestamp()
        
        # Publish internal event
        event = DomainEvent(
            event_type="user.profile_updated",
            payload={
                "user_id": self.id,
                "old_data": old_data,
                "new_data": profile_updates
            }
        )
        event_bus.publish(event)

# user/repositories.py
class UserRepository(BaseRepository):
    """User data access layer"""
    
    def __init__(self, database_session):
        self.db = database_session
    
    def save(self, user: User) -> User:
        """Save user to database"""
        # In a real implementation, this would use SQLAlchemy or similar ORM
        query = """
            INSERT INTO users (id, email, password_hash, first_name, last_name, phone, 
                             is_active, email_verified, created_at, updated_at)
            VALUES (%(id)s, %(email)s, %(password_hash)s, %(first_name)s, %(last_name)s, 
                   %(phone)s, %(is_active)s, %(email_verified)s, %(created_at)s, %(updated_at)s)
            ON CONFLICT (id) DO UPDATE SET
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                phone = EXCLUDED.phone,
                is_active = EXCLUDED.is_active,
                email_verified = EXCLUDED.email_verified,
                updated_at = EXCLUDED.updated_at
        """
        
        self.db.execute(query, {
            'id': user.id,
            'email': user.email,
            'password_hash': user.password_hash,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
            'is_active': user.is_active,
            'email_verified': user.email_verified,
            'created_at': user.created_at,
            'updated_at': user.updated_at
        })
        
        self.db.commit()
        return user
    
    def find_by_id(self, user_id: str) -> Optional[User]:
        """Find user by ID"""
        query = "SELECT * FROM users WHERE id = %(user_id)s"
        result = self.db.execute(query, {'user_id': user_id}).fetchone()
        
        if result:
            return self._map_to_user(result)
        return None
    
    def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email"""
        query = "SELECT * FROM users WHERE email = %(email)s"
        result = self.db.execute(query, {'email': email}).fetchone()
        
        if result:
            return self._map_to_user(result)
        return None
    
    def delete(self, user_id: str) -> bool:
        """Soft delete user"""
        query = "UPDATE users SET is_active = false WHERE id = %(user_id)s"
        self.db.execute(query, {'user_id': user_id})
        self.db.commit()
        return True
    
    def _map_to_user(self, row) -> User:
        """Map database row to User entity"""
        user = User(
            email=row['email'],
            password_hash=row['password_hash'],
            profile_data={
                'first_name': row['first_name'],
                'last_name': row['last_name'],
                'phone': row['phone']
            }
        )
        user.id = row['id']
        user.is_active = row['is_active']
        user.email_verified = row['email_verified']
        user.created_at = row['created_at']
        user.updated_at = row['updated_at']
        return user

# user/services.py
class UserService:
    """User business logic"""
    
    def __init__(self, user_repository: UserRepository, email_service):
        self.user_repository = user_repository
        self.email_service = email_service
    
    def register_user(self, registration_data: Dict[str, Any]) -> User:
        """Register a new user"""
        # Business validation
        if self.user_repository.find_by_email(registration_data['email']):
            raise ValueError("Email already registered")
        
        # Create user entity
        user = User(
            email=registration_data['email'],
            password_hash=self._hash_password(registration_data['password']),
            profile_data={
                'first_name': registration_data.get('first_name', ''),
                'last_name': registration_data.get('last_name', ''),
                'phone': registration_data.get('phone', '')
            }
        )
        
        # Save user
        saved_user = self.user_repository.save(user)
        
        # Send verification email
        self.email_service.send_verification_email(saved_user)
        
        # Publish domain event
        event = DomainEvent(
            event_type="user.registered",
            payload={
                "user_id": saved_user.id,
                "email": saved_user.email,
                "registration_source": "web"
            }
        )
        event_bus.publish(event)
        
        return saved_user
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user credentials"""
        user = self.user_repository.find_by_email(email)
        
        if user and self._verify_password(password, user.password_hash):
            if not user.is_active:
                raise ValueError("Account is deactivated")
            
            # Publish login event
            event = DomainEvent(
                event_type="user.logged_in",
                payload={
                    "user_id": user.id,
                    "email": user.email,
                    "login_timestamp": datetime.utcnow().isoformat()
                }
            )
            event_bus.publish(event)
            
            return user
        
        return None
    
    def update_user_profile(self, user_id: str, profile_updates: Dict[str, Any]) -> User:
        """Update user profile"""
        user = self.user_repository.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        user.update_profile(profile_updates)
        return self.user_repository.save(user)
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        import bcrypt
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

# Orders Module Implementation
# orders/models.py
class OrderItem:
    """Order item value object"""
    
    def __init__(self, product_id: str, sku: str, quantity: int, unit_price: float):
        self.product_id = product_id
        self.sku = sku
        self.quantity = quantity
        self.unit_price = unit_price
    
    @property
    def total_price(self) -> float:
        return self.quantity * self.unit_price

class Order(BaseEntity):
    """Order domain entity"""
    
    def __init__(self, customer_id: str, shipping_address: Dict[str, str]):
        super().__init__()
        self.customer_id = customer_id
        self.shipping_address = shipping_address
        self.items = []
        self.status = "pending"
        self.subtotal = 0.0
        self.tax_amount = 0.0
        self.shipping_cost = 0.0
        self.total_amount = 0.0
        self.payment_id = None
        self.shipped_at = None
        self.delivered_at = None
    
    def add_item(self, item: OrderItem):
        """Add item to order"""
        if self.status != "pending":
            raise ValueError("Cannot modify confirmed order")
        
        # Check if item already exists
        existing_item = next(
            (i for i in self.items if i.product_id == item.product_id), 
            None
        )
        
        if existing_item:
            existing_item.quantity += item.quantity
        else:
            self.items.append(item)
        
        self._recalculate_totals()
        self.update_timestamp()
    
    def remove_item(self, product_id: str):
        """Remove item from order"""
        if self.status != "pending":
            raise ValueError("Cannot modify confirmed order")
        
        self.items = [item for item in self.items if item.product_id != product_id]
        self._recalculate_totals()
        self.update_timestamp()
    
    def confirm(self, payment_id: str):
        """Confirm the order with payment"""
        if self.status != "pending":
            raise ValueError("Order already confirmed")
        
        if not self.items:
            raise ValueError("Cannot confirm empty order")
        
        self.status = "confirmed"
        self.payment_id = payment_id
        self.update_timestamp()
        
        # Publish order confirmed event
        event = DomainEvent(
            event_type="order.confirmed",
            payload={
                "order_id": self.id,
                "customer_id": self.customer_id,
                "total_amount": self.total_amount,
                "items": [
                    {
                        "product_id": item.product_id,
                        "sku": item.sku,
                        "quantity": item.quantity,
                        "unit_price": item.unit_price
                    }
                    for item in self.items
                ]
            }
        )
        event_bus.publish(event)
    
    def ship(self, tracking_number: str = None):
        """Mark order as shipped"""
        if self.status != "confirmed":
            raise ValueError("Order must be confirmed before shipping")
        
        self.status = "shipped"
        self.shipped_at = datetime.utcnow()
        self.update_timestamp()
        
        # Publish order shipped event
        event = DomainEvent(
            event_type="order.shipped",
            payload={
                "order_id": self.id,
                "customer_id": self.customer_id,
                "tracking_number": tracking_number,
                "shipped_at": self.shipped_at.isoformat()
            }
        )
        event_bus.publish(event)
    
    def _recalculate_totals(self):
        """Recalculate order totals"""
        self.subtotal = sum(item.total_price for item in self.items)
        self.tax_amount = self.subtotal * 0.08  # 8% tax rate
        self.shipping_cost = 10.0 if self.subtotal < 100 else 0.0  # Free shipping over $100
        self.total_amount = self.subtotal + self.tax_amount + self.shipping_cost

# orders/services.py
class OrderService:
    """Order business logic"""
    
    def __init__(self, order_repository, inventory_service, payment_service, notification_service):
        self.order_repository = order_repository
        self.inventory_service = inventory_service
        self.payment_service = payment_service
        self.notification_service = notification_service
        
        # Subscribe to relevant events
        event_bus.subscribe("inventory.reserved", self._handle_inventory_reserved)
        event_bus.subscribe("payment.processed", self._handle_payment_processed)
    
    def create_order(self, customer_id: str, items_data: List[Dict], shipping_address: Dict) -> Order:
        """Create a new order"""
        # Create order entity
        order = Order(customer_id, shipping_address)
        
        # Add items to order
        for item_data in items_data:
            # Get product details from catalog module
            product = self._get_product_details(item_data['product_id'])
            
            order_item = OrderItem(
                product_id=item_data['product_id'],
                sku=product['sku'],
                quantity=item_data['quantity'],
                unit_price=product['price']
            )
            order.add_item(order_item)
        
        # Save order
        saved_order = self.order_repository.save(order)
        
        # Check inventory availability
        self._check_and_reserve_inventory(saved_order)
        
        return saved_order
    
    def process_payment_and_confirm(self, order_id: str, payment_details: Dict) -> Order:
        """Process payment and confirm order"""
        order = self.order_repository.find_by_id(order_id)
        if not order:
            raise ValueError("Order not found")
        
        # Process payment
        payment_result = self.payment_service.process_payment(
            amount=order.total_amount,
            payment_details=payment_details
        )
        
        if payment_result['success']:
            # Confirm order
            order.confirm(payment_result['payment_id'])
            saved_order = self.order_repository.save(order)
            
            # Send confirmation notification
            self.notification_service.send_order_confirmation(saved_order)
            
            return saved_order
        else:
            raise ValueError(f"Payment failed: {payment_result['error']}")
    
    def _check_and_reserve_inventory(self, order: Order):
        """Check inventory and reserve items"""
        # This would interact with the inventory module
        reservation_request = {
            "order_id": order.id,
            "items": [
                {"sku": item.sku, "quantity": item.quantity}
                for item in order.items
            ]
        }
        
        # Publish inventory reservation request
        event = DomainEvent(
            event_type="inventory.reserve_request",
            payload=reservation_request
        )
        event_bus.publish(event)
    
    def _handle_inventory_reserved(self, event: DomainEvent):
        """Handle inventory reserved event"""
        order_id = event.payload.get('order_id')
        if order_id:
            # Update order status or trigger next step
            print(f"Inventory reserved for order {order_id}")
    
    def _handle_payment_processed(self, event: DomainEvent):
        """Handle payment processed event"""
        order_id = event.payload.get('order_id')
        if order_id:
            order = self.order_repository.find_by_id(order_id)
            if order:
                # Move to fulfillment
                self._initiate_fulfillment(order)
    
    def _get_product_details(self, product_id: str) -> Dict:
        """Get product details from catalog module"""
        # This would interact with the catalog module
        # For now, return mock data
        return {
            "id": product_id,
            "sku": f"SKU-{product_id}",
            "name": f"Product {product_id}",
            "price": 29.99
        }
    
    def _initiate_fulfillment(self, order: Order):
        """Initiate order fulfillment process"""
        # Publish fulfillment request
        event = DomainEvent(
            event_type="fulfillment.initiate",
            payload={
                "order_id": order.id,
                "shipping_address": order.shipping_address,
                "items": [
                    {"sku": item.sku, "quantity": item.quantity}
                    for item in order.items
                ]
            }
        )
        event_bus.publish(event)
```

#### Dependency Management
**Principle:** Clear dependency direction and minimal coupling between modules.

**Example - Dependency Injection Container:**
```python
# config/container.py - Dependency injection setup
class DIContainer:
    """Simple dependency injection container for the monolith"""
    
    def __init__(self):
        self._services = {}
        self._singletons = {}
    
    def register_singleton(self, interface, implementation):
        """Register a singleton service"""
        self._singletons[interface] = implementation
    
    def register_transient(self, interface, factory_func):
        """Register a transient service with factory function"""
        self._services[interface] = factory_func
    
    def get(self, interface):
        """Get service instance"""
        if interface in self._singletons:
            return self._singletons[interface]
        
        if interface in self._services:
            return self._services[interface]()
        
        raise ValueError(f"Service {interface} not registered")

# config/setup.py - Application setup with dependency injection
def setup_application():
    """Setup application with all dependencies"""
    container = DIContainer()
    
    # Database setup
    database_session = create_database_session()
    
    # Register repositories
    container.register_transient(
        'user_repository',
        lambda: UserRepository(database_session)
    )
    container.register_transient(
        'order_repository',
        lambda: OrderRepository(database_session)
    )
    container.register_transient(
        'product_repository',
        lambda: ProductRepository(database_session)
    )
    
    # Register external services
    container.register_singleton(
        'email_service',
        EmailService(smtp_config=get_smtp_config())
    )
    container.register_singleton(
        'payment_service',
        PaymentService(stripe_config=get_stripe_config())
    )
    container.register_singleton(
        'notification_service',
        NotificationService()
    )
    
    # Register business services
    container.register_transient(
        'user_service',
        lambda: UserService(
            container.get('user_repository'),
            container.get('email_service')
        )
    )
    container.register_transient(
        'order_service',
        lambda: OrderService(
            container.get('order_repository'),
            container.get('inventory_service'),
            container.get('payment_service'),
            container.get('notification_service')
        )
    )
    container.register_transient(
        'catalog_service',
        lambda: CatalogService(
            container.get('product_repository')
        )
    )
    
    return container

# Module interface contracts
# shared/interfaces.py
from abc import ABC, abstractmethod

class EmailServiceInterface(ABC):
    """Email service interface"""
    
    @abstractmethod
    def send_verification_email(self, user: User):
        pass
    
    @abstractmethod
    def send_order_confirmation(self, order: Order):
        pass

class PaymentServiceInterface(ABC):
    """Payment service interface"""
    
    @abstractmethod
    def process_payment(self, amount: float, payment_details: Dict) -> Dict:
        pass
    
    @abstractmethod
    def refund_payment(self, payment_id: str, amount: float) -> Dict:
        pass

class InventoryServiceInterface(ABC):
    """Inventory service interface"""
    
    @abstractmethod
    def check_availability(self, items: List[Dict]) -> Dict:
        pass
    
    @abstractmethod
    def reserve_items(self, order_id: str, items: List[Dict]) -> Dict:
        pass
    
    @abstractmethod
    def release_reservation(self, order_id: str) -> bool:
        pass

# Dependency rules enforcement
class ModuleDependencyChecker:
    """Enforce module dependency rules"""
    
    ALLOWED_DEPENDENCIES = {
        'user': ['shared'],
        'catalog': ['shared'],
        'orders': ['shared', 'user', 'catalog'],  # Orders can depend on user and catalog
        'inventory': ['shared', 'catalog'],  # Inventory can depend on catalog
        'payments': ['shared'],
        'fulfillment': ['shared', 'orders', 'inventory']  # Fulfillment can depend on orders and inventory
    }
    
    @classmethod
    def validate_import(cls, importing_module: str, imported_module: str) -> bool:
        """Validate if import is allowed based on dependency rules"""
        if importing_module not in cls.ALLOWED_DEPENDENCIES:
            return False
        
        allowed_deps = cls.ALLOWED_DEPENDENCIES[importing_module]
        return imported_module in allowed_deps or imported_module.startswith('shared.')
    
    @classmethod
    def check_circular_dependencies(cls) -> List[str]:
        """Check for circular dependencies"""
        def has_circular_dependency(module, visited, path):
            if module in path:
                return path[path.index(module):] + [module]
            
            if module in visited:
                return None
            
            visited.add(module)
            path.append(module)
            
            dependencies = cls.ALLOWED_DEPENDENCIES.get(module, [])
            for dep in dependencies:
                if dep != 'shared':  # Ignore shared module
                    result = has_circular_dependency(dep, visited, path.copy())
                    if result:
                        return result
            
            return None
        
        circular_deps = []
        for module in cls.ALLOWED_DEPENDENCIES:
            result = has_circular_dependency(module, set(), [])
            if result:
                circular_deps.append(" -> ".join(result))
        
        return circular_deps
```

### When to Choose Monolithic

#### Decision Criteria Matrix
**Use Case Analysis:** When monolithic architecture is the optimal choice.

**Example - Decision Framework:**
```python
class ArchitectureDecisionFramework:
    """Framework for deciding between monolithic and microservices architecture"""
    
    def __init__(self):
        self.criteria = {
            'team_size': {
                'small': {'monolithic': 5, 'microservices': 1},
                'medium': {'monolithic': 3, 'microservices': 3},
                'large': {'monolithic': 1, 'microservices': 5}
            },
            'complexity': {
                'simple': {'monolithic': 5, 'microservices': 1},
                'moderate': {'monolithic': 3, 'microservices': 3},
                'complex': {'monolithic': 2, 'microservices': 4}
            },
            'scalability_requirements': {
                'low': {'monolithic': 4, 'microservices': 2},
                'medium': {'monolithic': 3, 'microservices': 3},
                'high': {'monolithic': 2, 'microservices': 5}
            },
            'operational_maturity': {
                'low': {'monolithic': 5, 'microservices': 1},
                'medium': {'monolithic': 3, 'microservices': 3},
                'high': {'monolithic': 2, 'microservices': 4}
            },
            'time_to_market': {
                'critical': {'monolithic': 5, 'microservices': 2},
                'important': {'monolithic': 4, 'microservices': 3},
                'flexible': {'monolithic': 2, 'microservices': 4}
            },
            'data_consistency': {
                'strict': {'monolithic': 5, 'microservices': 2},
                'eventual': {'monolithic': 3, 'microservices': 4},
                'flexible': {'monolithic': 2, 'microservices': 5}
            }
        }
    
    def evaluate(self, requirements: Dict[str, str]) -> Dict[str, Any]:
        """Evaluate architecture choice based on requirements"""
        monolithic_score = 0
        microservices_score = 0
        
        for criterion, value in requirements.items():
            if criterion in self.criteria and value in self.criteria[criterion]:
                scores = self.criteria[criterion][value]
                monolithic_score += scores['monolithic']
                microservices_score += scores['microservices']
        
        total_score = monolithic_score + microservices_score
        monolithic_percentage = (monolithic_score / total_score) * 100
        microservices_percentage = (microservices_score / total_score) * 100
        
        recommendation = 'monolithic' if monolithic_score > microservices_score else 'microservices'
        confidence = max(monolithic_percentage, microservices_percentage)
        
        return {
            'recommendation': recommendation,
            'confidence': confidence,
            'scores': {
                'monolithic': monolithic_score,
                'microservices': microservices_score
            },
            'percentages': {
                'monolithic': monolithic_percentage,
                'microservices': microservices_percentage
            },
            'analysis': self._generate_analysis(requirements, recommendation)
        }
    
    def _generate_analysis(self, requirements: Dict[str, str], recommendation: str) -> str:
        """Generate textual analysis of the decision"""
        factors = []
        
        if requirements.get('team_size') == 'small':
            factors.append("Small team size favors monolithic for reduced coordination overhead")
        
        if requirements.get('operational_maturity') == 'low':
            factors.append("Low operational maturity makes monolithic easier to manage")
        
        if requirements.get('time_to_market') == 'critical':
            factors.append("Critical time-to-market requirement favors monolithic for faster initial development")
        
        if requirements.get('data_consistency') == 'strict':
            factors.append("Strict data consistency requirements are easier to achieve in monolithic architecture")
        
        return f"Recommendation: {recommendation}. Key factors: {'; '.join(factors)}"

# Usage example
def evaluate_startup_ecommerce():
    """Evaluate architecture for a startup e-commerce platform"""
    framework = ArchitectureDecisionFramework()
    
    startup_requirements = {
        'team_size': 'small',           # 3-5 developers
        'complexity': 'moderate',       # Standard e-commerce features
        'scalability_requirements': 'medium',  # Expecting growth
        'operational_maturity': 'low',  # No DevOps team yet
        'time_to_market': 'critical',   # Need to launch quickly
        'data_consistency': 'strict'    # Financial transactions
    }
    
    result = framework.evaluate(startup_requirements)
    print(f"Architecture Recommendation: {result['recommendation']}")
    print(f"Confidence: {result['confidence']:.1f}%")
    print(f"Analysis: {result['analysis']}")
    
    return result

# Example scenarios where monolithic is preferred
MONOLITHIC_SCENARIOS = {
    "startup_mvp": {
        "description": "Building an MVP for a startup",
        "rationale": [
            "Fast time-to-market is critical",
            "Small development team (2-5 people)",
            "Requirements likely to change frequently",
            "Simple deployment and testing",
            "Limited operational expertise"
        ],
        "example": "A new food delivery app with basic ordering and payment features"
    },
    
    "internal_tools": {
        "description": "Building internal business tools",
        "rationale": [
            "Known user base and usage patterns",
            "Predictable scaling requirements",
            "Shared data and business logic",
            "Simpler maintenance and updates",
            "Lower operational overhead"
        ],
        "example": "Employee management system with HR, payroll, and time tracking"
    },
    
    "data_intensive_applications": {
        "description": "Applications requiring complex transactions",
        "rationale": [
            "ACID transaction requirements",
            "Complex queries across multiple entities",
            "Strong consistency needs",
            "Simplified data management",
            "Better performance for complex operations"
        ],
        "example": "Financial trading platform with real-time risk calculations"
    },
    
    "prototyping": {
        "description": "Rapid prototyping and experimentation",
        "rationale": [
            "Quick iteration and testing",
            "Simplified development workflow",
            "Easy to refactor and restructure",
            "Lower infrastructure costs",
            "Faster debugging and troubleshooting"
        ],
        "example": "Testing new machine learning algorithms with data processing pipeline"
    }
}
```

This comprehensive section demonstrates how to build well-structured monolithic applications with clear module boundaries, proper dependency management, and decision frameworks for when to choose this architecture pattern. All examples show production-ready patterns with proper separation of concerns, dependency injection, and event-driven communication within the monolith.