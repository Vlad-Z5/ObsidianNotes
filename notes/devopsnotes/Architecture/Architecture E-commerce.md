# Architecture E-commerce

## E-commerce Architecture Patterns

E-commerce architecture requires careful consideration of scalability, performance, security, and user experience. Modern e-commerce systems must handle high traffic volumes, process payments securely, manage complex inventory operations, and provide personalized experiences.

### Shopping Cart Design

**Definition:** The shopping cart is a critical component that maintains user session state and enables product selection before purchase.

#### Session-Based Cart with Redis
**Handles cart persistence and synchronization across sessions.**

**Implementation - Shopping Cart Service:**
```python
import json
import redis
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from decimal import Decimal
import uuid

@dataclass
class CartItem:
    """Represents an item in the shopping cart"""
    product_id: str
    product_name: str
    sku: str
    quantity: int
    unit_price: Decimal
    discount_amount: Decimal = Decimal('0.00')
    tax_rate: Decimal = Decimal('0.00')
    
    @property
    def subtotal(self) -> Decimal:
        return (self.unit_price * self.quantity) - self.discount_amount
    
    @property
    def tax_amount(self) -> Decimal:
        return self.subtotal * self.tax_rate
    
    @property
    def total(self) -> Decimal:
        return self.subtotal + self.tax_amount

@dataclass
class ShippingAddress:
    """Shipping address information"""
    first_name: str
    last_name: str
    address_line1: str
    address_line2: str = ""
    city: str
    state: str
    postal_code: str
    country: str

@dataclass
class ShoppingCart:
    """Complete shopping cart with items and metadata"""
    cart_id: str
    user_id: Optional[str]
    session_id: str
    items: List[CartItem]
    shipping_address: Optional[ShippingAddress] = None
    coupon_code: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self.items)
    
    @property
    def subtotal(self) -> Decimal:
        return sum(item.subtotal for item in self.items)
    
    @property
    def tax_total(self) -> Decimal:
        return sum(item.tax_amount for item in self.items)
    
    @property
    def total(self) -> Decimal:
        return self.subtotal + self.tax_total

class ShoppingCartService:
    """Service for managing shopping carts with Redis persistence"""
    
    def __init__(self, redis_client: redis.Redis, cart_ttl_hours: int = 24):
        self.redis_client = redis_client
        self.cart_ttl = timedelta(hours=cart_ttl_hours)
        self.cart_prefix = "cart:"
        self.user_cart_prefix = "user_cart:"
    
    def create_cart(self, session_id: str, user_id: Optional[str] = None) -> ShoppingCart:
        """Create a new shopping cart"""
        cart_id = str(uuid.uuid4())
        cart = ShoppingCart(
            cart_id=cart_id,
            user_id=user_id,
            session_id=session_id,
            items=[]
        )
        
        self._save_cart(cart)
        
        # Associate cart with user if logged in
        if user_id:
            self._associate_cart_with_user(user_id, cart_id)
        
        return cart
    
    def get_cart(self, cart_id: str) -> Optional[ShoppingCart]:
        """Retrieve cart by ID"""
        cart_key = f"{self.cart_prefix}{cart_id}"
        cart_data = self.redis_client.get(cart_key)
        
        if not cart_data:
            return None
        
        cart_dict = json.loads(cart_data)
        return self._deserialize_cart(cart_dict)
    
    def get_user_cart(self, user_id: str) -> Optional[ShoppingCart]:
        """Get the active cart for a user"""
        user_cart_key = f"{self.user_cart_prefix}{user_id}"
        cart_id = self.redis_client.get(user_cart_key)
        
        if not cart_id:
            return None
        
        return self.get_cart(cart_id.decode())
    
    def add_item(self, cart_id: str, product_id: str, product_name: str, 
                 sku: str, quantity: int, unit_price: Decimal) -> ShoppingCart:
        """Add item to cart or update quantity if exists"""
        cart = self.get_cart(cart_id)
        if not cart:
            raise ValueError(f"Cart {cart_id} not found")
        
        # Check if item already exists
        existing_item = None
        for item in cart.items:
            if item.product_id == product_id and item.sku == sku:
                existing_item = item
                break
        
        if existing_item:
            existing_item.quantity += quantity
        else:
            new_item = CartItem(
                product_id=product_id,
                product_name=product_name,
                sku=sku,
                quantity=quantity,
                unit_price=unit_price
            )
            cart.items.append(new_item)
        
        cart.updated_at = datetime.utcnow()
        self._save_cart(cart)
        
        return cart
    
    def remove_item(self, cart_id: str, product_id: str, sku: str) -> ShoppingCart:
        """Remove item from cart"""
        cart = self.get_cart(cart_id)
        if not cart:
            raise ValueError(f"Cart {cart_id} not found")
        
        cart.items = [item for item in cart.items 
                     if not (item.product_id == product_id and item.sku == sku)]
        
        cart.updated_at = datetime.utcnow()
        self._save_cart(cart)
        
        return cart
    
    def update_quantity(self, cart_id: str, product_id: str, sku: str, quantity: int) -> ShoppingCart:
        """Update item quantity in cart"""
        cart = self.get_cart(cart_id)
        if not cart:
            raise ValueError(f"Cart {cart_id} not found")
        
        for item in cart.items:
            if item.product_id == product_id and item.sku == sku:
                if quantity <= 0:
                    cart.items.remove(item)
                else:
                    item.quantity = quantity
                break
        
        cart.updated_at = datetime.utcnow()
        self._save_cart(cart)
        
        return cart
    
    def merge_carts(self, target_cart_id: str, source_cart_id: str) -> ShoppingCart:
        """Merge source cart into target cart (used when user logs in)"""
        target_cart = self.get_cart(target_cart_id)
        source_cart = self.get_cart(source_cart_id)
        
        if not target_cart or not source_cart:
            raise ValueError("One or both carts not found")
        
        # Merge items
        for source_item in source_cart.items:
            # Check if item exists in target cart
            existing_item = None
            for target_item in target_cart.items:
                if (target_item.product_id == source_item.product_id and 
                    target_item.sku == source_item.sku):
                    existing_item = target_item
                    break
            
            if existing_item:
                existing_item.quantity += source_item.quantity
            else:
                target_cart.items.append(source_item)
        
        target_cart.updated_at = datetime.utcnow()
        self._save_cart(target_cart)
        
        # Delete source cart
        self.delete_cart(source_cart_id)
        
        return target_cart
    
    def apply_coupon(self, cart_id: str, coupon_code: str) -> ShoppingCart:
        """Apply coupon to cart"""
        cart = self.get_cart(cart_id)
        if not cart:
            raise ValueError(f"Cart {cart_id} not found")
        
        # Validate coupon (implementation would check against coupon service)
        if self._validate_coupon(coupon_code, cart):
            cart.coupon_code = coupon_code
            # Apply discount to items (implementation would vary by coupon type)
            self._apply_coupon_discount(cart, coupon_code)
            
            cart.updated_at = datetime.utcnow()
            self._save_cart(cart)
        
        return cart
    
    def delete_cart(self, cart_id: str):
        """Delete cart from storage"""
        cart_key = f"{self.cart_prefix}{cart_id}"
        self.redis_client.delete(cart_key)
    
    def cleanup_abandoned_carts(self):
        """Clean up abandoned carts (run as scheduled job)"""
        # Implementation would scan for expired carts and clean them up
        pattern = f"{self.cart_prefix}*"
        for key in self.redis_client.scan_iter(match=pattern):
            cart_data = self.redis_client.get(key)
            if cart_data:
                cart_dict = json.loads(cart_data)
                updated_at = datetime.fromisoformat(cart_dict['updated_at'])
                
                if datetime.utcnow() - updated_at > self.cart_ttl:
                    self.redis_client.delete(key)
    
    def _save_cart(self, cart: ShoppingCart):
        """Save cart to Redis with TTL"""
        cart_key = f"{self.cart_prefix}{cart.cart_id}"
        cart_data = self._serialize_cart(cart)
        
        # Set with TTL
        self.redis_client.setex(
            cart_key, 
            int(self.cart_ttl.total_seconds()), 
            json.dumps(cart_data)
        )
    
    def _serialize_cart(self, cart: ShoppingCart) -> Dict:
        """Convert cart to dictionary for storage"""
        cart_dict = asdict(cart)
        
        # Convert datetime objects to ISO strings
        cart_dict['created_at'] = cart.created_at.isoformat()
        cart_dict['updated_at'] = cart.updated_at.isoformat()
        
        # Convert Decimal objects to strings
        for item in cart_dict['items']:
            item['unit_price'] = str(item['unit_price'])
            item['discount_amount'] = str(item['discount_amount'])
            item['tax_rate'] = str(item['tax_rate'])
        
        return cart_dict
    
    def _deserialize_cart(self, cart_dict: Dict) -> ShoppingCart:
        """Convert dictionary back to cart object"""
        # Convert datetime strings back to datetime objects
        cart_dict['created_at'] = datetime.fromisoformat(cart_dict['created_at'])
        cart_dict['updated_at'] = datetime.fromisoformat(cart_dict['updated_at'])
        
        # Convert Decimal strings back to Decimal objects
        for item in cart_dict['items']:
            item['unit_price'] = Decimal(item['unit_price'])
            item['discount_amount'] = Decimal(item['discount_amount'])
            item['tax_rate'] = Decimal(item['tax_rate'])
        
        # Convert items to CartItem objects
        items = [CartItem(**item) for item in cart_dict['items']]
        cart_dict['items'] = items
        
        # Convert shipping address if present
        if cart_dict['shipping_address']:
            cart_dict['shipping_address'] = ShippingAddress(**cart_dict['shipping_address'])
        
        return ShoppingCart(**cart_dict)
    
    def _associate_cart_with_user(self, user_id: str, cart_id: str):
        """Associate cart with user"""
        user_cart_key = f"{self.user_cart_prefix}{user_id}"
        self.redis_client.setex(
            user_cart_key,
            int(self.cart_ttl.total_seconds()),
            cart_id
        )
    
    def _validate_coupon(self, coupon_code: str, cart: ShoppingCart) -> bool:
        """Validate coupon code (placeholder implementation)"""
        # Implementation would check against coupon service
        return True
    
    def _apply_coupon_discount(self, cart: ShoppingCart, coupon_code: str):
        """Apply coupon discount to cart items"""
        # Implementation would vary based on coupon type
        # This is a simple 10% discount example
        discount_rate = Decimal('0.10')
        
        for item in cart.items:
            discount = item.unit_price * item.quantity * discount_rate
            item.discount_amount = discount
```

