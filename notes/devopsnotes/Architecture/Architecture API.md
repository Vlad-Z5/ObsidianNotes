# Architecture API

## Core Concepts

API (Application Programming Interface) architecture defines how software components communicate with each other. Modern API architecture focuses on creating reliable, scalable, and maintainable interfaces that enable system integration and service composition.

### API Design Principles

#### REST (Representational State Transfer)

**Definition:** An architectural style for designing networked applications based on stateless, uniform interface principles.

**Core Principles:**
- **Stateless:** Each request contains all information needed to process it
- **Uniform Interface:** Consistent resource identification and manipulation
- **Client-Server:** Clear separation of concerns
- **Cacheable:** Responses should indicate cacheability
- **Layered System:** Architecture composed of hierarchical layers

**REST Resource Design Example:**
```python
from flask import Flask, request, jsonify
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
import uuid

app = Flask(__name__)

@dataclass
class Product:
    id: str
    name: str
    description: str
    price: float
    category_id: str
    created_at: datetime
    updated_at: datetime
    in_stock: bool = True

class ProductService:
    def __init__(self):
        self.products = {}
    
    def create_product(self, product_data: dict) -> Product:
        product = Product(
            id=str(uuid.uuid4()),
            name=product_data['name'],
            description=product_data['description'],
            price=product_data['price'],
            category_id=product_data['category_id'],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.products[product.id] = product
        return product
    
    def get_product(self, product_id: str) -> Optional[Product]:
        return self.products.get(product_id)
    
    def update_product(self, product_id: str, updates: dict) -> Optional[Product]:
        product = self.products.get(product_id)
        if not product:
            return None
        
        for key, value in updates.items():
            if hasattr(product, key):
                setattr(product, key, value)
        
        product.updated_at = datetime.utcnow()
        return product
    
    def delete_product(self, product_id: str) -> bool:
        return self.products.pop(product_id, None) is not None
    
    def list_products(self, category_id: str = None, in_stock: bool = None) -> List[Product]:
        products = list(self.products.values())
        
        if category_id:
            products = [p for p in products if p.category_id == category_id]
        
        if in_stock is not None:
            products = [p for p in products if p.in_stock == in_stock]
        
        return products

product_service = ProductService()

# REST Endpoints following Richardson Maturity Model Level 2
@app.route('/api/v1/products', methods=['GET'])
def get_products():
    """
    GET /api/v1/products
    Query parameters: category_id, in_stock, page, per_page
    """
    category_id = request.args.get('category_id')
    in_stock_param = request.args.get('in_stock')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    in_stock = None
    if in_stock_param is not None:
        in_stock = in_stock_param.lower() == 'true'
    
    products = product_service.list_products(category_id, in_stock)
    
    # Pagination
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_products = products[start_idx:end_idx]
    
    return jsonify({
        'data': [_serialize_product(p) for p in paginated_products],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': len(products),
            'has_next': end_idx < len(products),
            'has_previous': page > 1
        },
        'links': {
            'self': f'/api/v1/products?page={page}&per_page={per_page}',
            'next': f'/api/v1/products?page={page+1}&per_page={per_page}' if end_idx < len(products) else None,
            'previous': f'/api/v1/products?page={page-1}&per_page={per_page}' if page > 1 else None
        }
    }), 200

@app.route('/api/v1/products', methods=['POST'])
def create_product():
    """
    POST /api/v1/products
    Content-Type: application/json
    """
    try:
        data = request.get_json()
        
        # Validation
        required_fields = ['name', 'description', 'price', 'category_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'error': 'Validation Error',
                    'message': f'Missing required field: {field}',
                    'code': 'MISSING_FIELD'
                }), 400
        
        if data['price'] <= 0:
            return jsonify({
                'error': 'Validation Error',
                'message': 'Price must be greater than 0',
                'code': 'INVALID_PRICE'
            }), 400
        
        product = product_service.create_product(data)
        
        response = jsonify({
            'data': _serialize_product(product),
            'links': {
                'self': f'/api/v1/products/{product.id}'
            }
        })
        response.status_code = 201
        response.headers['Location'] = f'/api/v1/products/{product.id}'
        
        return response
        
    except Exception as e:
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500

@app.route('/api/v1/products/<product_id>', methods=['GET'])
def get_product(product_id):
    """
    GET /api/v1/products/{id}
    """
    product = product_service.get_product(product_id)
    
    if not product:
        return jsonify({
            'error': 'Not Found',
            'message': f'Product with id {product_id} not found',
            'code': 'PRODUCT_NOT_FOUND'
        }), 404
    
    return jsonify({
        'data': _serialize_product(product),
        'links': {
            'self': f'/api/v1/products/{product_id}',
            'category': f'/api/v1/categories/{product.category_id}'
        }
    }), 200

@app.route('/api/v1/products/<product_id>', methods=['PUT'])
def update_product(product_id):
    """
    PUT /api/v1/products/{id}
    Content-Type: application/json
    """
    product = product_service.get_product(product_id)
    
    if not product:
        return jsonify({
            'error': 'Not Found',
            'message': f'Product with id {product_id} not found',
            'code': 'PRODUCT_NOT_FOUND'
        }), 404
    
    try:
        updates = request.get_json()
        
        # Validate updates
        if 'price' in updates and updates['price'] <= 0:
            return jsonify({
                'error': 'Validation Error',
                'message': 'Price must be greater than 0',
                'code': 'INVALID_PRICE'
            }), 400
        
        updated_product = product_service.update_product(product_id, updates)
        
        return jsonify({
            'data': _serialize_product(updated_product),
            'links': {
                'self': f'/api/v1/products/{product_id}'
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500

@app.route('/api/v1/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    """
    DELETE /api/v1/products/{id}
    """
    success = product_service.delete_product(product_id)
    
    if not success:
        return jsonify({
            'error': 'Not Found',
            'message': f'Product with id {product_id} not found',
            'code': 'PRODUCT_NOT_FOUND'
        }), 404
    
    return '', 204

def _serialize_product(product: Product) -> dict:
    """Convert Product object to API representation"""
    return {
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': product.price,
        'category_id': product.category_id,
        'created_at': product.created_at.isoformat(),
        'updated_at': product.updated_at.isoformat(),
        'in_stock': product.in_stock
    }

# HATEOAS (Hypermedia as the Engine of Application State) Level 3
@app.route('/api/v1/products/<product_id>/actions', methods=['GET'])
def get_product_actions(product_id):
    """
    Returns available actions for a product based on its current state
    """
    product = product_service.get_product(product_id)
    
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    actions = []
    
    # Dynamic actions based on product state
    if product.in_stock:
        actions.append({
            'name': 'add_to_cart',
            'method': 'POST',
            'href': f'/api/v1/cart/items',
            'body': {
                'product_id': product_id,
                'quantity': 1
            }
        })
        
        actions.append({
            'name': 'mark_out_of_stock',
            'method': 'PATCH',
            'href': f'/api/v1/products/{product_id}',
            'body': {
                'in_stock': False
            }
        })
    else:
        actions.append({
            'name': 'mark_in_stock',
            'method': 'PATCH',
            'href': f'/api/v1/products/{product_id}',
            'body': {
                'in_stock': True
            }
        })
    
    actions.extend([
        {
            'name': 'update',
            'method': 'PUT',
            'href': f'/api/v1/products/{product_id}',
            'body': _serialize_product(product)
        },
        {
            'name': 'delete',
            'method': 'DELETE',
            'href': f'/api/v1/products/{product_id}'
        }
    ])
    
    return jsonify({
        'data': _serialize_product(product),
        'actions': actions
    }), 200
```

