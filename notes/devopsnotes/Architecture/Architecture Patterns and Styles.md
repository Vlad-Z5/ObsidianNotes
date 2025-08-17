# Architecture Patterns and Styles

## Common Patterns

Architectural patterns are reusable solutions to commonly occurring problems in software architecture. They represent proven approaches to organizing code and system components that have been refined through years of practice.

### Layered Pattern

**Definition:** Organizes the system into horizontal layers, where each layer serves the layer above it and is served by the layer below it.

**When to Use:**
- Traditional enterprise applications
- Systems with clear separation of concerns
- Applications requiring isolation of business logic
- Legacy system modernization

**Example - Enterprise Web Application:**
```python
# Presentation Layer
class UserController:
    def __init__(self, user_service):
        self.user_service = user_service
    
    @app.route('/users', methods=['POST'])
    def create_user(self):
        try:
            # Input validation and transformation
            user_data = self._validate_request(request.json)
            
            # Delegate to business layer
            user = self.user_service.create_user(user_data)
            
            # Format response
            return self._format_response(user), 201
            
        except ValidationError as e:
            return {"error": str(e)}, 400
        except BusinessRuleError as e:
            return {"error": str(e)}, 409

# Business Logic Layer
class UserService:
    def __init__(self, user_repository, email_service, audit_service):
        self.user_repository = user_repository
        self.email_service = email_service
        self.audit_service = audit_service
    
    def create_user(self, user_data):
        # Business rule validation
        if self.user_repository.email_exists(user_data.email):
            raise BusinessRuleError("Email already registered")
        
        # Apply business logic
        user = User(
            email=user_data.email,
            password_hash=self._hash_password(user_data.password),
            status=UserStatus.PENDING_VERIFICATION,
            created_at=datetime.utcnow()
        )
        
        # Persist through data layer
        saved_user = self.user_repository.save(user)
        
        # Business process continuation
        self.email_service.send_verification_email(saved_user)
        self.audit_service.log_user_creation(saved_user.id)
        
        return saved_user

# Data Access Layer
class UserRepository:
    def __init__(self, database_connection):
        self.db = database_connection
    
    def save(self, user):
        """Persist user to database"""
        query = """
            INSERT INTO users (email, password_hash, status, created_at)
            VALUES (%(email)s, %(password_hash)s, %(status)s, %(created_at)s)
            RETURNING id
        """
        
        with self.db.cursor() as cursor:
            cursor.execute(query, {
                'email': user.email,
                'password_hash': user.password_hash,
                'status': user.status.value,
                'created_at': user.created_at
            })
            user.id = cursor.fetchone()[0]
            self.db.commit()
        
        return user
    
    def email_exists(self, email):
        """Check if email already exists"""
        query = "SELECT COUNT(*) FROM users WHERE email = %(email)s"
        
        with self.db.cursor() as cursor:
            cursor.execute(query, {'email': email})
            return cursor.fetchone()[0] > 0

# Infrastructure Layer
class DatabaseConnection:
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.connection = None
    
    def connect(self):
        self.connection = psycopg2.connect(self.connection_string)
        return self.connection
    
    def cursor(self):
        return self.connection.cursor()
    
    def commit(self):
        self.connection.commit()
```

**Layer Communication Rules:**
```python
# Strict Layering - Only adjacent layers communicate
class StrictLayeredArchitecture:
    """
    Presentation → Business → Data → Database
    Each layer only knows about the layer directly below it
    """
    
    def __init__(self):
        # Infrastructure Layer
        self.db_connection = DatabaseConnection(DB_URL)
        
        # Data Access Layer
        self.user_repository = UserRepository(self.db_connection)
        self.audit_repository = AuditRepository(self.db_connection)
        
        # Business Logic Layer
        self.email_service = EmailService()
        self.audit_service = AuditService(self.audit_repository)
        self.user_service = UserService(
            self.user_repository, 
            self.email_service, 
            self.audit_service
        )
        
        # Presentation Layer
        self.user_controller = UserController(self.user_service)

# Relaxed Layering - Upper layers can skip intermediate layers
class RelaxedLayeredArchitecture:
    """
    Allows presentation layer to directly access data layer
    for read-only operations (performance optimization)
    """
    
    def __init__(self):
        # Same setup as strict, but presentation can access data directly
        self.user_controller = UserController(
            self.user_service,
            self.user_repository  # Direct access for queries
        )
```