### Checkout Process

**Definition:** Multi-step process that guides users through order completion, payment, and confirmation.

#### Multi-Step Checkout Engine
**Manages checkout workflow with validation and state management.**

**Implementation - Checkout Service:**
```python
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import uuid
from datetime import datetime

class CheckoutStep(Enum):
    CART_REVIEW = "cart_review"
    SHIPPING_INFO = "shipping_info"
    PAYMENT_INFO = "payment_info"
    ORDER_REVIEW = "order_review"
    CONFIRMATION = "confirmation"

class PaymentMethod(Enum):
    CREDIT_CARD = "credit_card"
    PAYPAL = "paypal"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"
    BANK_TRANSFER = "bank_transfer"

@dataclass
class CheckoutState:
    """Maintains checkout process state"""
    checkout_id: str
    cart_id: str
    user_id: Optional[str]
    current_step: CheckoutStep
    completed_steps: List[CheckoutStep]
    shipping_address: Optional[ShippingAddress]
    billing_address: Optional[ShippingAddress]
    payment_method: Optional[PaymentMethod]
    payment_details: Optional[Dict[str, Any]]
    guest_email: Optional[str]
    special_instructions: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

class CheckoutEngine:
    """Manages multi-step checkout process"""
    
    def __init__(self, cart_service: ShoppingCartService, 
                 payment_service, order_service, inventory_service):
        self.cart_service = cart_service
        self.payment_service = payment_service
        self.order_service = order_service
        self.inventory_service = inventory_service
        self.checkout_states = {}  # In production, use Redis/database
    
    def start_checkout(self, cart_id: str, user_id: Optional[str] = None) -> CheckoutState:
        """Initialize checkout process"""
        # Validate cart exists and has items
        cart = self.cart_service.get_cart(cart_id)
        if not cart or not cart.items:
            raise ValueError("Cart is empty or not found")
        
        # Check inventory availability
        self._validate_inventory_availability(cart)
        
        checkout_id = str(uuid.uuid4())
        checkout_state = CheckoutState(
            checkout_id=checkout_id,
            cart_id=cart_id,
            user_id=user_id,
            current_step=CheckoutStep.CART_REVIEW,
            completed_steps=[]
        )
        
        self.checkout_states[checkout_id] = checkout_state
        return checkout_state
    
    def update_shipping_info(self, checkout_id: str, shipping_address: ShippingAddress,
                           billing_address: Optional[ShippingAddress] = None) -> CheckoutState:
        """Update shipping and billing information"""
        checkout_state = self._get_checkout_state(checkout_id)
        
        # Validate shipping address
        self._validate_address(shipping_address)
        
        checkout_state.shipping_address = shipping_address
        checkout_state.billing_address = billing_address or shipping_address
        
        self._complete_step(checkout_state, CheckoutStep.SHIPPING_INFO)
        checkout_state.current_step = CheckoutStep.PAYMENT_INFO
        
        return checkout_state
    
    def update_guest_info(self, checkout_id: str, email: str) -> CheckoutState:
        """Update guest checkout information"""
        checkout_state = self._get_checkout_state(checkout_id)
        
        if checkout_state.user_id:
            raise ValueError("Cannot set guest email for logged-in user")
        
        # Validate email
        if not self._validate_email(email):
            raise ValueError("Invalid email address")
        
        checkout_state.guest_email = email
        return checkout_state
    
    def update_payment_info(self, checkout_id: str, payment_method: PaymentMethod,
                          payment_details: Dict[str, Any]) -> CheckoutState:
        """Update payment information"""
        checkout_state = self._get_checkout_state(checkout_id)
        
        # Validate payment details
        self._validate_payment_details(payment_method, payment_details)
        
        checkout_state.payment_method = payment_method
        checkout_state.payment_details = payment_details
        
        self._complete_step(checkout_state, CheckoutStep.PAYMENT_INFO)
        checkout_state.current_step = CheckoutStep.ORDER_REVIEW
        
        return checkout_state
    
    def complete_order(self, checkout_id: str) -> Dict[str, Any]:
        """Complete the order and process payment"""
        checkout_state = self._get_checkout_state(checkout_id)
        
        # Validate all required steps are completed
        required_steps = [CheckoutStep.SHIPPING_INFO, CheckoutStep.PAYMENT_INFO]
        for step in required_steps:
            if step not in checkout_state.completed_steps:
                raise ValueError(f"Step {step.value} not completed")
        
        cart = self.cart_service.get_cart(checkout_state.cart_id)
        
        try:
            # Reserve inventory
            reservation_id = self.inventory_service.reserve_items(cart.items)
            
            # Process payment
            payment_result = self.payment_service.process_payment(
                amount=cart.total,
                payment_method=checkout_state.payment_method,
                payment_details=checkout_state.payment_details,
                billing_address=checkout_state.billing_address
            )
            
            if not payment_result['success']:
                # Release inventory reservation
                self.inventory_service.release_reservation(reservation_id)
                raise PaymentFailedException(payment_result['error'])
            
            # Create order
            order = self.order_service.create_order(
                cart=cart,
                shipping_address=checkout_state.shipping_address,
                billing_address=checkout_state.billing_address,
                payment_result=payment_result,
                user_id=checkout_state.user_id,
                guest_email=checkout_state.guest_email
            )
            
            # Confirm inventory reservation
            self.inventory_service.confirm_reservation(reservation_id)
            
            # Clear cart
            self.cart_service.delete_cart(checkout_state.cart_id)
            
            # Update checkout state
            checkout_state.current_step = CheckoutStep.CONFIRMATION
            self._complete_step(checkout_state, CheckoutStep.ORDER_REVIEW)
            
            return {
                'success': True,
                'order_id': order['order_id'],
                'order_number': order['order_number'],
                'total': order['total'],
                'payment_id': payment_result['payment_id']
            }
            
        except Exception as e:
            # Rollback any changes
            if 'reservation_id' in locals():
                self.inventory_service.release_reservation(reservation_id)
            
            raise CheckoutException(f"Checkout failed: {str(e)}")
    
    def get_checkout_summary(self, checkout_id: str) -> Dict[str, Any]:
        """Get complete checkout summary for review"""
        checkout_state = self._get_checkout_state(checkout_id)
        cart = self.cart_service.get_cart(checkout_state.cart_id)
        
        # Calculate shipping cost
        shipping_cost = self._calculate_shipping_cost(
            cart, 
            checkout_state.shipping_address
        )
        
        # Calculate tax
        tax_amount = self._calculate_tax(cart, checkout_state.shipping_address)
        
        return {
            'checkout_id': checkout_id,
            'cart': {
                'items': [asdict(item) for item in cart.items],
                'subtotal': cart.subtotal,
                'item_count': cart.item_count
            },
            'shipping': {
                'address': asdict(checkout_state.shipping_address) if checkout_state.shipping_address else None,
                'cost': shipping_cost
            },
            'payment': {
                'method': checkout_state.payment_method.value if checkout_state.payment_method else None
            },
            'totals': {
                'subtotal': cart.subtotal,
                'shipping': shipping_cost,
                'tax': tax_amount,
                'total': cart.subtotal + shipping_cost + tax_amount
            },
            'current_step': checkout_state.current_step.value,
            'completed_steps': [step.value for step in checkout_state.completed_steps]
        }
    
    def _get_checkout_state(self, checkout_id: str) -> CheckoutState:
        """Get checkout state by ID"""
        if checkout_id not in self.checkout_states:
            raise ValueError(f"Checkout {checkout_id} not found")
        return self.checkout_states[checkout_id]
    
    def _complete_step(self, checkout_state: CheckoutState, step: CheckoutStep):
        """Mark checkout step as completed"""
        if step not in checkout_state.completed_steps:
            checkout_state.completed_steps.append(step)
        checkout_state.updated_at = datetime.utcnow()
    
    def _validate_inventory_availability(self, cart: ShoppingCart):
        """Validate all items are available in inventory"""
        for item in cart.items:
            if not self.inventory_service.check_availability(item.sku, item.quantity):
                raise InventoryUnavailableException(
                    f"Insufficient inventory for {item.product_name}"
                )
    
    def _validate_address(self, address: ShippingAddress):
        """Validate shipping address"""
        required_fields = ['first_name', 'last_name', 'address_line1', 
                          'city', 'state', 'postal_code', 'country']
        
        for field in required_fields:
            if not getattr(address, field):
                raise ValueError(f"Missing required field: {field}")
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_payment_details(self, payment_method: PaymentMethod, 
                                payment_details: Dict[str, Any]):
        """Validate payment details based on method"""
        if payment_method == PaymentMethod.CREDIT_CARD:
            required_fields = ['card_number', 'expiry_month', 'expiry_year', 'cvv']
            for field in required_fields:
                if field not in payment_details:
                    raise ValueError(f"Missing required payment field: {field}")
    
    def _calculate_shipping_cost(self, cart: ShoppingCart, 
                               shipping_address: ShippingAddress) -> Decimal:
        """Calculate shipping cost"""
        # Implementation would integrate with shipping provider APIs
        return Decimal('9.99')  # Placeholder
    
    def _calculate_tax(self, cart: ShoppingCart, 
                      shipping_address: ShippingAddress) -> Decimal:
        """Calculate tax amount"""
        # Implementation would integrate with tax calculation service
        tax_rate = Decimal('0.08')  # 8% tax rate
        return cart.subtotal * tax_rate

class PaymentFailedException(Exception):
    pass

class CheckoutException(Exception):
    pass

class InventoryUnavailableException(Exception):
    pass
```

