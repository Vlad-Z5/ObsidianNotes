# Architecture Cloud-Native

## Core Concepts

Cloud-Native architecture is an approach to building and running applications that fully exploits the advantages of cloud computing platforms. It embraces containerization, microservices, orchestration, and continuous delivery to enable organizations to build resilient, manageable, and observable systems.

### 12-Factor App Methodology

**Definition:** A methodology for building software-as-a-service applications that provides a clear contract with the underlying execution platform.

**The Twelve Factors:**

#### I. Codebase
**Principle:** One codebase tracked in revision control, many deploys.

**Implementation Example:**
```yaml
# Git repository structure for cloud-native application
my-cloud-app/
├── .git/
├── src/
│   ├── api/          # API service code
│   ├── web/          # Web frontend code
│   └── worker/       # Background worker code
├── deploy/
│   ├── dev/          # Development environment configs
│   ├── staging/      # Staging environment configs
│   └── prod/         # Production environment configs
├── docker/
│   ├── api.Dockerfile
│   ├── web.Dockerfile
│   └── worker.Dockerfile
├── docker-compose.yml
├── kubernetes/
│   ├── api-deployment.yaml
│   ├── web-deployment.yaml
│   └── worker-deployment.yaml
└── README.md

# Environment-specific deployment configurations
# deploy/dev/config.yaml
environment: development
database_url: postgres://dev-db:5432/myapp
redis_url: redis://dev-redis:6379
debug: true
log_level: DEBUG

# deploy/prod/config.yaml
environment: production
database_url: postgres://prod-db.cluster.us-west-2.rds.amazonaws.com:5432/myapp
redis_url: redis://prod-redis.cluster.cache.amazonaws.com:6379
debug: false
log_level: INFO
```

#### II. Dependencies
**Principle:** Explicitly declare and isolate dependencies.

**Implementation Example:**
```python
# requirements.txt - Explicit dependency declaration
flask==2.3.3
psycopg2-binary==2.9.7
redis==4.6.0
celery==5.3.1
gunicorn==21.2.0
prometheus-client==0.17.1

# Dockerfile - Isolated dependency installation
FROM python:3.11-slim

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies in isolated environment
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Switch to non-root user
USER app

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:create_app()"]

# Application factory pattern with dependency injection
# app/__init__.py
from flask import Flask
from app.extensions import db, redis_client, celery
from app.config import Config

def create_app(config_class=Config):
    """Application factory with explicit dependency injection"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions (dependencies)
    db.init_app(app)
    redis_client.init_app(app)
    celery.init_app(app)
    
    # Register blueprints
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    return app

# app/extensions.py - Dependency declarations
from flask_sqlalchemy import SQLAlchemy
from flask_redis import FlaskRedis
from celery import Celery

db = SQLAlchemy()
redis_client = FlaskRedis()
celery = Celery()
```

#### III. Config
**Principle:** Store configuration in the environment.

**Implementation Example:**
```python
# app/config.py - Environment-based configuration
import os
from typing import Optional

class Config:
    """Base configuration with environment variable support"""
    
    # Database configuration
    DATABASE_URL: str = os.environ.get('DATABASE_URL') or 'postgresql://localhost/myapp'
    
    # Redis configuration
    REDIS_URL: str = os.environ.get('REDIS_URL') or 'redis://localhost:6379'
    
    # Security configuration
    SECRET_KEY: str = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    JWT_SECRET_KEY: str = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    
    # External service configuration
    STRIPE_API_KEY: str = os.environ.get('STRIPE_API_KEY', '')
    SENDGRID_API_KEY: str = os.environ.get('SENDGRID_API_KEY', '')
    
    # Application configuration
    DEBUG: bool = os.environ.get('DEBUG', 'False').lower() == 'true'
    LOG_LEVEL: str = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Feature flags
    ENABLE_ANALYTICS: bool = os.environ.get('ENABLE_ANALYTICS', 'True').lower() == 'true'
    ENABLE_CACHING: bool = os.environ.get('ENABLE_CACHING', 'True').lower() == 'true'
    
    @classmethod
    def validate_config(cls) -> None:
        """Validate required configuration"""
        required_vars = ['DATABASE_URL', 'SECRET_KEY']
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    
    @classmethod
    def validate_config(cls) -> None:
        super().validate_config()
        # Additional production validations
        if not cls.STRIPE_API_KEY.startswith('sk_live_'):
            raise ValueError("Production must use live Stripe API key")

# Environment-specific configuration selection
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': DevelopmentConfig
}

def get_config() -> Config:
    env = os.environ.get('FLASK_ENV', 'development')
    return config_map.get(env, DevelopmentConfig)
```

