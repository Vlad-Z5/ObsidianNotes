# Architecture Layered

## Core Concepts

Layered architecture is a software design pattern that organizes code into horizontal layers, where each layer has a specific responsibility and depends only on the layers below it. This approach promotes separation of concerns, maintainability, and testability by creating clear boundaries between different aspects of the application.

### N-Tier Architecture

#### Traditional Three-Tier Architecture
**Definition:** Separates applications into three distinct layers: presentation, business logic, and data access.

**Example - Enterprise E-commerce System:**
```python
# Presentation Layer (Web Controllers)
from flask import Flask, request, jsonify, render_template
from typing import Dict, Any, List
import logging

class ProductController:
    """Handles HTTP requests and responses for product operations"""
    
    def __init__(self, product_service):
        self.product_service = product_service
        self.logger = logging.getLogger(__name__)
    
    def get_product(self, product_id: str):
        """GET /products/{id} - Get product details"""
        try:
            # Input validation and sanitization
            if not product_id or not product_id.isdigit():
                return jsonify({'error': 'Invalid product ID'}), 400
            
            # Delegate to business layer
            product = self.product_service.get_product_details(int(product_id))
            
            if not product:
                return jsonify({'error': 'Product not found'}), 404
            
            # Format response for presentation
            return jsonify({
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': float(product.price),
                'availability': product.is_available(),
                'category': product.category.name if product.category else None,
                'images': [img.url for img in product.images],
                'reviews_summary': {
                    'average_rating': product.average_rating,
                    'total_reviews': product.total_reviews
                }
            })
            
        except BusinessLogicError as e:
            self.logger.warning(f"Business logic error: {e}")
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            self.logger.error(f"Unexpected error in get_product: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    def create_product(self):
        """POST /products - Create new product"""
        try:
            # Extract and validate request data
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'Request body required'}), 400
            
            # Input validation
            validation_errors = self._validate_product_data(data)
            if validation_errors:
                return jsonify({'errors': validation_errors}), 400
            
            # Delegate to business layer
            product = self.product_service.create_product(data)
            
            # Return created resource
            return jsonify({
                'id': product.id,
                'name': product.name,
                'message': 'Product created successfully'
            }), 201
            
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400
        except BusinessLogicError as e:
            return jsonify({'error': str(e)}), 409
        except Exception as e:
            self.logger.error(f"Unexpected error in create_product: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    def search_products(self):
        """GET /products/search - Search products with pagination"""
        try:
            # Extract query parameters
            query = request.args.get('q', '')
            category = request.args.get('category')
            min_price = request.args.get('min_price', type=float)
            max_price = request.args.get('max_price', type=float)
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 20, type=int), 100)
            sort_by = request.args.get('sort_by', 'relevance')
            
            # Create search criteria
            search_criteria = ProductSearchCriteria(
                query=query,
                category=category,
                min_price=min_price,
                max_price=max_price,
                sort_by=sort_by
            )
            
            # Delegate to business layer
            search_result = self.product_service.search_products(
                search_criteria, 
                page, 
                per_page
            )
            
            # Format response
            return jsonify({
                'products': [
                    self._format_product_summary(product) 
                    for product in search_result.products
                ],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': search_result.total_count,
                    'total_pages': search_result.total_pages,
                    'has_next': search_result.has_next,
                    'has_prev': search_result.has_prev
                },
                'facets': search_result.facets
            })
            
        except Exception as e:
            self.logger.error(f"Error in search_products: {e}")
            return jsonify({'error': 'Search failed'}), 500
    
    def _validate_product_data(self, data: Dict[str, Any]) -> List[str]:
        """Validate product creation data"""
        errors = []
        
        if not data.get('name'):
            errors.append('Product name is required')
        elif len(data['name']) < 3:
            errors.append('Product name must be at least 3 characters')
        
        if not data.get('description'):
            errors.append('Product description is required')
        
        try:
            price = float(data.get('price', 0))
            if price <= 0:
                errors.append('Product price must be greater than 0')
        except (ValueError, TypeError):
            errors.append('Invalid price format')
        
        if 'category_id' in data:
            try:
                int(data['category_id'])
            except (ValueError, TypeError):
                errors.append('Invalid category ID')
        
        return errors
    
    def _format_product_summary(self, product) -> Dict[str, Any]:
        """Format product for list display"""
        return {
            'id': product.id,
            'name': product.name,
            'price': float(product.price),
            'image_url': product.primary_image_url,
            'average_rating': product.average_rating,
            'is_available': product.is_available()
        }

# Business Logic Layer (Services)
from decimal import Decimal
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional

@dataclass
class ProductSearchCriteria:
    query: str = ""
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    sort_by: str = "relevance"

class ProductService:
    """Contains business logic for product operations"""
    
    def __init__(self, product_repository, category_repository, inventory_service, pricing_service):
        self.product_repository = product_repository
        self.category_repository = category_repository
        self.inventory_service = inventory_service
        self.pricing_service = pricing_service
        self.logger = logging.getLogger(__name__)
    
    def get_product_details(self, product_id: int) -> Optional['Product']:
        """Get complete product details with business rules applied"""
        # Retrieve from data layer
        product = self.product_repository.find_by_id(product_id)
        
        if not product:
            return None
        
        # Apply business logic
        product = self._enrich_product_data(product)
        
        # Check if product should be visible
        if not self._is_product_visible(product):
            return None
        
        return product
    
    def create_product(self, product_data: Dict[str, Any]) -> 'Product':
        """Create new product with business validation"""
        # Business validation
        self._validate_product_business_rules(product_data)
        
        # Check category exists
        if 'category_id' in product_data:
            category = self.category_repository.find_by_id(product_data['category_id'])
            if not category:
                raise BusinessLogicError("Invalid category")
        
        # Create product entity
        product = Product(
            name=product_data['name'],
            description=product_data['description'],
            base_price=Decimal(str(product_data['price'])),
            category_id=product_data.get('category_id'),
            sku=self._generate_sku(product_data['name']),
            created_at=datetime.utcnow(),
            status=ProductStatus.DRAFT
        )
        
        # Apply business rules
        product.slug = self._generate_slug(product.name)
        
        # Set initial inventory
        if 'initial_stock' in product_data:
            product.initial_stock = product_data['initial_stock']
        
        # Save through data layer
        saved_product = self.product_repository.save(product)
        
        # Create initial inventory record
        if hasattr(product, 'initial_stock'):
            self.inventory_service.create_inventory_record(
                saved_product.id, 
                product.initial_stock
            )
        
        # Log business event
        self.logger.info(f"Product created: {saved_product.id} - {saved_product.name}")
        
        return saved_product
    
    def search_products(self, criteria: ProductSearchCriteria, page: int, per_page: int) -> 'ProductSearchResult':
        """Search products with business logic applied"""
        # Apply business rules to search criteria
        processed_criteria = self._process_search_criteria(criteria)
        
        # Delegate to data layer
        search_result = self.product_repository.search(
            processed_criteria, 
            page, 
            per_page
        )
        
        # Apply business logic to results
        enriched_products = []
        for product in search_result.products:
            enriched_product = self._enrich_product_data(product)
            if self._is_product_visible(enriched_product):
                enriched_products.append(enriched_product)
        
        # Apply pricing rules
        for product in enriched_products:
            product.current_price = self.pricing_service.calculate_current_price(
                product.base_price,
                product.category_id,
                product.id
            )
        
        return ProductSearchResult(
            products=enriched_products,
            total_count=search_result.total_count,
            facets=search_result.facets
        )
    
    def update_product_status(self, product_id: int, new_status: 'ProductStatus') -> 'Product':
        """Update product status with business rules"""
        product = self.product_repository.find_by_id(product_id)
        
        if not product:
            raise BusinessLogicError("Product not found")
        
        # Business rules for status transitions
        if not self._is_valid_status_transition(product.status, new_status):
            raise BusinessLogicError(
                f"Cannot transition from {product.status} to {new_status}"
            )
        
        # Special business logic for publishing
        if new_status == ProductStatus.PUBLISHED:
            self._validate_product_for_publishing(product)
        
        # Update status
        product.status = new_status
        product.updated_at = datetime.utcnow()
        
        # Apply status-specific business logic
        if new_status == ProductStatus.PUBLISHED:
            product.published_at = datetime.utcnow()
        elif new_status == ProductStatus.DISCONTINUED:
            # Remove from active inventory
            self.inventory_service.discontinue_product(product_id)
        
        return self.product_repository.save(product)
    
    def _enrich_product_data(self, product: 'Product') -> 'Product':
        """Apply business logic to enrich product data"""
        # Get current inventory
        inventory = self.inventory_service.get_current_inventory(product.id)
        product.current_stock = inventory.available_quantity if inventory else 0
        
        # Calculate availability
        product.is_in_stock = product.current_stock > 0
        
        # Get current pricing
        product.current_price = self.pricing_service.calculate_current_price(
            product.base_price,
            product.category_id,
            product.id
        )
        
        # Calculate ratings
        reviews = self.product_repository.get_product_reviews(product.id)
        if reviews:
            product.average_rating = sum(r.rating for r in reviews) / len(reviews)
            product.total_reviews = len(reviews)
        else:
            product.average_rating = 0.0
            product.total_reviews = 0
        
        return product
    
    def _is_product_visible(self, product: 'Product') -> bool:
        """Business rules for product visibility"""
        if product.status != ProductStatus.PUBLISHED:
            return False
        
        if hasattr(product, 'category') and product.category:
            if not product.category.is_active:
                return False
        
        # Hide products that have been out of stock for too long
        if not product.is_in_stock:
            last_stock_date = self.inventory_service.get_last_stock_date(product.id)
            if last_stock_date and (datetime.utcnow() - last_stock_date).days > 30:
                return False
        
        return True
    
    def _validate_product_business_rules(self, product_data: Dict[str, Any]):
        """Validate business rules for product creation"""
        # Check for duplicate names in same category
        if 'category_id' in product_data:
            existing = self.product_repository.find_by_name_and_category(
                product_data['name'], 
                product_data['category_id']
            )
            if existing:
                raise BusinessLogicError("Product with same name exists in category")
        
        # Validate price rules
        price = Decimal(str(product_data['price']))
        if price > Decimal('10000'):  # Business rule: max price
            raise BusinessLogicError("Product price cannot exceed $10,000")
    
    def _generate_sku(self, product_name: str) -> str:
        """Generate unique SKU based on business rules"""
        import re
        
        # Extract alphanumeric characters and convert to uppercase
        base_sku = re.sub(r'[^a-zA-Z0-9]', '', product_name.upper())[:8]
        
        # Add timestamp for uniqueness
        timestamp = datetime.utcnow().strftime("%m%d")
        
        # Check uniqueness and add suffix if needed
        counter = 1
        sku = f"{base_sku}{timestamp}"
        
        while self.product_repository.find_by_sku(sku):
            sku = f"{base_sku}{timestamp}{counter:02d}"
            counter += 1
        
        return sku

# Data Access Layer (Repositories)
from abc import ABC, abstractmethod
import sqlite3
from contextlib import contextmanager

class ProductRepository(ABC):
    """Abstract interface for product data access"""
    
    @abstractmethod
    def find_by_id(self, product_id: int) -> Optional['Product']:
        pass
    
    @abstractmethod
    def find_by_sku(self, sku: str) -> Optional['Product']:
        pass
    
    @abstractmethod
    def save(self, product: 'Product') -> 'Product':
        pass
    
    @abstractmethod
    def search(self, criteria: ProductSearchCriteria, page: int, per_page: int) -> 'ProductSearchResult':
        pass

class SQLiteProductRepository(ProductRepository):
    """SQLite implementation of product repository"""
    
    def __init__(self, database_path: str):
        self.database_path = database_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    sku TEXT UNIQUE NOT NULL,
                    slug TEXT UNIQUE,
                    base_price DECIMAL(10,2) NOT NULL,
                    category_id INTEGER,
                    status TEXT DEFAULT 'draft',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    published_at TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES categories (id)
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_products_status ON products(status)
            ''')
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper cleanup"""
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise
        else:
            conn.commit()
        finally:
            conn.close()
    
    def find_by_id(self, product_id: int) -> Optional['Product']:
        """Find product by ID"""
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT p.*, c.name as category_name, c.is_active as category_active
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.id = ?
            ''', (product_id,))
            
            row = cursor.fetchone()
            if row:
                return self._map_row_to_product(row)
            return None
    
    def find_by_sku(self, sku: str) -> Optional['Product']:
        """Find product by SKU"""
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT p.*, c.name as category_name, c.is_active as category_active
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.sku = ?
            ''', (sku,))
            
            row = cursor.fetchone()
            if row:
                return self._map_row_to_product(row)
            return None
    
    def save(self, product: 'Product') -> 'Product':
        """Save product to database"""
        with self._get_connection() as conn:
            if product.id:
                # Update existing product
                conn.execute('''
                    UPDATE products 
                    SET name = ?, description = ?, base_price = ?, 
                        category_id = ?, status = ?, updated_at = CURRENT_TIMESTAMP,
                        published_at = ?
                    WHERE id = ?
                ''', (
                    product.name,
                    product.description,
                    float(product.base_price),
                    product.category_id,
                    product.status.value if hasattr(product.status, 'value') else product.status,
                    product.published_at.isoformat() if product.published_at else None,
                    product.id
                ))
            else:
                # Insert new product
                cursor = conn.execute('''
                    INSERT INTO products (name, description, sku, slug, base_price, category_id, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    product.name,
                    product.description,
                    product.sku,
                    product.slug,
                    float(product.base_price),
                    product.category_id,
                    product.status.value if hasattr(product.status, 'value') else product.status
                ))
                
                product.id = cursor.lastrowid
        
        return product
    
    def search(self, criteria: ProductSearchCriteria, page: int, per_page: int) -> 'ProductSearchResult':
        """Search products with criteria"""
        with self._get_connection() as conn:
            # Build dynamic query
            where_clauses = ['p.status = ?']
            params = ['published']
            
            if criteria.query:
                where_clauses.append('(p.name LIKE ? OR p.description LIKE ?)')
                search_term = f"%{criteria.query}%"
                params.extend([search_term, search_term])
            
            if criteria.category:
                where_clauses.append('c.name = ?')
                params.append(criteria.category)
            
            if criteria.min_price is not None:
                where_clauses.append('p.base_price >= ?')
                params.append(criteria.min_price)
            
            if criteria.max_price is not None:
                where_clauses.append('p.base_price <= ?')
                params.append(criteria.max_price)
            
            where_clause = ' AND '.join(where_clauses)
            
            # Order by clause
            order_mapping = {
                'name': 'p.name ASC',
                'price_low': 'p.base_price ASC',
                'price_high': 'p.base_price DESC',
                'newest': 'p.created_at DESC',
                'relevance': 'p.name ASC'  # Simplified relevance
            }
            order_clause = order_mapping.get(criteria.sort_by, 'p.name ASC')
            
            # Count total results
            count_query = f'''
                SELECT COUNT(*) as total
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE {where_clause}
            '''
            
            cursor = conn.execute(count_query, params)
            total_count = cursor.fetchone()['total']
            
            # Get paginated results
            offset = (page - 1) * per_page
            
            search_query = f'''
                SELECT p.*, c.name as category_name, c.is_active as category_active
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE {where_clause}
                ORDER BY {order_clause}
                LIMIT ? OFFSET ?
            '''
            
            cursor = conn.execute(search_query, params + [per_page, offset])
            products = [self._map_row_to_product(row) for row in cursor.fetchall()]
            
            return ProductSearchResult(
                products=products,
                total_count=total_count,
                total_pages=(total_count + per_page - 1) // per_page,
                has_next=offset + per_page < total_count,
                has_prev=page > 1,
                facets={}  # Simplified - would include category counts, price ranges, etc.
            )
    
    def _map_row_to_product(self, row) -> 'Product':
        """Map database row to Product entity"""
        product = Product(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            sku=row['sku'],
            slug=row['slug'],
            base_price=Decimal(str(row['base_price'])),
            category_id=row['category_id'],
            status=ProductStatus(row['status']) if row['status'] else ProductStatus.DRAFT,
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
            published_at=datetime.fromisoformat(row['published_at']) if row['published_at'] else None
        )
        
        # Add category information if available
        if row['category_name']:
            product.category = Category(
                id=row['category_id'],
                name=row['category_name'],
                is_active=bool(row['category_active'])
            )
        
        return product

# Domain Models
from enum import Enum

class ProductStatus(Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    DISCONTINUED = "discontinued"

@dataclass
class Product:
    name: str
    description: str
    sku: str
    base_price: Decimal
    status: ProductStatus = ProductStatus.DRAFT
    id: Optional[int] = None
    slug: Optional[str] = None
    category_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    
    # Enriched fields (populated by business layer)
    current_price: Optional[Decimal] = None
    current_stock: int = 0
    is_in_stock: bool = False
    average_rating: float = 0.0
    total_reviews: int = 0
    category: Optional['Category'] = None
    
    def is_available(self) -> bool:
        """Business rule for product availability"""
        return (self.status == ProductStatus.PUBLISHED and 
                self.is_in_stock and 
                (not self.category or self.category.is_active))

@dataclass
class Category:
    id: int
    name: str
    is_active: bool = True

@dataclass
class ProductSearchResult:
    products: List[Product]
    total_count: int
    total_pages: int = 0
    has_next: bool = False
    has_prev: bool = False
    facets: Dict[str, Any] = None

# Exception Classes
class BusinessLogicError(Exception):
    """Raised when business rules are violated"""
    pass

class ValidationError(Exception):
    """Raised when input validation fails"""
    pass
```