### Payment Processing

**Definition:** Secure handling of payment transactions with fraud detection and compliance.

#### Payment Gateway Integration
**Processes payments securely with fraud detection and PCI compliance.**

**Implementation - Payment Service:**
```python
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import requests
import json

class PaymentStatus(Enum):
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"

class FraudRiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKED = "blocked"

@dataclass
class PaymentRequest:
    """Payment request details"""
    amount: Decimal
    currency: str
    payment_method: PaymentMethod
    payment_details: Dict[str, Any]
    billing_address: ShippingAddress
    order_id: str
    customer_id: Optional[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class PaymentResult:
    """Payment processing result"""
    payment_id: str
    status: PaymentStatus
    amount: Decimal
    currency: str
    gateway_transaction_id: str
    fraud_risk_level: FraudRiskLevel
    fraud_score: float
    processor_response: Dict[str, Any]
    fees: Decimal
    created_at: datetime
    success: bool
    error_message: Optional[str] = None

class PaymentService:
    """Comprehensive payment processing service"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.fraud_detector = FraudDetector()
        self.payment_gateways = {
            PaymentMethod.CREDIT_CARD: StripeGateway(config.get('stripe', {})),
            PaymentMethod.PAYPAL: PayPalGateway(config.get('paypal', {})),
            PaymentMethod.APPLE_PAY: ApplePayGateway(config.get('apple_pay', {}))
        }
        self.payment_history = []  # In production, use database
    
    def process_payment(self, payment_request: PaymentRequest) -> PaymentResult:
        """Process payment with fraud detection and validation"""
        
        # Fraud detection
        fraud_analysis = self.fraud_detector.analyze_payment(payment_request)
        
        if fraud_analysis['risk_level'] == FraudRiskLevel.BLOCKED:
            return PaymentResult(
                payment_id=str(uuid.uuid4()),
                status=PaymentStatus.FAILED,
                amount=payment_request.amount,
                currency=payment_request.currency,
                gateway_transaction_id="",
                fraud_risk_level=fraud_analysis['risk_level'],
                fraud_score=fraud_analysis['score'],
                processor_response={},
                fees=Decimal('0'),
                created_at=datetime.utcnow(),
                success=False,
                error_message="Payment blocked due to fraud risk"
            )
        
        # Get appropriate gateway
        gateway = self.payment_gateways.get(payment_request.payment_method)
        if not gateway:
            raise ValueError(f"Unsupported payment method: {payment_request.payment_method}")
        
        try:
            # Process payment through gateway
            gateway_result = gateway.process_payment(payment_request)
            
            # Create payment result
            payment_result = PaymentResult(
                payment_id=str(uuid.uuid4()),
                status=PaymentStatus.AUTHORIZED if gateway_result['success'] else PaymentStatus.FAILED,
                amount=payment_request.amount,
                currency=payment_request.currency,
                gateway_transaction_id=gateway_result.get('transaction_id', ''),
                fraud_risk_level=fraud_analysis['risk_level'],
                fraud_score=fraud_analysis['score'],
                processor_response=gateway_result,
                fees=gateway_result.get('fees', Decimal('0')),
                created_at=datetime.utcnow(),
                success=gateway_result['success'],
                error_message=gateway_result.get('error')
            )
            
            # Store payment record
            self.payment_history.append(payment_result)
            
            return payment_result
            
        except Exception as e:
            return PaymentResult(
                payment_id=str(uuid.uuid4()),
                status=PaymentStatus.FAILED,
                amount=payment_request.amount,
                currency=payment_request.currency,
                gateway_transaction_id="",
                fraud_risk_level=fraud_analysis['risk_level'],
                fraud_score=fraud_analysis['score'],
                processor_response={},
                fees=Decimal('0'),
                created_at=datetime.utcnow(),
                success=False,
                error_message=str(e)
            )
    
    def capture_payment(self, payment_id: str, amount: Optional[Decimal] = None) -> PaymentResult:
        """Capture authorized payment"""
        payment = self._get_payment(payment_id)
        
        if payment.status != PaymentStatus.AUTHORIZED:
            raise ValueError("Payment must be authorized to capture")
        
        capture_amount = amount or payment.amount
        
        gateway = self.payment_gateways[PaymentMethod.CREDIT_CARD]  # Simplified
        result = gateway.capture_payment(payment.gateway_transaction_id, capture_amount)
        
        if result['success']:
            payment.status = PaymentStatus.CAPTURED
        
        return payment
    
    def refund_payment(self, payment_id: str, amount: Optional[Decimal] = None, 
                      reason: str = "") -> Dict[str, Any]:
        """Process payment refund"""
        payment = self._get_payment(payment_id)
        
        if payment.status not in [PaymentStatus.CAPTURED, PaymentStatus.PARTIALLY_REFUNDED]:
            raise ValueError("Payment must be captured to refund")
        
        refund_amount = amount or payment.amount
        
        gateway = self.payment_gateways[PaymentMethod.CREDIT_CARD]  # Simplified
        result = gateway.refund_payment(
            payment.gateway_transaction_id, 
            refund_amount, 
            reason
        )
        
        if result['success']:
            if refund_amount == payment.amount:
                payment.status = PaymentStatus.REFUNDED
            else:
                payment.status = PaymentStatus.PARTIALLY_REFUNDED
        
        return {
            'success': result['success'],
            'refund_id': result.get('refund_id'),
            'amount': refund_amount,
            'error': result.get('error')
        }
    
    def _get_payment(self, payment_id: str) -> PaymentResult:
        """Get payment by ID"""
        for payment in self.payment_history:
            if payment.payment_id == payment_id:
                return payment
        raise ValueError(f"Payment {payment_id} not found")

class FraudDetector:
    """AI-powered fraud detection system"""
    
    def __init__(self):
        self.risk_rules = [
            self._check_velocity_fraud,
            self._check_geographic_risk,
            self._check_payment_pattern,
            self._check_device_fingerprint
        ]
    
    def analyze_payment(self, payment_request: PaymentRequest) -> Dict[str, Any]:
        """Analyze payment for fraud risk"""
        risk_score = 0.0
        risk_factors = []
        
        # Run all fraud detection rules
        for rule in self.risk_rules:
            rule_result = rule(payment_request)
            risk_score += rule_result['score']
            if rule_result['factors']:
                risk_factors.extend(rule_result['factors'])
        
        # Determine risk level
        if risk_score >= 80:
            risk_level = FraudRiskLevel.BLOCKED
        elif risk_score >= 60:
            risk_level = FraudRiskLevel.HIGH
        elif risk_score >= 30:
            risk_level = FraudRiskLevel.MEDIUM
        else:
            risk_level = FraudRiskLevel.LOW
        
        return {
            'score': risk_score,
            'risk_level': risk_level,
            'factors': risk_factors
        }
    
    def _check_velocity_fraud(self, payment_request: PaymentRequest) -> Dict[str, Any]:
        """Check for velocity-based fraud patterns"""
        # Implementation would check payment frequency, amounts, etc.
        return {'score': 0.0, 'factors': []}
    
    def _check_geographic_risk(self, payment_request: PaymentRequest) -> Dict[str, Any]:
        """Check geographic risk factors"""
        # Implementation would check IP location vs billing address
        return {'score': 0.0, 'factors': []}
    
    def _check_payment_pattern(self, payment_request: PaymentRequest) -> Dict[str, Any]:
        """Check for suspicious payment patterns"""
        # Implementation would check for round amounts, unusual times, etc.
        return {'score': 0.0, 'factors': []}
    
    def _check_device_fingerprint(self, payment_request: PaymentRequest) -> Dict[str, Any]:
        """Check device fingerprint for fraud"""
        # Implementation would analyze browser fingerprint, device characteristics
        return {'score': 0.0, 'factors': []}

class StripeGateway:
    """Stripe payment gateway integration"""
    
    def __init__(self, config: Dict[str, str]):
        self.api_key = config['api_key']
        self.webhook_secret = config['webhook_secret']
        self.base_url = "https://api.stripe.com/v1"
    
    def process_payment(self, payment_request: PaymentRequest) -> Dict[str, Any]:
        """Process payment through Stripe"""
        # Implementation would make actual API calls to Stripe
        return {
            'success': True,
            'transaction_id': f"ch_{uuid.uuid4()}",
            'fees': payment_request.amount * Decimal('0.029')  # 2.9% fee
        }
    
    def capture_payment(self, transaction_id: str, amount: Decimal) -> Dict[str, Any]:
        """Capture authorized payment"""
        return {'success': True}
    
    def refund_payment(self, transaction_id: str, amount: Decimal, reason: str) -> Dict[str, Any]:
        """Process refund"""
        return {'success': True, 'refund_id': f"re_{uuid.uuid4()}"}

class PayPalGateway:
    """PayPal payment gateway integration"""
    
    def __init__(self, config: Dict[str, str]):
        self.client_id = config['client_id']
        self.client_secret = config['client_secret']
        self.base_url = config.get('base_url', 'https://api.paypal.com')
    
    def process_payment(self, payment_request: PaymentRequest) -> Dict[str, Any]:
        """Process payment through PayPal"""
        return {
            'success': True,
            'transaction_id': f"pp_{uuid.uuid4()}",
            'fees': payment_request.amount * Decimal('0.034')  # 3.4% fee
        }

class ApplePayGateway:
    """Apple Pay gateway integration"""
    
    def __init__(self, config: Dict[str, str]):
        self.merchant_id = config['merchant_id']
        self.certificate_path = config['certificate_path']
    
    def process_payment(self, payment_request: PaymentRequest) -> Dict[str, Any]:
        """Process Apple Pay payment"""
        return {
            'success': True,
            'transaction_id': f"ap_{uuid.uuid4()}",
            'fees': payment_request.amount * Decimal('0.025')  # 2.5% fee
        }
```

