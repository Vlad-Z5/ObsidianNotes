# Networking Load Balancing

> **Service Type:** Networking & Content Delivery | **Scope:** Regional | **Serverless:** Yes

## Overview

Load balancing distributes network traffic across multiple servers to ensure high availability, optimal performance, and fault tolerance. Modern load balancing encompasses Layer 4 (transport) and Layer 7 (application) distribution, health monitoring, SSL termination, and intelligent traffic routing for enterprise applications.

## Core Load Balancing Types

### Layer 4 Load Balancing (Transport Layer)
**Function**: Distributes traffic based on IP addresses and TCP/UDP ports
- **Speed**: High performance with minimal latency
- **Protocol Awareness**: TCP/UDP connection-based routing
- **Use Cases**: Database connections, gaming servers, high-throughput applications

### Layer 7 Load Balancing (Application Layer)  
**Function**: Distributes traffic based on application data (HTTP headers, URLs, cookies)
- **Intelligence**: Content-aware routing and advanced features
- **Protocol Awareness**: HTTP/HTTPS, application-specific logic
- **Use Cases**: Web applications, API gateways, microservices

## Load Balancing Algorithms

### Round Robin
```python
class RoundRobinBalancer:
    def __init__(self, servers):
        self.servers = servers
        self.current = 0
    
    def get_server(self):
        server = self.servers[self.current]
        self.current = (self.current + 1) % len(self.servers)
        return server

# Usage
balancer = RoundRobinBalancer(['server1', 'server2', 'server3'])
next_server = balancer.get_server()
```

### Weighted Round Robin
```python
class WeightedRoundRobinBalancer:
    def __init__(self, servers_weights):
        self.servers_weights = servers_weights
        self.current_weights = {server: 0 for server in servers_weights}
    
    def get_server(self):
        total_weight = sum(self.servers_weights.values())
        
        for server in self.servers_weights:
            self.current_weights[server] += self.servers_weights[server]
        
        selected = max(self.current_weights, key=self.current_weights.get)
        self.current_weights[selected] -= total_weight
        
        return selected

# Usage with different server capacities
balancer = WeightedRoundRobinBalancer({
    'server1': 3,  # High capacity
    'server2': 2,  # Medium capacity  
    'server3': 1   # Low capacity
})
```

### Least Connections
```python
class LeastConnectionsBalancer:
    def __init__(self, servers):
        self.servers = servers
        self.connections = {server: 0 for server in servers}
    
    def get_server(self):
        return min(self.connections, key=self.connections.get)
    
    def add_connection(self, server):
        if server in self.connections:
            self.connections[server] += 1
    
    def remove_connection(self, server):
        if server in self.connections and self.connections[server] > 0:
            self.connections[server] -= 1
```

### IP Hash
```python
import hashlib

class IPHashBalancer:
    def __init__(self, servers):
        self.servers = servers
    
    def get_server(self, client_ip):
        hash_value = int(hashlib.md5(client_ip.encode()).hexdigest(), 16)
        server_index = hash_value % len(self.servers)
        return self.servers[server_index]

# Ensures same client always reaches same server
balancer = IPHashBalancer(['server1', 'server2', 'server3'])
server = balancer.get_server('192.168.1.100')
```

## Health Check Implementation

