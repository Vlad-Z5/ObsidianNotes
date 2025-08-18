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

### Advanced Monolithic Patterns

#### Plugin Architecture for Monoliths

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Type
import importlib
import inspect
from dataclasses import dataclass
from enum import Enum

class PluginType(Enum):
    PAYMENT_PROCESSOR = "payment_processor"
    NOTIFICATION_PROVIDER = "notification_provider"
    AUTHENTICATION_PROVIDER = "authentication_provider"
    STORAGE_BACKEND = "storage_backend"
    ANALYTICS_PROVIDER = "analytics_provider"

@dataclass
class PluginMetadata:
    name: str
    version: str
    description: str
    author: str
    dependencies: List[str]
    config_schema: Dict[str, Any]

class Plugin(ABC):
    """Base plugin interface"""
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        pass

class PaymentPlugin(Plugin):
    """Payment processor plugin interface"""
    
    @abstractmethod
    def process_payment(self, amount: float, currency: str, 
                       payment_method: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def refund_payment(self, transaction_id: str, amount: float) -> Dict[str, Any]:
        pass

class StripePaymentPlugin(PaymentPlugin):
    """Stripe payment processor implementation"""
    
    def __init__(self):
        self.stripe_client = None
        self.config = {}
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="stripe_payment",
            version="1.0.0",
            description="Stripe payment processing plugin",
            author="Payment Team",
            dependencies=["stripe"],
            config_schema={
                "api_key": {"type": "string", "required": True, "secret": True},
                "webhook_secret": {"type": "string", "required": True, "secret": True},
                "test_mode": {"type": "boolean", "default": False}
            }
        )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize Stripe client with configuration"""
        try:
            import stripe
            self.config = config
            stripe.api_key = config['api_key']
            self.stripe_client = stripe
            return True
        except ImportError:
            print("Stripe library not available")
            return False
        except Exception as e:
            print(f"Failed to initialize Stripe plugin: {e}")
            return False
    
    def process_payment(self, amount: float, currency: str, 
                       payment_method: Dict[str, Any]) -> Dict[str, Any]:
        """Process payment through Stripe"""
        try:
            payment_intent = self.stripe_client.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency=currency,
                payment_method=payment_method['id'],
                confirm=True
            )
            
            return {
                'success': True,
                'transaction_id': payment_intent.id,
                'status': payment_intent.status,
                'amount': amount,
                'currency': currency
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': 'payment_failed'
            }
    
    def refund_payment(self, transaction_id: str, amount: float) -> Dict[str, Any]:
        """Process refund through Stripe"""
        try:
            refund = self.stripe_client.Refund.create(
                payment_intent=transaction_id,
                amount=int(amount * 100)
            )
            
            return {
                'success': True,
                'refund_id': refund.id,
                'status': refund.status,
                'amount': amount
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': 'refund_failed'
            }
    
    def shutdown(self) -> None:
        """Cleanup Stripe resources"""
        self.stripe_client = None
        self.config = {}

class PluginRegistry:
    """Central registry for managing plugins"""
    
    def __init__(self):
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_types: Dict[PluginType, List[str]] = {}
        self.plugin_configs: Dict[str, Dict] = {}
    
    def register_plugin(self, plugin_type: PluginType, plugin: Plugin, 
                       config: Dict[str, Any] = None) -> bool:
        """Register a plugin with the system"""
        plugin_name = plugin.metadata.name
        
        # Validate configuration
        if config and not self._validate_config(plugin, config):
            return False
        
        # Initialize plugin
        if not plugin.initialize(config or {}):
            return False
        
        # Register plugin
        self.plugins[plugin_name] = plugin
        
        if plugin_type not in self.plugin_types:
            self.plugin_types[plugin_type] = []
        self.plugin_types[plugin_type].append(plugin_name)
        
        if config:
            self.plugin_configs[plugin_name] = config
        
        return True
    
    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """Get plugin by name"""
        return self.plugins.get(plugin_name)
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[Plugin]:
        """Get all plugins of a specific type"""
        plugin_names = self.plugin_types.get(plugin_type, [])
        return [self.plugins[name] for name in plugin_names if name in self.plugins]
    
    def unregister_plugin(self, plugin_name: str) -> bool:
        """Unregister a plugin"""
        if plugin_name not in self.plugins:
            return False
        
        plugin = self.plugins[plugin_name]
        plugin.shutdown()
        
        del self.plugins[plugin_name]
        
        # Remove from type registry
        for plugin_type, names in self.plugin_types.items():
            if plugin_name in names:
                names.remove(plugin_name)
        
        if plugin_name in self.plugin_configs:
            del self.plugin_configs[plugin_name]
        
        return True
    
    def _validate_config(self, plugin: Plugin, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration against schema"""
        schema = plugin.metadata.config_schema
        
        for field, rules in schema.items():
            if rules.get('required', False) and field not in config:
                print(f"Required field '{field}' missing in plugin config")
                return False
        
        return True

