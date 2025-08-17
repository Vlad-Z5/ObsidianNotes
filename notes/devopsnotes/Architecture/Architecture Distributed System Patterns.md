# Architecture Distributed System Patterns

## Distributed System Fundamentals

Distributed systems are complex architectures that span multiple nodes and networks. This guide provides comprehensive patterns and implementations for building resilient, scalable distributed systems.

### CAP Theorem

The CAP theorem states that any distributed system can guarantee only two of the three properties: Consistency, Availability, and Partition tolerance.

```python
from enum import Enum
from typing import Dict, List, Optional, Any
import time
import threading
import logging

class CAPChoice(Enum):
    CP = "consistency_partition_tolerance"  # Sacrifice availability
    AP = "availability_partition_tolerance"  # Sacrifice consistency
    CA = "consistency_availability"  # Sacrifice partition tolerance (not realistic in distributed systems)

class DistributedSystemDesigner:
    """CAP theorem implementation and decision framework"""
    
    def __init__(self, system_requirements: Dict[str, Any]):
        self.requirements = system_requirements
        self.logger = logging.getLogger(__name__)
        
    def analyze_cap_requirements(self) -> CAPChoice:
        """Analyze system requirements to determine CAP choice"""
        
        consistency_critical = self.requirements.get('consistency_critical', False)
        availability_critical = self.requirements.get('availability_critical', False)
        network_partitions_expected = self.requirements.get('network_partitions_expected', True)
        
        if consistency_critical and network_partitions_expected:
            return CAPChoice.CP
        elif availability_critical and network_partitions_expected:
            return CAPChoice.AP
        else:
            # In practice, CA is rarely chosen for distributed systems
            return CAPChoice.CP
    
    def implement_cp_system(self):
        """Implement CP system (Consistency + Partition tolerance)"""
        
        class CPDataStore:
            def __init__(self):
                self.data = {}
                self.replicas = []
                self.quorum_size = None
                
            def write(self, key: str, value: Any, timeout: float = 5.0) -> bool:
                """Strong consistency write with quorum"""
                start_time = time.time()
                successful_writes = 0
                
                # Write to all available replicas
                for replica in self.replicas:
                    if time.time() - start_time > timeout:
                        break
                        
                    if replica.is_available():
                        try:
                            replica.write(key, value)
                            successful_writes += 1
                        except Exception as e:
                            self.logger.error(f"Write failed to replica {replica.id}: {e}")
                
                # Require quorum for success
                if successful_writes >= self.quorum_size:
                    self.data[key] = value
                    return True
                else:
                    # Rollback writes if quorum not achieved
                    self._rollback_writes(key, self.replicas[:successful_writes])
                    raise Exception("Write failed: insufficient replicas available")
            
            def read(self, key: str, timeout: float = 5.0) -> Optional[Any]:
                """Strong consistency read with quorum"""
                start_time = time.time()
                read_results = []
                
                for replica in self.replicas:
                    if time.time() - start_time > timeout:
                        break
                        
                    if replica.is_available():
                        try:
                            value = replica.read(key)
                            read_results.append(value)
                        except Exception as e:
                            self.logger.error(f"Read failed from replica {replica.id}: {e}")
                
                if len(read_results) >= self.quorum_size:
                    # Return most recent value (assuming timestamps)
                    return self._resolve_read_conflicts(read_results)
                else:
                    raise Exception("Read failed: insufficient replicas available")
        
        return CPDataStore()
    
    def implement_ap_system(self):
        """Implement AP system (Availability + Partition tolerance)"""
        
        class APDataStore:
            def __init__(self):
                self.data = {}
                self.vector_clock = {}
                self.replicas = []
                
            def write(self, key: str, value: Any, node_id: str) -> bool:
                """Eventually consistent write"""
                try:
                    # Update vector clock
                    if key not in self.vector_clock:
                        self.vector_clock[key] = {}
                    
                    self.vector_clock[key][node_id] = time.time()
                    
                    # Write locally first (always available)
                    self.data[key] = {
                        'value': value,
                        'timestamp': time.time(),
                        'node_id': node_id,
                        'vector_clock': self.vector_clock[key].copy()
                    }
                    
                    # Asynchronously propagate to other replicas
                    self._async_propagate(key, value, node_id)
                    
                    return True
                    
                except Exception as e:
                    self.logger.error(f"Write failed: {e}")
                    return False
            
            def read(self, key: str) -> Optional[Any]:
                """Always available read (may return stale data)"""
                try:
                    if key in self.data:
                        return self.data[key]['value']
                    return None
                except Exception:
                    # Even if there are issues, try to return something
                    return self.data.get(key, {}).get('value')
            
            def _async_propagate(self, key: str, value: Any, node_id: str):
                """Asynchronously propagate writes to other replicas"""
                def propagate():
                    for replica in self.replicas:
                        try:
                            replica.receive_update(key, value, node_id, self.vector_clock[key])
                        except Exception as e:
                            self.logger.warning(f"Failed to propagate to {replica.id}: {e}")
                
                thread = threading.Thread(target=propagate)
                thread.daemon = True
                thread.start()
        
        return APDataStore()
```