#### IV. Backing Services
**Principle:** Treat backing services as attached resources.

**Implementation Example:**
```python
# app/services/backing_services.py - Service abstractions
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import redis
import boto3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class DatabaseService(ABC):
    """Abstract database service interface"""
    
    @abstractmethod
    def execute_query(self, query: str, params: Dict[str, Any] = None) -> Any:
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        pass

class PostgreSQLService(DatabaseService):
    """PostgreSQL implementation of database service"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
    
    def execute_query(self, query: str, params: Dict[str, Any] = None) -> Any:
        with self.Session() as session:
            result = session.execute(query, params or {})
            session.commit()
            return result.fetchall()
    
    def health_check(self) -> bool:
        try:
            with self.Session() as session:
                session.execute("SELECT 1")
                return True
        except Exception:
            return False

class CacheService(ABC):
    """Abstract cache service interface"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        pass
    
    @abstractmethod
    def set(self, key: str, value: str, ttl: int = 3600) -> bool:
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        pass

class RedisService(CacheService):
    """Redis implementation of cache service"""
    
    def __init__(self, redis_url: str):
        self.client = redis.from_url(redis_url)
    
    def get(self, key: str) -> Optional[str]:
        result = self.client.get(key)
        return result.decode('utf-8') if result else None
    
    def set(self, key: str, value: str, ttl: int = 3600) -> bool:
        return self.client.setex(key, ttl, value)
    
    def delete(self, key: str) -> bool:
        return bool(self.client.delete(key))

class StorageService(ABC):
    """Abstract storage service interface"""
    
    @abstractmethod
    def upload_file(self, key: str, file_content: bytes) -> str:
        pass
    
    @abstractmethod
    def download_file(self, key: str) -> bytes:
        pass
    
    @abstractmethod
    def delete_file(self, key: str) -> bool:
        pass

class S3StorageService(StorageService):
    """AWS S3 implementation of storage service"""
    
    def __init__(self, bucket_name: str, aws_access_key: str, aws_secret_key: str):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        )
    
    def upload_file(self, key: str, file_content: bytes) -> str:
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=file_content
        )
        return f"s3://{self.bucket_name}/{key}"
    
    def download_file(self, key: str) -> bytes:
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
        return response['Body'].read()
    
    def delete_file(self, key: str) -> bool:
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except Exception:
            return False

# Service factory for dependency injection
class ServiceFactory:
    """Factory for creating backing service instances"""
    
    def __init__(self, config: Config):
        self.config = config
        self._database_service = None
        self._cache_service = None
        self._storage_service = None
    
    @property
    def database(self) -> DatabaseService:
        if not self._database_service:
            self._database_service = PostgreSQLService(self.config.DATABASE_URL)
        return self._database_service
    
    @property
    def cache(self) -> CacheService:
        if not self._cache_service:
            self._cache_service = RedisService(self.config.REDIS_URL)
        return self._cache_service
    
    @property
    def storage(self) -> StorageService:
        if not self._storage_service:
            self._storage_service = S3StorageService(
                self.config.S3_BUCKET_NAME,
                self.config.AWS_ACCESS_KEY_ID,
                self.config.AWS_SECRET_ACCESS_KEY
            )
        return self._storage_service

# Usage in application
# app/api/users.py
from flask import Blueprint, request, jsonify
from app.services.backing_services import ServiceFactory
from app.config import get_config

bp = Blueprint('users', __name__)
services = ServiceFactory(get_config())

@bp.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    # Try cache first
    cached_user = services.cache.get(f"user:{user_id}")
    if cached_user:
        return jsonify(json.loads(cached_user))
    
    # Fetch from database
    user_data = services.database.execute_query(
        "SELECT * FROM users WHERE id = :user_id",
        {"user_id": user_id}
    )
    
    if user_data:
        user = dict(user_data[0])
        # Cache for 1 hour
        services.cache.set(f"user:{user_id}", json.dumps(user), 3600)
        return jsonify(user)
    
    return jsonify({"error": "User not found"}), 404
```