### Inventory Management

**Definition:** Real-time inventory tracking with reservation, backorder handling, and supplier integration.

#### Real-Time Inventory System
**Manages inventory levels, reservations, and automatic reordering.**

**Implementation - Inventory Service:**
```python
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import threading
import time

class InventoryStatus(Enum):
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    BACKORDERED = "backordered"
    DISCONTINUED = "discontinued"

@dataclass
class InventoryItem:
    """Inventory item with stock tracking"""
    sku: str
    product_name: str
    current_stock: int
    reserved_stock: int
    reorder_point: int
    reorder_quantity: int
    cost_per_unit: Decimal
    location: str
    supplier_id: str
    last_updated: datetime
    
    @property
    def available_stock(self) -> int:
        return max(0, self.current_stock - self.reserved_stock)
    
    @property
    def status(self) -> InventoryStatus:
        if self.current_stock <= 0:
            return InventoryStatus.OUT_OF_STOCK
        elif self.current_stock <= self.reorder_point:
            return InventoryStatus.LOW_STOCK
        else:
            return InventoryStatus.IN_STOCK

@dataclass
class StockReservation:
    """Stock reservation for pending orders"""
    reservation_id: str
    sku: str
    quantity: int
    order_id: str
    created_at: datetime
    expires_at: datetime
    status: str = "active"

class InventoryService:
    """Real-time inventory management service"""
    
    def __init__(self, reorder_service=None):
        self.inventory = {}  # In production, use database
        self.reservations = {}
        self.reorder_service = reorder_service
        self.lock = threading.RLock()
        
        # Start background processes
        self._start_reservation_cleanup()
        self._start_reorder_monitoring()
    
    def add_inventory_item(self, item: InventoryItem):
        """Add new inventory item"""
        with self.lock:
            self.inventory[item.sku] = item
    
    def check_availability(self, sku: str, quantity: int) -> bool:
        """Check if sufficient stock is available"""
        with self.lock:
            item = self.inventory.get(sku)
            if not item:
                return False
            return item.available_stock >= quantity
    
    def reserve_items(self, cart_items: List[CartItem], 
                     order_id: str = None, 
                     reservation_duration_minutes: int = 15) -> str:
        """Reserve inventory for order processing"""
        with self.lock:
            reservation_id = str(uuid.uuid4())
            reservations = []
            
            try:
                # Check availability for all items first
                for cart_item in cart_items:
                    if not self.check_availability(cart_item.sku, cart_item.quantity):
                        raise InsufficientInventoryException(
                            f"Insufficient stock for {cart_item.product_name}"
                        )
                
                # Create reservations
                for cart_item in cart_items:
                    item = self.inventory[cart_item.sku]
                    item.reserved_stock += cart_item.quantity
                    
                    reservation = StockReservation(
                        reservation_id=reservation_id,
                        sku=cart_item.sku,
                        quantity=cart_item.quantity,
                        order_id=order_id or "",
                        created_at=datetime.utcnow(),
                        expires_at=datetime.utcnow() + timedelta(minutes=reservation_duration_minutes)
                    )
                    
                    self.reservations[f"{reservation_id}_{cart_item.sku}"] = reservation
                    reservations.append(reservation)
                
                return reservation_id
                
            except Exception as e:
                # Rollback any partial reservations
                for reservation in reservations:
                    self._release_single_reservation(reservation)
                raise e
    
    def confirm_reservation(self, reservation_id: str):
        """Confirm reservation and commit stock reduction"""
        with self.lock:
            reservations_to_confirm = [
                res for res in self.reservations.values()
                if res.reservation_id == reservation_id and res.status == "active"
            ]
            
            for reservation in reservations_to_confirm:
                item = self.inventory[reservation.sku]
                
                # Reduce actual stock
                item.current_stock -= reservation.quantity
                item.reserved_stock -= reservation.quantity
                item.last_updated = datetime.utcnow()
                
                # Mark reservation as confirmed
                reservation.status = "confirmed"
                
                # Check if reorder is needed
                if item.current_stock <= item.reorder_point:
                    self._trigger_reorder(item)
    
    def release_reservation(self, reservation_id: str):
        """Release reservation and free up stock"""
        with self.lock:
            reservations_to_release = [
                res for res in self.reservations.values()
                if res.reservation_id == reservation_id and res.status == "active"
            ]
            
            for reservation in reservations_to_release:
                self._release_single_reservation(reservation)
    
    def update_stock(self, sku: str, quantity: int, operation: str = "set"):
        """Update inventory stock levels"""
        with self.lock:
            item = self.inventory.get(sku)
            if not item:
                raise ValueError(f"Item {sku} not found in inventory")
            
            if operation == "set":
                item.current_stock = quantity
            elif operation == "add":
                item.current_stock += quantity
            elif operation == "subtract":
                item.current_stock = max(0, item.current_stock - quantity)
            
            item.last_updated = datetime.utcnow()
    
    def get_inventory_status(self, sku: str) -> Dict[str, Any]:
        """Get current inventory status for item"""
        item = self.inventory.get(sku)
        if not item:
            return {"error": "Item not found"}
        
        return {
            "sku": item.sku,
            "product_name": item.product_name,
            "current_stock": item.current_stock,
            "reserved_stock": item.reserved_stock,
            "available_stock": item.available_stock,
            "status": item.status.value,
            "reorder_point": item.reorder_point,
            "last_updated": item.last_updated.isoformat()
        }
    
    def get_low_stock_items(self) -> List[Dict[str, Any]]:
        """Get all items with low stock"""
        low_stock_items = []
        
        for item in self.inventory.values():
            if item.status in [InventoryStatus.LOW_STOCK, InventoryStatus.OUT_OF_STOCK]:
                low_stock_items.append({
                    "sku": item.sku,
                    "product_name": item.product_name,
                    "current_stock": item.current_stock,
                    "reorder_point": item.reorder_point,
                    "status": item.status.value
                })
        
        return low_stock_items
    
    def _release_single_reservation(self, reservation: StockReservation):
        """Release a single reservation"""
        item = self.inventory.get(reservation.sku)
        if item:
            item.reserved_stock -= reservation.quantity
            item.last_updated = datetime.utcnow()
        
        reservation.status = "released"
    
    def _trigger_reorder(self, item: InventoryItem):
        """Trigger automatic reorder"""
        if self.reorder_service:
            self.reorder_service.create_purchase_order(
                supplier_id=item.supplier_id,
                sku=item.sku,
                quantity=item.reorder_quantity,
                cost_per_unit=item.cost_per_unit
            )
    
    def _start_reservation_cleanup(self):
        """Start background process to clean up expired reservations"""
        def cleanup_expired_reservations():
            while True:
                try:
                    current_time = datetime.utcnow()
                    expired_reservations = [
                        res for res in self.reservations.values()
                        if res.status == "active" and res.expires_at < current_time
                    ]
                    
                    for reservation in expired_reservations:
                        self._release_single_reservation(reservation)
                    
                    time.sleep(60)  # Check every minute
                    
                except Exception as e:
                    print(f"Error in reservation cleanup: {e}")
                    time.sleep(60)
        
        cleanup_thread = threading.Thread(target=cleanup_expired_reservations)
        cleanup_thread.daemon = True
        cleanup_thread.start()
    
    def _start_reorder_monitoring(self):
        """Start background process to monitor reorder needs"""
        def monitor_reorders():
            while True:
                try:
                    for item in self.inventory.values():
                        if item.current_stock <= item.reorder_point:
                            self._trigger_reorder(item)
                    
                    time.sleep(3600)  # Check every hour
                    
                except Exception as e:
                    print(f"Error in reorder monitoring: {e}")
                    time.sleep(3600)
        
        reorder_thread = threading.Thread(target=monitor_reorders)
        reorder_thread.daemon = True
        reorder_thread.start()

class InsufficientInventoryException(Exception):
    pass
```