### Consistency Models

Implementation of different consistency models for distributed systems.

```python
import asyncio
from typing import Dict, Any, List
from datetime import datetime
import hashlib

class ConsistencyManager:
    """Implementation of various consistency models"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def strong_consistency(self):
        """Strong consistency implementation with synchronous replication"""
        
        class StrongConsistentStore:
            def __init__(self, replicas: List[str]):
                self.replicas = replicas
                self.data = {}
                self.locks = {}
            
            async def write(self, key: str, value: Any) -> bool:
                """Synchronous write to all replicas"""
                
                # Acquire distributed lock
                lock_acquired = await self._acquire_distributed_lock(key)
                if not lock_acquired:
                    raise Exception("Failed to acquire lock for write")
                
                try:
                    # Write to all replicas synchronously
                    write_tasks = []
                    for replica in self.replicas:
                        task = self._write_to_replica(replica, key, value)
                        write_tasks.append(task)
                    
                    results = await asyncio.gather(*write_tasks, return_exceptions=True)
                    
                    # Check if all writes succeeded
                    failed_writes = [r for r in results if isinstance(r, Exception)]
                    if failed_writes:
                        # Rollback all writes
                        await self._rollback_writes(key)
                        raise Exception(f"Write failed: {len(failed_writes)} replicas failed")
                    
                    self.data[key] = value
                    return True
                    
                finally:
                    await self._release_distributed_lock(key)
            
            async def read(self, key: str) -> Any:
                """Read with strong consistency guarantee"""
                
                # Read from majority of replicas to ensure consistency
                read_tasks = []
                for replica in self.replicas:
                    task = self._read_from_replica(replica, key)
                    read_tasks.append(task)
                
                results = await asyncio.gather(*read_tasks, return_exceptions=True)
                
                # Get successful reads
                successful_reads = [r for r in results if not isinstance(r, Exception)]
                
                if len(successful_reads) < len(self.replicas) // 2 + 1:
                    raise Exception("Cannot guarantee strong consistency: insufficient replicas")
                
                # All values should be the same in strong consistency
                if len(set(successful_reads)) > 1:
                    # Repair inconsistency
                    await self._repair_inconsistency(key, successful_reads)
                
                return successful_reads[0] if successful_reads else None
        
        return StrongConsistentStore
    
    def eventual_consistency(self):
        """Eventual consistency with anti-entropy and conflict resolution"""
        
        class EventuallyConsistentStore:
            def __init__(self, node_id: str):
                self.node_id = node_id
                self.data = {}
                self.vector_clocks = {}
                self.anti_entropy_interval = 30
                
            async def write(self, key: str, value: Any) -> bool:
                """Write with eventual consistency"""
                timestamp = datetime.now().timestamp()
                
                # Update vector clock
                if key not in self.vector_clocks:
                    self.vector_clocks[key] = {}
                
                self.vector_clocks[key][self.node_id] = timestamp
                
                # Store with metadata
                self.data[key] = {
                    'value': value,
                    'timestamp': timestamp,
                    'node_id': self.node_id,
                    'vector_clock': self.vector_clocks[key].copy()
                }
                
                # Asynchronously propagate
                asyncio.create_task(self._propagate_update(key, value))
                
                return True
            
            async def read(self, key: str) -> Any:
                """Read local value (may be stale)"""
                return self.data.get(key, {}).get('value')
            
            async def _propagate_update(self, key: str, value: Any):
                """Propagate update to other nodes"""
                pass  # Implementation would send to other nodes
            
            async def anti_entropy_repair(self, other_nodes: List['EventuallyConsistentStore']):
                """Anti-entropy process to repair inconsistencies"""
                
                for other_node in other_nodes:
                    for key in set(self.data.keys()) | set(other_node.data.keys()):
                        local_entry = self.data.get(key)
                        remote_entry = other_node.data.get(key)
                        
                        if self._should_update(local_entry, remote_entry):
                            self.data[key] = remote_entry
                            self.vector_clocks[key] = remote_entry['vector_clock']
            
            def _should_update(self, local: Dict, remote: Dict) -> bool:
                """Determine if local entry should be updated with remote"""
                if not local:
                    return bool(remote)
                if not remote:
                    return False
                
                # Compare vector clocks
                local_clock = local.get('vector_clock', {})
                remote_clock = remote.get('vector_clock', {})
                
                # Remote is newer if it has later timestamps
                for node_id, timestamp in remote_clock.items():
                    if timestamp > local_clock.get(node_id, 0):
                        return True
                
                return False
        
        return EventuallyConsistentStore
    
    def session_consistency(self):
        """Session consistency implementation"""
        
        class SessionConsistentStore:
            def __init__(self):
                self.data = {}
                self.session_versions = {}
                self.global_version = 0
            
            def create_session(self, session_id: str) -> str:
                """Create new session with consistency tracking"""
                self.session_versions[session_id] = {
                    'read_version': self.global_version,
                    'write_version': self.global_version
                }
                return session_id
            
            async def session_write(self, session_id: str, key: str, value: Any) -> bool:
                """Write with session consistency"""
                if session_id not in self.session_versions:
                    raise Exception("Invalid session")
                
                self.global_version += 1
                
                self.data[key] = {
                    'value': value,
                    'version': self.global_version,
                    'session_id': session_id
                }
                
                # Update session write version
                self.session_versions[session_id]['write_version'] = self.global_version
                
                return True
            
            async def session_read(self, session_id: str, key: str) -> Any:
                """Read with session consistency guarantee"""
                if session_id not in self.session_versions:
                    raise Exception("Invalid session")
                
                session_info = self.session_versions[session_id]
                entry = self.data.get(key)
                
                if entry:
                    # Ensure read-your-writes consistency
                    if entry['version'] >= session_info['write_version']:
                        # Update session read version
                        self.session_versions[session_id]['read_version'] = max(
                            session_info['read_version'],
                            entry['version']
                        )
                        return entry['value']
                
                return None
        
        return SessionConsistentStore
```