class PluginManager:
    """High-level plugin management system"""
    
    def __init__(self):
        self.registry = PluginRegistry()
        self.default_plugins: Dict[PluginType, str] = {}
    
    def load_plugins_from_config(self, config: Dict[str, Any]) -> None:
        """Load plugins from configuration"""
        for plugin_config in config.get('plugins', []):
            plugin_class = self._load_plugin_class(plugin_config['class'])
            if plugin_class:
                plugin = plugin_class()
                plugin_type = PluginType(plugin_config['type'])
                
                success = self.registry.register_plugin(
                    plugin_type, 
                    plugin, 
                    plugin_config.get('config', {})
                )
                
                if success and plugin_config.get('default', False):
                    self.default_plugins[plugin_type] = plugin.metadata.name
    
    def get_default_plugin(self, plugin_type: PluginType) -> Optional[Plugin]:
        """Get the default plugin for a type"""
        plugin_name = self.default_plugins.get(plugin_type)
        if plugin_name:
            return self.registry.get_plugin(plugin_name)
        
        # Fallback to first available plugin
        plugins = self.registry.get_plugins_by_type(plugin_type)
        return plugins[0] if plugins else None
    
    def _load_plugin_class(self, class_path: str) -> Optional[Type[Plugin]]:
        """Dynamically load plugin class"""
        try:
            module_path, class_name = class_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            plugin_class = getattr(module, class_name)
            
            if not issubclass(plugin_class, Plugin):
                print(f"Class {class_path} is not a valid Plugin")
                return None
            
            return plugin_class
        except Exception as e:
            print(f"Failed to load plugin class {class_path}: {e}")
            return None

# Usage example in the main application
class PaymentService:
    """Service that uses payment plugins"""
    
    def __init__(self, plugin_manager: PluginManager):
        self.plugin_manager = plugin_manager
    
    def process_payment(self, amount: float, currency: str, 
                       payment_method: Dict[str, Any], 
                       processor_name: str = None) -> Dict[str, Any]:
        """Process payment using specified or default processor"""
        
        if processor_name:
            plugin = self.plugin_manager.registry.get_plugin(processor_name)
        else:
            plugin = self.plugin_manager.get_default_plugin(PluginType.PAYMENT_PROCESSOR)
        
        if not plugin:
            return {
                'success': False,
                'error': 'No payment processor available',
                'error_type': 'configuration_error'
            }
        
        if not isinstance(plugin, PaymentPlugin):
            return {
                'success': False,
                'error': 'Invalid payment processor type',
                'error_type': 'configuration_error'
            }
        
        return plugin.process_payment(amount, currency, payment_method)
```

#### Monolith Decomposition Strategy

```python
import ast
import networkx as nx
from typing import Set, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

class DecompositionStrategy(Enum):
    BY_DOMAIN = "by_domain"
    BY_DATA = "by_data"
    BY_USAGE_PATTERNS = "by_usage_patterns"
    BY_TEAM_BOUNDARIES = "by_team_boundaries"

@dataclass
class ModuleMetrics:
    name: str
    lines_of_code: int
    cyclomatic_complexity: int
    coupling_in: int
    coupling_out: int
    cohesion_score: float
    change_frequency: int
    team_ownership: str