#### V. Build, Release, Run
**Principle:** Strictly separate build and run stages.

**Implementation Example:**
```yaml
# .github/workflows/ci-cd.yml - CI/CD pipeline
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # Build Stage
  build:
    runs-on: ubuntu-latest
    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
      image-digest: ${{ steps.build.outputs.digest }}
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=sha,prefix={{branch}}-
    
    - name: Build and push image
      id: build
      uses: docker/build-push-action@v5
      with:
        context: .
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
        platforms: linux/amd64,linux/arm64

  # Test Stage
  test:
    needs: build
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:testpass@localhost:5432/testdb
        REDIS_URL: redis://localhost:6379
        SECRET_KEY: test-secret-key
      run: |
        python -m pytest tests/ -v --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  # Security Scan Stage
  security:
    needs: build
    runs-on: ubuntu-latest
    
    steps:
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: ${{ needs.build.outputs.image-tag }}
        format: 'sarif'
        output: 'trivy-results.sarif'
    
    - name: Upload Trivy scan results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'

  # Release Stage
  release:
    needs: [build, test, security]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Create release
      id: release
      run: |
        echo "version=$(date +%Y.%m.%d)-${GITHUB_SHA::7}" >> $GITHUB_OUTPUT
        echo "Creating release for ${{ needs.build.outputs.image-tag }}"

  # Deploy to Staging
  deploy-staging:
    needs: [build, test, security]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    environment: staging
    
    steps:
    - name: Deploy to staging
      run: |
        echo "Deploying ${{ needs.build.outputs.image-tag }} to staging"
        # Update Kubernetes deployment
        kubectl set image deployment/myapp-staging myapp=${{ needs.build.outputs.image-tag }}

  # Deploy to Production
  deploy-production:
    needs: [release]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production
    
    steps:
    - name: Deploy to production
      run: |
        echo "Deploying ${{ needs.build.outputs.image-tag }} to production"
        # Blue-green deployment
        kubectl apply -f k8s/production/
        kubectl set image deployment/myapp-blue myapp=${{ needs.build.outputs.image-tag }}
        # Health check and traffic switch logic here
```

#### VI. Processes
**Principle:** Execute the app as one or more stateless processes.

