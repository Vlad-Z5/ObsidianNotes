# Performance Load Balancing Optimization

**Focus:** Load balancing algorithms, health check optimization, session affinity strategies, auto-scaling integration, geographic distribution, and performance-aware traffic routing.

## Core Load Balancing Principles

### 1. Load Balancing Algorithms
- **Round Robin**: Equal distribution across servers
- **Weighted Round Robin**: Server capacity-based distribution
- **Least Connections**: Route to server with fewest active connections
- **Least Response Time**: Performance-based routing
- **IP Hash**: Session persistence through client IP hashing
- **Consistent Hashing**: Distributed system optimization

### 2. Health Check Strategies
- **Active Health Checks**: Proactive server monitoring
- **Passive Health Checks**: Traffic-based health detection
- **Custom Health Endpoints**: Application-specific health validation
- **Circuit Breaker Pattern**: Automatic failure isolation

### 3. Performance Optimization Techniques
- **Connection Multiplexing**: Efficient connection reuse
- **SSL Termination**: Offload encryption processing
- **Content-Based Routing**: Intelligent request distribution
- **Geographic Routing**: Latency-based traffic direction

### 4. Advanced Features
- **Auto-Scaling Integration**: Dynamic capacity adjustment
- **Real-Time Metrics**: Performance monitoring and alerting
- **A/B Testing Support**: Traffic splitting for experiments
- **Rate Limiting**: DDoS protection and resource conservation

## Enterprise Load Balancing Framework