@dataclass
class DecompositionRecommendation:
    source_module: str
    target_microservice: str
    confidence_score: float
    rationale: List[str]
    migration_complexity: str  # low, medium, high
    estimated_effort_days: int

class MonolithAnalyzer:
    """Analyze monolithic codebase for decomposition opportunities"""
    
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.dependency_graph = nx.DiGraph()
        self.module_metrics: Dict[str, ModuleMetrics] = {}
        self.domain_boundaries: Dict[str, Set[str]] = {}
    
    def analyze_codebase(self) -> Dict[str, Any]:
        """Perform comprehensive codebase analysis"""
        analysis_results = {
            'module_metrics': self._analyze_modules(),
            'dependency_analysis': self._analyze_dependencies(),
            'domain_clustering': self._identify_domain_clusters(),
            'hotspots': self._identify_change_hotspots(),
            'coupling_metrics': self._calculate_coupling_metrics()
        }
        
        return analysis_results
    
    def _analyze_modules(self) -> Dict[str, ModuleMetrics]:
        """Analyze individual module metrics"""
        metrics = {}
        
        # This would involve actual static code analysis
        # For demonstration, using mock data
        mock_modules = [
            ModuleMetrics("user", 1200, 15, 3, 8, 0.8, 25, "user_team"),
            ModuleMetrics("catalog", 2100, 22, 5, 12, 0.7, 18, "catalog_team"),
            ModuleMetrics("orders", 1800, 28, 8, 15, 0.6, 35, "order_team"),
            ModuleMetrics("payments", 900, 18, 4, 6, 0.9, 12, "payment_team"),
            ModuleMetrics("inventory", 1100, 16, 6, 9, 0.75, 20, "inventory_team")
        ]
        
        for module in mock_modules:
            metrics[module.name] = module
            
        return metrics
    
    def _analyze_dependencies(self) -> Dict[str, Any]:
        """Analyze inter-module dependencies"""
        # Build dependency graph
        dependencies = [
            ("orders", "user"), ("orders", "catalog"), ("orders", "payments"),
            ("orders", "inventory"), ("catalog", "inventory"), 
            ("payments", "user"), ("inventory", "catalog")
        ]
        
        for source, target in dependencies:
            self.dependency_graph.add_edge(source, target)
        
        return {
            'total_dependencies': len(dependencies),
            'circular_dependencies': list(nx.simple_cycles(self.dependency_graph)),
            'strongly_connected_components': list(nx.strongly_connected_components(self.dependency_graph)),
            'dependency_depth': nx.dag_longest_path_length(self.dependency_graph) if nx.is_directed_acyclic_graph(self.dependency_graph) else "N/A (cycles exist)"
        }
    
    def _identify_domain_clusters(self) -> Dict[str, Set[str]]:
        """Identify potential domain boundaries using clustering"""
        # Use community detection algorithms
        undirected_graph = self.dependency_graph.to_undirected()
        
        # Simple clustering based on connectivity
        clusters = {}
        processed = set()
        
        for node in undirected_graph.nodes():
            if node not in processed:
                cluster = set()
                self._dfs_cluster(undirected_graph, node, cluster, processed)
                if len(cluster) > 1:
                    cluster_name = f"domain_{len(clusters) + 1}"
                    clusters[cluster_name] = cluster
        
        return clusters
    
    def _dfs_cluster(self, graph, node, cluster, processed, max_depth=2, current_depth=0):
        """DFS-based clustering with depth limit"""
        if current_depth > max_depth or node in processed:
            return
        
        cluster.add(node)
        processed.add(node)
        
        for neighbor in graph.neighbors(node):
            if neighbor not in processed:
                self._dfs_cluster(graph, neighbor, cluster, processed, max_depth, current_depth + 1)
    
    def _identify_change_hotspots(self) -> List[str]:
        """Identify modules that change frequently"""
        hotspots = []
        
        for module_name, metrics in self.module_metrics.items():
            if metrics.change_frequency > 30:  # Threshold for high change frequency
                hotspots.append(module_name)
        
        return sorted(hotspots, key=lambda x: self.module_metrics[x].change_frequency, reverse=True)
    
    def _calculate_coupling_metrics(self) -> Dict[str, float]:
        """Calculate various coupling metrics"""
        metrics = {}
        
        for module_name, module_metrics in self.module_metrics.items():
            # Afferent coupling (Ca) - incoming dependencies
            ca = module_metrics.coupling_in
            
            # Efferent coupling (Ce) - outgoing dependencies
            ce = module_metrics.coupling_out
            
            # Instability (I) = Ce / (Ca + Ce)
            instability = ce / (ca + ce) if (ca + ce) > 0 else 0
            
            # Abstractness (A) - would need to be calculated from actual code
            abstractness = 0.5  # Mock value
            
            # Distance from main sequence (D) = |A + I - 1|
            distance = abs(abstractness + instability - 1)
            
            metrics[module_name] = {
                'afferent_coupling': ca,
                'efferent_coupling': ce,
                'instability': instability,
                'abstractness': abstractness,
                'distance_from_main_sequence': distance
            }
        
        return metrics