### Consensus Algorithms

Implementation of Raft consensus algorithm for distributed coordination.

```python
import random
import asyncio
from enum import Enum
from typing import Dict, List, Optional, Any
import json

class NodeState(Enum):
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"

class RaftNode:
    """Raft consensus algorithm implementation"""
    
    def __init__(self, node_id: str, cluster_nodes: List[str]):
        self.node_id = node_id
        self.cluster_nodes = cluster_nodes
        self.state = NodeState.FOLLOWER
        
        # Persistent state
        self.current_term = 0
        self.voted_for = None
        self.log = []  # List of log entries
        
        # Volatile state
        self.commit_index = 0
        self.last_applied = 0
        
        # Leader state
        self.next_index = {}
        self.match_index = {}
        
        # Timers
        self.election_timeout = self._random_election_timeout()
        self.heartbeat_interval = 0.05  # 50ms
        
        self.logger = logging.getLogger(f"raft-{node_id}")
    
    def _random_election_timeout(self) -> float:
        """Random election timeout between 150-300ms"""
        return random.uniform(0.15, 0.3)
    
    async def start(self):
        """Start the Raft node"""
        asyncio.create_task(self._election_timer())
        if self.state == NodeState.LEADER:
            asyncio.create_task(self._heartbeat_timer())
    
    async def _election_timer(self):
        """Handle election timeout"""
        while True:
            await asyncio.sleep(self.election_timeout)
            
            if self.state != NodeState.LEADER:
                # Start election
                await self._start_election()
    
    async def _heartbeat_timer(self):
        """Send heartbeats as leader"""
        while self.state == NodeState.LEADER:
            await self._send_heartbeats()
            await asyncio.sleep(self.heartbeat_interval)
    
    async def _start_election(self):
        """Start leader election"""
        self.state = NodeState.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        self.election_timeout = self._random_election_timeout()
        
        self.logger.info(f"Starting election for term {self.current_term}")
        
        # Vote for self
        votes_received = 1
        
        # Request votes from other nodes
        vote_tasks = []
        for node in self.cluster_nodes:
            if node != self.node_id:
                task = self._request_vote(node)
                vote_tasks.append(task)
        
        if vote_tasks:
            vote_responses = await asyncio.gather(*vote_tasks, return_exceptions=True)
            
            for response in vote_responses:
                if isinstance(response, dict) and response.get('vote_granted'):
                    votes_received += 1
        
        # Check if won election
        if votes_received > len(self.cluster_nodes) // 2:
            await self._become_leader()
        else:
            self.state = NodeState.FOLLOWER
            self.voted_for = None
    
    async def _become_leader(self):
        """Become the leader"""
        self.state = NodeState.LEADER
        self.logger.info(f"Became leader for term {self.current_term}")
        
        # Initialize leader state
        for node in self.cluster_nodes:
            if node != self.node_id:
                self.next_index[node] = len(self.log)
                self.match_index[node] = 0
        
        # Start sending heartbeats
        asyncio.create_task(self._heartbeat_timer())
    
    async def _request_vote(self, target_node: str) -> Dict[str, Any]:
        """Request vote from another node"""
        
        last_log_index = len(self.log) - 1
        last_log_term = self.log[last_log_index]['term'] if self.log else 0
        
        request = {
            'term': self.current_term,
            'candidate_id': self.node_id,
            'last_log_index': last_log_index,
            'last_log_term': last_log_term
        }
        
        # In real implementation, this would be sent over network
        return await self._simulate_vote_request(target_node, request)
    
    async def _simulate_vote_request(self, target_node: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate vote request (in real implementation, this would be network call)"""
        
        # Simulate network delay
        await asyncio.sleep(random.uniform(0.01, 0.05))
        
        # Simulate vote response based on Raft rules
        vote_granted = (
            request['term'] > self.current_term and
            (self.voted_for is None or self.voted_for == request['candidate_id'])
        )
        
        return {
            'term': max(self.current_term, request['term']),
            'vote_granted': vote_granted
        }
    
    async def _send_heartbeats(self):
        """Send heartbeat/append entries to all followers"""
        
        for node in self.cluster_nodes:
            if node != self.node_id:
                await self._send_append_entries(node)
    
    async def _send_append_entries(self, target_node: str):
        """Send append entries RPC to follower"""
        
        prev_log_index = self.next_index[target_node] - 1
        prev_log_term = self.log[prev_log_index]['term'] if prev_log_index >= 0 else 0
        
        entries = self.log[self.next_index[target_node]:]
        
        request = {
            'term': self.current_term,
            'leader_id': self.node_id,
            'prev_log_index': prev_log_index,
            'prev_log_term': prev_log_term,
            'entries': entries,
            'leader_commit': self.commit_index
        }
        
        response = await self._simulate_append_entries(target_node, request)
        
        if response['success']:
            # Update next_index and match_index
            self.next_index[target_node] = prev_log_index + len(entries) + 1
            self.match_index[target_node] = prev_log_index + len(entries)
            
            # Update commit index
            await self._update_commit_index()
        else:
            # Decrement next_index and retry
            self.next_index[target_node] = max(1, self.next_index[target_node] - 1)
    
    async def _simulate_append_entries(self, target_node: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate append entries response"""
        
        await asyncio.sleep(random.uniform(0.01, 0.03))
        
        # Simulate success based on log consistency
        success = (
            request['term'] >= self.current_term and
            (request['prev_log_index'] == 0 or 
             (request['prev_log_index'] < len(self.log) and
              self.log[request['prev_log_index']]['term'] == request['prev_log_term']))
        )
        
        return {
            'term': self.current_term,
            'success': success
        }
    
    async def _update_commit_index(self):
        """Update commit index based on majority replication"""
        
        for n in range(self.commit_index + 1, len(self.log)):
            if self.log[n]['term'] == self.current_term:
                # Count nodes that have replicated this entry
                count = 1  # Count self
                for node in self.cluster_nodes:
                    if node != self.node_id and self.match_index.get(node, 0) >= n:
                        count += 1
                
                # If majority has replicated, commit
                if count > len(self.cluster_nodes) // 2:
                    self.commit_index = n
                else:
                    break
    
    async def client_request(self, command: Any) -> bool:
        """Handle client request (only leader can handle)"""
        
        if self.state != NodeState.LEADER:
            return False
        
        # Append to log
        log_entry = {
            'term': self.current_term,
            'command': command,
            'index': len(self.log)
        }
        
        self.log.append(log_entry)
        
        # Replicate to followers
        await self._send_heartbeats()
        
        # Wait for majority replication
        while self.commit_index < len(self.log) - 1:
            await asyncio.sleep(0.01)
        
        return True
```

