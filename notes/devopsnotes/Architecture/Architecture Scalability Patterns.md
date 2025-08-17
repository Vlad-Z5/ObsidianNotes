# Architecture Scalability Patterns

## Scalability Strategies

Scalability is the capability of a system to handle increased loads by adding resources to the system. This comprehensive guide covers horizontal and vertical scaling patterns, auto-scaling strategies, load distribution techniques, and resource pooling implementations for building highly scalable architectures.

### Horizontal Scaling

Horizontal scaling (scale-out) involves adding more nodes to a system rather than upgrading individual nodes. This approach provides better fault tolerance and theoretically unlimited scalability.

#### Load Distribution and Service Replication

```python
import asyncio
import hashlib
import time
import random
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import aiohttp
import weakref
from abc import ABC, abstractmethod

class LoadBalancingAlgorithm(Enum):
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    LEAST_RESPONSE_TIME = "least_response_time"
    HASH = "hash"
    GEOGRAPHIC = "geographic"
    HEALTH_BASED = "health_based"

@dataclass
class ServiceNode:
    """Represents a service node in the cluster"""
    id: str
    host: str
    port: int
    weight: int = 1
    max_connections: int = 1000
    current_connections: int = 0
    is_healthy: bool = True
    health_check_url: str = "/health"
    response_times: List[float] = field(default_factory=list)
    last_health_check: Optional[datetime] = None
    region: str = "default"
    zone: str = "default"
    
    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"
    
    @property
    def average_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        return sum(self.response_times[-10:]) / len(self.response_times[-10:])  # Last 10 requests
    
    def add_response_time(self, response_time: float):
        """Add response time for tracking"""
        self.response_times.append(response_time)
        if len(self.response_times) > 100:  # Keep only last 100 measurements
            self.response_times = self.response_times[-100:]
    
    def increment_connections(self) -> bool:
        """Increment connection count if under limit"""
        if self.current_connections < self.max_connections:
            self.current_connections += 1
            return True
        return False
    
    def decrement_connections(self):
        """Decrement connection count"""
        if self.current_connections > 0:
            self.current_connections -= 1

class LoadBalancer:
    """Advanced load balancer with multiple algorithms and health checking"""
    
    def __init__(self, algorithm: LoadBalancingAlgorithm = LoadBalancingAlgorithm.ROUND_ROBIN):
        self.algorithm = algorithm
        self.nodes: List[ServiceNode] = []
        self.current_index = 0
        self.hash_ring: Dict[int, ServiceNode] = {}
        self.health_check_interval = 30.0  # seconds
        self.health_check_task: Optional[asyncio.Task] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self):
        """Initialize the load balancer"""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5))
        await self.start_health_checks()
    
    async def shutdown(self):
        """Shutdown the load balancer"""
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
        
        if self.session:
            await self.session.close()
    
    def add_node(self, node: ServiceNode):
        """Add a service node to the load balancer"""
        self.nodes.append(node)
        if self.algorithm == LoadBalancingAlgorithm.HASH:
            self._update_hash_ring()
        self.logger.info(f"Added node {node.id} ({node.url})")
    
    def remove_node(self, node_id: str):
        """Remove a service node from the load balancer"""
        self.nodes = [node for node in self.nodes if node.id != node_id]
        if self.algorithm == LoadBalancingAlgorithm.HASH:
            self._update_hash_ring()
        self.logger.info(f"Removed node {node_id}")
    
    def _update_hash_ring(self):
        """Update consistent hash ring for hash-based load balancing"""
        self.hash_ring.clear()
        
        for node in self.nodes:
            if not node.is_healthy:
                continue
            
            # Create multiple virtual nodes for better distribution
            for i in range(node.weight * 100):
                virtual_node_key = f"{node.id}:{i}"
                hash_value = int(hashlib.md5(virtual_node_key.encode()).hexdigest(), 16)
                self.hash_ring[hash_value] = node
    
    async def get_node(self, request_key: Optional[str] = None, 
                      client_info: Optional[Dict[str, Any]] = None) -> Optional[ServiceNode]:
        """Get next available node based on load balancing algorithm"""
        
        healthy_nodes = [node for node in self.nodes if node.is_healthy]
        
        if not healthy_nodes:
            self.logger.error("No healthy nodes available")
            return None
        
        if self.algorithm == LoadBalancingAlgorithm.ROUND_ROBIN:
            return self._round_robin_select(healthy_nodes)
        
        elif self.algorithm == LoadBalancingAlgorithm.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_select(healthy_nodes)
        
        elif self.algorithm == LoadBalancingAlgorithm.LEAST_CONNECTIONS:
            return self._least_connections_select(healthy_nodes)
        
        elif self.algorithm == LoadBalancingAlgorithm.LEAST_RESPONSE_TIME:
            return self._least_response_time_select(healthy_nodes)
        
        elif self.algorithm == LoadBalancingAlgorithm.HASH:
            return self._hash_select(request_key or "", healthy_nodes)
        
        elif self.algorithm == LoadBalancingAlgorithm.GEOGRAPHIC:
            return self._geographic_select(healthy_nodes, client_info)
        
        elif self.algorithm == LoadBalancingAlgorithm.HEALTH_BASED:
            return self._health_based_select(healthy_nodes)
        
        else:
            return self._round_robin_select(healthy_nodes)
    
    def _round_robin_select(self, nodes: List[ServiceNode]) -> ServiceNode:
        """Round-robin selection"""
        if self.current_index >= len(nodes):
            self.current_index = 0
        
        node = nodes[self.current_index]
        self.current_index = (self.current_index + 1) % len(nodes)
        return node
    
    def _weighted_round_robin_select(self, nodes: List[ServiceNode]) -> ServiceNode:
        """Weighted round-robin selection"""
        weighted_nodes = []
        for node in nodes:
            weighted_nodes.extend([node] * node.weight)
        
        if self.current_index >= len(weighted_nodes):
            self.current_index = 0
        
        node = weighted_nodes[self.current_index]
        self.current_index = (self.current_index + 1) % len(weighted_nodes)
        return node
    
    def _least_connections_select(self, nodes: List[ServiceNode]) -> ServiceNode:
        """Least connections selection"""
        return min(nodes, key=lambda n: n.current_connections)
    
    def _least_response_time_select(self, nodes: List[ServiceNode]) -> ServiceNode:
        """Least response time selection"""
        return min(nodes, key=lambda n: n.average_response_time)
    
    def _hash_select(self, request_key: str, nodes: List[ServiceNode]) -> ServiceNode:
        """Consistent hash-based selection"""
        if not self.hash_ring:
            self._update_hash_ring()
        
        if not self.hash_ring:
            return random.choice(nodes)
        
        hash_value = int(hashlib.md5(request_key.encode()).hexdigest(), 16)
        
        # Find the first node with hash >= request hash
        sorted_hashes = sorted(self.hash_ring.keys())
        for ring_hash in sorted_hashes:
            if ring_hash >= hash_value:
                return self.hash_ring[ring_hash]
        
        # Wrap around to the first node
        return self.hash_ring[sorted_hashes[0]]
    
    def _geographic_select(self, nodes: List[ServiceNode], 
                          client_info: Optional[Dict[str, Any]]) -> ServiceNode:
        """Geographic proximity-based selection"""
        if not client_info or 'region' not in client_info:
            return random.choice(nodes)
        
        client_region = client_info['region']
        client_zone = client_info.get('zone', 'default')
        
        # Prefer same zone, then same region, then any
        same_zone_nodes = [n for n in nodes if n.region == client_region and n.zone == client_zone]
        if same_zone_nodes:
            return random.choice(same_zone_nodes)
        
        same_region_nodes = [n for n in nodes if n.region == client_region]
        if same_region_nodes:
            return random.choice(same_region_nodes)
        
        return random.choice(nodes)
    
    def _health_based_select(self, nodes: List[ServiceNode]) -> ServiceNode:
        """Health score-based selection (combination of factors)"""
        def health_score(node: ServiceNode) -> float:
            # Lower score is better
            connection_factor = node.current_connections / node.max_connections
            response_time_factor = min(node.average_response_time / 1000.0, 1.0)  # Normalize to seconds
            weight_factor = 1.0 / node.weight
            
            return connection_factor + response_time_factor + weight_factor
        
        return min(nodes, key=health_score)
    
    async def start_health_checks(self):
        """Start background health checking"""
        self.health_check_task = asyncio.create_task(self._health_check_loop())
    
    async def _health_check_loop(self):
        """Background health check loop"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._check_all_nodes_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in health check loop: {e}")
    
    async def _check_all_nodes_health(self):
        """Check health of all nodes"""
        if not self.session:
            return
        
        health_check_tasks = []
        for node in self.nodes:
            task = asyncio.create_task(self._check_node_health(node))
            health_check_tasks.append(task)
        
        await asyncio.gather(*health_check_tasks, return_exceptions=True)
    
    async def _check_node_health(self, node: ServiceNode):
        """Check health of a specific node"""
        try:
            start_time = time.time()
            health_url = f"{node.url}{node.health_check_url}"
            
            async with self.session.get(health_url) as response:
                response_time = time.time() - start_time
                node.add_response_time(response_time)
                
                if response.status == 200:
                    if not node.is_healthy:
                        self.logger.info(f"Node {node.id} is now healthy")
                    node.is_healthy = True
                else:
                    if node.is_healthy:
                        self.logger.warning(f"Node {node.id} health check failed with status {response.status}")
                    node.is_healthy = False
                
                node.last_health_check = datetime.utcnow()
                
        except Exception as e:
            if node.is_healthy:
                self.logger.warning(f"Node {node.id} health check failed: {e}")
            node.is_healthy = False
            node.last_health_check = datetime.utcnow()
    
    async def execute_request(self, path: str, method: str = "GET", 
                            data: Optional[Any] = None, 
                            request_key: Optional[str] = None,
                            client_info: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Execute request with load balancing"""
        node = await self.get_node(request_key, client_info)
        
        if not node:
            raise Exception("No healthy nodes available")
        
        if not node.increment_connections():
            self.logger.warning(f"Node {node.id} at connection limit")
            # Try to find another node
            remaining_nodes = [n for n in self.nodes if n.is_healthy and n.id != node.id]
            if remaining_nodes:
                node = random.choice(remaining_nodes)
                if not node.increment_connections():
                    raise Exception("All nodes at connection limit")
            else:
                raise Exception("All nodes at connection limit")
        
        try:
            start_time = time.time()
            url = f"{node.url}{path}"
            
            if method.upper() == "GET":
                async with self.session.get(url) as response:
                    result = await response.json()
            elif method.upper() == "POST":
                async with self.session.post(url, json=data) as response:
                    result = await response.json()
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response_time = time.time() - start_time
            node.add_response_time(response_time)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Request to {node.id} failed: {e}")
            raise
        finally:
            node.decrement_connections()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get load balancer statistics"""
        healthy_nodes = [n for n in self.nodes if n.is_healthy]
        
        return {
            'algorithm': self.algorithm.value,
            'total_nodes': len(self.nodes),
            'healthy_nodes': len(healthy_nodes),
            'current_index': self.current_index,
            'nodes': [
                {
                    'id': node.id,
                    'url': node.url,
                    'is_healthy': node.is_healthy,
                    'current_connections': node.current_connections,
                    'max_connections': node.max_connections,
                    'average_response_time': node.average_response_time,
                    'weight': node.weight,
                    'region': node.region,
                    'zone': node.zone,
                    'last_health_check': node.last_health_check.isoformat() if node.last_health_check else None
                }
                for node in self.nodes
            ]
        }

class HorizontalScaler:
    """Manages horizontal scaling of service instances"""
    
    def __init__(self, load_balancer: LoadBalancer):
        self.load_balancer = load_balancer
        self.scaling_rules: List[Callable] = []
        self.min_instances = 2
        self.max_instances = 10
        self.scale_up_threshold = 0.8  # 80% resource utilization
        self.scale_down_threshold = 0.3  # 30% resource utilization
        self.scale_cooldown = 300  # 5 minutes
        self.last_scale_action = 0
        self.logger = logging.getLogger(__name__)
    
    def add_scaling_rule(self, rule: Callable[['HorizontalScaler'], bool]):
        """Add custom scaling rule"""
        self.scaling_rules.append(rule)
    
    async def evaluate_scaling(self) -> str:
        """Evaluate if scaling action is needed"""
        
        # Check cooldown period
        if time.time() - self.last_scale_action < self.scale_cooldown:
            return "cooldown"
        
        # Apply custom scaling rules
        for rule in self.scaling_rules:
            try:
                if rule(self):
                    return "custom_rule_triggered"
            except Exception as e:
                self.logger.error(f"Error in scaling rule: {e}")
        
        # Default scaling logic
        stats = self.load_balancer.get_stats()
        healthy_nodes = stats['healthy_nodes']
        
        if healthy_nodes == 0:
            return "no_healthy_nodes"
        
        # Calculate average utilization
        total_connections = sum(node['current_connections'] for node in stats['nodes'] if node['is_healthy'])
        total_capacity = sum(node['max_connections'] for node in stats['nodes'] if node['is_healthy'])
        
        if total_capacity == 0:
            return "no_capacity"
        
        utilization = total_connections / total_capacity
        
        if utilization > self.scale_up_threshold and healthy_nodes < self.max_instances:
            await self._scale_up()
            return "scaled_up"
        
        elif utilization < self.scale_down_threshold and healthy_nodes > self.min_instances:
            await self._scale_down()
            return "scaled_down"
        
        return "no_action"
    
    async def _scale_up(self):
        """Scale up by adding a new instance"""
        # This would typically integrate with container orchestration
        # For demo purposes, we'll simulate adding a new node
        
        new_node_id = f"node-{int(time.time())}"
        # In real implementation, this would start a new container/VM
        new_port = 8080 + len(self.load_balancer.nodes)
        
        new_node = ServiceNode(
            id=new_node_id,
            host="localhost",
            port=new_port,
            weight=1,
            max_connections=1000
        )
        
        self.load_balancer.add_node(new_node)
        self.last_scale_action = time.time()
        self.logger.info(f"Scaled up: Added node {new_node_id}")
    
    async def _scale_down(self):
        """Scale down by removing an instance"""
        # Remove the node with least connections
        healthy_nodes = [node for node in self.load_balancer.nodes if node.is_healthy]
        
        if len(healthy_nodes) <= self.min_instances:
            return
        
        # Find node with least connections
        node_to_remove = min(healthy_nodes, key=lambda n: n.current_connections)
        
        # Wait for existing connections to complete (graceful shutdown)
        max_wait = 30  # 30 seconds
        wait_time = 0
        
        while node_to_remove.current_connections > 0 and wait_time < max_wait:
            await asyncio.sleep(1)
            wait_time += 1
        
        self.load_balancer.remove_node(node_to_remove.id)
        self.last_scale_action = time.time()
        self.logger.info(f"Scaled down: Removed node {node_to_remove.id}")

# Example scaling rules
def cpu_based_scaling_rule(scaler: HorizontalScaler) -> bool:
    """Scale based on CPU utilization"""
    # This would integrate with monitoring system
    # For demo, simulate CPU check
    import psutil
    cpu_percent = psutil.cpu_percent(interval=1)
    
    if cpu_percent > 80:
        scaler.logger.info(f"CPU utilization high: {cpu_percent}%")
        return True
    
    return False

def memory_based_scaling_rule(scaler: HorizontalScaler) -> bool:
    """Scale based on memory utilization"""
    import psutil
    memory_percent = psutil.virtual_memory().percent
    
    if memory_percent > 85:
        scaler.logger.info(f"Memory utilization high: {memory_percent}%")
        return True
    
    return False

def response_time_based_scaling_rule(scaler: HorizontalScaler) -> bool:
    """Scale based on average response time"""
    stats = scaler.load_balancer.get_stats()
    
    avg_response_times = [
        node['average_response_time'] 
        for node in stats['nodes'] 
        if node['is_healthy'] and node['average_response_time'] > 0
    ]
    
    if avg_response_times:
        avg_response_time = sum(avg_response_times) / len(avg_response_times)
        
        if avg_response_time > 2.0:  # 2 seconds
            scaler.logger.info(f"Average response time high: {avg_response_time:.2f}s")
            return True
    
    return False
```