**Benefits and Trade-offs:**
```
Benefits:
✓ Clear separation of concerns
✓ Testability (can mock each layer)
✓ Maintainability (changes isolated to layers)
✓ Team organization (different teams per layer)

Trade-offs:
✗ Performance overhead from layer traversal
✗ Can become rigid and bureaucratic
✗ Risk of anemic domain models
✗ Difficult to implement cross-cutting concerns
```

### Client-Server Pattern

**Definition:** Separates functionality into two main components: clients (request services) and servers (provide services).

**Variations and Use Cases:**

**1. Thick Client (Rich Client)**
```python
# Desktop application with business logic on client
class DesktopInventoryClient:
    """
    Rich client with local business logic and caching
    Suitable for: CAD software, IDEs, desktop productivity apps
    """
    
    def __init__(self, server_api):
        self.server_api = server_api
        self.local_cache = {}
        self.offline_queue = []
        
    def update_inventory_item(self, item_id, quantity):
        # Client-side validation
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")
        
        # Optimistic update in local cache
        self.local_cache[item_id] = quantity
        
        # Queue for server synchronization
        update_command = UpdateInventoryCommand(item_id, quantity)
        
        try:
            # Immediate server update
            result = self.server_api.update_inventory(update_command)
            self._handle_server_response(result)
            
        except NetworkError:
            # Offline support - queue for later
            self.offline_queue.append(update_command)
            self._schedule_retry()
    
    def sync_with_server(self):
        """Synchronize offline changes when connection restored"""
        for command in self.offline_queue:
            try:
                self.server_api.update_inventory(command)
                self.offline_queue.remove(command)
            except NetworkError:
                break  # Still offline, try again later
```

**2. Thin Client (Web Application)**
```javascript
// Browser-based thin client
class WebInventoryClient {
    constructor(apiBaseUrl) {
        this.apiBaseUrl = apiBaseUrl;
        this.authToken = localStorage.getItem('authToken');
    }
    
    async updateInventoryItem(itemId, quantity) {
        // Minimal client-side validation
        if (!itemId || quantity === undefined) {
            throw new Error('Invalid input');
        }
        
        // Server does all business logic
        const response = await fetch(`${this.apiBaseUrl}/inventory/${itemId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.authToken}`
            },
            body: JSON.stringify({ quantity })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message);
        }
        
        return await response.json();
    }
    
    // UI updates based on server response
    async refreshInventoryDisplay() {
        const inventory = await this.fetchInventory();
        this.renderInventoryTable(inventory);
    }
}
```

**3. Three-Tier Architecture**
```python
# Presentation Tier (Web Server)
class InventoryWebServer:
    def __init__(self, business_tier_client):
        self.business_tier = business_tier_client
        
    @app.route('/inventory/<item_id>', methods=['PUT'])
    def update_inventory(self, item_id):
        """Handles HTTP requests, delegates to business tier"""
        try:
            quantity = request.json.get('quantity')
            
            # Delegate to business tier
            result = self.business_tier.update_inventory(item_id, quantity)
            
            return jsonify(result), 200
            
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400

# Business Tier (Application Server)
class InventoryBusinessServer:
    def __init__(self, data_tier_client):
        self.data_tier = data_tier_client
        
    def update_inventory(self, item_id, quantity):
        """Business logic processing"""
        # Business validation
        if quantity < 0:
            raise ValidationError("Quantity cannot be negative")
        
        # Get current state from data tier
        current_item = self.data_tier.get_inventory_item(item_id)
        
        if not current_item:
            raise NotFoundError("Item not found")
        
        # Business rules
        if quantity == 0 and current_item.has_pending_orders():
            raise BusinessRuleError("Cannot zero inventory with pending orders")
        
        # Update through data tier
        updated_item = self.data_tier.update_inventory_quantity(item_id, quantity)
        
        # Trigger business processes
        if quantity < current_item.reorder_level:
            self._trigger_reorder_process(item_id)
        
        return updated_item

# Data Tier (Database Server)
class InventoryDataServer:
    def __init__(self, database):
        self.db = database
        
    def update_inventory_quantity(self, item_id, quantity):
        """Data persistence and retrieval"""
        with self.db.transaction():
            # Update inventory
            self.db.execute(
                "UPDATE inventory SET quantity = %s WHERE item_id = %s",
                (quantity, item_id)
            )
            
            # Log change for audit
            self.db.execute(
                "INSERT INTO inventory_audit (item_id, old_quantity, new_quantity, timestamp) "
                "VALUES (%s, %s, %s, %s)",
                (item_id, current_quantity, quantity, datetime.utcnow())
            )
            
            return self.get_inventory_item(item_id)
```