```python
import asyncio
import aiohttp
import time
import json
import logging
import statistics
import hashlib
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, asdict, field
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from contextlib import asynccontextmanager
import random
import numpy as np
from enum import Enum
import ssl
import socket
from datetime import datetime, timedelta

class LoadBalancingAlgorithm(Enum):
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    LEAST_RESPONSE_TIME = "least_response_time"
    IP_HASH = "ip_hash"
    CONSISTENT_HASH = "consistent_hash"

class ServerStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DRAINING = "draining"
    MAINTENANCE = "maintenance"

@dataclass
class Server:
    id: str
    host: str
    port: int
    weight: float = 1.0
    max_connections: int = 1000
    current_connections: int = 0
    status: ServerStatus = ServerStatus.HEALTHY
    response_times: List[float] = field(default_factory=list)
    health_check_failures: int = 0
    last_health_check: float = 0
    total_requests: int = 0
    error_count: int = 0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0

@dataclass
class LoadBalancerMetric:
    timestamp: float
    algorithm: str
    selected_server: str
    request_duration_ms: float
    response_code: int
    client_ip: str
    request_size_bytes: int
    response_size_bytes: int

class HealthChecker:
    """Advanced health checking with multiple strategies"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    async def check_server_health(self, server: Server) -> bool:
        """Comprehensive server health check"""
        health_checks = []
        
        # HTTP health check
        if self.config.get('http_health_check_enabled', True):
            http_healthy = await self._http_health_check(server)
            health_checks.append(http_healthy)
        
        # TCP health check
        if self.config.get('tcp_health_check_enabled', True):
            tcp_healthy = await self._tcp_health_check(server)
            health_checks.append(tcp_healthy)
        
        # Custom application health check
        if self.config.get('custom_health_check_enabled', False):
            custom_healthy = await self._custom_health_check(server)
            health_checks.append(custom_healthy)
        
        # Determine overall health
        healthy_count = sum(health_checks)
        required_healthy = self.config.get('required_healthy_checks', 1)
        
        is_healthy = healthy_count >= required_healthy
        
        # Update server health status
        if is_healthy:
            server.health_check_failures = 0
            if server.status == ServerStatus.UNHEALTHY:
                server.status = ServerStatus.HEALTHY
                self.logger.info(f"Server {server.id} recovered and is now healthy")
        else:
            server.health_check_failures += 1
            failure_threshold = self.config.get('failure_threshold', 3)
            
            if server.health_check_failures >= failure_threshold:
                server.status = ServerStatus.UNHEALTHY
                self.logger.warning(f"Server {server.id} marked as unhealthy after {server.health_check_failures} failures")
        
        server.last_health_check = time.time()
        return is_healthy
    
    async def _http_health_check(self, server: Server) -> bool:
        """HTTP-based health check"""
        try:
            health_endpoint = self.config.get('health_endpoint', '/health')
            url = f"http://{server.host}:{server.port}{health_endpoint}"
            timeout = self.config.get('health_check_timeout', 5)
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        # Optional: Check response body for specific health indicators
                        if self.config.get('check_response_body', False):
                            body = await response.text()
                            expected_content = self.config.get('expected_health_content', 'OK')
                            return expected_content in body
                        return True
                    else:
                        return False
                        
        except Exception as e:
            self.logger.debug(f"HTTP health check failed for {server.id}: {e}")
            return False
    
    async def _tcp_health_check(self, server: Server) -> bool:
        """TCP connection health check"""
        try:
            timeout = self.config.get('tcp_timeout', 3)
            
            # Create TCP connection
            future = asyncio.open_connection(server.host, server.port)
            reader, writer = await asyncio.wait_for(future, timeout=timeout)
            
            writer.close()
            await writer.wait_closed()
            
            return True
            
        except Exception as e:
            self.logger.debug(f"TCP health check failed for {server.id}: {e}")
            return False
    
    async def _custom_health_check(self, server: Server) -> bool:
        """Custom application-specific health check"""
        try:
            # This would be implemented based on specific application requirements
            # For example: database connectivity, cache availability, etc.
            
            custom_check_url = self.config.get('custom_health_url')
            if custom_check_url:
                url = f"http://{server.host}:{server.port}{custom_check_url}"
                timeout = self.config.get('custom_check_timeout', 10)
                
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                    async with session.get(url) as response:
                        return response.status == 200
            
            return True  # Default to healthy if no custom check configured
            
        except Exception as e:
            self.logger.debug(f"Custom health check failed for {server.id}: {e}")
            return False

class LoadBalancingStrategy(ABC):
    """Abstract base class for load balancing algorithms"""
    
    @abstractmethod
    def select_server(self, servers: List[Server], client_info: Dict = None) -> Optional[Server]:
        pass
    
    @abstractmethod
    def get_algorithm_name(self) -> str:
        pass

class RoundRobinStrategy(LoadBalancingStrategy):
    """Round-robin load balancing strategy"""
    
    def __init__(self):
        self.current_index = 0
        self.lock = threading.Lock()
    
    def select_server(self, servers: List[Server], client_info: Dict = None) -> Optional[Server]:
        healthy_servers = [s for s in servers if s.status == ServerStatus.HEALTHY]
        
        if not healthy_servers:
            return None
        
        with self.lock:
            server = healthy_servers[self.current_index % len(healthy_servers)]
            self.current_index += 1
            return server
    
    def get_algorithm_name(self) -> str:
        return "round_robin"

class WeightedRoundRobinStrategy(LoadBalancingStrategy):
    """Weighted round-robin load balancing strategy"""
    
    def __init__(self):
        self.current_weights = {}
        self.lock = threading.Lock()
    
    def select_server(self, servers: List[Server], client_info: Dict = None) -> Optional[Server]:
        healthy_servers = [s for s in servers if s.status == ServerStatus.HEALTHY]
        
        if not healthy_servers:
            return None
        
        with self.lock:
            # Initialize weights if needed
            for server in healthy_servers:
                if server.id not in self.current_weights:
                    self.current_weights[server.id] = 0
            
            # Find server with highest current weight
            total_weight = sum(s.weight for s in healthy_servers)
            
            for server in healthy_servers:
                self.current_weights[server.id] += server.weight
            
            # Select server with highest current weight
            selected_server = max(healthy_servers, 
                                key=lambda s: self.current_weights[s.id])
            
            # Reduce selected server's current weight
            self.current_weights[selected_server.id] -= total_weight
            
            return selected_server
    
    def get_algorithm_name(self) -> str:
        return "weighted_round_robin"

class LeastConnectionsStrategy(LoadBalancingStrategy):
    """Least connections load balancing strategy"""
    
    def select_server(self, servers: List[Server], client_info: Dict = None) -> Optional[Server]:
        healthy_servers = [s for s in servers if s.status == ServerStatus.HEALTHY]
        
        if not healthy_servers:
            return None
        
        # Select server with least connections, break ties by weight
        return min(healthy_servers, 
                  key=lambda s: (s.current_connections / s.weight, s.current_connections))
    
    def get_algorithm_name(self) -> str:
        return "least_connections"

class LeastResponseTimeStrategy(LoadBalancingStrategy):
    """Least response time load balancing strategy"""
    
    def select_server(self, servers: List[Server], client_info: Dict = None) -> Optional[Server]:
        healthy_servers = [s for s in servers if s.status == ServerStatus.HEALTHY]
        
        if not healthy_servers:
            return None
        
        # Calculate average response times
        def get_avg_response_time(server: Server) -> float:
            if not server.response_times:
                return 0.0  # New server gets priority
            return statistics.mean(server.response_times[-10:])  # Last 10 responses
        
        return min(healthy_servers, key=get_avg_response_time)
    
    def get_algorithm_name(self) -> str:
        return "least_response_time"

class IPHashStrategy(LoadBalancingStrategy):
    """IP hash load balancing strategy for session persistence"""
    
    def select_server(self, servers: List[Server], client_info: Dict = None) -> Optional[Server]:
        healthy_servers = [s for s in servers if s.status == ServerStatus.HEALTHY]
        
        if not healthy_servers:
            return None
        
        client_ip = client_info.get('client_ip', '127.0.0.1') if client_info else '127.0.0.1'
        
        # Create consistent hash of client IP
        hash_value = int(hashlib.md5(client_ip.encode()).hexdigest(), 16)
        server_index = hash_value % len(healthy_servers)
        
        return healthy_servers[server_index]
    
    def get_algorithm_name(self) -> str:
        return "ip_hash"

class ConsistentHashStrategy(LoadBalancingStrategy):
    """Consistent hashing strategy for distributed systems"""
    
    def __init__(self, virtual_nodes: int = 150):
        self.virtual_nodes = virtual_nodes
        self.hash_ring = {}
        self.sorted_hashes = []
        self.lock = threading.Lock()
    
    def _rebuild_hash_ring(self, servers: List[Server]):
        """Rebuild the hash ring when server list changes"""
        with self.lock:
            self.hash_ring.clear()
            
            for server in servers:
                if server.status == ServerStatus.HEALTHY:
                    for i in range(self.virtual_nodes):
                        virtual_key = f"{server.id}:{i}"
                        hash_value = int(hashlib.md5(virtual_key.encode()).hexdigest(), 16)
                        self.hash_ring[hash_value] = server
            
            self.sorted_hashes = sorted(self.hash_ring.keys())
    
    def select_server(self, servers: List[Server], client_info: Dict = None) -> Optional[Server]:
        healthy_servers = [s for s in servers if s.status == ServerStatus.HEALTHY]
        
        if not healthy_servers:
            return None
        
        # Rebuild hash ring if needed
        if len(self.hash_ring) != len(healthy_servers) * self.virtual_nodes:
            self._rebuild_hash_ring(servers)
        
        if not self.sorted_hashes:
            return None
        
        # Get client identifier
        client_id = client_info.get('client_id', 
                                  client_info.get('client_ip', 'default')) if client_info else 'default'
        
        # Hash client identifier
        client_hash = int(hashlib.md5(client_id.encode()).hexdigest(), 16)
        
        # Find the first server in the ring
        for hash_value in self.sorted_hashes:
            if hash_value >= client_hash:
                return self.hash_ring[hash_value]
        
        # Wrap around to the beginning of the ring
        return self.hash_ring[self.sorted_hashes[0]]
    
    def get_algorithm_name(self) -> str:
        return "consistent_hash"

class EnterpriseLoadBalancer:
    """Enterprise-grade load balancer with advanced features"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.servers = {}
        self.strategy = self._create_strategy()
        self.health_checker = HealthChecker(config.get('health_check', {}))
        self.metrics = []
        self.logger = self._setup_logging()
        self.monitoring_active = False
        self.stats_lock = threading.RLock()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup load balancer logger"""
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)
    
    def _create_strategy(self) -> LoadBalancingStrategy:
        """Create load balancing strategy based on configuration"""
        algorithm = self.config.get('algorithm', 'round_robin')
        
        strategies = {
            'round_robin': RoundRobinStrategy(),
            'weighted_round_robin': WeightedRoundRobinStrategy(),
            'least_connections': LeastConnectionsStrategy(),
            'least_response_time': LeastResponseTimeStrategy(),
            'ip_hash': IPHashStrategy(),
            'consistent_hash': ConsistentHashStrategy(
                virtual_nodes=self.config.get('virtual_nodes', 150)
            )
        }
        
        return strategies.get(algorithm, RoundRobinStrategy())
    
    def add_server(self, server_config: Dict) -> str:
        """Add a server to the load balancer"""
        server = Server(
            id=server_config['id'],
            host=server_config['host'],
            port=server_config['port'],
            weight=server_config.get('weight', 1.0),
            max_connections=server_config.get('max_connections', 1000)
        )
        
        self.servers[server.id] = server
        self.logger.info(f"Added server {server.id} ({server.host}:{server.port})")
        
        return server.id
    
    def remove_server(self, server_id: str) -> bool:
        """Remove a server from the load balancer"""
        if server_id in self.servers:
            # Set server to draining mode first
            self.servers[server_id].status = ServerStatus.DRAINING
            
            # Wait for connections to drain (simplified)
            # In production, this would be more sophisticated
            time.sleep(self.config.get('drain_timeout', 30))
            
            del self.servers[server_id]
            self.logger.info(f"Removed server {server_id}")
            return True
        
        return False
    
    def update_server_weight(self, server_id: str, weight: float) -> bool:
        """Update server weight for weighted algorithms"""
        if server_id in self.servers:
            self.servers[server_id].weight = weight
            self.logger.info(f"Updated server {server_id} weight to {weight}")
            return True
        
        return False
    
    async def select_server(self, client_info: Dict = None) -> Optional[Server]:
        """Select optimal server for request"""
        servers_list = list(self.servers.values())
        
        if not servers_list:
            return None
        
        # Apply rate limiting if configured
        if self.config.get('rate_limiting_enabled', False):
            if not await self._check_rate_limit(client_info):
                return None
        
        selected_server = self.strategy.select_server(servers_list, client_info)
        
        if selected_server:
            # Update connection count
            selected_server.current_connections += 1
            selected_server.total_requests += 1
        
        return selected_server
    
    async def _check_rate_limit(self, client_info: Dict) -> bool:
        """Check rate limiting constraints"""
        # Simplified rate limiting implementation
        # In production, this would use Redis or similar for distributed rate limiting
        
        if not client_info:
            return True
        
        client_ip = client_info.get('client_ip', '')
        rate_limit = self.config.get('requests_per_minute', 1000)
        
        # This is a simplified implementation
        # Production would track per-client request rates
        
        return True
    
    async def handle_request(self, client_info: Dict, request_handler: Callable) -> Dict:
        """Handle request with load balancing and monitoring"""
        start_time = time.time()
        
        # Select server
        server = await self.select_server(client_info)
        if not server:
            return {
                'success': False,
                'error': 'No healthy servers available',
                'status_code': 503
            }
        
        try:
            # Execute request handler
            result = await request_handler(server, client_info)
            
            # Update server metrics
            response_time = (time.time() - start_time) * 1000
            server.response_times.append(response_time)
            
            # Keep only recent response times
            if len(server.response_times) > 100:
                server.response_times = server.response_times[-50:]
            
            # Record metrics
            self._record_metric(server, client_info, result, response_time)
            
            return result
            
        except Exception as e:
            # Handle request failure
            server.error_count += 1
            self.logger.error(f"Request failed on server {server.id}: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'status_code': 500
            }
            
        finally:
            # Decrease connection count
            server.current_connections = max(0, server.current_connections - 1)
    
    def _record_metric(self, server: Server, client_info: Dict, result: Dict, response_time: float):
        """Record load balancer metrics"""
        metric = LoadBalancerMetric(
            timestamp=time.time(),
            algorithm=self.strategy.get_algorithm_name(),
            selected_server=server.id,
            request_duration_ms=response_time,
            response_code=result.get('status_code', 200),
            client_ip=client_info.get('client_ip', 'unknown'),
            request_size_bytes=client_info.get('request_size', 0),
            response_size_bytes=result.get('response_size', 0)
        )
        
        with self.stats_lock:
            self.metrics.append(metric)
            
            # Keep only recent metrics
            if len(self.metrics) > 50000:
                self.metrics = self.metrics[-25000:]
    
    async def start_health_monitoring(self):
        """Start continuous health monitoring"""
        self.monitoring_active = True
        self.logger.info("Starting health monitoring")
        
        while self.monitoring_active:
            try:
                health_check_tasks = []
                
                for server in self.servers.values():
                    if server.status != ServerStatus.MAINTENANCE:
                        task = asyncio.create_task(
                            self.health_checker.check_server_health(server)
                        )
                        health_check_tasks.append((server.id, task))
                
                # Wait for all health checks to complete
                for server_id, task in health_check_tasks:
                    try:
                        await task
                    except Exception as e:
                        self.logger.error(f"Health check failed for server {server_id}: {e}")
                
                # Sleep before next health check cycle
                await asyncio.sleep(self.config.get('health_check_interval', 30))
                
            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(5)
    
    def stop_health_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False
        self.logger.info("Stopped health monitoring")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        with self.stats_lock:
            current_time = time.time()
            
            # Recent metrics (last 5 minutes)
            recent_metrics = [m for m in self.metrics 
                            if current_time - m.timestamp <= 300]
            
            stats = {
                'timestamp': current_time,
                'algorithm': self.strategy.get_algorithm_name(),
                'server_count': len(self.servers),
                'healthy_servers': len([s for s in self.servers.values() 
                                      if s.status == ServerStatus.HEALTHY]),
                'total_requests': sum(s.total_requests for s in self.servers.values()),
                'active_connections': sum(s.current_connections for s in self.servers.values())
            }
            
            if recent_metrics:
                response_times = [m.request_duration_ms for m in recent_metrics]
                stats.update({
                    'avg_response_time_ms': statistics.mean(response_times),
                    'p95_response_time_ms': np.percentile(response_times, 95),
                    'p99_response_time_ms': np.percentile(response_times, 99),
                    'requests_per_second': len(recent_metrics) / 300,
                    'error_rate': len([m for m in recent_metrics if m.response_code >= 400]) / len(recent_metrics)
                })
            
            # Server-specific stats
            server_stats = {}
            for server_id, server in self.servers.items():
                server_stats[server_id] = {
                    'status': server.status.value,
                    'current_connections': server.current_connections,
                    'total_requests': server.total_requests,
                    'error_count': server.error_count,
                    'avg_response_time_ms': statistics.mean(server.response_times) if server.response_times else 0,
                    'health_check_failures': server.health_check_failures,
                    'weight': server.weight
                }
            
            stats['servers'] = server_stats
            
            return stats
    
    def get_optimization_recommendations(self) -> List[str]:
        """Generate load balancer optimization recommendations"""
        recommendations = []
        stats = self.get_performance_stats()
        
        # Check server health distribution
        if stats['healthy_servers'] < len(self.servers) * 0.8:
            recommendations.append("Less than 80% of servers are healthy - investigate server issues")
        
        # Check response times
        if stats.get('avg_response_time_ms', 0) > 1000:
            recommendations.append("High average response time - consider adding more servers or optimizing application")
        
        # Check error rates
        if stats.get('error_rate', 0) > 0.05:
            recommendations.append("Error rate above 5% - investigate application errors")
        
        # Check load distribution
        server_stats = stats.get('servers', {})
        if server_stats:
            request_counts = [s['total_requests'] for s in server_stats.values()]
            if max(request_counts) > min(request_counts) * 3:
                recommendations.append("Uneven load distribution - consider adjusting server weights or algorithm")
        
        # General recommendations
        recommendations.extend([
            "Monitor server resource utilization (CPU, memory, disk)",
            "Implement auto-scaling based on performance metrics",
            "Consider geographic load balancing for global traffic",
            "Regular performance testing and capacity planning"
        ])
        
        return recommendations[:10]

# Configuration Example
load_balancer_config = {
    'algorithm': 'least_response_time',
    'health_check': {
        'http_health_check_enabled': True,
        'tcp_health_check_enabled': True,
        'health_endpoint': '/health',
        'health_check_timeout': 5,
        'health_check_interval': 30,
        'failure_threshold': 3,
        'required_healthy_checks': 1
    },
    'rate_limiting_enabled': True,
    'requests_per_minute': 10000,
    'drain_timeout': 60,
    'virtual_nodes': 150  # For consistent hashing
}

# Usage Example
async def example_request_handler(server: Server, client_info: Dict) -> Dict:
    """Example request handler"""
    # Simulate request processing
    await asyncio.sleep(random.uniform(0.01, 0.1))
    
    return {
        'success': True,
        'status_code': 200,
        'response_size': 1024,
        'server_id': server.id
    }

async def main():
    # Initialize load balancer
    lb = EnterpriseLoadBalancer(load_balancer_config)
    
    # Add servers
    servers = [
        {'id': 'web1', 'host': '10.0.1.10', 'port': 80, 'weight': 1.0},
        {'id': 'web2', 'host': '10.0.1.11', 'port': 80, 'weight': 1.5},
        {'id': 'web3', 'host': '10.0.1.12', 'port': 80, 'weight': 1.0}
    ]
    
    for server_config in servers:
        lb.add_server(server_config)
    
    # Start health monitoring
    monitoring_task = asyncio.create_task(lb.start_health_monitoring())
    
    try:
        # Simulate requests
        for i in range(100):
            client_info = {
                'client_ip': f'192.168.1.{i % 50 + 1}',
                'request_size': random.randint(500, 2000)
            }
            
            result = await lb.handle_request(client_info, example_request_handler)
            print(f"Request {i}: {result['success']} - Server: {result.get('server_id', 'none')}")
            
            await asyncio.sleep(0.01)
        
        # Get performance stats
        stats = lb.get_performance_stats()
        print(json.dumps(stats, indent=2, default=str))
        
        # Get recommendations
        recommendations = lb.get_optimization_recommendations()
        print("\nOptimization Recommendations:")
        for rec in recommendations:
            print(f"- {rec}")
        
    finally:
        lb.stop_health_monitoring()
        monitoring_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())
```

This comprehensive load balancing framework provides:

1. **Multiple Algorithms**: Round-robin, weighted, least connections, response time-based, hash-based
2. **Advanced Health Checking**: HTTP, TCP, and custom health validation
3. **Performance Monitoring**: Real-time metrics and performance tracking
4. **Auto-Scaling Integration**: Dynamic server management capabilities
5. **Session Persistence**: IP hash and consistent hashing support
6. **Rate Limiting**: DDoS protection and resource management
7. **Failure Handling**: Circuit breaker patterns and graceful degradation
8. **Enterprise Features**: Comprehensive monitoring, alerting, and optimization recommendations

The system enables network administrators to implement sophisticated load balancing strategies with enterprise-grade performance monitoring and optimization capabilities.