### HTTP Health Checks
```python
import requests
import asyncio
import aiohttp
from datetime import datetime, timedelta

class HealthCheckManager:
    def __init__(self, servers, check_interval=30):
        self.servers = servers
        self.check_interval = check_interval
        self.server_status = {server: True for server in servers}
        self.last_check = {}
    
    async def check_server_health(self, session, server):
        try:
            health_url = f"http://{server}/health"
            
            async with session.get(health_url, timeout=5) as response:
                if response.status == 200:
                    health_data = await response.json()
                    
                    # Advanced health criteria
                    cpu_usage = health_data.get('cpu_usage', 0)
                    memory_usage = health_data.get('memory_usage', 0)
                    active_connections = health_data.get('active_connections', 0)
                    
                    # Mark unhealthy if resource usage too high
                    is_healthy = (
                        cpu_usage < 80 and 
                        memory_usage < 85 and 
                        active_connections < 1000
                    )
                    
                    self.server_status[server] = is_healthy
                    self.last_check[server] = datetime.now()
                    
                    return is_healthy
                else:
                    self.server_status[server] = False
                    return False
                    
        except Exception as e:
            print(f"Health check failed for {server}: {e}")
            self.server_status[server] = False
            return False
    
    async def run_health_checks(self):
        while True:
            async with aiohttp.ClientSession() as session:
                tasks = [
                    self.check_server_health(session, server) 
                    for server in self.servers
                ]
                await asyncio.gather(*tasks, return_exceptions=True)
            
            await asyncio.sleep(self.check_interval)
    
    def get_healthy_servers(self):
        return [server for server, status in self.server_status.items() if status]
```

### TCP Health Checks
```python
import socket
import threading
import time

class TCPHealthChecker:
    def __init__(self, servers, port, timeout=3):
        self.servers = servers
        self.port = port
        self.timeout = timeout
        self.server_status = {}
        self.running = True
    
    def check_tcp_connectivity(self, server):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            
            result = sock.connect_ex((server, self.port))
            sock.close()
            
            is_healthy = result == 0
            self.server_status[server] = is_healthy
            
            return is_healthy
            
        except Exception as e:
            print(f"TCP check failed for {server}:{self.port} - {e}")
            self.server_status[server] = False
            return False
    
    def run_checks(self):
        while self.running:
            threads = []
            
            for server in self.servers:
                thread = threading.Thread(
                    target=self.check_tcp_connectivity,
                    args=(server,)
                )
                threads.append(thread)
                thread.start()
            
            # Wait for all checks to complete
            for thread in threads:
                thread.join()
            
            time.sleep(30)  # Check every 30 seconds
```

## Enterprise Load Balancer Configurations

### AWS Application Load Balancer
```yaml
# CloudFormation template for ALB
Resources:
  ApplicationLoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Name: production-alb
      Scheme: internet-facing
      Type: application
      IpAddressType: ipv4
      Subnets:
        - !Ref PublicSubnet1
        - !Ref PublicSubnet2
      SecurityGroups:
        - !Ref ALBSecurityGroup
      Tags:
        - Key: Environment
          Value: Production
        - Key: Purpose
          Value: WebTierLoadBalancing

  ALBTargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      Name: production-web-tg
      Port: 80
      Protocol: HTTP
      VpcId: !Ref VPC
      HealthCheckEnabled: true
      HealthCheckPath: /health
      HealthCheckProtocol: HTTP
      HealthCheckIntervalSeconds: 30
      HealthyThresholdCount: 2
      UnhealthyThresholdCount: 3
      TargetType: instance
      
      # Advanced health check settings
      HealthCheckTimeoutSeconds: 5
      Matcher:
        HttpCode: '200,204'

  ALBListener:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      DefaultActions:
        - Type: forward
          TargetGroupArn: !Ref ALBTargetGroup
      LoadBalancerArn: !Ref ApplicationLoadBalancer
      Port: 443
      Protocol: HTTPS
      SslPolicy: ELBSecurityPolicy-TLS-1-2-2017-01
      Certificates:
        - CertificateArn: !Ref SSLCertificate

  # Advanced routing rules
  ALBListenerRule:
    Type: AWS::ElasticLoadBalancingV2::ListenerRule
    Properties:
      Actions:
        - Type: forward
          TargetGroupArn: !Ref APITargetGroup
      Conditions:
        - Field: path-pattern
          Values: ['/api/*']
        - Field: host-header
          Values: ['api.company.com']
      ListenerArn: !Ref ALBListener
      Priority: 100
```