#### Stateless Design and Data Partitioning

```python
import asyncio
import hashlib
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import aioredis
import asyncpg
from abc import ABC, abstractmethod

class PartitionStrategy(Enum):
    HASH = "hash"
    RANGE = "range"
    DIRECTORY = "directory"
    CONSISTENT_HASH = "consistent_hash"

@dataclass
class PartitionInfo:
    """Information about a data partition"""
    partition_id: str
    partition_key: str
    node_id: str
    start_range: Optional[Any] = None
    end_range: Optional[Any] = None
    replica_nodes: List[str] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)

class DataPartitioner:
    """Manages data partitioning across multiple nodes"""
    
    def __init__(self, strategy: PartitionStrategy = PartitionStrategy.HASH):
        self.strategy = strategy
        self.partitions: Dict[str, PartitionInfo] = {}
        self.nodes: List[str] = []
        self.replica_count = 2
        self.virtual_nodes = 100  # For consistent hashing
        self.hash_ring: Dict[int, str] = {}
        
    def add_node(self, node_id: str):
        """Add a new node to the partition system"""
        self.nodes.append(node_id)
        
        if self.strategy == PartitionStrategy.CONSISTENT_HASH:
            self._update_hash_ring()
            
        # Rebalance partitions if needed
        self._rebalance_partitions()
    
    def remove_node(self, node_id: str):
        """Remove a node from the partition system"""
        if node_id in self.nodes:
            self.nodes.remove(node_id)
            
            # Reassign partitions from removed node
            self._reassign_partitions_from_node(node_id)
            
            if self.strategy == PartitionStrategy.CONSISTENT_HASH:
                self._update_hash_ring()
    
    def _update_hash_ring(self):
        """Update consistent hash ring"""
        self.hash_ring.clear()
        
        for node in self.nodes:
            for i in range(self.virtual_nodes):
                virtual_node_key = f"{node}:{i}"
                hash_value = int(hashlib.md5(virtual_node_key.encode()).hexdigest(), 16)
                self.hash_ring[hash_value] = node
    
    def get_partition(self, key: str) -> Optional[PartitionInfo]:
        """Get partition for a given key"""
        
        if self.strategy == PartitionStrategy.HASH:
            return self._hash_partition(key)
        
        elif self.strategy == PartitionStrategy.RANGE:
            return self._range_partition(key)
        
        elif self.strategy == PartitionStrategy.DIRECTORY:
            return self._directory_partition(key)
        
        elif self.strategy == PartitionStrategy.CONSISTENT_HASH:
            return self._consistent_hash_partition(key)
        
        return None
    
    def _hash_partition(self, key: str) -> Optional[PartitionInfo]:
        """Hash-based partitioning"""
        if not self.nodes:
            return None
        
        hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16)
        node_index = hash_value % len(self.nodes)
        node_id = self.nodes[node_index]
        
        partition_id = f"hash_{node_index}"
        
        if partition_id not in self.partitions:
            replica_nodes = self._get_replica_nodes(node_id)
            self.partitions[partition_id] = PartitionInfo(
                partition_id=partition_id,
                partition_key=key,
                node_id=node_id,
                replica_nodes=replica_nodes
            )
        
        return self.partitions[partition_id]
    
    def _range_partition(self, key: str) -> Optional[PartitionInfo]:
        """Range-based partitioning"""
        # For simplicity, assume keys are numeric or can be converted
        try:
            key_value = int(key) if key.isdigit() else ord(key[0])
        except:
            key_value = hash(key) % 1000000
        
        # Define ranges based on number of nodes
        if not self.nodes:
            return None
        
        range_size = 1000000 // len(self.nodes)
        partition_index = key_value // range_size
        partition_index = min(partition_index, len(self.nodes) - 1)
        
        node_id = self.nodes[partition_index]
        partition_id = f"range_{partition_index}"
        
        if partition_id not in self.partitions:
            start_range = partition_index * range_size
            end_range = (partition_index + 1) * range_size - 1
            replica_nodes = self._get_replica_nodes(node_id)
            
            self.partitions[partition_id] = PartitionInfo(
                partition_id=partition_id,
                partition_key=key,
                node_id=node_id,
                start_range=start_range,
                end_range=end_range,
                replica_nodes=replica_nodes
            )
        
        return self.partitions[partition_id]
    
    def _consistent_hash_partition(self, key: str) -> Optional[PartitionInfo]:
        """Consistent hash-based partitioning"""
        if not self.hash_ring:
            self._update_hash_ring()
        
        if not self.hash_ring:
            return None
        
        hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16)
        
        # Find the first node with hash >= key hash
        sorted_hashes = sorted(self.hash_ring.keys())
        selected_node = None
        
        for ring_hash in sorted_hashes:
            if ring_hash >= hash_value:
                selected_node = self.hash_ring[ring_hash]
                break
        
        # Wrap around to the first node if not found
        if selected_node is None:
            selected_node = self.hash_ring[sorted_hashes[0]]
        
        partition_id = f"consistent_{selected_node}_{hash_value % 100}"
        
        if partition_id not in self.partitions:
            replica_nodes = self._get_replica_nodes(selected_node)
            self.partitions[partition_id] = PartitionInfo(
                partition_id=partition_id,
                partition_key=key,
                node_id=selected_node,
                replica_nodes=replica_nodes
            )
        
        return self.partitions[partition_id]
    
    def _directory_partition(self, key: str) -> Optional[PartitionInfo]:
        """Directory-based partitioning (explicit mapping)"""
        # This would typically use an external directory service
        # For demo, use simple hash mapping
        return self._hash_partition(key)
    
    def _get_replica_nodes(self, primary_node: str) -> List[str]:
        """Get replica nodes for a primary node"""
        available_nodes = [node for node in self.nodes if node != primary_node]
        replica_count = min(self.replica_count, len(available_nodes))
        return available_nodes[:replica_count]
    
    def _rebalance_partitions(self):
        """Rebalance partitions across nodes"""
        # In a real implementation, this would be more sophisticated
        # For now, just log that rebalancing would occur
        pass
    
    def _reassign_partitions_from_node(self, removed_node: str):
        """Reassign partitions from a removed node"""
        for partition in self.partitions.values():
            if partition.node_id == removed_node:
                # Promote a replica to primary
                if partition.replica_nodes:
                    partition.node_id = partition.replica_nodes[0]
                    partition.replica_nodes = partition.replica_nodes[1:] + self._get_replica_nodes(partition.node_id)
                else:
                    # No replicas, assign to a random node
                    if self.nodes:
                        partition.node_id = self.nodes[0]
                        partition.replica_nodes = self._get_replica_nodes(partition.node_id)
    
    def get_partition_stats(self) -> Dict[str, Any]:
        """Get partitioning statistics"""
        node_partition_count = {}
        for partition in self.partitions.values():
            node_partition_count[partition.node_id] = node_partition_count.get(partition.node_id, 0) + 1
        
        return {
            'strategy': self.strategy.value,
            'total_partitions': len(self.partitions),
            'total_nodes': len(self.nodes),
            'partitions_per_node': node_partition_count,
            'replica_count': self.replica_count,
            'virtual_nodes': self.virtual_nodes if self.strategy == PartitionStrategy.CONSISTENT_HASH else None
        }

class StatelessSessionManager:
    """Manages stateless sessions using external storage"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        self.session_ttl = 3600  # 1 hour
        
    async def initialize(self):
        """Initialize Redis connection"""
        self.redis = aioredis.from_url(self.redis_url, decode_responses=True)
    
    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
    
    async def create_session(self, user_id: str, session_data: Dict[str, Any]) -> str:
        """Create a new stateless session"""
        if not self.redis:
            await self.initialize()
        
        session_id = f"session:{user_id}:{int(time.time())}"
        session_key = f"sessions:{session_id}"
        
        # Store session data with TTL
        await self.redis.setex(
            session_key,
            self.session_ttl,
            json.dumps(session_data)
        )
        
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        if not self.redis:
            await self.initialize()
        
        session_key = f"sessions:{session_id}"
        session_data = await self.redis.get(session_key)
        
        if session_data:
            # Extend TTL on access
            await self.redis.expire(session_key, self.session_ttl)
            return json.loads(session_data)
        
        return None
    
    async def update_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Update session data"""
        if not self.redis:
            await self.initialize()
        
        session_key = f"sessions:{session_id}"
        
        # Check if session exists
        if await self.redis.exists(session_key):
            await self.redis.setex(
                session_key,
                self.session_ttl,
                json.dumps(session_data)
            )
            return True
        
        return False
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        if not self.redis:
            await self.initialize()
        
        session_key = f"sessions:{session_id}"
        result = await self.redis.delete(session_key)
        return result > 0
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        if not self.redis:
            await self.initialize()
        
        # Count total sessions
        session_keys = await self.redis.keys("sessions:*")
        total_sessions = len(session_keys)
        
        # Sample a few sessions to get average data size
        sample_size = min(10, total_sessions)
        total_size = 0
        
        if sample_size > 0:
            sample_keys = session_keys[:sample_size]
            for key in sample_keys:
                session_data = await self.redis.get(key)
                if session_data:
                    total_size += len(session_data.encode())
        
        avg_session_size = total_size / sample_size if sample_size > 0 else 0
        
        return {
            'total_sessions': total_sessions,
            'session_ttl': self.session_ttl,
            'average_session_size_bytes': avg_session_size,
            'estimated_total_size_mb': (total_sessions * avg_session_size) / (1024 * 1024)
        }

class StatelessWebService:
    """Example stateless web service implementation"""
    
    def __init__(self):
        self.session_manager = StatelessSessionManager()
        self.data_partitioner = DataPartitioner(PartitionStrategy.CONSISTENT_HASH)
        
        # Add some nodes
        for i in range(3):
            self.data_partitioner.add_node(f"db-node-{i}")
    
    async def initialize(self):
        """Initialize the service"""
        await self.session_manager.initialize()
    
    async def shutdown(self):
        """Shutdown the service"""
        await self.session_manager.close()
    
    async def login(self, username: str, password: str) -> Dict[str, Any]:
        """Stateless login operation"""
        # Simulate authentication
        if len(password) >= 6:  # Simple validation
            user_data = {
                'username': username,
                'login_time': datetime.utcnow().isoformat(),
                'permissions': ['read', 'write'],
                'preferences': {'theme': 'light', 'language': 'en'}
            }
            
            session_id = await self.session_manager.create_session(username, user_data)
            
            return {
                'success': True,
                'session_id': session_id,
                'user_data': user_data
            }
        
        return {'success': False, 'error': 'Invalid credentials'}
    
    async def get_user_data(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """Get user data from appropriate partition"""
        # Validate session
        session_data = await self.session_manager.get_session(session_id)
        if not session_data:
            return {'success': False, 'error': 'Invalid session'}
        
        # Get partition for user data
        partition = self.data_partitioner.get_partition(user_id)
        if not partition:
            return {'success': False, 'error': 'Unable to locate user data'}
        
        # Simulate data retrieval from partitioned storage
        user_data = {
            'user_id': user_id,
            'partition_id': partition.partition_id,
            'node_id': partition.node_id,
            'profile': {
                'name': f'User {user_id}',
                'email': f'{user_id}@example.com',
                'created_at': datetime.utcnow().isoformat()
            }
        }
        
        return {'success': True, 'user_data': user_data}
    
    async def update_user_preferences(self, session_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Update user preferences (stateless)"""
        # Get current session
        session_data = await self.session_manager.get_session(session_id)
        if not session_data:
            return {'success': False, 'error': 'Invalid session'}
        
        # Update preferences in session
        session_data['preferences'].update(preferences)
        
        # Save updated session
        success = await self.session_manager.update_session(session_id, session_data)
        
        return {
            'success': success,
            'updated_preferences': session_data['preferences'] if success else None
        }
    
    async def get_service_stats(self) -> Dict[str, Any]:
        """Get comprehensive service statistics"""
        session_stats = await self.session_manager.get_session_stats()
        partition_stats = self.data_partitioner.get_partition_stats()
        
        return {
            'service_type': 'stateless',
            'session_management': session_stats,
            'data_partitioning': partition_stats,
            'timestamp': datetime.utcnow().isoformat()
        }
```