**Implementation Example:**
```python
# app/processes.py - Stateless process implementations
import os
import signal
import sys
from typing import Dict, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import json

@dataclass
class ProcessState:
    """Immutable process state"""
    process_id: str
    start_time: float
    request_count: int = 0
    error_count: int = 0

class StatelessProcess:
    """Base class for stateless processes"""
    
    def __init__(self, process_id: str):
        self.process_id = process_id
        self.state = ProcessState(process_id, time.time())
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """Setup graceful shutdown handlers"""
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)
    
    def handle_shutdown(self, signum, frame):
        """Graceful shutdown handler"""
        print(f"Process {self.process_id} received shutdown signal {signum}")
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """Cleanup resources before shutdown"""
        print(f"Process {self.process_id} cleaning up resources")
    
    def get_process_info(self) -> Dict[str, Any]:
        """Return current process information"""
        return {
            'process_id': self.process_id,
            'start_time': self.state.start_time,
            'uptime': time.time() - self.state.start_time,
            'request_count': self.state.request_count,
            'error_count': self.state.error_count,
            'memory_usage': self._get_memory_usage()
        }
    
    def _get_memory_usage(self) -> int:
        """Get current memory usage in bytes"""
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss

# Web process implementation
class WebProcess(StatelessProcess):
    """Stateless web server process"""
    
    def __init__(self, process_id: str, port: int = 8000):
        super().__init__(process_id)
        self.port = port
        self.app = self.create_app()
    
    def create_app(self):
        """Create Flask application with stateless configuration"""
        from flask import Flask, request, jsonify, g
        import time
        import uuid
        
        app = Flask(__name__)
        
        @app.before_request
        def before_request():
            # Generate unique request ID for tracing
            g.request_id = str(uuid.uuid4())
            g.start_time = time.time()
            
            # Update process state (immutably)
            self.state = ProcessState(
                self.state.process_id,
                self.state.start_time,
                self.state.request_count + 1,
                self.state.error_count
            )
        
        @app.after_request
        def after_request(response):
            # Log request completion
            duration = time.time() - g.start_time
            print(f"Request {g.request_id} completed in {duration:.3f}s")
            return response
        
        @app.errorhandler(Exception)
        def handle_error(error):
            # Update error count
            self.state = ProcessState(
                self.state.process_id,
                self.state.start_time,
                self.state.request_count,
                self.state.error_count + 1
            )
            
            return jsonify({
                'error': str(error),
                'request_id': g.get('request_id', '')
            }), 500
        
        @app.route('/health')
        def health():
            return jsonify(self.get_process_info())
        
        return app
    
    def run(self):
        """Run the web process"""
        print(f"Starting web process {self.process_id} on port {self.port}")
        self.app.run(host='0.0.0.0', port=self.port)

# Worker process implementation
class WorkerProcess(StatelessProcess):
    """Stateless background worker process"""
    
    def __init__(self, process_id: str, queue_name: str = 'default'):
        super().__init__(process_id)
        self.queue_name = queue_name
        self.running = True
    
    def process_job(self, job_data: Dict[str, Any]) -> bool:
        """Process a single job (stateless)"""
        try:
            job_type = job_data.get('type')
            job_payload = job_data.get('payload', {})
            
            print(f"Processing job {job_type} with payload: {job_payload}")
            
            # Simulate job processing
            if job_type == 'send_email':
                self._send_email(job_payload)
            elif job_type == 'process_image':
                self._process_image(job_payload)
            else:
                raise ValueError(f"Unknown job type: {job_type}")
            
            return True
            
        except Exception as e:
            print(f"Job processing failed: {e}")
            # Update error count
            self.state = ProcessState(
                self.state.process_id,
                self.state.start_time,
                self.state.request_count,
                self.state.error_count + 1
            )
            return False
    
    def _send_email(self, payload: Dict[str, Any]):
        """Send email (stateless operation)"""
        # Email sending logic here
        pass
    
    def _process_image(self, payload: Dict[str, Any]):
        """Process image (stateless operation)"""
        # Image processing logic here
        pass
    
    def run(self):
        """Run the worker process"""
        print(f"Starting worker process {self.process_id} for queue {self.queue_name}")
        
        # In a real implementation, this would connect to a message queue
        # like Redis, RabbitMQ, or AWS SQS
        import time
        import random
        
        while self.running:
            try:
                # Simulate receiving job from queue
                if random.random() < 0.3:  # 30% chance of having work
                    job_data = {
                        'type': random.choice(['send_email', 'process_image']),
                        'payload': {'user_id': random.randint(1, 1000)}
                    }
                    
                    success = self.process_job(job_data)
                    
                    # Update request count
                    self.state = ProcessState(
                        self.state.process_id,
                        self.state.start_time,
                        self.state.request_count + 1,
                        self.state.error_count
                    )
                
                time.sleep(1)  # Poll interval
                
            except KeyboardInterrupt:
                self.running = False
                break

# Process manager for horizontal scaling
class ProcessManager:
    """Manages multiple stateless processes"""
    
    def __init__(self):
        self.processes = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
    
    def start_web_processes(self, count: int, base_port: int = 8000):
        """Start multiple web processes"""
        for i in range(count):
            process_id = f"web-{i}"
            port = base_port + i
            process = WebProcess(process_id, port)
            
            # Start process in thread pool
            future = self.executor.submit(process.run)
            self.processes[process_id] = {
                'process': process,
                'future': future,
                'type': 'web',
                'port': port
            }
    
    def start_worker_processes(self, count: int, queue_name: str = 'default'):
        """Start multiple worker processes"""
        for i in range(count):
            process_id = f"worker-{queue_name}-{i}"
            process = WorkerProcess(process_id, queue_name)
            
            # Start process in thread pool
            future = self.executor.submit(process.run)
            self.processes[process_id] = {
                'process': process,
                'future': future,
                'type': 'worker',
                'queue': queue_name
            }
    
    def get_all_process_info(self) -> Dict[str, Any]:
        """Get information about all running processes"""
        info = {}
        for process_id, process_data in self.processes.items():
            process = process_data['process']
            info[process_id] = {
                **process.get_process_info(),
                'type': process_data['type'],
                'running': not process_data['future'].done()
            }
        return info
    
    def scale_processes(self, process_type: str, target_count: int):
        """Scale processes up or down"""
        current_processes = [
            pid for pid, data in self.processes.items() 
            if data['type'] == process_type
        ]
        current_count = len(current_processes)
        
        if target_count > current_count:
            # Scale up
            if process_type == 'web':
                self.start_web_processes(target_count - current_count, 8000 + current_count)
            elif process_type == 'worker':
                self.start_worker_processes(target_count - current_count)
        
        elif target_count < current_count:
            # Scale down
            processes_to_stop = current_processes[target_count:]
            for process_id in processes_to_stop:
                process_data = self.processes[process_id]
                process_data['future'].cancel()
                del self.processes[process_id]

# Usage example
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python processes.py [web|worker|manager]")
        sys.exit(1)
    
    process_type = sys.argv[1]
    
    if process_type == 'web':
        process = WebProcess('web-1', 8000)
        process.run()
    
    elif process_type == 'worker':
        process = WorkerProcess('worker-1', 'default')
        process.run()
    
    elif process_type == 'manager':
        manager = ProcessManager()
        manager.start_web_processes(2)
        manager.start_worker_processes(3)
        
        # Keep manager running
        try:
            while True:
                time.sleep(10)
                print("Process status:", manager.get_all_process_info())
        except KeyboardInterrupt:
            print("Shutting down process manager")
```