### NGINX Load Balancer Configuration
```nginx
# /etc/nginx/nginx.conf
upstream backend_servers {
    # Load balancing method
    least_conn;
    
    # Backend servers with weights and health checks
    server 10.0.1.10:8080 weight=3 max_fails=2 fail_timeout=30s;
    server 10.0.1.11:8080 weight=2 max_fails=2 fail_timeout=30s;
    server 10.0.1.12:8080 weight=1 max_fails=2 fail_timeout=30s backup;
    
    # Health check configuration
    keepalive 32;
    keepalive_requests 100;
    keepalive_timeout 60s;
}

upstream api_servers {
    # IP hash for session persistence
    ip_hash;
    
    server 10.0.2.10:3000 max_fails=1 fail_timeout=10s;
    server 10.0.2.11:3000 max_fails=1 fail_timeout=10s;
    server 10.0.2.12:3000 max_fails=1 fail_timeout=10s;
}

# Main server configuration
server {
    listen 80;
    listen 443 ssl http2;
    server_name company.com www.company.com;
    
    # SSL configuration
    ssl_certificate /etc/ssl/certs/company.com.pem;
    ssl_certificate_key /etc/ssl/private/company.com.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    
    # Global settings
    client_max_body_size 10M;
    proxy_connect_timeout 5s;
    proxy_send_timeout 10s;
    proxy_read_timeout 10s;
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
    
    # Main application routing
    location / {
        proxy_pass http://backend_servers;
        
        # Headers for backend servers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Load balancer identification
        add_header X-Load-Balancer "nginx-primary";
        
        # Circuit breaker simulation
        proxy_next_upstream error timeout http_502 http_503 http_504;
        proxy_next_upstream_tries 3;
        proxy_next_upstream_timeout 10s;
    }
    
    # API routing with different backend
    location /api/ {
        proxy_pass http://api_servers;
        
        # API-specific headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-API-Version "v1";
        
        # CORS headers for APIs
        add_header Access-Control-Allow-Origin "*";
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization";
        
        # Handle preflight requests
        if ($request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin "*";
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
            add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization";
            add_header Access-Control-Max-Age 1728000;
            add_header Content-Type 'text/plain; charset=utf-8';
            add_header Content-Length 0;
            return 204;
        }
    }
    
    # Static content with caching
    location /static/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header X-Load-Balancer "nginx-primary";
        
        # Try local first, fallback to backend
        try_files $uri @backend;
    }
    
    location @backend {
        proxy_pass http://backend_servers;
        proxy_cache_bypass $http_pragma;
        proxy_cache_revalidate on;
    }
}

# Monitoring and metrics endpoint
server {
    listen 8080;
    server_name localhost;
    
    # Basic auth for metrics
    auth_basic "Metrics";
    auth_basic_user_file /etc/nginx/.htpasswd;
    
    location /nginx_status {
        stub_status on;
        access_log off;
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        deny all;
    }
    
    location /upstream_status {
        upstream_show;
        access_log off;
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        deny all;
    }
}
```

## Session Persistence Strategies

### Cookie-Based Session Affinity
```python
# Flask application with session affinity
from flask import Flask, session, request, make_response
import hashlib

app = Flask(__name__)
app.secret_key = 'your-secret-key'

class SessionAffinityManager:
    def __init__(self, servers):
        self.servers = servers
    
    def get_server_for_session(self, session_id):
        """Deterministic server selection based on session ID"""
        hash_value = int(hashlib.md5(session_id.encode()).hexdigest(), 16)
        server_index = hash_value % len(self.servers)
        return self.servers[server_index]
    
    def set_affinity_cookie(self, response, session_id):
        """Set cookie to maintain session affinity"""
        server = self.get_server_for_session(session_id)
        response.set_cookie(
            'lb_affinity', 
            server, 
            httponly=True, 
            secure=True,
            samesite='Strict'
        )

affinity_manager = SessionAffinityManager(['server1', 'server2', 'server3'])

@app.route('/login')
def login():
    session_id = request.headers.get('X-Session-ID')
    response = make_response("Login successful")
    
    if session_id:
        affinity_manager.set_affinity_cookie(response, session_id)
    
    return response
```