#### GraphQL Architecture

**Definition:** A query language and runtime for APIs that enables clients to request exactly the data they need.

**Core Concepts:**
- **Schema-first development:** API design starts with schema definition
- **Type system:** Strong typing for queries, mutations, and subscriptions
- **Single endpoint:** All operations through one URL
- **Client-specified queries:** Clients request only needed data

**GraphQL Implementation Example:**
```python
import graphene
from graphene import ObjectType, String, Float, Boolean, List, Field, Mutation, Schema
from graphene import Argument, Int, ID
from datetime import datetime
import uuid

# GraphQL Types
class Product(ObjectType):
    id = ID(required=True)
    name = String(required=True)
    description = String()
    price = Float(required=True)
    category_id = ID(required=True)
    created_at = String()
    updated_at = String()
    in_stock = Boolean()
    
    # Computed fields
    formatted_price = String()
    category = Field(lambda: Category)
    
    def resolve_formatted_price(self, info):
        return f"${self.price:.2f}"
    
    def resolve_category(self, info):
        # This would typically fetch from a service or database
        return Category(id=self.category_id, name="Electronics")

class Category(ObjectType):
    id = ID(required=True)
    name = String(required=True)
    products = List(Product)
    
    def resolve_products(self, info):
        # Filter products by category
        return [p for p in product_service.list_products() if p.category_id == self.id]

# Input Types for Mutations
class ProductInput(graphene.InputObjectType):
    name = String(required=True)
    description = String()
    price = Float(required=True)
    category_id = ID(required=True)

class ProductUpdateInput(graphene.InputObjectType):
    name = String()
    description = String()
    price = Float()
    category_id = ID()
    in_stock = Boolean()

# Mutations
class CreateProduct(Mutation):
    class Arguments:
        input = ProductInput(required=True)
    
    product = Field(Product)
    success = Boolean()
    errors = List(String)
    
    def mutate(self, info, input):
        try:
            # Validation
            errors = []
            if input.price <= 0:
                errors.append("Price must be greater than 0")
            
            if errors:
                return CreateProduct(success=False, errors=errors)
            
            # Create product
            product_data = {
                'name': input.name,
                'description': input.description,
                'price': input.price,
                'category_id': input.category_id
            }
            
            product = product_service.create_product(product_data)
            
            return CreateProduct(
                product=product,
                success=True,
                errors=[]
            )
            
        except Exception as e:
            return CreateProduct(
                success=False,
                errors=[str(e)]
            )

class UpdateProduct(Mutation):
    class Arguments:
        id = ID(required=True)
        input = ProductUpdateInput(required=True)
    
    product = Field(Product)
    success = Boolean()
    errors = List(String)
    
    def mutate(self, info, id, input):
        try:
            product = product_service.get_product(id)
            
            if not product:
                return UpdateProduct(
                    success=False,
                    errors=["Product not found"]
                )
            
            # Validation
            errors = []
            if hasattr(input, 'price') and input.price is not None and input.price <= 0:
                errors.append("Price must be greater than 0")
            
            if errors:
                return UpdateProduct(success=False, errors=errors)
            
            # Update product
            updates = {k: v for k, v in input.__dict__.items() if v is not None}
            updated_product = product_service.update_product(id, updates)
            
            return UpdateProduct(
                product=updated_product,
                success=True,
                errors=[]
            )
            
        except Exception as e:
            return UpdateProduct(
                success=False,
                errors=[str(e)]
            )

class DeleteProduct(Mutation):
    class Arguments:
        id = ID(required=True)
    
    success = Boolean()
    errors = List(String)
    
    def mutate(self, info, id):
        try:
            success = product_service.delete_product(id)
            
            if not success:
                return DeleteProduct(
                    success=False,
                    errors=["Product not found"]
                )
            
            return DeleteProduct(success=True, errors=[])
            
        except Exception as e:
            return DeleteProduct(
                success=False,
                errors=[str(e)]
            )

# Query Root
class Query(ObjectType):
    # Single product query
    product = Field(
        Product,
        id=Argument(ID, required=True),
        description="Get a product by ID"
    )
    
    # Products list with filtering and pagination
    products = List(
        Product,
        category_id=Argument(ID),
        in_stock=Argument(Boolean),
        first=Argument(Int, default_value=10),
        offset=Argument(Int, default_value=0),
        description="Get a list of products with optional filtering"
    )
    
    # Categories
    categories = List(Category)
    category = Field(Category, id=Argument(ID, required=True))
    
    # Search
    search_products = List(
        Product,
        query=Argument(String, required=True),
        description="Search products by name or description"
    )
    
    def resolve_product(self, info, id):
        return product_service.get_product(id)
    
    def resolve_products(self, info, category_id=None, in_stock=None, first=10, offset=0):
        products = product_service.list_products(category_id, in_stock)
        return products[offset:offset + first]
    
    def resolve_search_products(self, info, query):
        products = product_service.list_products()
        return [
            p for p in products 
            if query.lower() in p.name.lower() or query.lower() in p.description.lower()
        ]

# Mutation Root
class Mutation(ObjectType):
    create_product = CreateProduct.Field()
    update_product = UpdateProduct.Field()
    delete_product = DeleteProduct.Field()

# Subscription Root (for real-time updates)
class Subscription(ObjectType):
    product_updated = Field(Product, id=Argument(ID))
    
    def resolve_product_updated(self, info, id=None):
        # This would typically use a pub/sub system like Redis
        # Return an async generator for real-time updates
        pass

# Create the schema
schema = Schema(query=Query, mutation=Mutation, subscription=Subscription)

# Example GraphQL queries:
"""
# Get specific product with related data
query GetProduct($id: ID!) {
  product(id: $id) {
    id
    name
    description
    formattedPrice
    inStock
    category {
      id
      name
    }
  }
}

# Get products with filtering
query GetProducts($categoryId: ID, $inStock: Boolean, $first: Int) {
  products(categoryId: $categoryId, inStock: $inStock, first: $first) {
    id
    name
    price
    inStock
  }
}

# Create new product
mutation CreateProduct($input: ProductInput!) {
  createProduct(input: $input) {
    success
    errors
    product {
      id
      name
      formattedPrice
    }
  }
}

# Search products
query SearchProducts($query: String!) {
  searchProducts(query: $query) {
    id
    name
    description
    formattedPrice
  }
}
"""

# GraphQL with Flask
from flask import Flask
from flask_graphql import GraphQLView

app = Flask(__name__)

app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True  # Enable GraphiQL interface for development
    )
)

if __name__ == '__main__':
    app.run(debug=True)
```