### Pipe and Filter Pattern

**Definition:** Decomposes a task that performs complex processing into a series of separate elements that can be reused.

**Use Cases:**
- Data processing pipelines
- Compiler design
- Image/video processing
- ETL (Extract, Transform, Load) operations

**Example - Data Processing Pipeline:**
```python
from abc import ABC, abstractmethod
from typing import Any, Iterator

class Filter(ABC):
    """Base class for all filters in the pipeline"""
    
    @abstractmethod
    def process(self, data: Iterator[Any]) -> Iterator[Any]:
        """Process input data and yield transformed results"""
        pass

class Pipe:
    """Connects filters and manages data flow"""
    
    def __init__(self):
        self.filters = []
    
    def add_filter(self, filter_instance: Filter):
        """Add a filter to the pipeline"""
        self.filters.append(filter_instance)
        return self  # Enable method chaining
    
    def execute(self, input_data: Iterator[Any]) -> Iterator[Any]:
        """Execute the pipeline"""
        current_data = input_data
        
        for filter_instance in self.filters:
            current_data = filter_instance.process(current_data)
        
        return current_data

# Concrete Filter Implementations
class CSVReader(Filter):
    """Reads CSV data and yields dictionaries"""
    
    def __init__(self, filename: str):
        self.filename = filename
    
    def process(self, data: Iterator[Any]) -> Iterator[dict]:
        import csv
        
        with open(self.filename, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                yield row

class DataValidator(Filter):
    """Validates data according to business rules"""
    
    def __init__(self, validation_rules: dict):
        self.rules = validation_rules
    
    def process(self, data: Iterator[dict]) -> Iterator[dict]:
        for record in data:
            if self._is_valid(record):
                yield record
            else:
                # Log invalid record or send to error queue
                self._handle_invalid_record(record)
    
    def _is_valid(self, record: dict) -> bool:
        for field, rule in self.rules.items():
            if not rule(record.get(field)):
                return False
        return True

class DataTransformer(Filter):
    """Transforms data fields"""
    
    def __init__(self, transformations: dict):
        self.transformations = transformations
    
    def process(self, data: Iterator[dict]) -> Iterator[dict]:
        for record in data:
            transformed_record = record.copy()
            
            for field, transform_func in self.transformations.items():
                if field in transformed_record:
                    transformed_record[field] = transform_func(transformed_record[field])
            
            yield transformed_record

class DataAggregator(Filter):
    """Aggregates data by specified keys"""
    
    def __init__(self, group_by: str, aggregate_field: str, operation: str):
        self.group_by = group_by
        self.aggregate_field = aggregate_field
        self.operation = operation
    
    def process(self, data: Iterator[dict]) -> Iterator[dict]:
        groups = {}
        
        # Collect all data for aggregation
        for record in data:
            key = record[self.group_by]
            if key not in groups:
                groups[key] = []
            groups[key].append(record[self.aggregate_field])
        
        # Yield aggregated results
        for key, values in groups.items():
            if self.operation == 'sum':
                result = sum(values)
            elif self.operation == 'avg':
                result = sum(values) / len(values)
            elif self.operation == 'count':
                result = len(values)
            
            yield {
                self.group_by: key,
                f'{self.operation}_{self.aggregate_field}': result
            }

class DatabaseWriter(Filter):
    """Writes data to database"""
    
    def __init__(self, table_name: str, db_connection):
        self.table_name = table_name
        self.db = db_connection
    
    def process(self, data: Iterator[dict]) -> Iterator[dict]:
        for record in data:
            # Insert into database
            self._insert_record(record)
            yield record  # Pass through for further processing if needed
    
    def _insert_record(self, record: dict):
        columns = ', '.join(record.keys())
        placeholders = ', '.join(['%s'] * len(record))
        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        
        self.db.execute(query, list(record.values()))

# Usage Example - Sales Data Processing Pipeline
def create_sales_processing_pipeline():
    """Creates a data processing pipeline for sales data"""
    
    # Validation rules
    validation_rules = {
        'amount': lambda x: x is not None and float(x) > 0,
        'customer_id': lambda x: x is not None and len(str(x)) > 0,
        'date': lambda x: x is not None
    }
    
    # Data transformations
    transformations = {
        'amount': lambda x: float(x),
        'date': lambda x: datetime.strptime(x, '%Y-%m-%d'),
        'customer_id': lambda x: int(x)
    }
    
    # Build pipeline
    pipeline = (Pipe()
        .add_filter(CSVReader('sales_data.csv'))
        .add_filter(DataValidator(validation_rules))
        .add_filter(DataTransformer(transformations))
        .add_filter(DataAggregator('customer_id', 'amount', 'sum'))
        .add_filter(DatabaseWriter('customer_sales_summary', db_connection))
    )
    
    return pipeline

# Execute pipeline
pipeline = create_sales_processing_pipeline()
results = list(pipeline.execute(iter([])))  # Empty input since CSVReader provides data

print(f"Processed {len(results)} customer sales summaries")
```