### Container Orchestration

#### Kubernetes Implementation

**Definition:** Kubernetes is an open-source container orchestration platform that automates deployment, scaling, and management of containerized applications.

**Core Kubernetes Resources:**

```yaml
# namespace.yaml - Logical isolation
apiVersion: v1
kind: Namespace
metadata:
  name: myapp
  labels:
    app: myapp
    environment: production

---
# configmap.yaml - Configuration management
apiVersion: v1
kind: ConfigMap
metadata:
  name: myapp-config
  namespace: myapp
data:
  app.properties: |
    database.host=postgres-service
    database.port=5432
    database.name=myapp
    redis.host=redis-service
    redis.port=6379
    log.level=INFO
    enable.analytics=true
  
  nginx.conf: |
    upstream backend {
        server myapp-api:8000;
    }
    
    server {
        listen 80;
        server_name myapp.example.com;
        
        location / {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
        
        location /health {
            access_log off;
            return 200 "healthy\n";
        }
    }

---
# secret.yaml - Sensitive data management
apiVersion: v1
kind: Secret
metadata:
  name: myapp-secrets
  namespace: myapp
type: Opaque
data:
  database-password: <base64-encoded-password>
  jwt-secret-key: <base64-encoded-jwt-secret>
  stripe-api-key: <base64-encoded-stripe-key>
  
---
# deployment.yaml - Application deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-api
  namespace: myapp
  labels:
    app: myapp
    component: api
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: myapp
      component: api
  template:
    metadata:
      labels:
        app: myapp
        component: api
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: api
        image: myapp:latest
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: DATABASE_URL
          value: "postgresql://$(DATABASE_USER):$(DATABASE_PASSWORD)@postgres-service:5432/myapp"
        - name: DATABASE_USER
          value: "myapp"
        - name: DATABASE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: myapp-secrets
              key: database-password
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: myapp-secrets
              key: jwt-secret-key
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: myapp-config
              key: log.level
        
        # Resource limits and requests
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        
        # Health checks
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        
        # Security context
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        
        # Volume mounts
        volumeMounts:
        - name: config-volume
          mountPath: /app/config
          readOnly: true
        - name: tmp-volume
          mountPath: /tmp
      
      # Pod security and scheduling
      securityContext:
        fsGroup: 1000
      
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values: [myapp]
                - key: component
                  operator: In
                  values: [api]
              topologyKey: kubernetes.io/hostname
      
      volumes:
      - name: config-volume
        configMap:
          name: myapp-config
      - name: tmp-volume
        emptyDir: {}

---
# service.yaml - Service discovery
apiVersion: v1
kind: Service
metadata:
  name: myapp-api-service
  namespace: myapp
  labels:
    app: myapp
    component: api
spec:
  type: ClusterIP
  selector:
    app: myapp
    component: api
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
    name: http

---
# hpa.yaml - Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: myapp-api-hpa
  namespace: myapp
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp-api
  minReplicas: 3
  maxReplicas: 20
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
  - type: Pods
    pods:
      metric:
        name: requests_per_second
      target:
        type: AverageValue
        averageValue: "100"
  
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60

---
# ingress.yaml - External access
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp-ingress
  namespace: myapp
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/cors-allow-methods: "GET, POST, PUT, DELETE, OPTIONS"
    nginx.ingress.kubernetes.io/cors-allow-headers: "DNT,X-CustomHeader,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Authorization"
spec:
  tls:
  - hosts:
    - api.myapp.com
    secretName: myapp-tls
  rules:
  - host: api.myapp.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: myapp-api-service
            port:
              number: 80

---
# network-policy.yaml - Network security
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: myapp-network-policy
  namespace: myapp
spec:
  podSelector:
    matchLabels:
      app: myapp
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    - podSelector:
        matchLabels:
          app: myapp
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
  - to: []
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
    - protocol: TCP
      port: 443
```