#### Four-Tier Architecture with Separate Database Layer
**Definition:** Extends three-tier by separating the database into its own physical tier.

**Example - Distributed E-commerce Architecture:**
```python
# Presentation Tier (API Gateway)
from flask import Flask, request, jsonify
import requests
import asyncio
import aiohttp
from typing import Dict, Any

class APIGateway:
    """API Gateway that routes requests to appropriate business services"""
    
    def __init__(self, service_registry):
        self.service_registry = service_registry
        self.app = Flask(__name__)
        self._setup_routes()
    
    def _setup_routes(self):
        @self.app.route('/api/products/<int:product_id>')
        def get_product(product_id):
            return self._route_to_service('product-service', f'/products/{product_id}')
        
        @self.app.route('/api/orders', methods=['POST'])
        def create_order():
            return self._route_to_service('order-service', '/orders', method='POST', data=request.json)
        
        @self.app.route('/api/customers/<int:customer_id>/recommendations')
        def get_recommendations(customer_id):
            return self._route_to_service('recommendation-service', f'/customers/{customer_id}/recommendations')
    
    def _route_to_service(self, service_name: str, path: str, method='GET', data=None):
        """Route request to appropriate service"""
        try:
            service_url = self.service_registry.get_service_url(service_name)
            
            if method == 'GET':
                response = requests.get(f"{service_url}{path}", timeout=30)
            elif method == 'POST':
                response = requests.post(f"{service_url}{path}", json=data, timeout=30)
            
            return jsonify(response.json()), response.status_code
            
        except requests.exceptions.Timeout:
            return jsonify({'error': 'Service timeout'}), 504
        except requests.exceptions.RequestException:
            return jsonify({'error': 'Service unavailable'}), 503

# Business Logic Tier (Microservices)
class ProductBusinessService:
    """Business service running on separate application server"""
    
    def __init__(self, data_service_client):
        self.data_service = data_service_client
    
    async def get_product_with_recommendations(self, product_id: int) -> Dict[str, Any]:
        """Complex business operation involving multiple data sources"""
        
        # Get product details from data tier
        product = await self.data_service.get_product(product_id)
        
        if not product:
            raise ProductNotFoundError()
        
        # Apply business rules
        product_data = {
            'id': product['id'],
            'name': product['name'],
            'price': self._calculate_current_price(product),
            'availability': self._check_availability(product),
            'shipping_info': self._calculate_shipping_options(product)
        }
        
        # Get related products (business logic)
        related_products = await self._get_related_products(product_id)
        product_data['related_products'] = related_products
        
        # Get customer-specific recommendations if user is logged in
        if self._get_current_user():
            recommendations = await self._get_personalized_recommendations(
                product_id, 
                self._get_current_user().id
            )
            product_data['personalized_recommendations'] = recommendations
        
        return product_data
    
    def _calculate_current_price(self, product: Dict[str, Any]) -> float:
        """Business logic for dynamic pricing"""
        base_price = product['base_price']
        
        # Apply time-based pricing
        if self._is_peak_season():
            base_price *= 1.1
        
        # Apply inventory-based pricing
        stock_level = product.get('stock_level', 0)
        if stock_level < 10:  # Low stock
            base_price *= 1.05
        elif stock_level > 100:  # Overstocked
            base_price *= 0.95
        
        # Apply customer tier pricing
        customer = self._get_current_user()
        if customer and customer.tier == 'premium':
            base_price *= 0.9  # 10% discount for premium customers
        
        return round(base_price, 2)
    
    def _check_availability(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Business logic for availability checking"""
        stock_level = product.get('stock_level', 0)
        reserved_stock = product.get('reserved_stock', 0)
        available_stock = stock_level - reserved_stock
        
        return {
            'in_stock': available_stock > 0,
            'quantity_available': available_stock,
            'estimated_restock_date': self._estimate_restock_date(product) if available_stock <= 0 else None,
            'can_backorder': product.get('allows_backorder', False),
            'shipping_delay': self._calculate_shipping_delay(available_stock)
        }

# Data Access Tier (Data Services)
class ProductDataService:
    """Data service running on separate tier, handles all data operations"""
    
    def __init__(self, database_cluster):
        self.db_cluster = database_cluster
        self.cache = RedisCache()
    
    async def get_product(self, product_id: int) -> Dict[str, Any]:
        """Get product from database with caching"""
        
        # Check cache first
        cache_key = f"product:{product_id}"
        cached_product = await self.cache.get(cache_key)
        
        if cached_product:
            return cached_product
        
        # Read from database cluster
        async with self.db_cluster.get_read_connection() as conn:
            query = '''
                SELECT p.*, c.name as category_name, i.stock_level, i.reserved_stock
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                LEFT JOIN inventory i ON p.id = i.product_id
                WHERE p.id = ? AND p.status = 'published'
            '''
            
            result = await conn.fetch_one(query, (product_id,))
            
            if result:
                product_data = dict(result)
                
                # Cache the result
                await self.cache.set(cache_key, product_data, expire=300)  # 5 minutes
                
                return product_data
            
        return None
    
    async def search_products(self, search_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Search products with complex queries"""
        
        # Build dynamic query based on criteria
        query_parts = ['SELECT p.*, c.name as category_name FROM products p LEFT JOIN categories c ON p.category_id = c.id']
        where_conditions = ['p.status = ?']
        params = ['published']
        
        if search_criteria.get('query'):
            where_conditions.append('(p.name LIKE ? OR p.description LIKE ?)')
            search_term = f"%{search_criteria['query']}%"
            params.extend([search_term, search_term])
        
        if search_criteria.get('category'):
            where_conditions.append('c.name = ?')
            params.append(search_criteria['category'])
        
        if search_criteria.get('price_range'):
            where_conditions.append('p.base_price BETWEEN ? AND ?')
            params.extend([search_criteria['price_range']['min'], search_criteria['price_range']['max']])
        
        # Combine query parts
        if where_conditions:
            query_parts.append('WHERE ' + ' AND '.join(where_conditions))
        
        # Add ordering
        sort_mapping = {
            'price_asc': 'p.base_price ASC',
            'price_desc': 'p.base_price DESC',
            'name': 'p.name ASC',
            'newest': 'p.created_at DESC'
        }
        order_by = sort_mapping.get(search_criteria.get('sort_by'), 'p.name ASC')
        query_parts.append(f'ORDER BY {order_by}')
        
        # Add pagination
        page = search_criteria.get('page', 1)
        per_page = search_criteria.get('per_page', 20)
        offset = (page - 1) * per_page
        query_parts.append(f'LIMIT {per_page} OFFSET {offset}')
        
        final_query = ' '.join(query_parts)
        
        # Execute search query
        async with self.db_cluster.get_read_connection() as conn:
            results = await conn.fetch_all(final_query, params)
            
            # Get total count for pagination
            count_query = final_query.replace('SELECT p.*, c.name as category_name', 'SELECT COUNT(*)')
            count_query = count_query.split('ORDER BY')[0]  # Remove ORDER BY and LIMIT
            
            total_count = await conn.fetch_val(count_query, params)
            
            return {
                'products': [dict(row) for row in results],
                'total_count': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': (total_count + per_page - 1) // per_page
            }
    
    async def save_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save product to database cluster"""
        
        # Use write connection for data modification
        async with self.db_cluster.get_write_connection() as conn:
            if product_data.get('id'):
                # Update existing product
                query = '''
                    UPDATE products 
                    SET name = ?, description = ?, base_price = ?, category_id = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                '''
                await conn.execute(query, (
                    product_data['name'],
                    product_data['description'],
                    product_data['base_price'],
                    product_data['category_id'],
                    product_data['id']
                ))
                
                product_id = product_data['id']
            else:
                # Insert new product
                query = '''
                    INSERT INTO products (name, description, base_price, category_id, status, created_at)
                    VALUES (?, ?, ?, ?, 'draft', CURRENT_TIMESTAMP)
                '''
                product_id = await conn.fetch_val(query, (
                    product_data['name'],
                    product_data['description'],
                    product_data['base_price'],
                    product_data['category_id']
                ))
        
        # Invalidate cache
        await self.cache.delete(f"product:{product_id}")
        
        # Return updated product
        return await self.get_product(product_id)

# Database Tier (Separate Physical Layer)
class DatabaseCluster:
    """Database cluster with read/write separation"""
    
    def __init__(self, write_connection_string: str, read_connection_strings: List[str]):
        self.write_db = DatabaseConnection(write_connection_string)
        self.read_dbs = [DatabaseConnection(conn_str) for conn_str in read_connection_strings]
        self.read_db_index = 0
    
    async def get_write_connection(self):
        """Get connection to write database (master)"""
        return self.write_db
    
    async def get_read_connection(self):
        """Get connection to read database (slave) with load balancing"""
        # Simple round-robin load balancing
        read_db = self.read_dbs[self.read_db_index]
        self.read_db_index = (self.read_db_index + 1) % len(self.read_dbs)
        return read_db
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all database connections"""
        health_status = {}
        
        # Check write database
        try:
            await self.write_db.execute('SELECT 1')
            health_status['write_db'] = True
        except Exception:
            health_status['write_db'] = False
        
        # Check read databases
        for i, read_db in enumerate(self.read_dbs):
            try:
                await read_db.execute('SELECT 1')
                health_status[f'read_db_{i}'] = True
            except Exception:
                health_status[f'read_db_{i}'] = False
        
        return health_status

class DatabaseConnection:
    """Individual database connection with connection pooling"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.pool = None
    
    async def execute(self, query: str, params=None):
        """Execute query on database"""
        if not self.pool:
            await self._create_pool()
        
        async with self.pool.acquire() as conn:
            if params:
                return await conn.execute(query, params)
            else:
                return await conn.execute(query)
    
    async def fetch_one(self, query: str, params=None):
        """Fetch single row"""
        if not self.pool:
            await self._create_pool()
        
        async with self.pool.acquire() as conn:
            if params:
                return await conn.fetchrow(query, params)
            else:
                return await conn.fetchrow(query)
    
    async def fetch_all(self, query: str, params=None):
        """Fetch multiple rows"""
        if not self.pool:
            await self._create_pool()
        
        async with self.pool.acquire() as conn:
            if params:
                return await conn.fetch(query, params)
            else:
                return await conn.fetch(query)
    
    async def _create_pool(self):
        """Create connection pool"""
        import asyncpg
        self.pool = await asyncpg.create_pool(
            self.connection_string,
            min_size=5,
            max_size=20,
            command_timeout=60
        )

# Cross-Cutting Concerns
class LoggingMiddleware:
    """Handles logging across all layers"""
    
    def __init__(self, logger):
        self.logger = logger
    
    def log_request(self, layer: str, operation: str, details: Dict[str, Any]):
        """Log request with standardized format"""
        self.logger.info(f"[{layer}] {operation}", extra={
            'layer': layer,
            'operation': operation,
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def log_error(self, layer: str, operation: str, error: Exception, details: Dict[str, Any]):
        """Log error with context"""
        self.logger.error(f"[{layer}] {operation} failed: {str(error)}", extra={
            'layer': layer,
            'operation': operation,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        })

class SecurityMiddleware:
    """Handles security across all layers"""
    
    def __init__(self, auth_service, authorization_service):
        self.auth_service = auth_service
        self.authorization_service = authorization_service
    
    def authenticate_request(self, request):
        """Authenticate incoming request"""
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            raise AuthenticationError("Missing authentication header")
        
        token = auth_header.replace('Bearer ', '')
        user = self.auth_service.validate_token(token)
        
        if not user:
            raise AuthenticationError("Invalid token")
        
        return user
    
    def authorize_operation(self, user, resource: str, operation: str):
        """Authorize user operation on resource"""
        if not self.authorization_service.check_permission(user, resource, operation):
            raise AuthorizationError(f"User {user.id} not authorized for {operation} on {resource}")
    
    def sanitize_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize input data"""
        sanitized = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                # Remove potential XSS and SQL injection patterns
                sanitized[key] = self._sanitize_string(value)
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _sanitize_string(self, value: str) -> str:
        """Sanitize string input"""
        import html
        
        # HTML escape
        value = html.escape(value)
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Limit length
        if len(value) > 1000:
            value = value[:1000]
        
        return value
```