class DecompositionPlanner:
    """Plan microservices decomposition strategy"""
    
    def __init__(self, analyzer: MonolithAnalyzer):
        self.analyzer = analyzer
        self.strategies = {
            DecompositionStrategy.BY_DOMAIN: self._plan_by_domain,
            DecompositionStrategy.BY_DATA: self._plan_by_data,
            DecompositionStrategy.BY_USAGE_PATTERNS: self._plan_by_usage_patterns,
            DecompositionStrategy.BY_TEAM_BOUNDARIES: self._plan_by_team_boundaries
        }
    
    def create_decomposition_plan(self, strategy: DecompositionStrategy) -> List[DecompositionRecommendation]:
        """Create decomposition plan using specified strategy"""
        if strategy not in self.strategies:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        return self.strategies[strategy]()
    
    def _plan_by_domain(self) -> List[DecompositionRecommendation]:
        """Plan decomposition based on domain boundaries"""
        recommendations = []
        analysis = self.analyzer.analyze_codebase()
        domain_clusters = analysis['domain_clustering']
        
        for domain_name, modules in domain_clusters.items():
            if len(modules) > 1:
                # Create microservice for each domain cluster
                primary_module = max(modules, key=lambda m: self.analyzer.module_metrics[m].lines_of_code)
                
                for module in modules:
                    if module != primary_module:
                        confidence = self._calculate_domain_confidence(module, modules)
                        
                        recommendations.append(DecompositionRecommendation(
                            source_module=module,
                            target_microservice=f"{domain_name}_service",
                            confidence_score=confidence,
                            rationale=[
                                f"Strong domain cohesion with {domain_name}",
                                f"Low coupling with other domains",
                                f"Clear business boundary"
                            ],
                            migration_complexity="medium",
                            estimated_effort_days=self._estimate_migration_effort(module)
                        ))
        
        return recommendations
    
    def _plan_by_data(self) -> List[DecompositionRecommendation]:
        """Plan decomposition based on data access patterns"""
        recommendations = []
        
        # Mock data access analysis
        data_ownership = {
            "user": ["users", "user_profiles", "user_sessions"],
            "catalog": ["products", "categories", "product_reviews"],
            "orders": ["orders", "order_items"],
            "payments": ["payments", "payment_methods"],
            "inventory": ["inventory", "stock_movements"]
        }
        
        for module, tables in data_ownership.items():
            if len(tables) >= 2:  # Modules with significant data ownership
                recommendations.append(DecompositionRecommendation(
                    source_module=module,
                    target_microservice=f"{module}_service",
                    confidence_score=0.8,
                    rationale=[
                        f"Owns {len(tables)} database tables",
                        "Clear data boundaries",
                        "Minimal cross-module data access"
                    ],
                    migration_complexity="high",  # Data migration is complex
                    estimated_effort_days=self._estimate_migration_effort(module) + 10
                ))
        
        return recommendations
    
    def _plan_by_usage_patterns(self) -> List[DecompositionRecommendation]:
        """Plan decomposition based on usage patterns and scalability needs"""
        recommendations = []
        
        # Mock usage pattern analysis
        usage_patterns = {
            "catalog": {"reads_per_day": 100000, "writes_per_day": 1000, "peak_factor": 5},
            "orders": {"reads_per_day": 50000, "writes_per_day": 10000, "peak_factor": 3},
            "user": {"reads_per_day": 80000, "writes_per_day": 5000, "peak_factor": 2},
            "payments": {"reads_per_day": 20000, "writes_per_day": 8000, "peak_factor": 4},
            "inventory": {"reads_per_day": 30000, "writes_per_day": 15000, "peak_factor": 2}
        }
        
        for module, patterns in usage_patterns.items():
            total_operations = patterns["reads_per_day"] + patterns["writes_per_day"]
            
            if total_operations > 75000 or patterns["peak_factor"] > 3:
                recommendations.append(DecompositionRecommendation(
                    source_module=module,
                    target_microservice=f"{module}_service",
                    confidence_score=0.9,
                    rationale=[
                        f"High traffic: {total_operations:,} operations/day",
                        f"High peak factor: {patterns['peak_factor']}x",
                        "Benefits from independent scaling"
                    ],
                    migration_complexity="medium",
                    estimated_effort_days=self._estimate_migration_effort(module) + 5
                ))
        
        return recommendations
    
    def _plan_by_team_boundaries(self) -> List[DecompositionRecommendation]:
        """Plan decomposition based on team ownership"""
        recommendations = []
        
        team_modules = {}
        for module_name, metrics in self.analyzer.module_metrics.items():
            team = metrics.team_ownership
            if team not in team_modules:
                team_modules[team] = []
            team_modules[team].append(module_name)
        
        for team, modules in team_modules.items():
            if len(modules) == 1:  # One team, one module = good microservice candidate
                module = modules[0]
                recommendations.append(DecompositionRecommendation(
                    source_module=module,
                    target_microservice=f"{module}_service",
                    confidence_score=0.85,
                    rationale=[
                        f"Clear team ownership by {team}",
                        "Reduced coordination overhead",
                        "Independent deployment capability"
                    ],
                    migration_complexity="low",
                    estimated_effort_days=self._estimate_migration_effort(module)
                ))
        
        return recommendations
    
    def _calculate_domain_confidence(self, module: str, domain_modules: Set[str]) -> float:
        """Calculate confidence score for domain-based decomposition"""
        metrics = self.analyzer.module_metrics[module]
        
        # Base confidence on cohesion and coupling
        base_confidence = metrics.cohesion_score
        
        # Adjust based on coupling with domain modules vs external modules
        domain_coupling = 0
        external_coupling = 0
        
        for target in self.analyzer.dependency_graph.neighbors(module):
            if target in domain_modules:
                domain_coupling += 1
            else:
                external_coupling += 1
        
        total_coupling = domain_coupling + external_coupling
        if total_coupling > 0:
            coupling_factor = domain_coupling / total_coupling
            base_confidence = (base_confidence + coupling_factor) / 2
        
        return min(base_confidence, 1.0)
    
    def _estimate_migration_effort(self, module: str) -> int:
        """Estimate migration effort in days"""
        metrics = self.analyzer.module_metrics[module]
        
        # Base effort on lines of code and complexity
        base_effort = (metrics.lines_of_code / 1000) * 5  # 5 days per 1000 LOC
        complexity_factor = metrics.cyclomatic_complexity / 10
        coupling_factor = (metrics.coupling_in + metrics.coupling_out) / 5
        
        total_effort = base_effort * (1 + complexity_factor + coupling_factor)
        
        return max(int(total_effort), 3)  # Minimum 3 days