**Advanced Pipeline with Error Handling:**
```python
class ErrorHandlingPipe(Pipe):
    """Enhanced pipe with error handling and monitoring"""
    
    def __init__(self):
        super().__init__()
        self.error_handlers = {}
        self.metrics = {
            'processed': 0,
            'errors': 0,
            'filter_metrics': {}
        }
    
    def add_error_handler(self, filter_class, handler):
        """Add error handler for specific filter type"""
        self.error_handlers[filter_class] = handler
    
    def execute(self, input_data: Iterator[Any]) -> Iterator[Any]:
        """Execute pipeline with error handling and metrics"""
        current_data = input_data
        
        for i, filter_instance in enumerate(self.filters):
            filter_name = filter_instance.__class__.__name__
            
            try:
                # Process with metrics collection
                processed_data = []
                error_count = 0
                
                for item in filter_instance.process(current_data):
                    processed_data.append(item)
                    self.metrics['processed'] += 1
                
                current_data = iter(processed_data)
                
                # Store filter metrics
                self.metrics['filter_metrics'][filter_name] = {
                    'processed': len(processed_data),
                    'errors': error_count
                }
                
            except Exception as e:
                # Handle filter errors
                if type(filter_instance) in self.error_handlers:
                    current_data = self.error_handlers[type(filter_instance)](e, current_data)
                else:
                    raise
                
                self.metrics['errors'] += 1
        
        return current_data

# Example: Compiler Pipeline
class LexicalAnalyzer(Filter):
    """Tokenizes source code"""
    
    def process(self, data: Iterator[str]) -> Iterator[list]:
        for line in data:
            tokens = self._tokenize(line)
            yield tokens
    
    def _tokenize(self, line: str) -> list:
        # Simplified tokenization
        import re
        token_patterns = [
            ('NUMBER', r'\d+'),
            ('IDENTIFIER', r'[a-zA-Z_][a-zA-Z0-9_]*'),
            ('OPERATOR', r'[+\-*/=]'),
            ('WHITESPACE', r'\s+')
        ]
        
        tokens = []
        for token_type, pattern in token_patterns:
            for match in re.finditer(pattern, line):
                if token_type != 'WHITESPACE':  # Skip whitespace
                    tokens.append((token_type, match.group()))
        
        return tokens

class SyntaxAnalyzer(Filter):
    """Parses tokens into AST"""
    
    def process(self, data: Iterator[list]) -> Iterator[dict]:
        for tokens in data:
            ast = self._parse(tokens)
            yield ast
    
    def _parse(self, tokens: list) -> dict:
        # Simplified parsing - just return structure
        return {
            'type': 'expression',
            'tokens': tokens,
            'valid': len(tokens) > 0
        }

class CodeGenerator(Filter):
    """Generates target code from AST"""
    
    def process(self, data: Iterator[dict]) -> Iterator[str]:
        for ast in data:
            if ast['valid']:
                code = self._generate_code(ast)
                yield code
    
    def _generate_code(self, ast: dict) -> str:
        # Simplified code generation
        return f"// Generated code for {len(ast['tokens'])} tokens"

# Compiler pipeline
def create_compiler_pipeline():
    return (Pipe()
        .add_filter(LexicalAnalyzer())
        .add_filter(SyntaxAnalyzer())
        .add_filter(CodeGenerator())
    )
```