#### Service Mesh Architecture

**Definition:** A dedicated infrastructure layer for facilitating service-to-service communications between microservices.

**Istio Implementation Example:**
```yaml
# istio-gateway.yaml - Gateway configuration
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: myapp-gateway
  namespace: myapp
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 443
      name: https
      protocol: HTTPS
    tls:
      mode: SIMPLE
      credentialName: myapp-tls
    hosts:
    - api.myapp.com
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - api.myapp.com
    tls:
      httpsRedirect: true

---
# virtual-service.yaml - Traffic routing
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: myapp-vs
  namespace: myapp
spec:
  hosts:
  - api.myapp.com
  gateways:
  - myapp-gateway
  http:
  # Canary deployment routing
  - match:
    - headers:
        canary:
          exact: "true"
    route:
    - destination:
        host: myapp-api-service
        subset: v2
      weight: 100
  # A/B testing routing
  - match:
    - headers:
        experiment:
          exact: "variant-b"
    route:
    - destination:
        host: myapp-api-service
        subset: v1
      weight: 50
    - destination:
        host: myapp-api-service
        subset: v2
      weight: 50
  # Default routing with traffic splitting
  - route:
    - destination:
        host: myapp-api-service
        subset: v1
      weight: 90
    - destination:
        host: myapp-api-service
        subset: v2
      weight: 10
    timeout: 30s
    retries:
      attempts: 3
      perTryTimeout: 10s
      retryOn: 5xx,reset,connect-failure,refused-stream

---
# destination-rule.yaml - Traffic policies
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: myapp-api-dr
  namespace: myapp
spec:
  host: myapp-api-service
  trafficPolicy:
    loadBalancer:
      simple: LEAST_CONN
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 50
        http2MaxRequests: 100
        maxRequestsPerConnection: 10
        maxRetries: 3
        connectTimeout: 30s
    circuitBreaker:
      consecutiveErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
      minHealthPercent: 30
  subsets:
  - name: v1
    labels:
      version: v1
    trafficPolicy:
      circuitBreaker:
        consecutiveErrors: 3
  - name: v2
    labels:
      version: v2
    trafficPolicy:
      circuitBreaker:
        consecutiveErrors: 5

---
# authorization-policy.yaml - Security policies
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: myapp-authz
  namespace: myapp
spec:
  selector:
    matchLabels:
      app: myapp
      component: api
  rules:
  # Allow health checks from anywhere
  - to:
    - operation:
        paths: ["/health", "/ready"]
  # Require JWT for API endpoints
  - to:
    - operation:
        paths: ["/api/*"]
    when:
    - key: request.auth.claims[iss]
      values: ["https://auth.myapp.com"]
    - key: request.auth.claims[aud]
      values: ["myapp-api"]
  # Allow internal service communication
  - from:
    - source:
        principals: ["cluster.local/ns/myapp/sa/myapp-worker"]
    to:
    - operation:
        methods: ["GET", "POST"]

---
# peer-authentication.yaml - mTLS configuration
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: myapp-mtls
  namespace: myapp
spec:
  selector:
    matchLabels:
      app: myapp
  mtls:
    mode: STRICT

---
# service-monitor.yaml - Prometheus monitoring
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: myapp-metrics
  namespace: myapp
  labels:
    app: myapp
spec:
  selector:
    matchLabels:
      app: myapp
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
```