### Partitioning Strategies

Implementation of different data partitioning strategies.

```python
import hashlib
import bisect
from typing import Any, List, Dict, Tuple, Optional
from abc import ABC, abstractmethod

class PartitionStrategy(ABC):
    """Abstract base class for partitioning strategies"""
    
    @abstractmethod
    def get_partition(self, key: str) -> int:
        """Get partition for given key"""
        pass
    
    @abstractmethod
    def get_partitions_for_range(self, start_key: str, end_key: str) -> List[int]:
        """Get partitions for key range"""
        pass

class HashPartitioning(PartitionStrategy):
    """Hash-based partitioning strategy"""
    
    def __init__(self, num_partitions: int):
        self.num_partitions = num_partitions
    
    def get_partition(self, key: str) -> int:
        """Hash key to determine partition"""
        hash_value = hashlib.md5(key.encode()).hexdigest()
        return int(hash_value, 16) % self.num_partitions
    
    def get_partitions_for_range(self, start_key: str, end_key: str) -> List[int]:
        """For hash partitioning, range queries require all partitions"""
        return list(range(self.num_partitions))

class RangePartitioning(PartitionStrategy):
    """Range-based partitioning strategy"""
    
    def __init__(self, partition_boundaries: List[str]):
        self.boundaries = sorted(partition_boundaries)
        self.num_partitions = len(partition_boundaries) + 1
    
    def get_partition(self, key: str) -> int:
        """Use binary search to find partition"""
        return bisect.bisect_left(self.boundaries, key)
    
    def get_partitions_for_range(self, start_key: str, end_key: str) -> List[int]:
        """Get partitions that overlap with range"""
        start_partition = self.get_partition(start_key)
        end_partition = self.get_partition(end_key)
        return list(range(start_partition, end_partition + 1))

class ConsistentHashing(PartitionStrategy):
    """Consistent hashing for better load distribution and minimal rehashing"""
    
    def __init__(self, nodes: List[str], virtual_nodes: int = 150):
        self.virtual_nodes = virtual_nodes
        self.ring = {}
        self.sorted_keys = []
        
        for node in nodes:
            self.add_node(node)
    
    def _hash(self, key: str) -> int:
        """Hash function for consistent hashing"""
        return int(hashlib.md5(key.encode()).hexdigest(), 16)
    
    def add_node(self, node: str):
        """Add node to consistent hash ring"""
        for i in range(self.virtual_nodes):
            virtual_key = f"{node}:{i}"
            hash_value = self._hash(virtual_key)
            self.ring[hash_value] = node
            bisect.insort(self.sorted_keys, hash_value)
    
    def remove_node(self, node: str):
        """Remove node from consistent hash ring"""
        for i in range(self.virtual_nodes):
            virtual_key = f"{node}:{i}"
            hash_value = self._hash(virtual_key)
            if hash_value in self.ring:
                del self.ring[hash_value]
                self.sorted_keys.remove(hash_value)
    
    def get_partition(self, key: str) -> str:
        """Get node for given key"""
        if not self.ring:
            return None
        
        hash_value = self._hash(key)
        
        # Find first node clockwise
        idx = bisect.bisect_right(self.sorted_keys, hash_value)
        if idx == len(self.sorted_keys):
            idx = 0
        
        return self.ring[self.sorted_keys[idx]]
    
    def get_partitions_for_range(self, start_key: str, end_key: str) -> List[str]:
        """Get nodes for key range"""
        nodes = set()
        
        start_hash = self._hash(start_key)
        end_hash = self._hash(end_key)
        
        # Handle wrap-around case
        if start_hash <= end_hash:
            for key in self.sorted_keys:
                if start_hash <= key <= end_hash:
                    nodes.add(self.ring[key])
        else:
            for key in self.sorted_keys:
                if key >= start_hash or key <= end_hash:
                    nodes.add(self.ring[key])
        
        return list(nodes)

class PartitionedDataStore:
    """Distributed data store with configurable partitioning"""
    
    def __init__(self, partitioning_strategy: PartitionStrategy, replication_factor: int = 3):
        self.partitioning = partitioning_strategy
        self.replication_factor = replication_factor
        self.partitions = {}
        self.metadata = {}
        self.logger = logging.getLogger(__name__)
    
    async def put(self, key: str, value: Any) -> bool:
        """Store key-value with partitioning and replication"""
        
        primary_partition = self.partitioning.get_partition(key)
        
        # Determine replica partitions
        replica_partitions = self._get_replica_partitions(primary_partition)
        
        # Write to primary first
        success = await self._write_to_partition(primary_partition, key, value, is_primary=True)
        if not success:
            return False
        
        # Asynchronously replicate to replicas
        replication_tasks = []
        for replica in replica_partitions:
            task = self._write_to_partition(replica, key, value, is_primary=False)
            replication_tasks.append(task)
        
        # Wait for at least majority of replicas
        if replication_tasks:
            results = await asyncio.gather(*replication_tasks, return_exceptions=True)
            successful_replicas = sum(1 for r in results if r is True)
            
            if successful_replicas < len(replica_partitions) // 2:
                self.logger.warning(f"Only {successful_replicas} replicas successful for key {key}")
        
        return True
    
    async def get(self, key: str) -> Optional[Any]:
        """Retrieve value with partition routing"""
        
        primary_partition = self.partitioning.get_partition(key)
        
        # Try primary first
        value = await self._read_from_partition(primary_partition, key)
        if value is not None:
            return value
        
        # If primary fails, try replicas
        replica_partitions = self._get_replica_partitions(primary_partition)
        
        for replica in replica_partitions:
            try:
                value = await self._read_from_partition(replica, key)
                if value is not None:
                    return value
            except Exception as e:
                self.logger.warning(f"Failed to read from replica {replica}: {e}")
        
        return None
    
    async def range_query(self, start_key: str, end_key: str) -> Dict[str, Any]:
        """Execute range query across partitions"""
        
        affected_partitions = self.partitioning.get_partitions_for_range(start_key, end_key)
        
        # Query all affected partitions in parallel
        query_tasks = []
        for partition in affected_partitions:
            task = self._range_query_partition(partition, start_key, end_key)
            query_tasks.append(task)
        
        results = await asyncio.gather(*query_tasks, return_exceptions=True)
        
        # Merge results
        merged_results = {}
        for result in results:
            if isinstance(result, dict):
                merged_results.update(result)
        
        return merged_results
    
    def _get_replica_partitions(self, primary_partition: int) -> List[int]:
        """Get replica partitions for a primary partition"""
        
        total_partitions = getattr(self.partitioning, 'num_partitions', 10)
        replicas = []
        
        for i in range(1, self.replication_factor):
            replica_partition = (primary_partition + i) % total_partitions
            replicas.append(replica_partition)
        
        return replicas
    
    async def _write_to_partition(self, partition: int, key: str, value: Any, is_primary: bool) -> bool:
        """Write to specific partition"""
        
        if partition not in self.partitions:
            self.partitions[partition] = {}
        
        try:
            self.partitions[partition][key] = {
                'value': value,
                'timestamp': time.time(),
                'is_primary': is_primary
            }
            
            return True
            
        except Exception as e:
            self.logger.error(f"Write failed to partition {partition}: {e}")
            return False
    
    async def _read_from_partition(self, partition: int, key: str) -> Optional[Any]:
        """Read from specific partition"""
        
        if partition in self.partitions and key in self.partitions[partition]:
            return self.partitions[partition][key]['value']
        
        return None
    
    async def _range_query_partition(self, partition: int, start_key: str, end_key: str) -> Dict[str, Any]:
        """Execute range query on specific partition"""
        
        results = {}
        
        if partition in self.partitions:
            for key, entry in self.partitions[partition].items():
                if start_key <= key <= end_key:
                    results[key] = entry['value']
        
        return results
```