### API Gateway Pattern

**Definition:** A service that acts as an API front-end, receiving API requests, enforcing throttling and security policies, passing requests to the back-end service, and then passing the response back to the requester.

**Key Responsibilities:**
- Request routing and load balancing
- Authentication and authorization
- Rate limiting and throttling
- Request/response transformation
- Caching
- Monitoring and analytics

**API Gateway Implementation Example:**
```python
from flask import Flask, request, jsonify, g
import requests
import time
import jwt
from functools import wraps
import redis
import json
import hashlib
from typing import Dict, Any

app = Flask(__name__)

# Configuration
SERVICES = {
    'user-service': 'http://localhost:8001',
    'product-service': 'http://localhost:8002',
    'order-service': 'http://localhost:8003',
    'payment-service': 'http://localhost:8004'
}

# Redis for caching and rate limiting
redis_client = redis.Redis(host='localhost', port=6379, db=0)

class APIGateway:
    def __init__(self):
        self.services = SERVICES
        self.cache = redis_client
        
    def route_request(self, service_name: str, path: str, method: str, 
                     headers: Dict[str, str], data: Any = None) -> requests.Response:
        """Route request to appropriate microservice"""
        
        if service_name not in self.services:
            raise ValueError(f"Unknown service: {service_name}")
        
        service_url = self.services[service_name]
        full_url = f"{service_url}{path}"
        
        # Remove hop-by-hop headers
        filtered_headers = {
            k: v for k, v in headers.items() 
            if k.lower() not in ['host', 'content-length', 'connection']
        }
        
        # Add internal service headers
        filtered_headers['X-Gateway-Request-ID'] = g.request_id
        filtered_headers['X-Gateway-User-ID'] = g.get('user_id', '')
        
        try:
            response = requests.request(
                method=method,
                url=full_url,
                headers=filtered_headers,
                json=data if data else None,
                timeout=30
            )
            return response
            
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Service {service_name} timeout")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Service {service_name} unavailable")

gateway = APIGateway()

# Middleware: Request ID generation
@app.before_request
def generate_request_id():
    g.request_id = f"req_{int(time.time() * 1000)}_{hash(request.remote_addr) % 10000}"

# Middleware: Authentication
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401
        
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        try:
            # Verify JWT token
            payload = jwt.decode(token, 'your-secret-key', algorithms=['HS256'])
            g.user_id = payload.get('user_id')
            g.user_roles = payload.get('roles', [])
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

# Middleware: Rate Limiting
def rate_limit(requests_per_minute: int = 60):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Create rate limit key
            user_id = g.get('user_id', request.remote_addr)
            key = f"rate_limit:{user_id}:{request.endpoint}"
            
            # Check current request count
            current_requests = redis_client.get(key)
            
            if current_requests is None:
                # First request in the window
                redis_client.setex(key, 60, 1)
            else:
                current_count = int(current_requests)
                
                if current_count >= requests_per_minute:
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'retry_after': redis_client.ttl(key)
                    }), 429
                
                redis_client.incr(key)
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

# Middleware: Response Caching
def cache_response(ttl_seconds: int = 300):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Only cache GET requests
            if request.method != 'GET':
                return f(*args, **kwargs)
            
            # Create cache key
            cache_key_data = {
                'endpoint': request.endpoint,
                'args': request.args.to_dict(),
                'user_id': g.get('user_id', '')
            }
            cache_key = f"cache:{hashlib.md5(json.dumps(cache_key_data, sort_keys=True).encode()).hexdigest()}"
            
            # Try to get from cache
            cached_response = redis_client.get(cache_key)
            if cached_response:
                return json.loads(cached_response)
            
            # Execute function and cache result
            response = f(*args, **kwargs)
            
            # Only cache successful responses
            if isinstance(response, tuple) and response[1] == 200:
                redis_client.setex(cache_key, ttl_seconds, json.dumps(response[0]))
            elif not isinstance(response, tuple):  # Assume 200 status
                redis_client.setex(cache_key, ttl_seconds, json.dumps(response))
            
            return response
        
        return decorated_function
    return decorator

# API Gateway Routes

@app.route('/api/v1/users/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@require_auth
@rate_limit(requests_per_minute=100)
@cache_response(ttl_seconds=300)
def proxy_users(path):
    """Proxy requests to user service"""
    try:
        response = gateway.route_request(
            service_name='user-service',
            path=f'/api/v1/users/{path}',
            method=request.method,
            headers=dict(request.headers),
            data=request.get_json() if request.is_json else None
        )
        
        return response.json(), response.status_code
        
    except (TimeoutError, ConnectionError) as e:
        return jsonify({
            'error': 'Service unavailable',
            'message': str(e),
            'request_id': g.request_id
        }), 503

@app.route('/api/v1/products/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@rate_limit(requests_per_minute=200)
@cache_response(ttl_seconds=600)  # Cache products longer
def proxy_products(path):
    """Proxy requests to product service"""
    # Products might not require authentication for GET requests
    if request.method in ['POST', 'PUT', 'DELETE']:
        # Check authentication for write operations
        auth_result = require_auth(lambda: None)()
        if auth_result:  # Error response
            return auth_result
    
    try:
        response = gateway.route_request(
            service_name='product-service',
            path=f'/api/v1/products/{path}',
            method=request.method,
            headers=dict(request.headers),
            data=request.get_json() if request.is_json else None
        )
        
        return response.json(), response.status_code
        
    except (TimeoutError, ConnectionError) as e:
        return jsonify({
            'error': 'Service unavailable',
            'message': str(e),
            'request_id': g.request_id
        }), 503

@app.route('/api/v1/orders/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@require_auth
@rate_limit(requests_per_minute=50)
def proxy_orders(path):
    """Proxy requests to order service"""
    # Check if user can access this order
    if 'admin' not in g.user_roles and request.method == 'GET' and path.isdigit():
        # Verify order ownership for non-admin users
        order_id = path
        # This would typically involve checking order ownership
        pass
    
    try:
        response = gateway.route_request(
            service_name='order-service',
            path=f'/api/v1/orders/{path}',
            method=request.method,
            headers=dict(request.headers),
            data=request.get_json() if request.is_json else None
        )
        
        return response.json(), response.status_code
        
    except (TimeoutError, ConnectionError) as e:
        return jsonify({
            'error': 'Service unavailable',
            'message': str(e),
            'request_id': g.request_id
        }), 503

# Aggregation endpoint - combines data from multiple services
@app.route('/api/v1/dashboard', methods=['GET'])
@require_auth
@rate_limit(requests_per_minute=30)
def get_dashboard():
    """Aggregate data from multiple services for dashboard"""
    try:
        user_id = g.user_id
        
        # Parallel requests to multiple services
        import concurrent.futures
        import threading
        
        results = {}
        
        def fetch_user_profile():
            response = gateway.route_request(
                'user-service',
                f'/api/v1/users/{user_id}',
                'GET',
                dict(request.headers)
            )
            results['user'] = response.json() if response.status_code == 200 else None
        
        def fetch_recent_orders():
            response = gateway.route_request(
                'order-service',
                f'/api/v1/orders?user_id={user_id}&limit=5',
                'GET',
                dict(request.headers)
            )
            results['recent_orders'] = response.json() if response.status_code == 200 else []
        
        def fetch_recommendations():
            response = gateway.route_request(
                'product-service',
                f'/api/v1/recommendations?user_id={user_id}',
                'GET',
                dict(request.headers)
            )
            results['recommendations'] = response.json() if response.status_code == 200 else []
        
        # Execute requests in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(fetch_user_profile),
                executor.submit(fetch_recent_orders),
                executor.submit(fetch_recommendations)
            ]
            
            # Wait for all requests to complete
            concurrent.futures.wait(futures, timeout=10)
        
        return jsonify({
            'user_profile': results.get('user'),
            'recent_orders': results.get('recent_orders', []),
            'recommendations': results.get('recommendations', []),
            'request_id': g.request_id
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to fetch dashboard data',
            'message': str(e),
            'request_id': g.request_id
        }), 500

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Check health of gateway and downstream services"""
    service_health = {}
    
    for service_name, service_url in SERVICES.items():
        try:
            response = requests.get(f"{service_url}/health", timeout=5)
            service_health[service_name] = {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'response_time': response.elapsed.total_seconds()
            }
        except Exception as e:
            service_health[service_name] = {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    overall_status = 'healthy' if all(
        service['status'] == 'healthy' 
        for service in service_health.values()
    ) else 'degraded'
    
    return jsonify({
        'status': overall_status,
        'services': service_health,
        'timestamp': time.time()
    }), 200

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested endpoint does not exist',
        'request_id': g.get('request_id', '')
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred',
        'request_id': g.get('request_id', '')
    }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
```