### Model-View-Controller (MVC)

**Definition:** Separates application logic into three interconnected components to separate internal representations from how information is presented to the user.

**Core Components:**

**1. Model - Data and Business Logic**
```python
class UserModel:
    """Represents user data and business logic"""
    
    def __init__(self, database):
        self.db = database
        self._observers = []  # Observer pattern for view updates
    
    def add_observer(self, observer):
        """Add view that should be notified of changes"""
        self._observers.append(observer)
    
    def remove_observer(self, observer):
        """Remove view observer"""
        self._observers.remove(observer)
    
    def notify_observers(self, event_type, data):
        """Notify all observers of model changes"""
        for observer in self._observers:
            observer.update(event_type, data)
    
    def create_user(self, user_data):
        """Business logic for user creation"""
        # Validation
        if not self._is_valid_email(user_data.get('email')):
            raise ValidationError("Invalid email format")
        
        if self.email_exists(user_data.get('email')):
            raise BusinessRuleError("Email already registered")
        
        # Create user
        user = {
            'id': self._generate_id(),
            'email': user_data['email'],
            'name': user_data['name'],
            'created_at': datetime.utcnow(),
            'status': 'active'
        }
        
        # Persist
        self.db.insert('users', user)
        
        # Notify views
        self.notify_observers('user_created', user)
        
        return user
    
    def get_user(self, user_id):
        """Retrieve user by ID"""
        return self.db.find_one('users', {'id': user_id})
    
    def update_user(self, user_id, updates):
        """Update user information"""
        user = self.get_user(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Apply updates
        user.update(updates)
        user['updated_at'] = datetime.utcnow()
        
        # Persist
        self.db.update('users', {'id': user_id}, user)
        
        # Notify views
        self.notify_observers('user_updated', user)
        
        return user
    
    def delete_user(self, user_id):
        """Delete user (soft delete)"""
        user = self.get_user(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Soft delete
        user['status'] = 'deleted'
        user['deleted_at'] = datetime.utcnow()
        
        self.db.update('users', {'id': user_id}, user)
        
        # Notify views
        self.notify_observers('user_deleted', user)

class UserListModel:
    """Model for user list operations"""
    
    def __init__(self, database):
        self.db = database
        self._observers = []
    
    def get_users(self, filters=None, pagination=None):
        """Get list of users with optional filtering and pagination"""
        query = filters or {}
        
        # Add default filter for active users
        if 'status' not in query:
            query['status'] = 'active'
        
        users = self.db.find('users', query)
        
        # Apply pagination
        if pagination:
            offset = (pagination['page'] - 1) * pagination['per_page']
            users = users[offset:offset + pagination['per_page']]
        
        return users
    
    def search_users(self, search_term):
        """Search users by name or email"""
        query = {
            '$or': [
                {'name': {'$regex': search_term, '$options': 'i'}},
                {'email': {'$regex': search_term, '$options': 'i'}}
            ],
            'status': 'active'
        }
        
        return self.db.find('users', query)
```