### Fault Tolerance Patterns

Implementation of fault tolerance patterns for distributed systems.

```python
import asyncio
import random
import time
from typing import List, Dict, Any, Optional, Callable
from enum import Enum

class ReplicationStrategy(Enum):
    MASTER_SLAVE = "master_slave"
    MASTER_MASTER = "master_master"
    CHAIN_REPLICATION = "chain_replication"

class FaultToleranceManager:
    """Comprehensive fault tolerance implementation"""
    
    def __init__(self, replication_strategy: ReplicationStrategy):
        self.replication_strategy = replication_strategy
        self.nodes = {}
        self.failure_detector = FailureDetector()
        self.logger = logging.getLogger(__name__)
    
    def create_replicated_service(self, service_name: str, node_count: int):
        """Create replicated service with fault tolerance"""
        
        if self.replication_strategy == ReplicationStrategy.MASTER_SLAVE:
            return self._create_master_slave_service(service_name, node_count)
        elif self.replication_strategy == ReplicationStrategy.MASTER_MASTER:
            return self._create_master_master_service(service_name, node_count)
        elif self.replication_strategy == ReplicationStrategy.CHAIN_REPLICATION:
            return self._create_chain_replication_service(service_name, node_count)
    
    def _create_master_slave_service(self, service_name: str, node_count: int):
        """Create master-slave replicated service"""
        
        class MasterSlaveService:
            def __init__(self, name: str, nodes: int):
                self.name = name
                self.master = None
                self.slaves = []
                self.data = {}
                
                # Initialize nodes
                for i in range(nodes):
                    node = ReplicaNode(f"{name}-node-{i}")
                    if i == 0:
                        self.master = node
                        node.role = "master"
                    else:
                        self.slaves.append(node)
                        node.role = "slave"
            
            async def write(self, key: str, value: Any) -> bool:
                """Write to master, replicate to slaves"""
                
                if not self.master or not self.master.is_healthy():
                    # Trigger failover
                    await self._failover()
                    if not self.master:
                        return False
                
                # Write to master
                success = await self.master.write(key, value)
                if not success:
                    return False
                
                # Replicate to slaves asynchronously
                replication_tasks = []
                for slave in self.slaves:
                    if slave.is_healthy():
                        task = slave.write(key, value)
                        replication_tasks.append(task)
                
                if replication_tasks:
                    await asyncio.gather(*replication_tasks, return_exceptions=True)
                
                return True
            
            async def read(self, key: str, allow_slave_reads: bool = True) -> Optional[Any]:
                """Read from master or slaves"""
                
                # Try master first
                if self.master and self.master.is_healthy():
                    value = await self.master.read(key)
                    if value is not None:
                        return value
                
                # If master fails and slave reads allowed
                if allow_slave_reads:
                    for slave in self.slaves:
                        if slave.is_healthy():
                            value = await slave.read(key)
                            if value is not None:
                                return value
                
                return None
            
            async def _failover(self):
                """Promote slave to master on failure"""
                
                if not self.master.is_healthy():
                    self.logger.info(f"Master failed, initiating failover for {self.name}")
                    
                    # Find most up-to-date slave
                    best_slave = None
                    highest_version = -1
                    
                    for slave in self.slaves:
                        if slave.is_healthy():
                            version = slave.get_data_version()
                            if version > highest_version:
                                highest_version = version
                                best_slave = slave
                    
                    if best_slave:
                        # Promote slave to master
                        best_slave.role = "master"
                        self.slaves.remove(best_slave)
                        self.master = best_slave
                        
                        self.logger.info(f"Promoted {best_slave.node_id} to master")
        
        return MasterSlaveService(service_name, node_count)
    
    def _create_chain_replication_service(self, service_name: str, node_count: int):
        """Create chain replication service"""
        
        class ChainReplicationService:
            def __init__(self, name: str, nodes: int):
                self.name = name
                self.chain = []
                
                # Create chain of nodes
                for i in range(nodes):
                    node = ReplicaNode(f"{name}-node-{i}")
                    self.chain.append(node)
                    
                    if i == 0:
                        node.role = "head"
                    elif i == nodes - 1:
                        node.role = "tail"
                    else:
                        node.role = "middle"
            
            async def write(self, key: str, value: Any) -> bool:
                """Write to head, propagate through chain"""
                
                if not self.chain or not self.chain[0].is_healthy():
                    await self._handle_head_failure()
                    if not self.chain:
                        return False
                
                # Start write at head
                return await self._propagate_write(0, key, value)
            
            async def read(self, key: str) -> Optional[Any]:
                """Read from tail (most consistent)"""
                
                if self.chain:
                    tail = self.chain[-1]
                    if tail.is_healthy():
                        return await tail.read(key)
                
                # If tail fails, try predecessor
                for i in range(len(self.chain) - 2, -1, -1):
                    node = self.chain[i]
                    if node.is_healthy():
                        return await node.read(key)
                
                return None
            
            async def _propagate_write(self, node_index: int, key: str, value: Any) -> bool:
                """Propagate write through chain"""
                
                if node_index >= len(self.chain):
                    return True
                
                node = self.chain[node_index]
                
                if not node.is_healthy():
                    # Skip failed node
                    return await self._propagate_write(node_index + 1, key, value)
                
                # Write to current node
                success = await node.write(key, value)
                if not success:
                    return False
                
                # Continue to next node
                return await self._propagate_write(node_index + 1, key, value)
            
            async def _handle_head_failure(self):
                """Handle head node failure"""
                
                if self.chain and not self.chain[0].is_healthy():
                    self.logger.info(f"Head node failed, removing from chain")
                    self.chain.pop(0)
                    
                    if self.chain:
                        self.chain[0].role = "head"
        
        return ChainReplicationService(service_name, node_count)

class ReplicaNode:
    """Individual replica node with health monitoring"""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.role = "replica"
        self.data = {}
        self.version = 0
        self.healthy = True
        self.last_heartbeat = time.time()
        
        # Simulate random failures
        self.failure_probability = 0.01
    
    async def write(self, key: str, value: Any) -> bool:
        """Write data with version tracking"""
        
        if not self.is_healthy():
            return False
        
        # Simulate operation delay
        await asyncio.sleep(random.uniform(0.001, 0.01))
        
        # Simulate failure
        if random.random() < self.failure_probability:
            self.healthy = False
            return False
        
        self.data[key] = value
        self.version += 1
        self.last_heartbeat = time.time()
        
        return True
    
    async def read(self, key: str) -> Optional[Any]:
        """Read data"""
        
        if not self.is_healthy():
            return None
        
        await asyncio.sleep(random.uniform(0.001, 0.005))
        
        # Simulate failure
        if random.random() < self.failure_probability:
            self.healthy = False
            return None
        
        self.last_heartbeat = time.time()
        return self.data.get(key)
    
    def is_healthy(self) -> bool:
        """Check node health"""
        
        # Consider node unhealthy if no heartbeat for 5 seconds
        if time.time() - self.last_heartbeat > 5.0:
            self.healthy = False
        
        return self.healthy
    
    def get_data_version(self) -> int:
        """Get current data version"""
        return self.version

class FailureDetector:
    """Failure detection service using heartbeats"""
    
    def __init__(self, heartbeat_interval: float = 1.0, timeout_threshold: float = 5.0):
        self.heartbeat_interval = heartbeat_interval
        self.timeout_threshold = timeout_threshold
        self.monitored_nodes = {}
        self.failure_callbacks = {}
    
    def monitor_node(self, node_id: str, health_check_func: Callable, failure_callback: Callable = None):
        """Start monitoring a node"""
        
        self.monitored_nodes[node_id] = {
            'health_check': health_check_func,
            'last_seen': time.time(),
            'healthy': True
        }
        
        if failure_callback:
            self.failure_callbacks[node_id] = failure_callback
        
        # Start monitoring task
        asyncio.create_task(self._monitor_node_health(node_id))
    
    async def _monitor_node_health(self, node_id: str):
        """Monitor individual node health"""
        
        while node_id in self.monitored_nodes:
            try:
                node_info = self.monitored_nodes[node_id]
                is_healthy = await node_info['health_check']()
                
                if is_healthy:
                    node_info['last_seen'] = time.time()
                    if not node_info['healthy']:
                        # Node recovered
                        node_info['healthy'] = True
                        self.logger.info(f"Node {node_id} recovered")
                else:
                    # Check if timeout exceeded
                    if time.time() - node_info['last_seen'] > self.timeout_threshold:
                        if node_info['healthy']:
                            # Node failed
                            node_info['healthy'] = False
                            self.logger.warning(f"Node {node_id} failed")
                            
                            # Trigger failure callback
                            if node_id in self.failure_callbacks:
                                await self.failure_callbacks[node_id]()
                
            except Exception as e:
                self.logger.error(f"Error monitoring node {node_id}: {e}")
            
            await asyncio.sleep(self.heartbeat_interval)
    
    def get_healthy_nodes(self) -> List[str]:
        """Get list of currently healthy nodes"""
        
        healthy_nodes = []
        for node_id, info in self.monitored_nodes.items():
            if info['healthy']:
                healthy_nodes.append(node_id)
        
        return healthy_nodes
```