```

#### Monolith Performance Optimization

```python
import time
import threading
from functools import wraps
from typing import Callable, Any, Dict, List
from collections import defaultdict, deque
import asyncio
from concurrent.futures import ThreadPoolExecutor
import weakref

class PerformanceProfiler:
    """Advanced performance profiler for monolithic applications"""
    
    def __init__(self):
        self.call_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0,
            'avg_time': 0,
            'max_time': 0,
            'min_time': float('inf')
        })
        self.memory_usage = deque(maxlen=1000)
        self.active_requests = 0
        self.request_queue = deque(maxlen=10000)
        self.lock = threading.Lock()
    
    def profile_function(self, func_name: str = None):
        """Decorator to profile function performance"""
        def decorator(func):
            name = func_name or f"{func.__module__}.{func.__name__}"
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    success = True
                    return result
                except Exception as e:
                    success = False
                    raise e
                finally:
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    with self.lock:
                        stats = self.call_stats[name]
                        stats['count'] += 1
                        stats['total_time'] += duration
                        stats['avg_time'] = stats['total_time'] / stats['count']
                        stats['max_time'] = max(stats['max_time'], duration)
                        stats['min_time'] = min(stats['min_time'], duration)
                        stats['success'] = success
            
            return wrapper
        return decorator
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        with self.lock:
            report = {
                'timestamp': time.time(),
                'function_stats': dict(self.call_stats),
                'system_stats': {
                    'active_requests': self.active_requests,
                    'total_requests_processed': sum(stats['count'] for stats in self.call_stats.values())
                },
                'hotspots': self._identify_hotspots(),
                'bottlenecks': self._identify_bottlenecks()
            }
        
        return report
    
    def _identify_hotspots(self) -> List[Dict[str, Any]]:
        """Identify performance hotspots"""
        hotspots = []
        
        for func_name, stats in self.call_stats.items():
            if stats['count'] > 100 and stats['avg_time'] > 0.1:  # High usage, slow functions
                hotspots.append({
                    'function': func_name,
                    'call_count': stats['count'],
                    'avg_time': stats['avg_time'],
                    'total_time': stats['total_time'],
                    'hotspot_score': stats['count'] * stats['avg_time']
                })
        
        return sorted(hotspots, key=lambda x: x['hotspot_score'], reverse=True)
    
    def _identify_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks"""
        bottlenecks = []
        
        for func_name, stats in self.call_stats.items():
            if stats['max_time'] > 1.0:  # Functions that sometimes take too long
                bottlenecks.append({
                    'function': func_name,
                    'max_time': stats['max_time'],
                    'avg_time': stats['avg_time'],
                    'variance': stats['max_time'] - stats['min_time']
                })
        
        return sorted(bottlenecks, key=lambda x: x['max_time'], reverse=True)

class SmartCachingLayer:
    """Intelligent caching layer with adaptive policies"""
    
    def __init__(self, max_size: int = 10000):
        self.cache = {}
        self.access_times = {}
        self.access_counts = defaultdict(int)
        self.cache_hits = 0
        self.cache_misses = 0
        self.max_size = max_size
        self.lock = threading.Lock()
        
        # Adaptive caching policies
        self.ttl_policies = {
            'frequent': 3600,    # 1 hour for frequently accessed items
            'normal': 1800,      # 30 minutes for normal items
            'rare': 600          # 10 minutes for rarely accessed items
        }
    
    def get(self, key: str, fetch_function: Callable = None) -> Any:
        """Get value from cache with automatic fetching"""
        with self.lock:
            if key in self.cache:
                self.cache_hits += 1
                self.access_times[key] = time.time()
                self.access_counts[key] += 1
                return self.cache[key]['value']
            
            self.cache_misses += 1
        
        if fetch_function:
            value = fetch_function()
            self.set(key, value)
            return value
        
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache with adaptive TTL"""
        with self.lock:
            if len(self.cache) >= self.max_size:
                self._evict_items()
            
            # Determine TTL based on access pattern
            access_count = self.access_counts.get(key, 0)
            if access_count > 100:
                ttl = self.ttl_policies['frequent']
            elif access_count > 10:
                ttl = self.ttl_policies['normal']
            else:
                ttl = self.ttl_policies['rare']
            
            self.cache[key] = {
                'value': value,
                'created_at': time.time(),
                'ttl': ttl,
                'access_count': access_count
            }
            self.access_times[key] = time.time()
    
    def _evict_items(self) -> None:
        """Evict items using adaptive LRU policy"""
        current_time = time.time()
        
        # First, remove expired items
        expired_keys = []
        for key, item in self.cache.items():
            if current_time - item['created_at'] > item['ttl']:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]
        
        # If still over capacity, use LRU
        if len(self.cache) >= self.max_size:
            # Sort by last access time
            lru_keys = sorted(self.access_times.keys(), 
                            key=lambda k: self.access_times[k])
            
            # Remove oldest 20% of items
            items_to_remove = max(1, len(lru_keys) // 5)
            for key in lru_keys[:items_to_remove]:
                if key in self.cache:
                    del self.cache[key]
                del self.access_times[key]
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests) if total_requests > 0 else 0
        
        return {
            'hit_rate': hit_rate,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_size': len(self.cache),
            'max_size': self.max_size,
            'utilization': len(self.cache) / self.max_size
        }