### Observability

#### Distributed Tracing Implementation

```python
# app/tracing.py - Distributed tracing setup
import os
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.b3 import B3MultiFormat
import logging

class TracingService:
    """Centralized tracing configuration"""
    
    def __init__(self, service_name: str, service_version: str = "1.0.0"):
        self.service_name = service_name
        self.service_version = service_version
        self.tracer = None
        
    def initialize_tracing(self):
        """Initialize distributed tracing"""
        
        # Create resource identifying the service
        resource = Resource.create({
            SERVICE_NAME: self.service_name,
            SERVICE_VERSION: self.service_version,
            "deployment.environment": os.environ.get("ENVIRONMENT", "development"),
            "service.instance.id": os.environ.get("HOSTNAME", "unknown")
        })
        
        # Set up tracer provider
        trace.set_tracer_provider(TracerProvider(resource=resource))
        
        # Configure Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name=os.environ.get("JAEGER_AGENT_HOST", "localhost"),
            agent_port=int(os.environ.get("JAEGER_AGENT_PORT", "6831")),
        )
        
        # Create span processor
        span_processor = BatchSpanProcessor(jaeger_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)
        
        # Set global propagator for cross-service tracing
        set_global_textmap(B3MultiFormat())
        
        # Get tracer
        self.tracer = trace.get_tracer(__name__)
        
        return self.tracer
    
    def instrument_flask_app(self, app):
        """Instrument Flask application"""
        FlaskInstrumentor().instrument_app(app)
        
        # Add custom request attributes
        @app.before_request
        def add_trace_attributes():
            span = trace.get_current_span()
            if span.is_recording():
                span.set_attribute("http.user_agent", request.headers.get("User-Agent", ""))
                span.set_attribute("http.remote_addr", request.remote_addr)
                span.set_attribute("user.id", g.get("user_id", "anonymous"))
    
    def instrument_external_libraries(self):
        """Instrument external libraries"""
        RequestsInstrumentor().instrument()
        Psycopg2Instrumentor().instrument()
        RedisInstrumentor().instrument()

# app/decorators.py - Tracing decorators
from functools import wraps
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
import time

def trace_function(operation_name: str = None):
    """Decorator to trace function execution"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            span_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with tracer.start_as_current_span(span_name) as span:
                try:
                    # Add function metadata
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)
                    
                    # Add arguments as attributes (be careful with sensitive data)
                    if args:
                        span.set_attribute("function.args.count", len(args))
                    if kwargs:
                        span.set_attribute("function.kwargs.count", len(kwargs))
                        # Only log non-sensitive kwargs
                        safe_kwargs = {k: v for k, v in kwargs.items() 
                                     if k not in ['password', 'token', 'secret']}
                        span.set_attribute("function.kwargs", str(safe_kwargs))
                    
                    start_time = time.time()
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    # Add performance metrics
                    span.set_attribute("function.duration_ms", duration * 1000)
                    span.set_status(Status(StatusCode.OK))
                    
                    return result
                    
                except Exception as e:
                    # Record exception
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise
        
        return wrapper
    return decorator

def trace_database_operation(table_name: str = None, operation: str = None):
    """Decorator to trace database operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            span_name = f"db.{operation or 'operation'}.{table_name or 'table'}"
            
            with tracer.start_as_current_span(span_name) as span:
                try:
                    # Add database metadata
                    span.set_attribute("db.system", "postgresql")
                    if table_name:
                        span.set_attribute("db.sql.table", table_name)
                    if operation:
                        span.set_attribute("db.operation", operation)
                    
                    result = func(*args, **kwargs)
                    
                    # Add result metadata
                    if hasattr(result, 'rowcount'):
                        span.set_attribute("db.rows_affected", result.rowcount)
                    
                    span.set_status(Status(StatusCode.OK))
                    return result
                    
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise
        
        return wrapper
    return decorator

# Usage examples
# app/services/user_service.py
from app.tracing import TracingService
from app.decorators import trace_function, trace_database_operation

class UserService:
    def __init__(self, database, cache):
        self.database = database
        self.cache = cache
    
    @trace_function("user_service.get_user")
    def get_user(self, user_id: str):
        """Get user with distributed tracing"""
        tracer = trace.get_tracer(__name__)
        
        # Check cache first
        with tracer.start_as_current_span("cache.get") as span:
            span.set_attribute("cache.key", f"user:{user_id}")
            cached_user = self.cache.get(f"user:{user_id}")
            
            if cached_user:
                span.set_attribute("cache.hit", True)
                return json.loads(cached_user)
            else:
                span.set_attribute("cache.hit", False)
        
        # Fetch from database
        user = self._fetch_user_from_db(user_id)
        
        if user:
            # Cache the result
            with tracer.start_as_current_span("cache.set") as span:
                span.set_attribute("cache.key", f"user:{user_id}")
                span.set_attribute("cache.ttl", 3600)
                self.cache.set(f"user:{user_id}", json.dumps(user), 3600)
        
        return user
    
    @trace_database_operation(table_name="users", operation="select")
    def _fetch_user_from_db(self, user_id: str):
        """Fetch user from database with tracing"""
        query = "SELECT * FROM users WHERE id = %s"
        
        # The decorator will automatically trace this database operation
        result = self.database.execute(query, (user_id,))
        
        return dict(result.fetchone()) if result.rowcount > 0 else None
    
    @trace_function("user_service.create_user")
    def create_user(self, user_data: dict):
        """Create user with comprehensive tracing"""
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("user_validation") as span:
            # Validate user data
            span.set_attribute("validation.email", user_data.get("email", ""))
            span.set_attribute("validation.fields_count", len(user_data))
            
            if not self._validate_user_data(user_data):
                span.set_status(Status(StatusCode.ERROR, "Validation failed"))
                raise ValueError("Invalid user data")
        
        # Create user in database
        user = self._create_user_in_db(user_data)
        
        # Send welcome email asynchronously
        with tracer.start_as_current_span("async.send_welcome_email") as span:
            span.set_attribute("email.recipient", user_data["email"])
            span.set_attribute("email.template", "welcome")
            self._queue_welcome_email(user["id"])
        
        return user
    
    @trace_database_operation(table_name="users", operation="insert")
    def _create_user_in_db(self, user_data: dict):
        """Create user in database"""
        query = """
            INSERT INTO users (email, name, created_at) 
            VALUES (%(email)s, %(name)s, NOW()) 
            RETURNING id, email, name, created_at
        """
        
        result = self.database.execute(query, user_data)
        return dict(result.fetchone())
    
    def _validate_user_data(self, user_data: dict) -> bool:
        """Validate user data"""
        required_fields = ["email", "name"]
        return all(field in user_data for field in required_fields)
    
    def _queue_welcome_email(self, user_id: str):
        """Queue welcome email for sending"""
        # This would typically use a message queue
        pass

# Initialize tracing in application
# app/__init__.py
from app.tracing import TracingService

def create_app():
    app = Flask(__name__)
    
    # Initialize tracing
    tracing_service = TracingService("myapp-api", "1.0.0")
    tracer = tracing_service.initialize_tracing()
    
    # Instrument Flask app
    tracing_service.instrument_flask_app(app)
    
    # Instrument external libraries
    tracing_service.instrument_external_libraries()
    
    return app
```

This comprehensive Cloud-Native architecture guide covers the 12-Factor App methodology, container orchestration with Kubernetes, service mesh implementation with Istio, and distributed tracing with OpenTelemetry, providing production-ready examples for building scalable, observable cloud-native applications.