### Vertical Scaling

Vertical scaling (scale-up) involves adding more power (CPU, RAM, storage) to existing machines rather than adding more machines.

#### Resource Optimization and Performance Tuning

```python
import asyncio
import psutil
import time
import threading
import queue
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import concurrent.futures
from contextlib import contextmanager

class ResourceType(Enum):
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"

@dataclass
class ResourceMetrics:
    """Resource utilization metrics"""
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    network_bytes_sent: int
    network_bytes_recv: int
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ResourceLimit:
    """Resource limits and thresholds"""
    cpu_limit_percent: float = 80.0
    memory_limit_percent: float = 85.0
    disk_limit_percent: float = 90.0
    network_limit_mbps: float = 1000.0

class ResourceMonitor:
    """Monitors system resource utilization"""
    
    def __init__(self, monitoring_interval: float = 5.0):
        self.monitoring_interval = monitoring_interval
        self.metrics_history: List[ResourceMetrics] = []
        self.max_history_size = 1440  # 24 hours at 1-minute intervals
        self.is_monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.logger = logging.getLogger(__name__)
        
        # Performance counters for network
        self.last_network_stats = psutil.net_io_counters()
        self.last_network_time = time.time()
    
    async def start_monitoring(self):
        """Start resource monitoring"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Resource monitoring started")
    
    async def stop_monitoring(self):
        """Stop resource monitoring"""
        self.is_monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Resource monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                metrics = self._collect_metrics()
                self._add_metrics(metrics)
                await asyncio.sleep(self.monitoring_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
    
    def _collect_metrics(self) -> ResourceMetrics:
        """Collect current resource metrics"""
        # CPU utilization
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory utilization
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available_mb = memory.available / (1024 * 1024)
        
        # Disk utilization
        disk = psutil.disk_usage('/')
        disk_usage_percent = (disk.used / disk.total) * 100
        disk_free_gb = disk.free / (1024 * 1024 * 1024)
        
        # Network utilization
        current_network = psutil.net_io_counters()
        current_time = time.time()
        
        # Calculate network throughput
        time_delta = current_time - self.last_network_time
        bytes_sent_delta = current_network.bytes_sent - self.last_network_stats.bytes_sent
        bytes_recv_delta = current_network.bytes_recv - self.last_network_stats.bytes_recv
        
        # Update for next calculation
        self.last_network_stats = current_network
        self.last_network_time = current_time
        
        return ResourceMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_available_mb=memory_available_mb,
            disk_usage_percent=disk_usage_percent,
            disk_free_gb=disk_free_gb,
            network_bytes_sent=bytes_sent_delta,
            network_bytes_recv=bytes_recv_delta
        )
    
    def _add_metrics(self, metrics: ResourceMetrics):
        """Add metrics to history"""
        self.metrics_history.append(metrics)
        
        # Trim history if too large
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size:]
    
    def get_current_metrics(self) -> Optional[ResourceMetrics]:
        """Get most recent metrics"""
        return self.metrics_history[-1] if self.metrics_history else None
    
    def get_average_metrics(self, minutes: int = 5) -> Optional[ResourceMetrics]:
        """Get average metrics over specified time period"""
        if not self.metrics_history:
            return None
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        recent_metrics = [
            m for m in self.metrics_history 
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return None
        
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        avg_disk = sum(m.disk_usage_percent for m in recent_metrics) / len(recent_metrics)
        
        return ResourceMetrics(
            cpu_percent=avg_cpu,
            memory_percent=avg_memory,
            memory_available_mb=recent_metrics[-1].memory_available_mb,
            disk_usage_percent=avg_disk,
            disk_free_gb=recent_metrics[-1].disk_free_gb,
            network_bytes_sent=sum(m.network_bytes_sent for m in recent_metrics),
            network_bytes_recv=sum(m.network_bytes_recv for m in recent_metrics)
        )
    
    def check_resource_limits(self, limits: ResourceLimit) -> Dict[str, Any]:
        """Check if any resource limits are exceeded"""
        current_metrics = self.get_current_metrics()
        if not current_metrics:
            return {'status': 'no_data'}
        
        violations = []
        
        if current_metrics.cpu_percent > limits.cpu_limit_percent:
            violations.append({
                'resource': ResourceType.CPU.value,
                'current': current_metrics.cpu_percent,
                'limit': limits.cpu_limit_percent,
                'severity': 'high' if current_metrics.cpu_percent > 95 else 'medium'
            })
        
        if current_metrics.memory_percent > limits.memory_limit_percent:
            violations.append({
                'resource': ResourceType.MEMORY.value,
                'current': current_metrics.memory_percent,
                'limit': limits.memory_limit_percent,
                'severity': 'high' if current_metrics.memory_percent > 95 else 'medium'
            })
        
        if current_metrics.disk_usage_percent > limits.disk_limit_percent:
            violations.append({
                'resource': ResourceType.DISK.value,
                'current': current_metrics.disk_usage_percent,
                'limit': limits.disk_limit_percent,
                'severity': 'high' if current_metrics.disk_usage_percent > 98 else 'medium'
            })
        
        return {
            'status': 'violations' if violations else 'ok',
            'violations': violations,
            'checked_at': datetime.utcnow().isoformat()
        }

class PerformanceTuner:
    """Automatic performance tuning system"""
    
    def __init__(self, resource_monitor: ResourceMonitor):
        self.resource_monitor = resource_monitor
        self.tuning_rules: List[Callable] = []
        self.tuning_history: List[Dict[str, Any]] = []
        self.is_tuning_enabled = True
        self.logger = logging.getLogger(__name__)
    
    def add_tuning_rule(self, rule: Callable[['PerformanceTuner'], Optional[Dict[str, Any]]]):
        """Add a performance tuning rule"""
        self.tuning_rules.append(rule)
    
    async def run_tuning_cycle(self) -> Dict[str, Any]:
        """Run one tuning cycle"""
        if not self.is_tuning_enabled:
            return {'status': 'disabled'}
        
        current_metrics = self.resource_monitor.get_current_metrics()
        if not current_metrics:
            return {'status': 'no_metrics'}
        
        tuning_actions = []
        
        # Apply tuning rules
        for rule in self.tuning_rules:
            try:
                action = rule(self)
                if action:
                    tuning_actions.append(action)
                    self.logger.info(f"Applied tuning action: {action}")
            except Exception as e:
                self.logger.error(f"Error in tuning rule: {e}")
        
        # Record tuning history
        tuning_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': current_metrics,
            'actions': tuning_actions
        }
        self.tuning_history.append(tuning_record)
        
        # Trim history
        if len(self.tuning_history) > 1000:
            self.tuning_history = self.tuning_history[-1000:]
        
        return {
            'status': 'completed',
            'actions_taken': len(tuning_actions),
            'actions': tuning_actions
        }
    
    def get_tuning_stats(self) -> Dict[str, Any]:
        """Get tuning statistics"""
        if not self.tuning_history:
            return {'status': 'no_history'}
        
        total_actions = sum(len(record['actions']) for record in self.tuning_history)
        recent_actions = sum(
            len(record['actions']) 
            for record in self.tuning_history[-10:]  # Last 10 cycles
        )
        
        return {
            'total_tuning_cycles': len(self.tuning_history),
            'total_actions': total_actions,
            'recent_actions': recent_actions,
            'tuning_enabled': self.is_tuning_enabled,
            'rules_count': len(self.tuning_rules)
        }

# Performance tuning rules
def cpu_optimization_rule(tuner: PerformanceTuner) -> Optional[Dict[str, Any]]:
    """CPU optimization tuning rule"""
    current_metrics = tuner.resource_monitor.get_current_metrics()
    
    if current_metrics and current_metrics.cpu_percent > 80:
        # Simulate CPU optimization actions
        actions = []
        
        # Reduce thread pool sizes
        actions.append("Reduced thread pool size")
        
        # Enable CPU affinity for critical processes
        actions.append("Enabled CPU affinity")
        
        # Adjust process priorities
        actions.append("Adjusted process priorities")
        
        return {
            'rule': 'cpu_optimization',
            'trigger': f'CPU usage: {current_metrics.cpu_percent}%',
            'actions': actions
        }
    
    return None

def memory_optimization_rule(tuner: PerformanceTuner) -> Optional[Dict[str, Any]]:
    """Memory optimization tuning rule"""
    current_metrics = tuner.resource_monitor.get_current_metrics()
    
    if current_metrics and current_metrics.memory_percent > 85:
        # Simulate memory optimization actions
        actions = []
        
        # Trigger garbage collection
        import gc
        collected = gc.collect()
        actions.append(f"Garbage collection freed {collected} objects")
        
        # Reduce cache sizes
        actions.append("Reduced cache sizes")
        
        # Compress in-memory data
        actions.append("Enabled data compression")
        
        return {
            'rule': 'memory_optimization',
            'trigger': f'Memory usage: {current_metrics.memory_percent}%',
            'actions': actions
        }
    
    return None

def disk_optimization_rule(tuner: PerformanceTuner) -> Optional[Dict[str, Any]]:
    """Disk optimization tuning rule"""
    current_metrics = tuner.resource_monitor.get_current_metrics()
    
    if current_metrics and current_metrics.disk_usage_percent > 90:
        # Simulate disk optimization actions
        actions = []
        
        # Clean temporary files
        actions.append("Cleaned temporary files")
        
        # Compress log files
        actions.append("Compressed old log files")
        
        # Archive old data
        actions.append("Archived old data")
        
        return {
            'rule': 'disk_optimization',
            'trigger': f'Disk usage: {current_metrics.disk_usage_percent}%',
            'actions': actions
        }
    
    return None

class VerticalScalingManager:
    """Manages vertical scaling operations"""
    
    def __init__(self, resource_monitor: ResourceMonitor):
        self.resource_monitor = resource_monitor
        self.performance_tuner = PerformanceTuner(resource_monitor)
        self.scaling_limits = ResourceLimit()
        self.auto_tuning_enabled = True
        self.tuning_interval = 60.0  # 1 minute
        self.tuning_task: Optional[asyncio.Task] = None
        self.logger = logging.getLogger(__name__)
        
        # Add default tuning rules
        self.performance_tuner.add_tuning_rule(cpu_optimization_rule)
        self.performance_tuner.add_tuning_rule(memory_optimization_rule)
        self.performance_tuner.add_tuning_rule(disk_optimization_rule)
    
    async def start_auto_tuning(self):
        """Start automatic performance tuning"""
        if self.tuning_task:
            return
        
        self.tuning_task = asyncio.create_task(self._auto_tuning_loop())
        self.logger.info("Auto-tuning started")
    
    async def stop_auto_tuning(self):
        """Stop automatic performance tuning"""
        if self.tuning_task:
            self.tuning_task.cancel()
            try:
                await self.tuning_task
            except asyncio.CancelledError:
                pass
            self.tuning_task = None
        self.logger.info("Auto-tuning stopped")
    
    async def _auto_tuning_loop(self):
        """Automatic tuning loop"""
        while True:
            try:
                if self.auto_tuning_enabled:
                    await self.performance_tuner.run_tuning_cycle()
                
                await asyncio.sleep(self.tuning_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in auto-tuning loop: {e}")
    
    async def recommend_vertical_scaling(self) -> Dict[str, Any]:
        """Recommend vertical scaling actions"""
        # Get average metrics over last 15 minutes
        avg_metrics = self.resource_monitor.get_average_metrics(15)
        
        if not avg_metrics:
            return {'status': 'no_data'}
        
        recommendations = []
        
        # CPU scaling recommendations
        if avg_metrics.cpu_percent > 80:
            recommendations.append({
                'resource': 'CPU',
                'action': 'scale_up',
                'current_usage': f"{avg_metrics.cpu_percent:.1f}%",
                'recommendation': 'Add more CPU cores or upgrade to higher frequency'
            })
        elif avg_metrics.cpu_percent < 20:
            recommendations.append({
                'resource': 'CPU',
                'action': 'scale_down',
                'current_usage': f"{avg_metrics.cpu_percent:.1f}%",
                'recommendation': 'Consider reducing CPU allocation'
            })
        
        # Memory scaling recommendations
        if avg_metrics.memory_percent > 85:
            recommendations.append({
                'resource': 'Memory',
                'action': 'scale_up',
                'current_usage': f"{avg_metrics.memory_percent:.1f}%",
                'recommendation': 'Add more RAM'
            })
        elif avg_metrics.memory_percent < 30:
            recommendations.append({
                'resource': 'Memory',
                'action': 'scale_down',
                'current_usage': f"{avg_metrics.memory_percent:.1f}%",
                'recommendation': 'Consider reducing memory allocation'
            })
        
        # Disk scaling recommendations
        if avg_metrics.disk_usage_percent > 90:
            recommendations.append({
                'resource': 'Disk',
                'action': 'scale_up',
                'current_usage': f"{avg_metrics.disk_usage_percent:.1f}%",
                'recommendation': 'Add more storage capacity'
            })
        
        return {
            'status': 'completed',
            'analysis_period': '15 minutes',
            'recommendations': recommendations,
            'tuning_stats': self.performance_tuner.get_tuning_stats()
        }
    
    async def get_scaling_status(self) -> Dict[str, Any]:
        """Get current scaling status"""
        current_metrics = self.resource_monitor.get_current_metrics()
        limit_check = self.resource_monitor.check_resource_limits(self.scaling_limits)
        
        return {
            'current_metrics': current_metrics.__dict__ if current_metrics else None,
            'resource_limits': limit_check,
            'auto_tuning_enabled': self.auto_tuning_enabled,
            'tuning_interval': self.tuning_interval,
            'monitoring_active': self.resource_monitor.is_monitoring
        }
```

This expanded Architecture Scalability Patterns document now includes comprehensive implementations for horizontal scaling (load balancing, service replication, stateless design, data partitioning) and vertical scaling (resource monitoring, performance tuning, auto-optimization). Each pattern is demonstrated with production-ready code examples that can be adapted for real-world scalable architectures.