### Redis-Based Session Storage
```python
import redis
import json
from datetime import timedelta

class DistributedSessionManager:
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0):
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True
        )
        self.session_timeout = timedelta(hours=24)
    
    def create_session(self, user_id, session_data):
        """Create new session with distributed storage"""
        import uuid
        session_id = str(uuid.uuid4())
        
        session_info = {
            'user_id': user_id,
            'created_at': str(datetime.now()),
            'data': session_data
        }
        
        # Store with expiration
        self.redis_client.setex(
            f"session:{session_id}",
            self.session_timeout,
            json.dumps(session_info)
        )
        
        return session_id
    
    def get_session(self, session_id):
        """Retrieve session data"""
        session_data = self.redis_client.get(f"session:{session_id}")
        
        if session_data:
            return json.loads(session_data)
        return None
    
    def update_session(self, session_id, new_data):
        """Update existing session"""
        existing_session = self.get_session(session_id)
        
        if existing_session:
            existing_session['data'].update(new_data)
            existing_session['last_updated'] = str(datetime.now())
            
            self.redis_client.setex(
                f"session:{session_id}",
                self.session_timeout,
                json.dumps(existing_session)
            )
            
            return True
        return False
```

## SSL/TLS Termination

### SSL Certificate Management
```bash
#!/bin/bash
# ssl-cert-manager.sh - Automated SSL certificate deployment

DOMAINS=("company.com" "www.company.com" "api.company.com")
CERT_DIR="/etc/ssl/certs"
PRIVATE_KEY_DIR="/etc/ssl/private"
ACME_DIR="/var/lib/acme"

# Function to obtain Let's Encrypt certificate
obtain_certificate() {
    local domain=$1
    
    echo "Obtaining certificate for $domain"
    
    certbot certonly \
        --webroot \
        --webroot-path=$ACME_DIR \
        --email admin@company.com \
        --agree-tos \
        --non-interactive \
        --domain $domain
    
    if [ $? -eq 0 ]; then
        echo "Certificate obtained successfully for $domain"
        
        # Copy certificates to nginx directory
        cp "/etc/letsencrypt/live/$domain/fullchain.pem" "$CERT_DIR/$domain.pem"
        cp "/etc/letsencrypt/live/$domain/privkey.pem" "$PRIVATE_KEY_DIR/$domain.key"
        
        # Set proper permissions
        chmod 644 "$CERT_DIR/$domain.pem"
        chmod 600 "$PRIVATE_KEY_DIR/$domain.key"
        
        return 0
    else
        echo "Failed to obtain certificate for $domain"
        return 1
    fi
}

# Function to test SSL configuration
test_ssl_config() {
    local domain=$1
    
    echo "Testing SSL configuration for $domain"
    
    # Test SSL handshake
    openssl s_client -connect $domain:443 -servername $domain < /dev/null
    
    # Test certificate validity
    echo | openssl s_client -connect $domain:443 -servername $domain 2>/dev/null | \
        openssl x509 -noout -dates
}

# Main execution
for domain in "${DOMAINS[@]}"; do
    if obtain_certificate "$domain"; then
        test_ssl_config "$domain"
    fi
done

# Reload nginx configuration
nginx -t && systemctl reload nginx

echo "SSL certificate deployment completed"
```

## Advanced Load Balancing Features