**2. View - User Interface**
```python
class UserView:
    """Handles user interface rendering and user input"""
    
    def __init__(self, template_engine):
        self.templates = template_engine
    
    def render_user_form(self, user=None, errors=None):
        """Render user creation/edit form"""
        return self.templates.render('user_form.html', {
            'user': user or {},
            'errors': errors or {},
            'title': 'Edit User' if user else 'Create User'
        })
    
    def render_user_list(self, users, pagination=None):
        """Render list of users"""
        return self.templates.render('user_list.html', {
            'users': users,
            'pagination': pagination,
            'total_count': len(users)
        })
    
    def render_user_detail(self, user):
        """Render user detail page"""
        return self.templates.render('user_detail.html', {
            'user': user
        })
    
    def render_error(self, error_message, status_code=400):
        """Render error page"""
        return self.templates.render('error.html', {
            'error': error_message,
            'status': status_code
        }), status_code
    
    def render_success(self, message, redirect_url=None):
        """Render success message"""
        return self.templates.render('success.html', {
            'message': message,
            'redirect_url': redirect_url
        })
    
    # Observer pattern implementation
    def update(self, event_type, data):
        """Called by model when data changes"""
        if event_type == 'user_created':
            # Could trigger real-time UI updates via WebSocket
            self._broadcast_update('user_added', data)
        elif event_type == 'user_updated':
            self._broadcast_update('user_modified', data)
        elif event_type == 'user_deleted':
            self._broadcast_update('user_removed', data)
    
    def _broadcast_update(self, event, data):
        """Send real-time updates to connected clients"""
        # Implementation depends on chosen real-time technology
        # WebSocket, Server-Sent Events, etc.
        pass

class APIView:
    """JSON API view for user operations"""
    
    def __init__(self):
        self.json_encoder = JSONEncoder()
    
    def render_user_json(self, user):
        """Render user as JSON"""
        return self.json_encoder.encode({
            'status': 'success',
            'data': self._serialize_user(user)
        })
    
    def render_user_list_json(self, users, pagination=None):
        """Render user list as JSON"""
        return self.json_encoder.encode({
            'status': 'success',
            'data': [self._serialize_user(user) for user in users],
            'pagination': pagination
        })
    
    def render_error_json(self, error_message, status_code=400):
        """Render error as JSON"""
        return self.json_encoder.encode({
            'status': 'error',
            'message': error_message,
            'code': status_code
        })
    
    def _serialize_user(self, user):
        """Convert user model to API representation"""
        return {
            'id': user['id'],
            'email': user['email'],
            'name': user['name'],
            'created_at': user['created_at'].isoformat(),
            'status': user['status']
            # Exclude sensitive fields like password_hash
        }
```