This N-Tier architecture example demonstrates how to properly separate concerns across multiple physical and logical tiers, with each layer having distinct responsibilities and clear interfaces between them.

### Clean Architecture

#### Core Principles and Structure
**Definition:** An architecture that emphasizes independence of frameworks, testability, and dependency inversion by organizing code into concentric circles with dependencies pointing inward.

**Example - Banking System with Clean Architecture:**
```python
# Entities Layer (Innermost Circle - Enterprise Business Rules)
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from typing import List, Optional
from enum import Enum

class AccountType(Enum):
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT = "credit"

@dataclass
class Money:
    """Value object representing monetary amounts"""
    amount: Decimal
    currency: str = "USD"
    
    def __post_init__(self):
        if self.amount < 0 and self.currency != "USD":
            raise ValueError("Negative amounts only allowed for USD (credit)")
        self.amount = self.amount.quantize(Decimal('0.01'))
    
    def add(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)
    
    def subtract(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot subtract different currencies")
        return Money(self.amount - other.amount, self.currency)
    
    def is_positive(self) -> bool:
        return self.amount > 0
    
    def is_zero(self) -> bool:
        return self.amount == 0

class Account:
    """Core business entity representing a bank account"""
    
    def __init__(self, account_number: str, account_type: AccountType, initial_balance: Money):
        self.account_number = account_number
        self.account_type = account_type
        self.balance = initial_balance
        self.created_at = datetime.utcnow()
        self.is_active = True
        self._transaction_history: List['Transaction'] = []
    
    def deposit(self, amount: Money, description: str = "") -> 'Transaction':
        """Deposit money into account - core business rule"""
        if not self.is_active:
            raise AccountClosedError("Cannot deposit to closed account")
        
        if not amount.is_positive():
            raise InvalidAmountError("Deposit amount must be positive")
        
        transaction = Transaction(
            amount=amount,
            transaction_type=TransactionType.DEPOSIT,
            description=description,
            account_number=self.account_number
        )
        
        self.balance = self.balance.add(amount)
        self._transaction_history.append(transaction)
        
        return transaction
    
    def withdraw(self, amount: Money, description: str = "") -> 'Transaction':
        """Withdraw money from account - core business rule with overdraft logic"""
        if not self.is_active:
            raise AccountClosedError("Cannot withdraw from closed account")
        
        if not amount.is_positive():
            raise InvalidAmountError("Withdrawal amount must be positive")
        
        # Business rule: Check if withdrawal is allowed
        if not self._can_withdraw(amount):
            raise InsufficientFundsError(
                f"Insufficient funds. Balance: {self.balance.amount}, Requested: {amount.amount}"
            )
        
        transaction = Transaction(
            amount=amount,
            transaction_type=TransactionType.WITHDRAWAL,
            description=description,
            account_number=self.account_number
        )
        
        self.balance = self.balance.subtract(amount)
        self._transaction_history.append(transaction)
        
        return transaction
    
    def transfer_to(self, target_account: 'Account', amount: Money, description: str = "") -> List['Transaction']:
        """Transfer money to another account - orchestrates business rules"""
        if not self.is_active or not target_account.is_active:
            raise AccountClosedError("Cannot transfer involving closed accounts")
        
        if self.account_number == target_account.account_number:
            raise InvalidTransferError("Cannot transfer to same account")
        
        # Execute as atomic operation
        withdrawal_transaction = self.withdraw(amount, f"Transfer to {target_account.account_number}: {description}")
        deposit_transaction = target_account.deposit(amount, f"Transfer from {self.account_number}: {description}")
        
        return [withdrawal_transaction, deposit_transaction]
    
    def calculate_interest(self, annual_rate: Decimal, days: int) -> Money:
        """Calculate interest based on account type and balance - business rule"""
        if self.account_type == AccountType.CHECKING:
            # Checking accounts only earn interest on balances > $1000
            if self.balance.amount <= Decimal('1000'):
                return Money(Decimal('0'))
        
        elif self.account_type == AccountType.CREDIT:
            # Credit accounts charge interest on negative balances
            if self.balance.amount >= 0:
                return Money(Decimal('0'))
            # Higher interest rate for credit accounts
            annual_rate = annual_rate * Decimal('1.5')
        
        # Calculate daily interest
        daily_rate = annual_rate / Decimal('365')
        interest_amount = self.balance.amount * daily_rate * Decimal(str(days))
        
        return Money(interest_amount, self.balance.currency)
    
    def _can_withdraw(self, amount: Money) -> bool:
        """Business rule for withdrawal limits"""
        if self.account_type == AccountType.SAVINGS:
            # Savings accounts cannot go negative
            return self.balance.amount >= amount.amount
        
        elif self.account_type == AccountType.CHECKING:
            # Checking accounts allow $500 overdraft
            overdraft_limit = Decimal('500')
            return (self.balance.amount + overdraft_limit) >= amount.amount
        
        elif self.account_type == AccountType.CREDIT:
            # Credit accounts have credit limit of $5000
            credit_limit = Decimal('5000')
            return (amount.amount - self.balance.amount) <= credit_limit
        
        return False
    
    def get_transaction_history(self) -> List['Transaction']:
        """Get immutable copy of transaction history"""
        return self._transaction_history.copy()

class TransactionType(Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    INTEREST = "interest"
    FEE = "fee"

@dataclass
class Transaction:
    """Entity representing a financial transaction"""
    amount: Money
    transaction_type: TransactionType
    account_number: str
    description: str = ""
    timestamp: datetime = None
    transaction_id: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.transaction_id is None:
            import uuid
            self.transaction_id = str(uuid.uuid4())

# Use Cases Layer (Application Business Rules)
class DepositMoneyUseCase:
    """Use case for depositing money into an account"""
    
    def __init__(self, account_repository, transaction_repository, notification_service):
        self.account_repository = account_repository
        self.transaction_repository = transaction_repository
        self.notification_service = notification_service
    
    async def execute(self, request: 'DepositRequest') -> 'DepositResponse':
        """Execute deposit use case with all business rules and side effects"""
        
        # Get account from repository
        account = await self.account_repository.get_by_number(request.account_number)
        if not account:
            raise AccountNotFoundError(f"Account {request.account_number} not found")
        
        # Execute core business logic
        transaction = account.deposit(
            Money(request.amount, request.currency),
            request.description
        )
        
        # Persist changes
        await self.account_repository.save(account)
        await self.transaction_repository.save(transaction)
        
        # Side effects
        await self._handle_side_effects(account, transaction)
        
        return DepositResponse(
            transaction_id=transaction.transaction_id,
            new_balance=account.balance.amount,
            timestamp=transaction.timestamp
        )
    
    async def _handle_side_effects(self, account: Account, transaction: Transaction):
        """Handle side effects like notifications and compliance"""
        
        # Large deposit reporting (compliance requirement)
        if transaction.amount.amount > Decimal('10000'):
            await self.notification_service.send_large_deposit_alert(
                account.account_number,
                transaction.amount,
                transaction.timestamp
            )
        
        # Send confirmation to account holder
        await self.notification_service.send_transaction_confirmation(
            account.account_number,
            transaction
        )

class TransferMoneyUseCase:
    """Use case for transferring money between accounts"""
    
    def __init__(self, account_repository, transaction_repository, fee_calculator, notification_service):
        self.account_repository = account_repository
        self.transaction_repository = transaction_repository
        self.fee_calculator = fee_calculator
        self.notification_service = notification_service
    
    async def execute(self, request: 'TransferRequest') -> 'TransferResponse':
        """Execute transfer with atomic transaction handling"""
        
        # Get both accounts
        source_account = await self.account_repository.get_by_number(request.source_account)
        target_account = await self.account_repository.get_by_number(request.target_account)
        
        if not source_account:
            raise AccountNotFoundError(f"Source account {request.source_account} not found")
        if not target_account:
            raise AccountNotFoundError(f"Target account {request.target_account} not found")
        
        transfer_amount = Money(request.amount, request.currency)
        
        # Calculate fees
        fee = await self.fee_calculator.calculate_transfer_fee(
            source_account, 
            target_account, 
            transfer_amount
        )
        
        # Execute transfer (atomic operation)
        try:
            # Start transaction
            async with self.account_repository.transaction():
                # Execute core business logic
                transfer_transactions = source_account.transfer_to(
                    target_account, 
                    transfer_amount, 
                    request.description
                )
                
                # Apply fee if applicable
                fee_transaction = None
                if fee.amount > 0:
                    fee_transaction = source_account.withdraw(fee, "Transfer fee")
                    transfer_transactions.append(fee_transaction)
                
                # Persist all changes
                await self.account_repository.save(source_account)
                await self.account_repository.save(target_account)
                
                for transaction in transfer_transactions:
                    await self.transaction_repository.save(transaction)
                
                # Side effects
                await self._handle_transfer_side_effects(
                    source_account, 
                    target_account, 
                    transfer_transactions,
                    fee_transaction
                )
                
                return TransferResponse(
                    transfer_transactions=[t.transaction_id for t in transfer_transactions],
                    fee_charged=fee.amount,
                    source_new_balance=source_account.balance.amount,
                    target_new_balance=target_account.balance.amount
                )
                
        except Exception as e:
            # Transaction will be rolled back automatically
            raise TransferFailedError(f"Transfer failed: {str(e)}")
    
    async def _handle_transfer_side_effects(self, source_account, target_account, transactions, fee_transaction):
        """Handle notifications and compliance for transfers"""
        
        # International transfer compliance
        if await self._is_international_transfer(source_account, target_account):
            await self.notification_service.send_international_transfer_alert(
                source_account.account_number,
                target_account.account_number,
                transactions[0].amount
            )
        
        # Send confirmations
        await self.notification_service.send_transfer_confirmation(
            source_account.account_number,
            target_account.account_number,
            transactions
        )

class CalculateInterestUseCase:
    """Use case for calculating and applying interest to accounts"""
    
    def __init__(self, account_repository, transaction_repository, interest_rate_service):
        self.account_repository = account_repository
        self.transaction_repository = transaction_repository
        self.interest_rate_service = interest_rate_service
    
    async def execute(self, request: 'InterestCalculationRequest') -> 'InterestCalculationResponse':
        """Calculate and apply interest for a specific period"""
        
        # Get all eligible accounts
        accounts = await self.account_repository.get_accounts_by_type(request.account_types)
        
        results = []
        total_interest_paid = Money(Decimal('0'))
        
        for account in accounts:
            # Get current interest rate for account type
            rate = await self.interest_rate_service.get_current_rate(account.account_type)
            
            # Calculate interest
            interest = account.calculate_interest(rate, request.days)
            
            if not interest.is_zero():
                # Apply interest as a transaction
                interest_transaction = account.deposit(interest, f"Interest for {request.days} days")
                
                # Persist changes
                await self.account_repository.save(account)
                await self.transaction_repository.save(interest_transaction)
                
                total_interest_paid = total_interest_paid.add(interest)
                
                results.append({
                    'account_number': account.account_number,
                    'interest_earned': interest.amount,
                    'new_balance': account.balance.amount
                })
        
        return InterestCalculationResponse(
            accounts_processed=len(results),
            total_interest_paid=total_interest_paid.amount,
            account_results=results
        )

# Interface Adapters Layer (Controllers, Presenters, Gateways)
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Union

# Request/Response Models (Data Transfer Objects)
class DepositRequest(BaseModel):
    account_number: str = Field(..., min_length=8, max_length=20)
    amount: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    currency: str = Field(default="USD", regex="^[A-Z]{3}$")
    description: str = Field(default="", max_length=200)

class DepositResponse(BaseModel):
    transaction_id: str
    new_balance: Decimal
    timestamp: datetime
    status: str = "success"

class TransferRequest(BaseModel):
    source_account: str = Field(..., min_length=8, max_length=20)
    target_account: str = Field(..., min_length=8, max_length=20)
    amount: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    currency: str = Field(default="USD", regex="^[A-Z]{3}$")
    description: str = Field(default="", max_length=200)

class TransferResponse(BaseModel):
    transfer_transactions: List[str]
    fee_charged: Decimal
    source_new_balance: Decimal
    target_new_balance: Decimal
    status: str = "success"

# Controllers (Interface Adapters)
class BankingController:
    """HTTP API controller that adapts web requests to use cases"""
    
    def __init__(self, deposit_use_case, transfer_use_case, withdrawal_use_case):
        self.deposit_use_case = deposit_use_case
        self.transfer_use_case = transfer_use_case
        self.withdrawal_use_case = withdrawal_use_case
        self.app = FastAPI(title="Banking API")
        self._setup_routes()
    
    def _setup_routes(self):
        @self.app.post("/accounts/deposit", response_model=DepositResponse)
        async def deposit_money(request: DepositRequest):
            try:
                response = await self.deposit_use_case.execute(request)
                return response
            except AccountNotFoundError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except (InvalidAmountError, AccountClosedError) as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail="Internal server error")
        
        @self.app.post("/accounts/transfer", response_model=TransferResponse)
        async def transfer_money(request: TransferRequest):
            try:
                response = await self.transfer_use_case.execute(request)
                return response
            except (AccountNotFoundError, InvalidTransferError) as e:
                raise HTTPException(status_code=404, detail=str(e))
            except (InsufficientFundsError, InvalidAmountError) as e:
                raise HTTPException(status_code=400, detail=str(e))
            except TransferFailedError as e:
                raise HTTPException(status_code=422, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail="Internal server error")
        
        @self.app.get("/accounts/{account_number}/balance")
        async def get_account_balance(account_number: str):
            try:
                account = await self.account_repository.get_by_number(account_number)
                if not account:
                    raise HTTPException(status_code=404, detail="Account not found")
                
                return {
                    "account_number": account.account_number,
                    "balance": account.balance.amount,
                    "currency": account.balance.currency,
                    "account_type": account.account_type.value,
                    "is_active": account.is_active
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail="Internal server error")

# Repository Interfaces (Interface Adapters - Abstract Gateways)
class AccountRepository(ABC):
    """Abstract repository interface for account persistence"""
    
    @abstractmethod
    async def get_by_number(self, account_number: str) -> Optional[Account]:
        pass
    
    @abstractmethod
    async def save(self, account: Account) -> None:
        pass
    
    @abstractmethod
    async def get_accounts_by_type(self, account_types: List[AccountType]) -> List[Account]:
        pass
    
    @abstractmethod
    def transaction(self):
        """Return a transaction context manager"""
        pass

class TransactionRepository(ABC):
    """Abstract repository interface for transaction persistence"""
    
    @abstractmethod
    async def save(self, transaction: Transaction) -> None:
        pass
    
    @abstractmethod
    async def get_by_account(self, account_number: str, limit: int = None) -> List[Transaction]:
        pass

# External Service Interfaces (Interface Adapters)
class NotificationService(ABC):
    """Abstract interface for notification services"""
    
    @abstractmethod
    async def send_transaction_confirmation(self, account_number: str, transaction: Transaction):
        pass
    
    @abstractmethod
    async def send_large_deposit_alert(self, account_number: str, amount: Money, timestamp: datetime):
        pass
    
    @abstractmethod
    async def send_transfer_confirmation(self, source_account: str, target_account: str, transactions: List[Transaction]):
        pass

# Frameworks and Drivers Layer (Outermost Circle)
import asyncpg
import asyncio
from contextlib import asynccontextmanager

# Database Implementation (Framework/Driver)
class PostgreSQLAccountRepository(AccountRepository):
    """PostgreSQL implementation of account repository"""
    
    def __init__(self, connection_pool):
        self.pool = connection_pool
    
    async def get_by_number(self, account_number: str) -> Optional[Account]:
        """Retrieve account from PostgreSQL database"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT account_number, account_type, balance_amount, balance_currency, 
                       created_at, is_active
                FROM accounts 
                WHERE account_number = $1
            ''', account_number)
            
            if row:
                account = Account(
                    account_number=row['account_number'],
                    account_type=AccountType(row['account_type']),
                    initial_balance=Money(
                        Decimal(str(row['balance_amount'])),
                        row['balance_currency']
                    )
                )
                account.created_at = row['created_at']
                account.is_active = row['is_active']
                
                # Load transaction history
                transactions = await self._load_transactions(conn, account_number)
                account._transaction_history = transactions
                
                return account
            
            return None
    
    async def save(self, account: Account) -> None:
        """Save account to PostgreSQL database"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO accounts (
                    account_number, account_type, balance_amount, balance_currency,
                    created_at, is_active
                ) VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (account_number) 
                DO UPDATE SET 
                    balance_amount = EXCLUDED.balance_amount,
                    is_active = EXCLUDED.is_active
            ''', 
                account.account_number,
                account.account_type.value,
                float(account.balance.amount),
                account.balance.currency,
                account.created_at,
                account.is_active
            )
    
    async def get_accounts_by_type(self, account_types: List[AccountType]) -> List[Account]:
        """Get all accounts of specified types"""
        type_values = [t.value for t in account_types]
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT account_number, account_type, balance_amount, balance_currency,
                       created_at, is_active
                FROM accounts 
                WHERE account_type = ANY($1::text[]) AND is_active = true
            ''', type_values)
            
            accounts = []
            for row in rows:
                account = Account(
                    account_number=row['account_number'],
                    account_type=AccountType(row['account_type']),
                    initial_balance=Money(
                        Decimal(str(row['balance_amount'])),
                        row['balance_currency']
                    )
                )
                account.created_at = row['created_at']
                account.is_active = row['is_active']
                accounts.append(account)
            
            return accounts
    
    @asynccontextmanager
    async def transaction(self):
        """Database transaction context manager"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                yield conn
    
    async def _load_transactions(self, conn, account_number: str) -> List[Transaction]:
        """Load transaction history for account"""
        rows = await conn.fetch('''
            SELECT transaction_id, amount, currency, transaction_type, 
                   description, timestamp
            FROM transactions 
            WHERE account_number = $1 
            ORDER BY timestamp DESC
        ''', account_number)
        
        transactions = []
        for row in rows:
            transaction = Transaction(
                amount=Money(Decimal(str(row['amount'])), row['currency']),
                transaction_type=TransactionType(row['transaction_type']),
                account_number=account_number,
                description=row['description'],
                timestamp=row['timestamp'],
                transaction_id=row['transaction_id']
            )
            transactions.append(transaction)
        
        return transactions

# Email Notification Implementation (Framework/Driver)
class EmailNotificationService(NotificationService):
    """Email-based notification service implementation"""
    
    def __init__(self, smtp_config):
        self.smtp_config = smtp_config
    
    async def send_transaction_confirmation(self, account_number: str, transaction: Transaction):
        """Send email confirmation for transaction"""
        subject = f"Transaction Confirmation - {transaction.transaction_type.value.title()}"
        body = f"""
        Dear Customer,
        
        A {transaction.transaction_type.value} of {transaction.amount.amount} {transaction.amount.currency}
        has been processed on your account {account_number}.
        
        Transaction ID: {transaction.transaction_id}
        Description: {transaction.description}
        Timestamp: {transaction.timestamp}
        
        Thank you for banking with us.
        """
        
        await self._send_email(account_number, subject, body)
    
    async def send_large_deposit_alert(self, account_number: str, amount: Money, timestamp: datetime):
        """Send compliance alert for large deposits"""
        subject = "Large Deposit Alert - Compliance Notification"
        body = f"""
        COMPLIANCE ALERT
        
        Large deposit detected:
        Account: {account_number}
        Amount: {amount.amount} {amount.currency}
        Timestamp: {timestamp}
        
        This transaction has been flagged for compliance review.
        """
        
        await self._send_email("compliance@bank.com", subject, body)
    
    async def send_transfer_confirmation(self, source_account: str, target_account: str, transactions: List[Transaction]):
        """Send transfer confirmation"""
        subject = "Transfer Confirmation"
        body = f"""
        Dear Customer,
        
        Your transfer has been completed successfully.
        
        From Account: {source_account}
        To Account: {target_account}
        Transaction IDs: {', '.join([t.transaction_id for t in transactions])}
        
        Thank you for banking with us.
        """
        
        await self._send_email(source_account, subject, body)
    
    async def _send_email(self, recipient: str, subject: str, body: str):
        """Send email using SMTP (simplified implementation)"""
        # In real implementation, would use proper SMTP client
        print(f"EMAIL TO: {recipient}")
        print(f"SUBJECT: {subject}")
        print(f"BODY: {body}")
        print("---")

# Dependency Injection Container (Framework/Driver)
class DIContainer:
    """Dependency injection container following dependency rule"""
    
    def __init__(self):
        self._services = {}
    
    async def setup(self):
        """Setup all dependencies respecting the dependency rule"""
        
        # Frameworks and Drivers (Outermost)
        db_pool = await asyncpg.create_pool(
            "postgresql://user:password@localhost/banking",
            min_size=5,
            max_size=20
        )
        
        account_repository = PostgreSQLAccountRepository(db_pool)
        transaction_repository = PostgreSQLTransactionRepository(db_pool)
        notification_service = EmailNotificationService(smtp_config={})
        interest_rate_service = ExternalInterestRateService()
        fee_calculator = StandardFeeCalculator()
        
        # Use Cases (Application Layer)
        deposit_use_case = DepositMoneyUseCase(
            account_repository,
            transaction_repository,
            notification_service
        )
        
        transfer_use_case = TransferMoneyUseCase(
            account_repository,
            transaction_repository,
            fee_calculator,
            notification_service
        )
        
        interest_use_case = CalculateInterestUseCase(
            account_repository,
            transaction_repository,
            interest_rate_service
        )
        
        # Interface Adapters
        banking_controller = BankingController(
            deposit_use_case,
            transfer_use_case,
            withdrawal_use_case=None  # Not implemented in this example
        )
        
        self._services.update({
            'account_repository': account_repository,
            'transaction_repository': transaction_repository,
            'notification_service': notification_service,
            'deposit_use_case': deposit_use_case,
            'transfer_use_case': transfer_use_case,
            'interest_use_case': interest_use_case,
            'banking_controller': banking_controller
        })
    
    def get(self, service_name: str):
        return self._services[service_name]

# Custom Exceptions
class AccountNotFoundError(Exception):
    pass

class AccountClosedError(Exception):
    pass

class InvalidAmountError(Exception):
    pass

class InsufficientFundsError(Exception):
    pass

class InvalidTransferError(Exception):
    pass

class TransferFailedError(Exception):
    pass
```

