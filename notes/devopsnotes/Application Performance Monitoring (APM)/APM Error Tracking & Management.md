# APM Error Tracking & Management

Error tracking and management systems provide comprehensive visibility into application failures, enabling rapid identification, classification, and resolution of issues. This guide covers error monitoring strategies, exception handling frameworks, automated error analysis, and enterprise-grade error management implementations essential for maintaining application reliability and user satisfaction.

## Comprehensive Error Tracking System

### Error Classification and Context Framework

```python
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import traceback
import sys
import hashlib
import time
import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading
import inspect

class ErrorSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high" 
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class ErrorCategory(Enum):
    RUNTIME = "runtime"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATABASE = "database"
    NETWORK = "network"
    EXTERNAL_SERVICE = "external_service"
    CONFIGURATION = "configuration"
    RESOURCE = "resource"
    BUSINESS_LOGIC = "business_logic"

class ErrorStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    IGNORED = "ignored"
    ARCHIVED = "archived"

@dataclass
class ErrorContext:
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    environment: Optional[str] = None
    version: Optional[str] = None
    custom_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class StackFrame:
    filename: str
    function: str
    line_number: int
    code_context: Optional[str] = None
    local_variables: Dict[str, str] = field(default_factory=dict)
    in_app: bool = True

@dataclass
class ErrorEvent:
    error_id: str
    fingerprint: str
    title: str
    message: str
    exception_type: str
    severity: ErrorSeverity
    category: ErrorCategory
    timestamp: datetime
    stack_trace: List[StackFrame]
    context: ErrorContext
    tags: Dict[str, str] = field(default_factory=dict)
    breadcrumbs: List[Dict[str, Any]] = field(default_factory=list)
    count: int = 1
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    status: ErrorStatus = ErrorStatus.OPEN
    assignee: Optional[str] = None
    resolution: Optional[str] = None

class ErrorTracker:
    def __init__(self, app_name: str, environment: str = "production"):
        self.app_name = app_name
        self.environment = environment
        self.errors: Dict[str, ErrorEvent] = {}
        self.error_counts: defaultdict = defaultdict(int)
        self.breadcrumbs: deque = deque(maxlen=100)
        self.lock = threading.Lock()
        
        # Error aggregation settings
        self.max_errors_per_fingerprint = 1000
        self.error_retention_hours = 168  # 7 days
        
        # Setup logging
        self.logger = logging.getLogger(f"error_tracker_{app_name}")
        
    def generate_fingerprint(self, exception: Exception, stack_trace: List[StackFrame]) -> str:
        """Generate unique fingerprint for error grouping"""
        # Use exception type, message, and top few stack frames
        fingerprint_data = f"{type(exception).__name__}"
        
        # Add message (sanitized to remove dynamic content)
        message = str(exception)
        # Remove common dynamic patterns
        import re
        sanitized_message = re.sub(r'\d+', 'N', message)  # Replace numbers
        sanitized_message = re.sub(r'[0-9a-f-]{36}', 'UUID', sanitized_message)  # Replace UUIDs
        sanitized_message = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', 'IP', sanitized_message)  # Replace IPs
        
        fingerprint_data += sanitized_message
        
        # Add top 3 in-app stack frames
        app_frames = [frame for frame in stack_trace if frame.in_app][:3]
        for frame in app_frames:
            fingerprint_data += f"{frame.filename}:{frame.function}:{frame.line_number}"
        
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]
    
    def extract_stack_trace(self, exception: Exception) -> List[StackFrame]:
        """Extract detailed stack trace information"""
        tb = exception.__traceback__
        stack_frames = []
        
        while tb is not None:
            frame = tb.tb_frame
            filename = frame.f_code.co_filename
            function = frame.f_code.co_name
            line_number = tb.tb_lineno
            
            # Determine if frame is in application code
            in_app = self._is_in_app_frame(filename)
            
            # Extract local variables (be careful with sensitive data)
            local_vars = {}
            try:
                for key, value in frame.f_locals.items():
                    if not key.startswith('_') and not callable(value):
                        try:
                            # Sanitize and limit variable representation
                            str_value = str(value)
                            if len(str_value) > 200:
                                str_value = str_value[:200] + "..."
                            
                            # Skip sensitive variables
                            if not any(sensitive in key.lower() for sensitive in 
                                     ['password', 'token', 'secret', 'key', 'auth']):
                                local_vars[key] = str_value
                        except:
                            local_vars[key] = "<unable to serialize>"
            except:
                pass
            
            # Get code context
            code_context = self._get_code_context(filename, line_number)
            
            stack_frames.append(StackFrame(
                filename=filename,
                function=function,
                line_number=line_number,
                code_context=code_context,
                local_variables=local_vars,
                in_app=in_app
            ))
            
            tb = tb.tb_next
        
        return stack_frames
    
    def _is_in_app_frame(self, filename: str) -> bool:
        """Determine if stack frame is in application code"""
        # Skip system and library code
        skip_patterns = [
            '/site-packages/',
            '/dist-packages/',
            '/lib/python',
            '/usr/lib/',
            '/usr/local/lib/',
            'importlib',
            'runpy',
            '<frozen',
        ]
        
        return not any(pattern in filename for pattern in skip_patterns)
    
    def _get_code_context(self, filename: str, line_number: int, context_lines: int = 3) -> Optional[str]:
        """Get code context around the error line"""
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
            
            start_line = max(0, line_number - context_lines - 1)
            end_line = min(len(lines), line_number + context_lines)
            
            context_lines_list = []
            for i in range(start_line, end_line):
                line_num = i + 1
                line_content = lines[i].rstrip()
                marker = ">>>" if line_num == line_number else "   "
                context_lines_list.append(f"{marker} {line_num:4d} | {line_content}")
            
            return "\n".join(context_lines_list)
        except:
            return None
    
    def add_breadcrumb(self, message: str, category: str = "default", 
                      level: str = "info", data: Dict[str, Any] = None):
        """Add breadcrumb for error context"""
        breadcrumb = {
            'timestamp': datetime.utcnow().isoformat(),
            'message': message,
            'category': category,
            'level': level,
            'data': data or {}
        }
        
        with self.lock:
            self.breadcrumbs.append(breadcrumb)
    
    def capture_exception(self, exception: Exception, context: ErrorContext = None,
                         tags: Dict[str, str] = None, severity: ErrorSeverity = None) -> str:
        """Capture and track an exception"""
        
        # Extract stack trace
        stack_trace = self.extract_stack_trace(exception)
        
        # Generate fingerprint for grouping
        fingerprint = self.generate_fingerprint(exception, stack_trace)
        
        # Determine severity if not provided
        if severity is None:
            severity = self._classify_severity(exception, stack_trace)
        
        # Determine category
        category = self._classify_category(exception)
        
        # Create or update error event
        with self.lock:
            if fingerprint in self.errors:
                # Update existing error
                error_event = self.errors[fingerprint]
                error_event.count += 1
                error_event.last_seen = datetime.utcnow()
                
                # Update context if more detailed
                if context and (not error_event.context.user_id and context.user_id):
                    error_event.context = context
                
                error_id = error_event.error_id
            else:
                # Create new error event
                error_id = f"{fingerprint}_{int(time.time())}"
                
                error_event = ErrorEvent(
                    error_id=error_id,
                    fingerprint=fingerprint,
                    title=self._generate_error_title(exception, stack_trace),
                    message=str(exception),
                    exception_type=type(exception).__name__,
                    severity=severity,
                    category=category,
                    timestamp=datetime.utcnow(),
                    stack_trace=stack_trace,
                    context=context or ErrorContext(),
                    tags=tags or {},
                    breadcrumbs=list(self.breadcrumbs),
                    first_seen=datetime.utcnow(),
                    last_seen=datetime.utcnow()
                )
                
                self.errors[fingerprint] = error_event
            
            # Update error counts
            self.error_counts[fingerprint] += 1
            
            # Log the error
            self.logger.error(
                f"Error captured: {error_event.title} (ID: {error_id}, "
                f"Count: {error_event.count}, Severity: {severity.value})"
            )
        
        return error_id
    
    def _classify_severity(self, exception: Exception, stack_trace: List[StackFrame]) -> ErrorSeverity:
        """Classify error severity based on exception type and context"""
        
        # Critical errors - system failures
        if isinstance(exception, (SystemExit, KeyboardInterrupt, MemoryError)):
            return ErrorSeverity.CRITICAL
        
        # High severity - security or data integrity issues
        if isinstance(exception, (PermissionError, ValueError)) and 'auth' in str(exception).lower():
            return ErrorSeverity.HIGH
        
        # Database errors
        if 'database' in str(type(exception)).lower() or 'sql' in str(type(exception)).lower():
            return ErrorSeverity.HIGH
        
        # Network/external service errors
        if any(term in str(type(exception)).lower() for term in ['connection', 'timeout', 'network']):
            return ErrorSeverity.MEDIUM
        
        # Validation errors
        if isinstance(exception, (ValueError, TypeError)):
            return ErrorSeverity.MEDIUM
        
        # Default to low severity
        return ErrorSeverity.LOW
    
    def _classify_category(self, exception: Exception) -> ErrorCategory:
        """Classify error category based on exception type"""
        
        exception_name = type(exception).__name__.lower()
        exception_message = str(exception).lower()
        
        # Database errors
        if any(term in exception_name for term in ['database', 'sql', 'connection']):
            return ErrorCategory.DATABASE
        
        # Network errors
        if any(term in exception_name for term in ['connection', 'timeout', 'network', 'http']):
            return ErrorCategory.NETWORK
        
        # Authentication/Authorization
        if any(term in exception_message for term in ['auth', 'login', 'permission', 'unauthorized']):
            if 'unauthorized' in exception_message or 'permission' in exception_message:
                return ErrorCategory.AUTHORIZATION
            else:
                return ErrorCategory.AUTHENTICATION
        
        # Validation errors
        if isinstance(exception, (ValueError, TypeError)):
            return ErrorCategory.VALIDATION
        
        # Resource errors
        if isinstance(exception, (MemoryError, OSError, IOError)):
            return ErrorCategory.RESOURCE
        
        # Default to runtime error
        return ErrorCategory.RUNTIME
    
    def _generate_error_title(self, exception: Exception, stack_trace: List[StackFrame]) -> str:
        """Generate descriptive error title"""
        
        # Find the first in-app frame
        app_frame = next((frame for frame in stack_trace if frame.in_app), None)
        
        if app_frame:
            return f"{type(exception).__name__} in {app_frame.function}"
        else:
            return f"{type(exception).__name__}: {str(exception)[:100]}"
    
    def get_error_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get error statistics for the specified time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        total_errors = 0
        errors_by_severity = defaultdict(int)
        errors_by_category = defaultdict(int)
        top_errors = []
        
        with self.lock:
            for error_event in self.errors.values():
                if error_event.last_seen and error_event.last_seen > cutoff_time:
                    total_errors += error_event.count
                    errors_by_severity[error_event.severity.value] += error_event.count
                    errors_by_category[error_event.category.value] += error_event.count
                    
                    top_errors.append({
                        'error_id': error_event.error_id,
                        'title': error_event.title,
                        'count': error_event.count,
                        'severity': error_event.severity.value,
                        'category': error_event.category.value,
                        'last_seen': error_event.last_seen.isoformat()
                    })
        
        # Sort top errors by count
        top_errors.sort(key=lambda x: x['count'], reverse=True)
        
        return {
            'time_period_hours': hours,
            'total_errors': total_errors,
            'unique_errors': len([e for e in self.errors.values() 
                                if e.last_seen and e.last_seen > cutoff_time]),
            'errors_by_severity': dict(errors_by_severity),
            'errors_by_category': dict(errors_by_category),
            'top_errors': top_errors[:10]
        }
    
    def search_errors(self, query: str = None, severity: ErrorSeverity = None,
                     category: ErrorCategory = None, status: ErrorStatus = None,
                     limit: int = 50) -> List[ErrorEvent]:
        """Search errors with filters"""
        
        results = []
        
        with self.lock:
            for error_event in self.errors.values():
                # Apply filters
                if severity and error_event.severity != severity:
                    continue
                
                if category and error_event.category != category:
                    continue
                
                if status and error_event.status != status:
                    continue
                
                if query:
                    # Search in title, message, and exception type
                    search_text = f"{error_event.title} {error_event.message} {error_event.exception_type}".lower()
                    if query.lower() not in search_text:
                        continue
                
                results.append(error_event)
        
        # Sort by last seen (most recent first)
        results.sort(key=lambda x: x.last_seen or x.timestamp, reverse=True)
        
        return results[:limit]
    
    def update_error_status(self, error_id: str, status: ErrorStatus, 
                           assignee: str = None, resolution: str = None) -> bool:
        """Update error status and assignment"""
        
        with self.lock:
            # Find error by ID
            for error_event in self.errors.values():
                if error_event.error_id == error_id:
                    error_event.status = status
                    if assignee:
                        error_event.assignee = assignee
                    if resolution:
                        error_event.resolution = resolution
                    
                    self.logger.info(f"Updated error {error_id} status to {status.value}")
                    return True
        
        return False
    
    def export_error_report(self, format: str = 'json', hours: int = 24) -> str:
        """Export error report in specified format"""
        
        stats = self.get_error_stats(hours)
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Get recent errors with full details
        recent_errors = []
        with self.lock:
            for error_event in self.errors.values():
                if error_event.last_seen and error_event.last_seen > cutoff_time:
                    recent_errors.append({
                        'error_id': error_event.error_id,
                        'fingerprint': error_event.fingerprint,
                        'title': error_event.title,
                        'message': error_event.message,
                        'exception_type': error_event.exception_type,
                        'severity': error_event.severity.value,
                        'category': error_event.category.value,
                        'count': error_event.count,
                        'first_seen': error_event.first_seen.isoformat() if error_event.first_seen else None,
                        'last_seen': error_event.last_seen.isoformat() if error_event.last_seen else None,
                        'status': error_event.status.value,
                        'assignee': error_event.assignee,
                        'resolution': error_event.resolution,
                        'context': {
                            'user_id': error_event.context.user_id,
                            'endpoint': error_event.context.endpoint,
                            'method': error_event.context.method,
                            'environment': error_event.context.environment
                        },
                        'tags': error_event.tags,
                        'stack_trace': [
                            {
                                'filename': frame.filename,
                                'function': frame.function,
                                'line_number': frame.line_number,
                                'in_app': frame.in_app
                            }
                            for frame in error_event.stack_trace[:5]  # Top 5 frames
                        ]
                    })
        
        report_data = {
            'report_generated': datetime.utcnow().isoformat(),
            'application': self.app_name,
            'environment': self.environment,
            'time_period_hours': hours,
            'statistics': stats,
            'errors': recent_errors
        }
        
        if format == 'json':
            return json.dumps(report_data, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")

# Error Tracking Decorators and Context Managers
class ErrorTrackingDecorator:
    def __init__(self, error_tracker: ErrorTracker):
        self.error_tracker = error_tracker
    
    def track_errors(self, severity: ErrorSeverity = None, tags: Dict[str, str] = None,
                    capture_args: bool = False):
        """Decorator to automatically track errors in functions"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    # Add breadcrumb for function call
                    func_info = f"{func.__module__}.{func.__name__}"
                    breadcrumb_data = {'function': func_info}
                    
                    if capture_args and args:
                        breadcrumb_data['args_count'] = len(args)
                    if capture_args and kwargs:
                        # Only capture non-sensitive kwargs
                        safe_kwargs = {k: v for k, v in kwargs.items() 
                                     if not any(sensitive in k.lower() 
                                              for sensitive in ['password', 'token', 'secret'])}
                        breadcrumb_data['kwargs'] = safe_kwargs
                    
                    self.error_tracker.add_breadcrumb(
                        f"Called {func_info}",
                        category="function_call",
                        data=breadcrumb_data
                    )
                    
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    # Capture the exception
                    context = ErrorContext(
                        custom_data={'function': func_info, 'args_count': len(args)}
                    )
                    
                    function_tags = {'function': func.__name__, 'module': func.__module__}
                    if tags:
                        function_tags.update(tags)
                    
                    self.error_tracker.capture_exception(e, context, function_tags, severity)
                    raise
            
            return wrapper
        return decorator

# Flask Integration
class FlaskErrorTracking:
    def __init__(self, app, error_tracker: ErrorTracker):
        self.app = app
        self.error_tracker = error_tracker
        self.setup_error_handlers()
    
    def setup_error_handlers(self):
        """Setup Flask error handlers"""
        
        @self.app.before_request
        def before_request():
            from flask import request, g
            
            # Add breadcrumb for request
            self.error_tracker.add_breadcrumb(
                f"{request.method} {request.path}",
                category="http_request",
                data={
                    'method': request.method,
                    'path': request.path,
                    'args': dict(request.args),
                    'remote_addr': request.remote_addr
                }
            )
            
            # Store request start time
            g.request_start_time = time.time()
        
        @self.app.errorhandler(Exception)
        def handle_exception(e):
            from flask import request, g
            
            # Create error context from Flask request
            context = ErrorContext(
                user_id=getattr(g, 'user_id', None),
                session_id=request.cookies.get('session_id'),
                request_id=getattr(g, 'request_id', None),
                endpoint=request.endpoint,
                method=request.method,
                user_agent=request.headers.get('User-Agent'),
                ip_address=request.remote_addr,
                environment=self.app.config.get('ENV', 'production'),
                version=self.app.config.get('VERSION', '1.0.0'),
                custom_data={
                    'url': request.url,
                    'args': dict(request.args),
                    'form': dict(request.form),
                    'json': request.get_json(silent=True),
                    'request_duration': time.time() - getattr(g, 'request_start_time', time.time())
                }
            )
            
            # Determine tags
            tags = {
                'endpoint': request.endpoint or 'unknown',
                'method': request.method,
                'status_code': '500'
            }
            
            # Capture the exception
            self.error_tracker.capture_exception(e, context, tags)
            
            # Return error response
            return {
                'error': 'Internal server error',
                'message': 'An error occurred while processing your request'
            }, 500

# Example usage and demonstration
def demonstrate_error_tracking():
    """Demonstrate the error tracking system"""
    
    print("🔍 Error Tracking & Management System Demo")
    print("=" * 50)
    
    # Initialize error tracker
    error_tracker = ErrorTracker("ecommerce-api", "production")
    decorator = ErrorTrackingDecorator(error_tracker)
    
    # Add some breadcrumbs
    error_tracker.add_breadcrumb("User logged in", "auth", data={'user_id': 'user123'})
    error_tracker.add_breadcrumb("Viewing product catalog", "navigation")
    error_tracker.add_breadcrumb("Adding item to cart", "business_logic", data={'product_id': 'prod456'})
    
    # Simulate various types of errors
    print("\n📊 Simulating different types of errors...")
    
    # 1. Database error
    try:
        error_tracker.add_breadcrumb("Attempting database query", "database")
        raise ConnectionError("Database connection failed: timeout after 30s")
    except Exception as e:
        context = ErrorContext(
            user_id="user123",
            endpoint="/api/products",
            method="GET",
            environment="production"
        )
        error_tracker.capture_exception(e, context, {'service': 'database'})
    
    # 2. Validation error
    try:
        @decorator.track_errors(severity=ErrorSeverity.MEDIUM, tags={'component': 'validation'})
        def validate_user_input(email, age):
            if age < 0:
                raise ValueError("Age cannot be negative")
            return True
        
        validate_user_input("test@example.com", -5)
    except:
        pass  # Already tracked by decorator
    
    # 3. Authentication error
    try:
        error_tracker.add_breadcrumb("Authentication attempt", "auth")
        raise PermissionError("Invalid authentication token")
    except Exception as e:
        context = ErrorContext(
            user_id="user456",
            endpoint="/api/auth/login",
            method="POST"
        )
        error_tracker.capture_exception(e, context, {'auth_method': 'jwt'})
    
    # 4. Network error
    try:
        error_tracker.add_breadcrumb("Calling external API", "external_service")
        raise TimeoutError("External service timeout: payment-gateway")
    except Exception as e:
        context = ErrorContext(
            user_id="user789",
            endpoint="/api/payments",
            method="POST"
        )
        error_tracker.capture_exception(e, context, {'external_service': 'payment-gateway'})
    
    # 5. Business logic error
    try:
        @decorator.track_errors(tags={'component': 'business_logic'})
        def process_order(order_data):
            if order_data['total'] <= 0:
                raise ValueError("Order total must be positive")
            return True
        
        process_order({'total': -100, 'items': []})
    except:
        pass
    
    print("✅ Generated 5 different error scenarios")
    
    # Display error statistics
    print("\n📈 Error Statistics (Last 24 Hours):")
    print("-" * 40)
    
    stats = error_tracker.get_error_stats()
    
    print(f"Total Errors: {stats['total_errors']}")
    print(f"Unique Errors: {stats['unique_errors']}")
    
    print("\nErrors by Severity:")
    for severity, count in stats['errors_by_severity'].items():
        print(f"  {severity.upper()}: {count}")
    
    print("\nErrors by Category:")
    for category, count in stats['errors_by_category'].items():
        print(f"  {category.replace('_', ' ').title()}: {count}")
    
    print("\nTop Errors:")
    for i, error in enumerate(stats['top_errors'], 1):
        print(f"  {i}. {error['title']}")
        print(f"     Count: {error['count']}, Severity: {error['severity']}")
    
    # Search for specific errors
    print("\n🔎 Searching for Database Errors:")
    print("-" * 35)
    
    db_errors = error_tracker.search_errors(category=ErrorCategory.DATABASE)
    for error in db_errors:
        print(f"  {error.title}")
        print(f"    ID: {error.error_id}")
        print(f"    Count: {error.count}")
        print(f"    Context: User {error.context.user_id} at {error.context.endpoint}")
    
    # Update error status
    if db_errors:
        error_id = db_errors[0].error_id
        error_tracker.update_error_status(
            error_id, 
            ErrorStatus.IN_PROGRESS, 
            assignee="devops-team",
            resolution="Investigating database timeout issues"
        )
        print(f"\n✅ Updated error {error_id} status to IN_PROGRESS")
    
    # Generate error report
    print("\n📋 Generating Error Report...")
    print("-" * 30)
    
    report = error_tracker.export_error_report('json', hours=1)
    report_data = json.loads(report)
    
    print(f"Report Generated: {report_data['report_generated']}")
    print(f"Application: {report_data['application']}")
    print(f"Environment: {report_data['environment']}")
    print(f"Errors in Report: {len(report_data['errors'])}")
    
    print("\nError Report Summary:")
    for error in report_data['errors'][:3]:  # Show first 3 errors
        print(f"  • {error['title']}")
        print(f"    Severity: {error['severity']}, Count: {error['count']}")
        print(f"    Status: {error['status']}")
        if error['stack_trace']:
            top_frame = error['stack_trace'][0]
            print(f"    Location: {top_frame['filename']}:{top_frame['line_number']}")

if __name__ == "__main__":
    demonstrate_error_tracking()
```

This comprehensive error tracking and management system provides enterprise-grade error monitoring capabilities essential for maintaining application reliability, enabling rapid issue identification and resolution in production environments.