### Circuit Breaker Implementation
```python
import time
from enum import Enum
from threading import Lock

class CircuitState(Enum):
    CLOSED = "closed"        # Normal operation
    OPEN = "open"           # Failing, reject requests
    HALF_OPEN = "half_open" # Testing recovery

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60, request_timeout=10):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.request_timeout = request_timeout
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self.lock = Lock()
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        with self.lock:
            if self.state == CircuitState.OPEN:
                # Check if we should attempt recovery
                if (time.time() - self.last_failure_time) > self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    print("Circuit breaker: Attempting recovery")
                else:
                    raise Exception("Circuit breaker OPEN - rejecting request")
        
        try:
            # Execute the function with timeout
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("Request timeout")
            
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.request_timeout)
            
            result = func(*args, **kwargs)
            
            signal.alarm(0)  # Cancel alarm
            
            # Success - reset failure count
            with self.lock:
                if self.state == CircuitState.HALF_OPEN:
                    self.state = CircuitState.CLOSED
                    print("Circuit breaker: Recovery successful - CLOSED")
                
                self.failure_count = 0
            
            return result
            
        except Exception as e:
            signal.alarm(0)  # Cancel alarm
            
            with self.lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = CircuitState.OPEN
                    print(f"Circuit breaker: OPEN due to {self.failure_count} failures")
            
            raise e

# Usage with load balancer
class LoadBalancerWithCircuitBreaker:
    def __init__(self, servers):
        self.servers = servers
        self.circuit_breakers = {
            server: CircuitBreaker() for server in servers
        }
        self.current_server = 0
    
    def make_request(self, request_func, *args, **kwargs):
        """Make request with circuit breaker protection"""
        attempts = 0
        max_attempts = len(self.servers)
        
        while attempts < max_attempts:
            server = self.servers[self.current_server]
            circuit_breaker = self.circuit_breakers[server]
            
            try:
                return circuit_breaker.call(request_func, server, *args, **kwargs)
            except Exception as e:
                print(f"Request failed for {server}: {e}")
                self.current_server = (self.current_server + 1) % len(self.servers)
                attempts += 1
        
        raise Exception("All servers are unavailable")
```

## Global Server Load Balancing (GSLB)

### DNS-Based Global Load Balancing
```python
import dns.resolver
import requests
from geopy.distance import geodesic

class GlobalLoadBalancer:
    def __init__(self):
        self.regions = {
            'us-east-1': {
                'endpoints': ['lb1.us-east-1.company.com', 'lb2.us-east-1.company.com'],
                'location': (39.0458, -76.6413),  # Virginia
                'weight': 10
            },
            'us-west-2': {
                'endpoints': ['lb1.us-west-2.company.com', 'lb2.us-west-2.company.com'],
                'location': (45.5152, -122.6784),  # Oregon
                'weight': 8
            },
            'eu-west-1': {
                'endpoints': ['lb1.eu-west-1.company.com', 'lb2.eu-west-1.company.com'],
                'location': (53.4084, -8.2426),  # Ireland
                'weight': 7
            }
        }
    
    def get_client_location(self, client_ip):
        """Get client location from IP (simplified)"""
        # In production, use GeoIP service
        try:
            import geoip2.database
            with geoip2.database.Reader('GeoLite2-City.mmdb') as reader:
                response = reader.city(client_ip)
                return (response.location.latitude, response.location.longitude)
        except:
            return (39.0458, -76.6413)  # Default to US East
    
    def find_nearest_region(self, client_location):
        """Find nearest region based on geographic distance"""
        min_distance = float('inf')
        nearest_region = None
        
        for region, config in self.regions.items():
            distance = geodesic(client_location, config['location']).kilometers
            
            if distance < min_distance:
                min_distance = distance
                nearest_region = region
        
        return nearest_region, min_distance
    
    def health_check_region(self, region):
        """Check health of region's load balancers"""
        healthy_endpoints = []
        
        for endpoint in self.regions[region]['endpoints']:
            try:
                response = requests.get(f"https://{endpoint}/health", timeout=5)
                if response.status_code == 200:
                    healthy_endpoints.append(endpoint)
            except:
                pass
        
        return healthy_endpoints
    
    def route_request(self, client_ip):
        """Route client request to optimal endpoint"""
        client_location = self.get_client_location(client_ip)
        nearest_region, distance = self.find_nearest_region(client_location)
        
        # Check if nearest region is healthy
        healthy_endpoints = self.health_check_region(nearest_region)
        
        if healthy_endpoints:
            return {
                'region': nearest_region,
                'endpoint': healthy_endpoints[0],  # Use first healthy endpoint
                'distance_km': distance
            }
        
        # Fallback to other regions if nearest is unhealthy
        for region in self.regions:
            if region != nearest_region:
                healthy_endpoints = self.health_check_region(region)
                if healthy_endpoints:
                    return {
                        'region': region,
                        'endpoint': healthy_endpoints[0],
                        'distance_km': geodesic(client_location, self.regions[region]['location']).kilometers,
                        'fallback': True
                    }
        
        raise Exception("No healthy regions available")
```