**3. Controller - Request Handling and Coordination**
```python
class UserController:
    """Coordinates between model and view"""
    
    def __init__(self, user_model, user_view, user_list_model):
        self.user_model = user_model
        self.user_view = user_view
        self.user_list_model = user_list_model
        
        # Register view as observer of model
        self.user_model.add_observer(user_view)
    
    def create_user_form(self, request):
        """Display user creation form"""
        if request.method == 'GET':
            return self.user_view.render_user_form()
        
        elif request.method == 'POST':
            try:
                # Extract and validate form data
                user_data = self._extract_user_data(request.form)
                
                # Create user via model
                user = self.user_model.create_user(user_data)
                
                # Return success response
                return self.user_view.render_success(
                    "User created successfully",
                    redirect_url=f"/users/{user['id']}"
                )
                
            except ValidationError as e:
                # Re-render form with errors
                return self.user_view.render_user_form(
                    user=request.form,
                    errors={'validation': str(e)}
                )
            
            except BusinessRuleError as e:
                return self.user_view.render_user_form(
                    user=request.form,
                    errors={'business': str(e)}
                )
    
    def show_user(self, request, user_id):
        """Display user details"""
        try:
            user = self.user_model.get_user(user_id)
            
            if not user:
                return self.user_view.render_error("User not found", 404)
            
            return self.user_view.render_user_detail(user)
            
        except Exception as e:
            return self.user_view.render_error("Internal server error", 500)
    
    def edit_user(self, request, user_id):
        """Handle user editing"""
        try:
            user = self.user_model.get_user(user_id)
            
            if not user:
                return self.user_view.render_error("User not found", 404)
            
            if request.method == 'GET':
                return self.user_view.render_user_form(user=user)
            
            elif request.method == 'POST':
                updates = self._extract_user_data(request.form)
                updated_user = self.user_model.update_user(user_id, updates)
                
                return self.user_view.render_success(
                    "User updated successfully",
                    redirect_url=f"/users/{user_id}"
                )
                
        except ValidationError as e:
            return self.user_view.render_user_form(
                user=user,
                errors={'validation': str(e)}
            )
    
    def list_users(self, request):
        """Display user list with search and pagination"""
        # Extract query parameters
        search_term = request.args.get('search', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Get users from model
        if search_term:
            users = self.user_list_model.search_users(search_term)
        else:
            users = self.user_list_model.get_users(
                pagination={'page': page, 'per_page': per_page}
            )
        
        # Prepare pagination info
        pagination = {
            'page': page,
            'per_page': per_page,
            'has_next': len(users) == per_page,
            'has_prev': page > 1
        }
        
        return self.user_view.render_user_list(users, pagination)
    
    def delete_user(self, request, user_id):
        """Handle user deletion"""
        try:
            self.user_model.delete_user(user_id)
            return self.user_view.render_success(
                "User deleted successfully",
                redirect_url="/users"
            )
            
        except NotFoundError:
            return self.user_view.render_error("User not found", 404)
    
    def _extract_user_data(self, form_data):
        """Extract and validate user data from form"""
        return {
            'email': form_data.get('email', '').strip(),
            'name': form_data.get('name', '').strip(),
            'phone': form_data.get('phone', '').strip()
        }

# API Controller for REST endpoints
class UserAPIController:
    """RESTful API controller for user operations"""
    
    def __init__(self, user_model, api_view):
        self.user_model = user_model
        self.api_view = api_view
    
    def create_user_api(self, request):
        """POST /api/users"""
        try:
            user_data = request.json
            user = self.user_model.create_user(user_data)
            return self.api_view.render_user_json(user), 201
            
        except ValidationError as e:
            return self.api_view.render_error_json(str(e), 400), 400
        except BusinessRuleError as e:
            return self.api_view.render_error_json(str(e), 409), 409
    
    def get_user_api(self, request, user_id):
        """GET /api/users/{id}"""
        user = self.user_model.get_user(user_id)
        
        if not user:
            return self.api_view.render_error_json("User not found", 404), 404
        
        return self.api_view.render_user_json(user), 200
    
    def update_user_api(self, request, user_id):
        """PUT /api/users/{id}"""
        try:
            updates = request.json
            user = self.user_model.update_user(user_id, updates)
            return self.api_view.render_user_json(user), 200
            
        except NotFoundError:
            return self.api_view.render_error_json("User not found", 404), 404
        except ValidationError as e:
            return self.api_view.render_error_json(str(e), 400), 400
```

**MVC Variations:**

**Model-View-Presenter (MVP):**
```python
class UserPresenter:
    """Presenter handles all UI logic and coordinates between view and model"""
    
    def __init__(self, view, model):
        self.view = view
        self.model = model
        
        # Presenter manages all view interactions
        self.view.set_presenter(self)
    
    def load_user(self, user_id):
        """Load user data and update view"""
        try:
            user = self.model.get_user(user_id)
            
            if user:
                # Transform model data for view
                view_data = {
                    'display_name': f"{user['name']} ({user['email']})",
                    'formatted_date': user['created_at'].strftime('%B %d, %Y'),
                    'status_label': user['status'].title(),
                    'can_edit': user['status'] == 'active'
                }
                self.view.display_user(view_data)
            else:
                self.view.show_error("User not found")
                
        except Exception as e:
            self.view.show_error(f"Failed to load user: {str(e)}")
    
    def save_user(self, form_data):
        """Save user data from view"""
        try:
            # Validate and transform view data for model
            user_data = self._prepare_user_data(form_data)
            
            if form_data.get('user_id'):
                # Update existing user
                user = self.model.update_user(form_data['user_id'], user_data)
                self.view.show_success("User updated successfully")
            else:
                # Create new user
                user = self.model.create_user(user_data)
                self.view.show_success("User created successfully")
            
            # Refresh view
            self.load_user(user['id'])
            
        except ValidationError as e:
            self.view.show_validation_errors(e.errors)
        except BusinessRuleError as e:
            self.view.show_error(str(e))
```

This comprehensive section covers the fundamental architectural patterns with detailed, production-ready examples that demonstrate real-world implementation approaches.