**Key Clean Architecture Principles Demonstrated:**

1. **Dependency Rule:** Dependencies point inward - outer layers depend on inner layers, never the reverse
2. **Entity Independence:** Core business entities (Account, Transaction) have no external dependencies
3. **Use Case Isolation:** Application business rules are separate from enterprise business rules
4. **Interface Segregation:** Abstract interfaces define contracts between layers
5. **Framework Independence:** Core business logic doesn't depend on specific frameworks

### Hexagonal Architecture (Ports & Adapters)

#### Core Structure and Implementation
**Definition:** Separates the application core from external concerns using ports (interfaces) and adapters (implementations).

**Example - Order Management System:**
```python
# Application Core (Business Logic)
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
from decimal import Decimal

# Domain Models (Application Core)
class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

@dataclass
class OrderItem:
    product_id: str
    product_name: str
    quantity: int
    unit_price: Decimal
    
    @property
    def total_price(self) -> Decimal:
        return self.unit_price * self.quantity

@dataclass
class ShippingAddress:
    street: str
    city: str
    state: str
    zip_code: str
    country: str

class Order:
    """Core domain entity for orders"""
    
    def __init__(self, customer_id: str, shipping_address: ShippingAddress):
        self.order_id = self._generate_order_id()
        self.customer_id = customer_id
        self.shipping_address = shipping_address
        self.items: List[OrderItem] = []
        self.status = OrderStatus.PENDING
        self.created_at = datetime.utcnow()
        self.total_amount = Decimal('0.00')
        self.payment_id: Optional[str] = None
    
    def add_item(self, item: OrderItem):
        """Add item to order with business validation"""
        if self.status != OrderStatus.PENDING:
            raise OrderModificationError("Cannot modify confirmed order")
        
        # Check if item already exists and update quantity
        existing_item = next(
            (i for i in self.items if i.product_id == item.product_id), 
            None
        )
        
        if existing_item:
            existing_item.quantity += item.quantity
        else:
            self.items.append(item)
        
        self._recalculate_total()
    
    def remove_item(self, product_id: str):
        """Remove item from order"""
        if self.status != OrderStatus.PENDING:
            raise OrderModificationError("Cannot modify confirmed order")
        
        self.items = [item for item in self.items if item.product_id != product_id]
        self._recalculate_total()
    
    def confirm(self):
        """Confirm order - business rule validation"""
        if not self.items:
            raise EmptyOrderError("Cannot confirm empty order")
        
        if self.status != OrderStatus.PENDING:
            raise InvalidOrderStateError("Order already confirmed")
        
        self.status = OrderStatus.CONFIRMED
    
    def mark_as_paid(self, payment_id: str):
        """Mark order as paid"""
        if self.status != OrderStatus.CONFIRMED:
            raise InvalidOrderStateError("Order must be confirmed before payment")
        
        self.payment_id = payment_id
        self.status = OrderStatus.PAID
    
    def ship(self, tracking_number: str):
        """Ship the order"""
        if self.status != OrderStatus.PAID:
            raise InvalidOrderStateError("Order must be paid before shipping")
        
        self.status = OrderStatus.SHIPPED
        self.tracking_number = tracking_number
    
    def cancel(self, reason: str):
        """Cancel order with business rules"""
        if self.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            raise InvalidOrderStateError("Cannot cancel shipped or delivered order")
        
        self.status = OrderStatus.CANCELLED
        self.cancellation_reason = reason
    
    def _recalculate_total(self):
        """Recalculate order total"""
        self.total_amount = sum(item.total_price for item in self.items)
    
    def _generate_order_id(self) -> str:
        import uuid
        return f"ORD-{uuid.uuid4().hex[:8].upper()}"

# Application Service (Application Core)
class OrderService:
    """Application service containing business use cases"""
    
    def __init__(self, 
                 order_repository,      # Port for persistence
                 inventory_service,     # Port for inventory
                 payment_service,       # Port for payments
                 shipping_service,      # Port for shipping
                 notification_service): # Port for notifications
        
        self.order_repository = order_repository
        self.inventory_service = inventory_service
        self.payment_service = payment_service
        self.shipping_service = shipping_service
        self.notification_service = notification_service
    
    async def create_order(self, customer_id: str, shipping_address: ShippingAddress, 
                          items_data: List[Dict[str, Any]]) -> Order:
        """Create new order use case"""
        
        # Create order entity
        order = Order(customer_id, shipping_address)
        
        # Add items with validation
        for item_data in items_data:
            # Validate product exists and get details
            product = await self.inventory_service.get_product(item_data['product_id'])
            if not product:
                raise ProductNotFoundError(f"Product {item_data['product_id']} not found")
            
            # Check inventory availability
            available_quantity = await self.inventory_service.check_availability(
                item_data['product_id']
            )
            
            if available_quantity < item_data['quantity']:
                raise InsufficientInventoryError(
                    f"Only {available_quantity} units available for product {item_data['product_id']}"
                )
            
            # Create order item
            order_item = OrderItem(
                product_id=item_data['product_id'],
                product_name=product['name'],
                quantity=item_data['quantity'],
                unit_price=Decimal(str(product['price']))
            )
            
            order.add_item(order_item)
        
        # Save order
        await self.order_repository.save(order)
        
        # Send order created notification
        await self.notification_service.send_order_created(order)
        
        return order
    
    async def process_payment(self, order_id: str, payment_details: Dict[str, Any]) -> Order:
        """Process payment for order"""
        
        # Get order
        order = await self.order_repository.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError(f"Order {order_id} not found")
        
        if order.status != OrderStatus.CONFIRMED:
            raise InvalidOrderStateError("Order must be confirmed before payment")
        
        # Reserve inventory
        try:
            for item in order.items:
                await self.inventory_service.reserve_item(
                    item.product_id, 
                    item.quantity,
                    order.order_id
                )
            
            # Process payment
            payment_result = await self.payment_service.process_payment(
                amount=order.total_amount,
                payment_details=payment_details,
                order_id=order.order_id
            )
            
            if payment_result.success:
                # Mark order as paid
                order.mark_as_paid(payment_result.payment_id)
                
                # Save updated order
                await self.order_repository.save(order)
                
                # Send payment confirmation
                await self.notification_service.send_payment_confirmation(order, payment_result)
                
                return order
            else:
                # Release reserved inventory on payment failure
                await self._release_inventory_reservation(order)
                raise PaymentFailedError(payment_result.error_message)
        
        except Exception as e:
            # Cleanup on any failure
            await self._release_inventory_reservation(order)
            raise
    
    async def ship_order(self, order_id: str) -> Order:
        """Ship order and provide tracking"""
        
        order = await self.order_repository.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError(f"Order {order_id} not found")
        
        # Create shipment
        shipment = await self.shipping_service.create_shipment(
            order.shipping_address,
            order.items,
            order.order_id
        )
        
        # Update order status
        order.ship(shipment.tracking_number)
        
        # Save updated order
        await self.order_repository.save(order)
        
        # Send shipping notification
        await self.notification_service.send_shipping_notification(order, shipment)
        
        return order
    
    async def cancel_order(self, order_id: str, reason: str) -> Order:
        """Cancel order with proper cleanup"""
        
        order = await self.order_repository.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError(f"Order {order_id} not found")
        
        # Cancel order
        order.cancel(reason)
        
        # Cleanup based on order state
        if order.status == OrderStatus.PAID:
            # Refund payment
            await self.payment_service.refund_payment(
                order.payment_id, 
                order.total_amount,
                reason
            )
            
            # Release inventory reservation
            await self._release_inventory_reservation(order)
        
        # Save updated order
        await self.order_repository.save(order)
        
        # Send cancellation notification
        await self.notification_service.send_cancellation_notification(order, reason)
        
        return order
    
    async def _release_inventory_reservation(self, order: Order):
        """Release reserved inventory for order"""
        for item in order.items:
            await self.inventory_service.release_reservation(
                item.product_id,
                item.quantity,
                order.order_id
            )

# PORTS (Interfaces) - Define contracts for external dependencies

# Secondary Ports (Driven/Right Side)
class OrderRepository(ABC):
    """Port for order persistence"""
    
    @abstractmethod
    async def save(self, order: Order) -> None:
        pass
    
    @abstractmethod
    async def get_by_id(self, order_id: str) -> Optional[Order]:
        pass
    
    @abstractmethod
    async def get_by_customer(self, customer_id: str) -> List[Order]:
        pass

class InventoryService(ABC):
    """Port for inventory management"""
    
    @abstractmethod
    async def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def check_availability(self, product_id: str) -> int:
        pass
    
    @abstractmethod
    async def reserve_item(self, product_id: str, quantity: int, order_id: str) -> None:
        pass
    
    @abstractmethod
    async def release_reservation(self, product_id: str, quantity: int, order_id: str) -> None:
        pass

class PaymentService(ABC):
    """Port for payment processing"""
    
    @abstractmethod
    async def process_payment(self, amount: Decimal, payment_details: Dict[str, Any], 
                            order_id: str) -> 'PaymentResult':
        pass
    
    @abstractmethod
    async def refund_payment(self, payment_id: str, amount: Decimal, reason: str) -> 'RefundResult':
        pass

class ShippingService(ABC):
    """Port for shipping management"""
    
    @abstractmethod
    async def create_shipment(self, address: ShippingAddress, items: List[OrderItem], 
                            order_id: str) -> 'Shipment':
        pass
    
    @abstractmethod
    async def get_tracking_info(self, tracking_number: str) -> 'TrackingInfo':
        pass

class NotificationService(ABC):
    """Port for sending notifications"""
    
    @abstractmethod
    async def send_order_created(self, order: Order) -> None:
        pass
    
    @abstractmethod
    async def send_payment_confirmation(self, order: Order, payment_result: 'PaymentResult') -> None:
        pass
    
    @abstractmethod
    async def send_shipping_notification(self, order: Order, shipment: 'Shipment') -> None:
        pass
    
    @abstractmethod
    async def send_cancellation_notification(self, order: Order, reason: str) -> None:
        pass

# Primary Ports (Driving/Left Side)
class OrderAPI(ABC):
    """Port for external API interactions"""
    
    @abstractmethod
    async def create_order(self, request: 'CreateOrderRequest') -> 'CreateOrderResponse':
        pass
    
    @abstractmethod
    async def get_order(self, order_id: str) -> 'OrderResponse':
        pass
    
    @abstractmethod
    async def confirm_order(self, order_id: str) -> 'OrderResponse':
        pass

# ADAPTERS (Implementations) - Concrete implementations of ports

# Secondary Adapters (Infrastructure)
class PostgreSQLOrderRepository(OrderRepository):
    """PostgreSQL adapter for order persistence"""
    
    def __init__(self, connection_pool):
        self.pool = connection_pool
    
    async def save(self, order: Order) -> None:
        async with self.pool.acquire() as conn:
            # Save order
            await conn.execute('''
                INSERT INTO orders (order_id, customer_id, status, total_amount, 
                                  created_at, shipping_address, payment_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (order_id) 
                DO UPDATE SET 
                    status = EXCLUDED.status,
                    total_amount = EXCLUDED.total_amount,
                    payment_id = EXCLUDED.payment_id
            ''', order.order_id, order.customer_id, order.status.value,
                float(order.total_amount), order.created_at,
                json.dumps(dataclasses.asdict(order.shipping_address)),
                order.payment_id)
            
            # Delete existing items and insert current items
            await conn.execute('DELETE FROM order_items WHERE order_id = $1', order.order_id)
            
            for item in order.items:
                await conn.execute('''
                    INSERT INTO order_items (order_id, product_id, product_name, 
                                           quantity, unit_price)
                    VALUES ($1, $2, $3, $4, $5)
                ''', order.order_id, item.product_id, item.product_name,
                    item.quantity, float(item.unit_price))
    
    async def get_by_id(self, order_id: str) -> Optional[Order]:
        async with self.pool.acquire() as conn:
            # Get order
            order_row = await conn.fetchrow('''
                SELECT order_id, customer_id, status, total_amount, created_at,
                       shipping_address, payment_id
                FROM orders WHERE order_id = $1
            ''', order_id)
            
            if not order_row:
                return None
            
            # Get order items
            item_rows = await conn.fetch('''
                SELECT product_id, product_name, quantity, unit_price
                FROM order_items WHERE order_id = $1
            ''', order_id)
            
            # Reconstruct order
            shipping_address = ShippingAddress(**json.loads(order_row['shipping_address']))
            order = Order(order_row['customer_id'], shipping_address)
            order.order_id = order_row['order_id']
            order.status = OrderStatus(order_row['status'])
            order.total_amount = Decimal(str(order_row['total_amount']))
            order.created_at = order_row['created_at']
            order.payment_id = order_row['payment_id']
            
            # Add items
            for item_row in item_rows:
                item = OrderItem(
                    product_id=item_row['product_id'],
                    product_name=item_row['product_name'],
                    quantity=item_row['quantity'],
                    unit_price=Decimal(str(item_row['unit_price']))
                )
                order.items.append(item)
            
            return order

class HTTPInventoryService(InventoryService):
    """HTTP adapter for external inventory service"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = await self.client.get(f"{self.base_url}/products/{product_id}")
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                response.raise_for_status()
        except httpx.RequestError as e:
            raise InventoryServiceError(f"Failed to get product: {e}")
    
    async def check_availability(self, product_id: str) -> int:
        try:
            response = await self.client.get(f"{self.base_url}/products/{product_id}/availability")
            response.raise_for_status()
            data = response.json()
            return data.get('available_quantity', 0)
        except httpx.RequestError as e:
            raise InventoryServiceError(f"Failed to check availability: {e}")
    
    async def reserve_item(self, product_id: str, quantity: int, order_id: str) -> None:
        try:
            response = await self.client.post(
                f"{self.base_url}/products/{product_id}/reserve",
                json={'quantity': quantity, 'order_id': order_id}
            )
            response.raise_for_status()
        except httpx.RequestError as e:
            raise InventoryServiceError(f"Failed to reserve item: {e}")
    
    async def release_reservation(self, product_id: str, quantity: int, order_id: str) -> None:
        try:
            response = await self.client.post(
                f"{self.base_url}/products/{product_id}/release",
                json={'quantity': quantity, 'order_id': order_id}
            )
            response.raise_for_status()
        except httpx.RequestError as e:
            raise InventoryServiceError(f"Failed to release reservation: {e}")

class StripePaymentService(PaymentService):
    """Stripe adapter for payment processing"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        import stripe
        stripe.api_key = api_key
    
    async def process_payment(self, amount: Decimal, payment_details: Dict[str, Any], 
                            order_id: str) -> 'PaymentResult':
        try:
            import stripe
            
            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency='usd',
                payment_method=payment_details['payment_method_id'],
                confirmation_method='manual',
                confirm=True,
                metadata={'order_id': order_id}
            )
            
            if intent.status == 'succeeded':
                return PaymentResult(
                    success=True,
                    payment_id=intent.id,
                    amount=amount,
                    currency='USD'
                )
            else:
                return PaymentResult(
                    success=False,
                    error_message=f"Payment failed with status: {intent.status}"
                )
                
        except stripe.error.StripeError as e:
            return PaymentResult(
                success=False,
                error_message=str(e)
            )
    
    async def refund_payment(self, payment_id: str, amount: Decimal, reason: str) -> 'RefundResult':
        try:
            import stripe
            
            refund = stripe.Refund.create(
                payment_intent=payment_id,
                amount=int(amount * 100),
                reason='requested_by_customer',
                metadata={'reason': reason}
            )
            
            return RefundResult(
                success=True,
                refund_id=refund.id,
                amount=amount
            )
            
        except stripe.error.StripeError as e:
            return RefundResult(
                success=False,
                error_message=str(e)
            )

# Primary Adapters (Interface/Controllers)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

class CreateOrderRequest(BaseModel):
    customer_id: str
    shipping_address: Dict[str, str]
    items: List[Dict[str, Any]]

class OrderResponse(BaseModel):
    order_id: str
    customer_id: str
    status: str
    total_amount: float
    items: List[Dict[str, Any]]

class RESTOrderAdapter(OrderAPI):
    """REST API adapter for order management"""
    
    def __init__(self, order_service: OrderService):
        self.order_service = order_service
        self.app = FastAPI(title="Order Management API")
        self._setup_routes()
    
    def _setup_routes(self):
        @self.app.post("/orders", response_model=OrderResponse)
        async def create_order(request: CreateOrderRequest):
            try:
                shipping_address = ShippingAddress(**request.shipping_address)
                order = await self.order_service.create_order(
                    request.customer_id,
                    shipping_address,
                    request.items
                )
                
                return OrderResponse(
                    order_id=order.order_id,
                    customer_id=order.customer_id,
                    status=order.status.value,
                    total_amount=float(order.total_amount),
                    items=[
                        {
                            'product_id': item.product_id,
                            'product_name': item.product_name,
                            'quantity': item.quantity,
                            'unit_price': float(item.unit_price)
                        }
                        for item in order.items
                    ]
                )
                
            except (ProductNotFoundError, InsufficientInventoryError) as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail="Internal server error")
        
        @self.app.get("/orders/{order_id}", response_model=OrderResponse)
        async def get_order(order_id: str):
            try:
                order = await self.order_service.order_repository.get_by_id(order_id)
                
                if not order:
                    raise HTTPException(status_code=404, detail="Order not found")
                
                return OrderResponse(
                    order_id=order.order_id,
                    customer_id=order.customer_id,
                    status=order.status.value,
                    total_amount=float(order.total_amount),
                    items=[
                        {
                            'product_id': item.product_id,
                            'product_name': item.product_name,
                            'quantity': item.quantity,
                            'unit_price': float(item.unit_price)
                        }
                        for item in order.items
                    ]
                )
                
            except Exception as e:
                raise HTTPException(status_code=500, detail="Internal server error")

# Value Objects and Results
@dataclass
class PaymentResult:
    success: bool
    payment_id: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    error_message: Optional[str] = None

@dataclass
class RefundResult:
    success: bool
    refund_id: Optional[str] = None
    amount: Optional[Decimal] = None
    error_message: Optional[str] = None

@dataclass
class Shipment:
    tracking_number: str
    carrier: str
    estimated_delivery: datetime

# Custom Exceptions
class OrderModificationError(Exception):
    pass

class EmptyOrderError(Exception):
    pass

class InvalidOrderStateError(Exception):
    pass

class ProductNotFoundError(Exception):
    pass

class InsufficientInventoryError(Exception):
    pass

class PaymentFailedError(Exception):
    pass

class InventoryServiceError(Exception):
    pass

class OrderNotFoundError(Exception):
    pass
```

**Key Hexagonal Architecture Benefits:**

1. **Isolation of Business Logic:** Core domain logic is completely isolated from external concerns
2. **Testability:** Easy to test business logic with mock adapters
3. **Flexibility:** Can swap implementations (e.g., database, payment provider) without changing core logic
4. **Port-Adapter Separation:** Clear contracts between application core and external systems
5. **Symmetry:** Treats all external interactions (UI, database, APIs) equally through ports and adapters