class ResourcePoolManager:
    """Manage resource pools for database connections, HTTP clients, etc."""
    
    def __init__(self):
        self.pools = {}
        self.pool_configs = {}
    
    def create_pool(self, pool_name: str, factory_func: Callable, 
                   min_size: int = 5, max_size: int = 20) -> None:
        """Create a new resource pool"""
        pool = ResourcePool(factory_func, min_size, max_size)
        self.pools[pool_name] = pool
        self.pool_configs[pool_name] = {
            'min_size': min_size,
            'max_size': max_size,
            'factory': factory_func
        }
    
    def get_resource(self, pool_name: str) -> Any:
        """Get resource from pool"""
        if pool_name not in self.pools:
            raise ValueError(f"Pool {pool_name} not found")
        
        return self.pools[pool_name].acquire()
    
    def return_resource(self, pool_name: str, resource: Any) -> None:
        """Return resource to pool"""
        if pool_name in self.pools:
            self.pools[pool_name].release(resource)
    
    def get_pool_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all pools"""
        stats = {}
        for pool_name, pool in self.pools.items():
            stats[pool_name] = pool.get_stats()
        return stats

class ResourcePool:
    """Generic resource pool implementation"""
    
    def __init__(self, factory_func: Callable, min_size: int, max_size: int):
        self.factory_func = factory_func
        self.min_size = min_size
        self.max_size = max_size
        self.available = deque()
        self.in_use = set()
        self.total_created = 0
        self.lock = threading.Lock()
        
        # Pre-populate with minimum resources
        for _ in range(min_size):
            resource = self._create_resource()
            self.available.append(resource)
    
    def acquire(self) -> Any:
        """Acquire resource from pool"""
        with self.lock:
            if self.available:
                resource = self.available.popleft()
                self.in_use.add(id(resource))
                return resource
            
            if len(self.in_use) < self.max_size:
                resource = self._create_resource()
                self.in_use.add(id(resource))
                return resource
        
        # Pool exhausted, wait for resource to become available
        raise RuntimeError("Resource pool exhausted")
    
    def release(self, resource: Any) -> None:
        """Release resource back to pool"""
        with self.lock:
            resource_id = id(resource)
            if resource_id in self.in_use:
                self.in_use.remove(resource_id)
                
                if self._is_resource_healthy(resource):
                    self.available.append(resource)
                else:
                    # Replace unhealthy resource
                    try:
                        new_resource = self._create_resource()
                        self.available.append(new_resource)
                    except Exception:
                        pass  # Failed to create replacement
    
    def _create_resource(self) -> Any:
        """Create new resource"""
        try:
            resource = self.factory_func()
            self.total_created += 1
            return resource
        except Exception as e:
            raise RuntimeError(f"Failed to create resource: {e}")
    
    def _is_resource_healthy(self, resource: Any) -> bool:
        """Check if resource is still healthy"""
        # Basic health check - can be overridden
        try:
            return hasattr(resource, '__dict__')  # Simple check
        except Exception:
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        with self.lock:
            return {
                'available': len(self.available),
                'in_use': len(self.in_use),
                'total_created': self.total_created,
                'utilization': len(self.in_use) / self.max_size,
                'min_size': self.min_size,
                'max_size': self.max_size
            }
```

This comprehensive section demonstrates how to build well-structured monolithic applications with clear module boundaries, proper dependency management, decision frameworks, advanced plugin architectures, decomposition strategies, and performance optimization techniques. All examples show production-ready patterns with proper separation of concerns, dependency injection, event-driven communication within the monolith, and sophisticated optimization approaches for enterprise-scale monolithic applications.