## Monitoring and Metrics

### Load Balancer Monitoring Dashboard
```python
# Prometheus metrics collection for load balancer
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
import random

class LoadBalancerMetrics:
    def __init__(self):
        # Request counters
        self.requests_total = Counter(
            'lb_requests_total', 
            'Total requests processed by load balancer',
            ['backend_server', 'method', 'status']
        )
        
        # Response time histogram
        self.response_time = Histogram(
            'lb_response_time_seconds',
            'Response time distribution',
            ['backend_server'],
            buckets=[0.1, 0.25, 0.5, 1, 2.5, 5, 10]
        )
        
        # Active connections gauge
        self.active_connections = Gauge(
            'lb_active_connections',
            'Active connections per backend',
            ['backend_server']
        )
        
        # Backend health gauge
        self.backend_health = Gauge(
            'lb_backend_health',
            'Backend server health status (1=healthy, 0=unhealthy)',
            ['backend_server']
        )
        
        # Load balancer throughput
        self.throughput = Gauge(
            'lb_throughput_requests_per_second',
            'Current throughput in requests per second'
        )
    
    def record_request(self, backend_server, method, status_code, response_time):
        """Record request metrics"""
        self.requests_total.labels(
            backend_server=backend_server,
            method=method,
            status=str(status_code)
        ).inc()
        
        self.response_time.labels(backend_server=backend_server).observe(response_time)
    
    def update_backend_health(self, backend_server, is_healthy):
        """Update backend health status"""
        self.backend_health.labels(backend_server=backend_server).set(1 if is_healthy else 0)
    
    def update_active_connections(self, backend_server, connection_count):
        """Update active connection count"""
        self.active_connections.labels(backend_server=backend_server).set(connection_count)

# Usage example
metrics = LoadBalancerMetrics()

# Start metrics server
start_http_server(8000)

# Simulate load balancer metrics
servers = ['server1', 'server2', 'server3']
while True:
    for server in servers:
        # Simulate request
        response_time = random.uniform(0.1, 2.0)
        status_code = random.choice([200, 200, 200, 500])
        method = random.choice(['GET', 'POST', 'PUT'])
        
        metrics.record_request(server, method, status_code, response_time)
        metrics.update_active_connections(server, random.randint(10, 100))
        metrics.update_backend_health(server, random.random() > 0.1)
    
    time.sleep(1)
```

## Best Practices

### Enterprise Load Balancing Strategy
- **Multi-layer approach**: Combine Layer 4 and Layer 7 load balancing
- **Health monitoring**: Comprehensive health checks with multiple criteria
- **Session management**: Appropriate session persistence strategy
- **SSL optimization**: Efficient certificate management and termination
- **Monitoring integration**: Real-time metrics and alerting
- **Disaster recovery**: Cross-region failover capabilities
- **Performance tuning**: Regular optimization based on traffic patterns
- **Security integration**: WAF and DDoS protection integration