### API Security Patterns

#### OAuth 2.0 / OpenID Connect

**Implementation Example:**
```python
from flask import Flask, request, jsonify, redirect, session
import requests
import jwt
import secrets
import base64
import hashlib
from urllib.parse import urlencode, parse_qs
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# OAuth 2.0 Configuration
OAUTH_CONFIG = {
    'client_id': 'your-client-id',
    'client_secret': 'your-client-secret',
    'authorization_endpoint': 'https://auth.example.com/oauth/authorize',
    'token_endpoint': 'https://auth.example.com/oauth/token',
    'userinfo_endpoint': 'https://auth.example.com/oauth/userinfo',
    'jwks_uri': 'https://auth.example.com/.well-known/jwks.json',
    'redirect_uri': 'http://localhost:5000/callback'
}

class OAuthService:
    def __init__(self, config):
        self.config = config
        
    def generate_authorization_url(self, scope='openid profile email'):
        """Generate OAuth 2.0 authorization URL with PKCE"""
        
        # Generate PKCE parameters
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        # Generate state parameter for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Store in session
        session['oauth_state'] = state
        session['code_verifier'] = code_verifier
        
        # Build authorization URL
        params = {
            'response_type': 'code',
            'client_id': self.config['client_id'],
            'redirect_uri': self.config['redirect_uri'],
            'scope': scope,
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }
        
        return f"{self.config['authorization_endpoint']}?{urlencode(params)}"
    
    def exchange_code_for_tokens(self, authorization_code, state):
        """Exchange authorization code for access and ID tokens"""
        
        # Verify state parameter
        if state != session.get('oauth_state'):
            raise ValueError('Invalid state parameter')
        
        # Prepare token request
        token_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': self.config['redirect_uri'],
            'client_id': self.config['client_id'],
            'client_secret': self.config['client_secret'],
            'code_verifier': session.get('code_verifier')
        }
        
        # Exchange code for tokens
        response = requests.post(
            self.config['token_endpoint'],
            data=token_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        if response.status_code != 200:
            raise ValueError(f'Token exchange failed: {response.text}')
        
        return response.json()
    
    def verify_id_token(self, id_token):
        """Verify JWT ID token"""
        # In production, fetch and cache JWKS keys
        # For this example, we'll skip signature verification
        
        try:
            # Decode without verification (for demo purposes)
            payload = jwt.decode(id_token, options={"verify_signature": False})
            
            # Verify claims
            if payload.get('iss') != 'https://auth.example.com':
                raise ValueError('Invalid issuer')
            
            if payload.get('aud') != self.config['client_id']:
                raise ValueError('Invalid audience')
            
            if payload.get('exp', 0) < datetime.utcnow().timestamp():
                raise ValueError('Token expired')
            
            return payload
            
        except jwt.InvalidTokenError as e:
            raise ValueError(f'Invalid ID token: {str(e)}')
    
    def get_user_info(self, access_token):
        """Fetch user information using access token"""
        response = requests.get(
            self.config['userinfo_endpoint'],
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        if response.status_code != 200:
            raise ValueError(f'Failed to fetch user info: {response.text}')
        
        return response.json()

oauth_service = OAuthService(OAUTH_CONFIG)

# OAuth 2.0 Authorization Code Flow Routes
@app.route('/login')
def login():
    """Initiate OAuth 2.0 login flow"""
    authorization_url = oauth_service.generate_authorization_url()
    return redirect(authorization_url)

@app.route('/callback')
def oauth_callback():
    """Handle OAuth 2.0 callback"""
    try:
        # Get authorization code and state from callback
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        if error:
            return jsonify({'error': f'OAuth error: {error}'}), 400
        
        if not code:
            return jsonify({'error': 'Missing authorization code'}), 400
        
        # Exchange code for tokens
        tokens = oauth_service.exchange_code_for_tokens(code, state)
        
        # Verify ID token and extract user info
        id_token_payload = oauth_service.verify_id_token(tokens['id_token'])
        user_info = oauth_service.get_user_info(tokens['access_token'])
        
        # Store tokens in session (in production, use secure storage)
        session['access_token'] = tokens['access_token']
        session['refresh_token'] = tokens.get('refresh_token')
        session['id_token'] = tokens['id_token']
        session['user_info'] = user_info
        
        return jsonify({
            'message': 'Login successful',
            'user': user_info
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    
    # Optionally redirect to OAuth provider logout
    logout_url = f"https://auth.example.com/logout?client_id={OAUTH_CONFIG['client_id']}"
    return redirect(logout_url)

# Protected route example
@app.route('/api/protected')
def protected_route():
    """Example protected API endpoint"""
    access_token = session.get('access_token')
    
    if not access_token:
        return jsonify({'error': 'Authentication required'}), 401
    
    # Validate token (in production, verify signature and expiration)
    user_info = session.get('user_info')
    
    return jsonify({
        'message': 'Access granted',
        'user': user_info,
        'data': 'Protected content'
    })
```

This comprehensive API architecture guide covers REST, GraphQL, API Gateway patterns, and security implementations with production-ready code examples that demonstrate real-world API design principles and best practices.