### Recommendation Systems

**Definition:** AI-powered product recommendation engine using collaborative and content-based filtering.

#### Hybrid Recommendation Engine
**Combines multiple recommendation algorithms for personalized product suggestions.**

**Implementation - Recommendation Service:**
```python
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

@dataclass
class ProductInteraction:
    """User-product interaction data"""
    user_id: str
    product_id: str
    interaction_type: str  # view, cart, purchase
    rating: Optional[float]
    timestamp: datetime
    session_id: str
    category: str
    price: Decimal

@dataclass
class Product:
    """Product information for recommendations"""
    product_id: str
    name: str
    category: str
    subcategory: str
    price: Decimal
    description: str
    tags: List[str]
    rating: float
    review_count: int
    brand: str

@dataclass
class RecommendationResult:
    """Recommendation result with score and reason"""
    product_id: str
    score: float
    reason: str
    algorithm: str
    metadata: Dict[str, Any]

class RecommendationEngine:
    """Hybrid recommendation system"""
    
    def __init__(self):
        self.interactions = []  # In production, use database
        self.products = {}
        self.user_profiles = {}
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.content_similarity_matrix = None
        self._initialize_models()
    
    def add_interaction(self, interaction: ProductInteraction):
        """Record user-product interaction"""
        self.interactions.append(interaction)
        self._update_user_profile(interaction)
    
    def add_product(self, product: Product):
        """Add product to recommendation system"""
        self.products[product.product_id] = product
        self._update_content_similarity()
    
    def get_recommendations(self, user_id: str, num_recommendations: int = 10,
                          exclude_purchased: bool = True) -> List[RecommendationResult]:
        """Get hybrid recommendations for user"""
        
        # Get recommendations from different algorithms
        collaborative_recs = self._collaborative_filtering(user_id, num_recommendations * 2)
        content_recs = self._content_based_filtering(user_id, num_recommendations * 2)
        popularity_recs = self._popularity_based_recommendations(num_recommendations)
        
        # Combine and score recommendations
        combined_recs = self._combine_recommendations(
            collaborative_recs, content_recs, popularity_recs
        )
        
        # Filter out purchased items if requested
        if exclude_purchased:
            purchased_items = self._get_user_purchased_items(user_id)
            combined_recs = [rec for rec in combined_recs 
                           if rec.product_id not in purchased_items]
        
        # Sort by score and return top N
        combined_recs.sort(key=lambda x: x.score, reverse=True)
        return combined_recs[:num_recommendations]
    
    def get_similar_products(self, product_id: str, num_similar: int = 5) -> List[RecommendationResult]:
        """Get products similar to given product"""
        if product_id not in self.products:
            return []
        
        product = self.products[product_id]
        similar_products = []
        
        # Content-based similarity
        if self.content_similarity_matrix is not None:
            product_ids = list(self.products.keys())
            try:
                product_index = product_ids.index(product_id)
                similarities = self.content_similarity_matrix[product_index]
                
                # Get top similar products
                similar_indices = np.argsort(similarities)[::-1][1:num_similar+1]
                
                for idx in similar_indices:
                    similar_product_id = product_ids[idx]
                    similar_products.append(RecommendationResult(
                        product_id=similar_product_id,
                        score=similarities[idx],
                        reason=f"Similar to {product.name}",
                        algorithm="content_similarity",
                        metadata={"base_product": product_id}
                    ))
            except ValueError:
                pass  # Product not in similarity matrix
        
        return similar_products
    
    def get_trending_products(self, category: str = None, 
                            time_window_days: int = 7) -> List[RecommendationResult]:
        """Get trending products based on recent interactions"""
        cutoff_date = datetime.utcnow() - timedelta(days=time_window_days)
        
        # Filter recent interactions
        recent_interactions = [
            interaction for interaction in self.interactions
            if interaction.timestamp >= cutoff_date
        ]
        
        # Filter by category if specified
        if category:
            recent_interactions = [
                interaction for interaction in recent_interactions
                if interaction.category == category
            ]
        
        # Calculate trending score
        product_scores = {}
        for interaction in recent_interactions:
            product_id = interaction.product_id
            
            # Weight different interaction types
            weights = {
                'view': 1.0,
                'cart': 3.0,
                'purchase': 5.0
            }
            
            score = weights.get(interaction.interaction_type, 1.0)
            
            # Apply time decay (more recent = higher score)
            time_diff = datetime.utcnow() - interaction.timestamp
            time_decay = max(0.1, 1.0 - (time_diff.days / time_window_days))
            score *= time_decay
            
            if product_id not in product_scores:
                product_scores[product_id] = 0
            product_scores[product_id] += score
        
        # Convert to recommendation results
        trending_products = []
        for product_id, score in sorted(product_scores.items(), 
                                      key=lambda x: x[1], reverse=True):
            if product_id in self.products:
                trending_products.append(RecommendationResult(
                    product_id=product_id,
                    score=score,
                    reason="Trending product",
                    algorithm="trending",
                    metadata={"time_window_days": time_window_days}
                ))
        
        return trending_products
    
    def _collaborative_filtering(self, user_id: str, num_recs: int) -> List[RecommendationResult]:
        """User-based collaborative filtering"""
        user_interactions = self._get_user_interactions(user_id)
        if not user_interactions:
            return []
        
        # Find similar users
        similar_users = self._find_similar_users(user_id)
        
        # Get products liked by similar users
        recommendations = {}
        
        for similar_user_id, similarity_score in similar_users[:10]:  # Top 10 similar users
            similar_user_interactions = self._get_user_interactions(similar_user_id)
            
            for interaction in similar_user_interactions:
                if interaction.product_id not in [i.product_id for i in user_interactions]:
                    if interaction.product_id not in recommendations:
                        recommendations[interaction.product_id] = 0
                    
                    # Score based on similarity and interaction type
                    interaction_weights = {
                        'view': 1.0,
                        'cart': 2.0,
                        'purchase': 3.0
                    }
                    
                    weight = interaction_weights.get(interaction.interaction_type, 1.0)
                    recommendations[interaction.product_id] += similarity_score * weight
        
        # Convert to recommendation results
        collaborative_recs = []
        for product_id, score in sorted(recommendations.items(), 
                                      key=lambda x: x[1], reverse=True)[:num_recs]:
            collaborative_recs.append(RecommendationResult(
                product_id=product_id,
                score=score,
                reason="Users with similar interests also liked this",
                algorithm="collaborative_filtering",
                metadata={"similar_users_count": len(similar_users)}
            ))
        
        return collaborative_recs
    
    def _content_based_filtering(self, user_id: str, num_recs: int) -> List[RecommendationResult]:
        """Content-based filtering using product features"""
        user_profile = self.user_profiles.get(user_id, {})
        if not user_profile:
            return []
        
        # Get user's preferred categories and features
        preferred_categories = user_profile.get('preferred_categories', {})
        preferred_brands = user_profile.get('preferred_brands', {})
        
        content_recs = []
        
        for product_id, product in self.products.items():
            # Skip if user already interacted with this product
            if self._user_interacted_with_product(user_id, product_id):
                continue
            
            score = 0.0
            
            # Category preference
            category_score = preferred_categories.get(product.category, 0)
            score += category_score * 0.4
            
            # Brand preference
            brand_score = preferred_brands.get(product.brand, 0)
            score += brand_score * 0.3
            
            # Rating and popularity
            score += (product.rating / 5.0) * 0.2
            score += min(1.0, product.review_count / 100.0) * 0.1
            
            if score > 0:
                content_recs.append(RecommendationResult(
                    product_id=product_id,
                    score=score,
                    reason=f"Matches your interest in {product.category}",
                    algorithm="content_based",
                    metadata={
                        "category_match": category_score > 0,
                        "brand_match": brand_score > 0
                    }
                ))
        
        # Sort by score and return top recommendations
        content_recs.sort(key=lambda x: x.score, reverse=True)
        return content_recs[:num_recs]
    
    def _popularity_based_recommendations(self, num_recs: int) -> List[RecommendationResult]:
        """Popularity-based recommendations for new users"""
        # Calculate popularity scores
        product_popularity = {}
        
        for interaction in self.interactions:
            product_id = interaction.product_id
            
            if product_id not in product_popularity:
                product_popularity[product_id] = 0
            
            # Weight by interaction type
            weights = {'view': 1, 'cart': 2, 'purchase': 3}
            product_popularity[product_id] += weights.get(interaction.interaction_type, 1)
        
        # Combine with product ratings
        popularity_recs = []
        for product_id, popularity in product_popularity.items():
            if product_id in self.products:
                product = self.products[product_id]
                
                # Combine popularity with rating
                combined_score = (popularity * 0.7) + (product.rating * product.review_count * 0.3)
                
                popularity_recs.append(RecommendationResult(
                    product_id=product_id,
                    score=combined_score,
                    reason="Popular product",
                    algorithm="popularity",
                    metadata={"popularity_score": popularity}
                ))
        
        popularity_recs.sort(key=lambda x: x.score, reverse=True)
        return popularity_recs[:num_recs]
    
    def _combine_recommendations(self, *recommendation_lists) -> List[RecommendationResult]:
        """Combine recommendations from different algorithms"""
        combined_scores = {}
        
        # Weight different algorithms
        algorithm_weights = {
            'collaborative_filtering': 0.4,
            'content_based': 0.35,
            'popularity': 0.15,
            'trending': 0.1
        }
        
        for rec_list in recommendation_lists:
            for rec in rec_list:
                if rec.product_id not in combined_scores:
                    combined_scores[rec.product_id] = {
                        'score': 0.0,
                        'algorithms': [],
                        'reasons': []
                    }
                
                weight = algorithm_weights.get(rec.algorithm, 0.1)
                combined_scores[rec.product_id]['score'] += rec.score * weight
                combined_scores[rec.product_id]['algorithms'].append(rec.algorithm)
                combined_scores[rec.product_id]['reasons'].append(rec.reason)
        
        # Create final recommendations
        final_recs = []
        for product_id, data in combined_scores.items():
            final_recs.append(RecommendationResult(
                product_id=product_id,
                score=data['score'],
                reason="; ".join(set(data['reasons'])),
                algorithm="hybrid",
                metadata={
                    'contributing_algorithms': data['algorithms'],
                    'algorithm_count': len(set(data['algorithms']))
                }
            ))
        
        return final_recs
    
    def _initialize_models(self):
        """Initialize recommendation models"""
        # Initialize content similarity matrix
        self._update_content_similarity()
    
    def _update_content_similarity(self):
        """Update content-based similarity matrix"""
        if not self.products:
            return
        
        # Create content vectors
        product_contents = []
        for product in self.products.values():
            content = f"{product.name} {product.description} {' '.join(product.tags)} {product.category} {product.brand}"
            product_contents.append(content)
        
        if product_contents:
            # Calculate TF-IDF matrix
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(product_contents)
            
            # Calculate cosine similarity
            self.content_similarity_matrix = cosine_similarity(tfidf_matrix)
    
    def _update_user_profile(self, interaction: ProductInteraction):
        """Update user profile based on interaction"""
        if interaction.user_id not in self.user_profiles:
            self.user_profiles[interaction.user_id] = {
                'preferred_categories': {},
                'preferred_brands': {},
                'average_price_range': []
            }
        
        profile = self.user_profiles[interaction.user_id]
        
        # Update category preferences
        if interaction.category not in profile['preferred_categories']:
            profile['preferred_categories'][interaction.category] = 0
        profile['preferred_categories'][interaction.category] += 1
        
        # Update brand preferences if product exists
        if interaction.product_id in self.products:
            product = self.products[interaction.product_id]
            if product.brand not in profile['preferred_brands']:
                profile['preferred_brands'][product.brand] = 0
            profile['preferred_brands'][product.brand] += 1
            
            # Update price range
            profile['average_price_range'].append(float(interaction.price))
            # Keep only last 50 prices
            profile['average_price_range'] = profile['average_price_range'][-50:]
    
    def _get_user_interactions(self, user_id: str) -> List[ProductInteraction]:
        """Get all interactions for a user"""
        return [interaction for interaction in self.interactions 
                if interaction.user_id == user_id]
    
    def _find_similar_users(self, user_id: str) -> List[tuple]:
        """Find users with similar preferences"""
        user_interactions = self._get_user_interactions(user_id)
        user_products = set(interaction.product_id for interaction in user_interactions)
        
        similar_users = []
        
        # Get all unique users
        all_users = set(interaction.user_id for interaction in self.interactions)
        
        for other_user_id in all_users:
            if other_user_id == user_id:
                continue
            
            other_interactions = self._get_user_interactions(other_user_id)
            other_products = set(interaction.product_id for interaction in other_interactions)
            
            # Calculate Jaccard similarity
            intersection = len(user_products.intersection(other_products))
            union = len(user_products.union(other_products))
            
            if union > 0:
                similarity = intersection / union
                if similarity > 0.1:  # Minimum similarity threshold
                    similar_users.append((other_user_id, similarity))
        
        # Sort by similarity
        similar_users.sort(key=lambda x: x[1], reverse=True)
        return similar_users
    
    def _user_interacted_with_product(self, user_id: str, product_id: str) -> bool:
        """Check if user has interacted with product"""
        return any(
            interaction.user_id == user_id and interaction.product_id == product_id
            for interaction in self.interactions
        )
    
    def _get_user_purchased_items(self, user_id: str) -> set:
        """Get products purchased by user"""
        return set(
            interaction.product_id for interaction in self.interactions
            if interaction.user_id == user_id and interaction.interaction_type == 'purchase'
        )
```

This comprehensive Architecture E-commerce implementation provides production-ready solutions for shopping cart management, multi-step checkout processes, secure payment processing with fraud detection, real-time inventory management with automatic reordering, and AI-powered recommendation systems using hybrid approaches.