This comprehensive distributed system patterns documentation provides production-ready implementations for CAP theorem decisions, consistency models, consensus algorithms, partitioning strategies, and fault tolerance patterns. Each pattern includes detailed code examples with error handling, monitoring, and best practices for building resilient distributed systems.

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Read Architecture Fundamentals.md to check content completeness", "status": "completed", "priority": "high", "id": "1"}, {"content": "Read Architecture System Design.md to check content completeness", "status": "completed", "priority": "high", "id": "2"}, {"content": "Read Architecture Patterns and Styles.md to check content completeness", "status": "completed", "priority": "high", "id": "3"}, {"content": "Check remaining architecture files for content gaps", "status": "completed", "priority": "medium", "id": "4"}, {"content": "Develop Architecture API.md with comprehensive content", "status": "completed", "priority": "high", "id": "5"}, {"content": "Develop Architecture Cloud-Native.md with comprehensive content", "status": "completed", "priority": "high", "id": "6"}, {"content": "Develop Architecture Resilience.md with comprehensive content", "status": "completed", "priority": "high", "id": "7"}, {"content": "Develop Architecture Security-First.md with comprehensive content", "status": "completed", "priority": "high", "id": "8"}, {"content": "Develop Architecture Data.md with comprehensive content", "status": "completed", "priority": "medium", "id": "9"}, {"content": "Develop Architecture Distributed System Patterns.md with comprehensive content", "status": "completed", "priority": "medium", "id": "10"}]