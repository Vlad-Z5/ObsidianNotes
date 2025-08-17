# Architecture Messaging

## Messaging Patterns

Messaging architecture forms the backbone of distributed systems, enabling reliable, scalable, and decoupled communication between services. This guide provides comprehensive implementations of messaging patterns, queue management, reliability mechanisms, and performance optimization strategies.

### Message Queue Patterns

Message queues provide reliable, asynchronous communication between producers and consumers, ensuring messages are delivered even when systems are temporarily unavailable.

#### Point-to-Point Messaging Implementation

```python
import asyncio
import json
import time
import uuid
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import redis
import aioredis
import aiormq
from abc import ABC, abstractmethod

class MessagePriority(Enum):
    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 15

class MessageStatus(Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    DEAD_LETTER = "DEAD_LETTER"

@dataclass
class Message:
    id: str
    payload: Dict[str, Any]
    headers: Dict[str, str] = field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    status: MessageStatus = MessageStatus.PENDING
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'payload': self.payload,
            'headers': self.headers,
            'priority': self.priority.value,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'status': self.status.value,
            'correlation_id': self.correlation_id,
            'reply_to': self.reply_to
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        return cls(
            id=data['id'],
            payload=data['payload'],
            headers=data.get('headers', {}),
            priority=MessagePriority(data.get('priority', MessagePriority.NORMAL.value)),
            created_at=datetime.fromisoformat(data['created_at']),
            expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None,
            retry_count=data.get('retry_count', 0),
            max_retries=data.get('max_retries', 3),
            status=MessageStatus(data.get('status', MessageStatus.PENDING.value)),
            correlation_id=data.get('correlation_id'),
            reply_to=data.get('reply_to')
        )

class MessageQueue(ABC):
    """Abstract base class for message queue implementations"""
    
    @abstractmethod
    async def enqueue(self, queue_name: str, message: Message) -> bool:
        pass
    
    @abstractmethod
    async def dequeue(self, queue_name: str, timeout: Optional[float] = None) -> Optional[Message]:
        pass
    
    @abstractmethod
    async def acknowledge(self, queue_name: str, message_id: str) -> bool:
        pass
    
    @abstractmethod
    async def nack(self, queue_name: str, message_id: str, requeue: bool = True) -> bool:
        pass
    
    @abstractmethod
    async def get_queue_size(self, queue_name: str) -> int:
        pass

class RedisMessageQueue(MessageQueue):
    """Redis-based message queue with priority support and reliability features"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        self.processing_queues: Dict[str, Dict[str, Message]] = {}
        self.dead_letter_queue_suffix = ":dlq"
        
    async def connect(self):
        """Initialize Redis connection"""
        self.redis = aioredis.from_url(self.redis_url, decode_responses=True)
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
    
    async def enqueue(self, queue_name: str, message: Message) -> bool:
        """Enqueue message with priority support"""
        if not self.redis:
            await self.connect()
        
        try:
            # Use Redis sorted set for priority queue
            priority_queue = f"{queue_name}:priority"
            
            # Store message data separately
            message_key = f"{queue_name}:messages:{message.id}"
            message_data = json.dumps(message.to_dict())
            
            # Use pipeline for atomic operations
            pipe = self.redis.pipeline()
            pipe.set(message_key, message_data)
            pipe.zadd(priority_queue, {message.id: message.priority.value})
            
            # Set expiration if specified
            if message.expires_at:
                expire_seconds = int((message.expires_at - datetime.utcnow()).total_seconds())
                if expire_seconds > 0:
                    pipe.expire(message_key, expire_seconds)
            
            await pipe.execute()
            return True
            
        except Exception as e:
            print(f"Error enqueuing message: {e}")
            return False
    
    async def dequeue(self, queue_name: str, timeout: Optional[float] = None) -> Optional[Message]:
        """Dequeue highest priority message"""
        if not self.redis:
            await self.connect()
        
        try:
            priority_queue = f"{queue_name}:priority"
            processing_queue = f"{queue_name}:processing"
            
            # Get highest priority message (ZREVRANGE for highest score first)
            result = await self.redis.zrevrange(priority_queue, 0, 0, withscores=True)
            
            if not result:
                return None
            
            message_id, priority = result[0]
            
            # Move message from priority queue to processing queue atomically
            pipe = self.redis.pipeline()
            pipe.zrem(priority_queue, message_id)
            pipe.zadd(processing_queue, {message_id: time.time()})  # Use timestamp for timeout
            pipe.execute()
            
            # Get message data
            message_key = f"{queue_name}:messages:{message_id}"
            message_data = await self.redis.get(message_key)
            
            if message_data:
                message_dict = json.loads(message_data)
                message = Message.from_dict(message_dict)
                message.status = MessageStatus.PROCESSING
                
                # Store in local processing queue for tracking
                if queue_name not in self.processing_queues:
                    self.processing_queues[queue_name] = {}
                self.processing_queues[queue_name][message_id] = message
                
                return message
            else:
                # Message expired or deleted, remove from processing queue
                await self.redis.zrem(processing_queue, message_id)
                return None
                
        except Exception as e:
            print(f"Error dequeuing message: {e}")
            return None
    
    async def acknowledge(self, queue_name: str, message_id: str) -> bool:
        """Acknowledge successful message processing"""
        if not self.redis:
            await self.connect()
        
        try:
            processing_queue = f"{queue_name}:processing"
            message_key = f"{queue_name}:messages:{message_id}"
            
            # Remove from processing queue and delete message data
            pipe = self.redis.pipeline()
            pipe.zrem(processing_queue, message_id)
            pipe.delete(message_key)
            await pipe.execute()
            
            # Remove from local processing queue
            if queue_name in self.processing_queues:
                self.processing_queues[queue_name].pop(message_id, None)
            
            return True
            
        except Exception as e:
            print(f"Error acknowledging message: {e}")
            return False
    
    async def nack(self, queue_name: str, message_id: str, requeue: bool = True) -> bool:
        """Negative acknowledge - handle failed message processing"""
        if not self.redis:
            await self.connect()
        
        try:
            processing_queue = f"{queue_name}:processing"
            message_key = f"{queue_name}:messages:{message_id}"
            
            # Get message to update retry count
            message_data = await self.redis.get(message_key)
            if not message_data:
                return False
            
            message_dict = json.loads(message_data)
            message = Message.from_dict(message_dict)
            message.retry_count += 1
            
            # Remove from processing queue
            await self.redis.zrem(processing_queue, message_id)
            
            if requeue and message.retry_count <= message.max_retries:
                # Requeue with exponential backoff
                delay_seconds = 2 ** message.retry_count
                message.status = MessageStatus.PENDING
                
                # Update message data
                updated_data = json.dumps(message.to_dict())
                await self.redis.set(message_key, updated_data)
                
                # Requeue with lower priority (subtract retry count from priority)
                priority_queue = f"{queue_name}:priority"
                adjusted_priority = max(1, message.priority.value - message.retry_count)
                
                # Delay requeue using Redis keyspace notifications or separate delayed queue
                await asyncio.sleep(delay_seconds)  # Simple delay, better to use Redis keyspace notifications
                await self.redis.zadd(priority_queue, {message_id: adjusted_priority})
                
            else:
                # Move to dead letter queue
                message.status = MessageStatus.DEAD_LETTER
                dlq_name = f"{queue_name}{self.dead_letter_queue_suffix}"
                
                updated_data = json.dumps(message.to_dict())
                dlq_key = f"{dlq_name}:messages:{message_id}"
                dlq_priority_queue = f"{dlq_name}:priority"
                
                pipe = self.redis.pipeline()
                pipe.set(dlq_key, updated_data)
                pipe.zadd(dlq_priority_queue, {message_id: message.priority.value})
                pipe.delete(message_key)  # Remove from original queue
                await pipe.execute()
            
            # Remove from local processing queue
            if queue_name in self.processing_queues:
                self.processing_queues[queue_name].pop(message_id, None)
            
            return True
            
        except Exception as e:
            print(f"Error nacking message: {e}")
            return False
    
    async def get_queue_size(self, queue_name: str) -> int:
        """Get total queue size (pending + processing)"""
        if not self.redis:
            await self.connect()
        
        try:
            priority_queue = f"{queue_name}:priority"
            processing_queue = f"{queue_name}:processing"
            
            pending_count = await self.redis.zcard(priority_queue)
            processing_count = await self.redis.zcard(processing_queue)
            
            return pending_count + processing_count
            
        except Exception as e:
            print(f"Error getting queue size: {e}")
            return 0
    
    async def cleanup_expired_messages(self, queue_name: str, timeout_seconds: int = 300) -> int:
        """Clean up messages that have been processing too long"""
        if not self.redis:
            await self.connect()
        
        try:
            processing_queue = f"{queue_name}:processing"
            current_time = time.time()
            timeout_threshold = current_time - timeout_seconds
            
            # Get messages that have been processing too long
            expired_messages = await self.redis.zrangebyscore(
                processing_queue, 0, timeout_threshold
            )
            
            cleaned_count = 0
            for message_id in expired_messages:
                # Nack the expired message to trigger retry or DLQ
                if await self.nack(queue_name, message_id, requeue=True):
                    cleaned_count += 1
            
            return cleaned_count
            
        except Exception as e:
            print(f"Error cleaning up expired messages: {e}")
            return 0

class MessageProducer:
    """High-level message producer with routing and reliability features"""
    
    def __init__(self, message_queue: MessageQueue):
        self.message_queue = message_queue
        self.routing_rules: Dict[str, Callable[[Message], str]] = {}
    
    async def send_message(
        self,
        queue_name: str,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        headers: Optional[Dict[str, str]] = None,
        ttl_seconds: Optional[int] = None,
        correlation_id: Optional[str] = None,
        reply_to: Optional[str] = None
    ) -> str:
        """Send message to queue"""
        
        message_id = str(uuid.uuid4())
        expires_at = None
        
        if ttl_seconds:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        
        message = Message(
            id=message_id,
            payload=payload,
            headers=headers or {},
            priority=priority,
            expires_at=expires_at,
            correlation_id=correlation_id,
            reply_to=reply_to
        )
        
        # Apply routing rules if configured
        if queue_name in self.routing_rules:
            actual_queue = self.routing_rules[queue_name](message)
        else:
            actual_queue = queue_name
        
        success = await self.message_queue.enqueue(actual_queue, message)
        
        if success:
            return message_id
        else:
            raise Exception(f"Failed to send message to queue: {actual_queue}")
    
    def add_routing_rule(self, queue_name: str, routing_function: Callable[[Message], str]):
        """Add routing rule for dynamic queue selection"""
        self.routing_rules[queue_name] = routing_function

class MessageConsumer:
    """High-level message consumer with automatic retry and error handling"""
    
    def __init__(self, message_queue: MessageQueue, queue_name: str):
        self.message_queue = message_queue
        self.queue_name = queue_name
        self.message_handlers: Dict[str, Callable] = {}
        self.middleware: List[Callable] = []
        self.is_running = False
        self.consumer_task: Optional[asyncio.Task] = None
        
    def register_handler(self, message_type: str, handler: Callable[[Message], Any]):
        """Register message handler for specific message type"""
        self.message_handlers[message_type] = handler
    
    def add_middleware(self, middleware: Callable[[Message], None]):
        """Add middleware for message processing pipeline"""
        self.middleware.append(middleware)
    
    async def start_consuming(self, concurrency: int = 1):
        """Start consuming messages"""
        self.is_running = True
        
        # Start multiple concurrent workers
        tasks = []
        for i in range(concurrency):
            task = asyncio.create_task(self._consume_worker(f"worker-{i}"))
            tasks.append(task)
        
        # Wait for all workers to complete
        await asyncio.gather(*tasks)
    
    async def stop_consuming(self):
        """Stop consuming messages"""
        self.is_running = False
        
        if self.consumer_task:
            self.consumer_task.cancel()
            try:
                await self.consumer_task
            except asyncio.CancelledError:
                pass
    
    async def _consume_worker(self, worker_id: str):
        """Worker coroutine for consuming messages"""
        
        while self.is_running:
            try:
                # Dequeue message with timeout
                message = await self.message_queue.dequeue(self.queue_name, timeout=5.0)
                
                if message:
                    await self._process_message(message, worker_id)
                else:
                    # No message available, short sleep
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                print(f"Error in consumer worker {worker_id}: {e}")
                await asyncio.sleep(1)  # Error backoff
    
    async def _process_message(self, message: Message, worker_id: str):
        """Process a single message"""
        
        try:
            # Apply middleware
            for middleware in self.middleware:
                await middleware(message)
            
            # Determine message type
            message_type = message.headers.get('type', 'default')
            
            # Find appropriate handler
            handler = self.message_handlers.get(message_type)
            
            if handler:
                # Execute handler
                result = await handler(message)
                
                # Acknowledge successful processing
                await self.message_queue.acknowledge(self.queue_name, message.id)
                
                print(f"Worker {worker_id} processed message {message.id} of type {message_type}")
                
            else:
                print(f"No handler found for message type: {message_type}")
                # Acknowledge to prevent reprocessing
                await self.message_queue.acknowledge(self.queue_name, message.id)
                
        except Exception as e:
            print(f"Error processing message {message.id}: {e}")
            
            # Negative acknowledge to trigger retry
            await self.message_queue.nack(self.queue_name, message.id, requeue=True)

# Example usage and request-reply pattern
class RequestReplyManager:
    """Manages request-reply messaging patterns"""
    
    def __init__(self, message_queue: MessageQueue):
        self.message_queue = message_queue
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.reply_consumer: Optional[MessageConsumer] = None
        
    async def start(self):
        """Start reply consumer"""
        self.reply_consumer = MessageConsumer(self.message_queue, "replies")
        self.reply_consumer.register_handler("reply", self._handle_reply)
        
        # Start consuming replies in background
        asyncio.create_task(self.reply_consumer.start_consuming())
    
    async def send_request(
        self,
        request_queue: str,
        payload: Dict[str, Any],
        timeout_seconds: int = 30
    ) -> Dict[str, Any]:
        """Send request and wait for reply"""
        
        correlation_id = str(uuid.uuid4())
        
        # Create future for reply
        reply_future = asyncio.Future()
        self.pending_requests[correlation_id] = reply_future
        
        # Send request
        producer = MessageProducer(self.message_queue)
        await producer.send_message(
            queue_name=request_queue,
            payload=payload,
            headers={"type": "request"},
            correlation_id=correlation_id,
            reply_to="replies"
        )
        
        try:
            # Wait for reply with timeout
            reply = await asyncio.wait_for(reply_future, timeout=timeout_seconds)
            return reply
            
        except asyncio.TimeoutError:
            # Clean up pending request
            self.pending_requests.pop(correlation_id, None)
            raise TimeoutError(f"Request timed out after {timeout_seconds} seconds")
        
        finally:
            # Clean up pending request
            self.pending_requests.pop(correlation_id, None)
    
    async def _handle_reply(self, message: Message):
        """Handle incoming reply message"""
        
        correlation_id = message.correlation_id
        
        if correlation_id and correlation_id in self.pending_requests:
            future = self.pending_requests[correlation_id]
            
            if not future.done():
                future.set_result(message.payload)
```

#### Message Ordering and Persistence

```python
import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import sqlite3
import aiosqlite
from enum import Enum

class OrderingStrategy(Enum):
    FIFO = "FIFO"  # First In, First Out
    LIFO = "LIFO"  # Last In, First Out
    PRIORITY = "PRIORITY"  # Priority-based
    TIMESTAMP = "TIMESTAMP"  # Timestamp-based

@dataclass
class OrderedMessage:
    id: str
    sequence_number: int
    partition_key: Optional[str]
    payload: Dict[str, Any]
    timestamp: datetime
    priority: int = 5
    
class PersistentOrderedQueue:
    """Persistent message queue with configurable ordering guarantees"""
    
    def __init__(self, db_path: str, queue_name: str, ordering: OrderingStrategy = OrderingStrategy.FIFO):
        self.db_path = db_path
        self.queue_name = queue_name
        self.ordering = ordering
        self.sequence_counter = 0
        
    async def initialize(self):
        """Initialize database schema"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    queue_name TEXT NOT NULL,
                    sequence_number INTEGER NOT NULL,
                    partition_key TEXT,
                    payload TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    priority INTEGER DEFAULT 5,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_queue_sequence (queue_name, sequence_number),
                    INDEX idx_queue_partition (queue_name, partition_key),
                    INDEX idx_queue_status (queue_name, status)
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS queue_metadata (
                    queue_name TEXT PRIMARY KEY,
                    last_sequence_number INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.commit()
            
            # Initialize sequence counter
            cursor = await db.execute(
                'SELECT last_sequence_number FROM queue_metadata WHERE queue_name = ?',
                (self.queue_name,)
            )
            result = await cursor.fetchone()
            
            if result:
                self.sequence_counter = result[0]
            else:
                await db.execute(
                    'INSERT INTO queue_metadata (queue_name, last_sequence_number) VALUES (?, 0)',
                    (self.queue_name,)
                )
                await db.commit()
    
    async def enqueue(self, message: OrderedMessage) -> bool:
        """Enqueue message with ordering guarantees"""
        
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Assign sequence number
                self.sequence_counter += 1
                message.sequence_number = self.sequence_counter
                
                # Insert message
                await db.execute('''
                    INSERT INTO messages 
                    (id, queue_name, sequence_number, partition_key, payload, timestamp, priority, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
                ''', (
                    message.id,
                    self.queue_name,
                    message.sequence_number,
                    message.partition_key,
                    json.dumps(message.payload),
                    message.timestamp.isoformat(),
                    message.priority
                ))
                
                # Update sequence counter in metadata
                await db.execute(
                    'UPDATE queue_metadata SET last_sequence_number = ? WHERE queue_name = ?',
                    (self.sequence_counter, self.queue_name)
                )
                
                await db.commit()
                return True
                
            except Exception as e:
                print(f"Error enqueuing message: {e}")
                await db.rollback()
                return False
    
    async def dequeue(self, partition_key: Optional[str] = None) -> Optional[OrderedMessage]:
        """Dequeue message respecting ordering strategy"""
        
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Build query based on ordering strategy
                base_query = '''
                    SELECT id, sequence_number, partition_key, payload, timestamp, priority
                    FROM messages 
                    WHERE queue_name = ? AND status = 'pending'
                '''
                
                params = [self.queue_name]
                
                # Add partition filter if specified
                if partition_key:
                    base_query += ' AND partition_key = ?'
                    params.append(partition_key)
                
                # Add ordering clause
                if self.ordering == OrderingStrategy.FIFO:
                    base_query += ' ORDER BY sequence_number ASC'
                elif self.ordering == OrderingStrategy.LIFO:
                    base_query += ' ORDER BY sequence_number DESC'
                elif self.ordering == OrderingStrategy.PRIORITY:
                    base_query += ' ORDER BY priority DESC, sequence_number ASC'
                elif self.ordering == OrderingStrategy.TIMESTAMP:
                    base_query += ' ORDER BY timestamp ASC'
                
                base_query += ' LIMIT 1'
                
                cursor = await db.execute(base_query, params)
                result = await cursor.fetchone()
                
                if result:
                    message_id, seq_num, part_key, payload, timestamp, priority = result
                    
                    # Mark as processing
                    await db.execute(
                        'UPDATE messages SET status = "processing" WHERE id = ?',
                        (message_id,)
                    )
                    await db.commit()
                    
                    return OrderedMessage(
                        id=message_id,
                        sequence_number=seq_num,
                        partition_key=part_key,
                        payload=json.loads(payload),
                        timestamp=datetime.fromisoformat(timestamp),
                        priority=priority
                    )
                
                return None
                
            except Exception as e:
                print(f"Error dequeuing message: {e}")
                await db.rollback()
                return None
    
    async def acknowledge(self, message_id: str) -> bool:
        """Acknowledge message completion"""
        
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    'UPDATE messages SET status = "completed" WHERE id = ?',
                    (message_id,)
                )
                await db.commit()
                return True
                
            except Exception as e:
                print(f"Error acknowledging message: {e}")
                return False
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get comprehensive queue statistics"""
        
        async with aiosqlite.connect(self.db_path) as db:
            # Get message counts by status
            cursor = await db.execute('''
                SELECT status, COUNT(*) as count
                FROM messages 
                WHERE queue_name = ?
                GROUP BY status
            ''', (self.queue_name,))
            
            status_counts = {row[0]: row[1] for row in await cursor.fetchall()}
            
            # Get partition distribution
            cursor = await db.execute('''
                SELECT partition_key, COUNT(*) as count
                FROM messages 
                WHERE queue_name = ? AND status = 'pending'
                GROUP BY partition_key
            ''', (self.queue_name,))
            
            partition_counts = {row[0]: row[1] for row in await cursor.fetchall()}
            
            return {
                'queue_name': self.queue_name,
                'ordering_strategy': self.ordering.value,
                'current_sequence': self.sequence_counter,
                'status_distribution': status_counts,
                'partition_distribution': partition_counts,
                'total_pending': status_counts.get('pending', 0),
                'total_processing': status_counts.get('processing', 0),
                'total_completed': status_counts.get('completed', 0)
            }

class PartitionedQueue:
    """Message queue with partition-based ordering guarantees"""
    
    def __init__(self, db_path: str, queue_name: str):
        self.db_path = db_path
        self.queue_name = queue_name
        self.partition_queues: Dict[str, PersistentOrderedQueue] = {}
    
    async def get_partition_queue(self, partition_key: str) -> PersistentOrderedQueue:
        """Get or create partition-specific queue"""
        
        if partition_key not in self.partition_queues:
            partition_queue_name = f"{self.queue_name}:partition:{partition_key}"
            queue = PersistentOrderedQueue(self.db_path, partition_queue_name)
            await queue.initialize()
            self.partition_queues[partition_key] = queue
        
        return self.partition_queues[partition_key]
    
    async def enqueue_to_partition(self, partition_key: str, message: OrderedMessage) -> bool:
        """Enqueue message to specific partition"""
        
        message.partition_key = partition_key
        partition_queue = await self.get_partition_queue(partition_key)
        return await partition_queue.enqueue(message)
    
    async def dequeue_from_partition(self, partition_key: str) -> Optional[OrderedMessage]:
        """Dequeue message from specific partition"""
        
        partition_queue = await self.get_partition_queue(partition_key)
        return await partition_queue.dequeue()
    
    async def dequeue_round_robin(self) -> Optional[OrderedMessage]:
        """Dequeue message using round-robin across partitions"""
        
        if not self.partition_queues:
            return None
        
        # Try each partition in round-robin fashion
        for partition_key in self.partition_queues:
            message = await self.dequeue_from_partition(partition_key)
            if message:
                return message
        
        return None
```

### Publish-Subscribe Patterns

Publish-Subscribe messaging enables loose coupling between message producers and consumers through topic-based message distribution.

#### Advanced Topic-Based Messaging

```python
import asyncio
import json
import re
from typing import Dict, List, Set, Optional, Callable, Any, Pattern
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import fnmatch
import weakref

class SubscriptionType(Enum):
    EXACT_MATCH = "EXACT_MATCH"
    WILDCARD = "WILDCARD"
    REGEX = "REGEX"
    CONTENT_FILTER = "CONTENT_FILTER"

@dataclass
class TopicMessage:
    topic: str
    payload: Dict[str, Any]
    headers: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass
class Subscription:
    id: str
    subscriber_id: str
    topic_pattern: str
    subscription_type: SubscriptionType
    content_filter: Optional[Callable[[TopicMessage], bool]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    message_count: int = 0
    last_message_at: Optional[datetime] = None

class TopicManager:
    """Advanced topic management with hierarchical topics and pattern matching"""
    
    def __init__(self):
        self.topics: Set[str] = set()
        self.subscriptions: Dict[str, Subscription] = {}
        self.subscriber_callbacks: Dict[str, Callable[[TopicMessage], None]] = {}
        self.topic_hierarchy_separator = "."
        
        # Pre-compiled patterns for performance
        self.wildcard_patterns: Dict[str, Pattern] = {}
        self.regex_patterns: Dict[str, Pattern] = {}
    
    def create_topic(self, topic_name: str) -> bool:
        """Create a new topic"""
        
        if not self._is_valid_topic_name(topic_name):
            raise ValueError(f"Invalid topic name: {topic_name}")
        
        self.topics.add(topic_name)
        
        # Auto-create parent topics for hierarchical structure
        self._create_parent_topics(topic_name)
        
        return True
    
    def _is_valid_topic_name(self, topic_name: str) -> bool:
        """Validate topic name format"""
        
        # Topic names should be alphanumeric with dots, hyphens, underscores
        pattern = r'^[a-zA-Z0-9._-]+$'
        return bool(re.match(pattern, topic_name))
    
    def _create_parent_topics(self, topic_name: str) -> None:
        """Auto-create parent topics in hierarchy"""
        
        parts = topic_name.split(self.topic_hierarchy_separator)
        
        for i in range(1, len(parts)):
            parent_topic = self.topic_hierarchy_separator.join(parts[:i])
            self.topics.add(parent_topic)
    
    def subscribe(
        self,
        subscriber_id: str,
        topic_pattern: str,
        callback: Callable[[TopicMessage], None],
        subscription_type: SubscriptionType = SubscriptionType.EXACT_MATCH,
        content_filter: Optional[Callable[[TopicMessage], bool]] = None
    ) -> str:
        """Subscribe to topic with various matching strategies"""
        
        subscription_id = f"{subscriber_id}:{str(uuid.uuid4())}"
        
        subscription = Subscription(
            id=subscription_id,
            subscriber_id=subscriber_id,
            topic_pattern=topic_pattern,
            subscription_type=subscription_type,
            content_filter=content_filter
        )
        
        self.subscriptions[subscription_id] = subscription
        self.subscriber_callbacks[subscription_id] = callback
        
        # Pre-compile patterns for performance
        if subscription_type == SubscriptionType.WILDCARD:
            self.wildcard_patterns[subscription_id] = self._compile_wildcard_pattern(topic_pattern)
        elif subscription_type == SubscriptionType.REGEX:
            self.regex_patterns[subscription_id] = re.compile(topic_pattern)
        
        return subscription_id
    
    def _compile_wildcard_pattern(self, pattern: str) -> Pattern:
        """Compile wildcard pattern to regex"""
        
        # Convert wildcard pattern to regex
        # * matches any characters within a level
        # ** matches any characters across levels
        
        escaped = re.escape(pattern)
        
        # Replace escaped wildcards with regex equivalents
        regex_pattern = escaped.replace(r'\*\*', '.*')  # ** -> .*
        regex_pattern = regex_pattern.replace(r'\*', '[^.]*')  # * -> [^.]*
        regex_pattern = f'^{regex_pattern}$'
        
        return re.compile(regex_pattern)
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from topic"""
        
        if subscription_id in self.subscriptions:
            del self.subscriptions[subscription_id]
            del self.subscriber_callbacks[subscription_id]
            
            # Clean up pre-compiled patterns
            self.wildcard_patterns.pop(subscription_id, None)
            self.regex_patterns.pop(subscription_id, None)
            
            return True
        
        return False
    
    async def publish(self, topic: str, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> int:
        """Publish message to topic and deliver to matching subscribers"""
        
        message = TopicMessage(
            topic=topic,
            payload=payload,
            headers=headers or {}
        )
        
        # Find matching subscriptions
        matching_subscriptions = self._find_matching_subscriptions(message)
        
        # Deliver message to subscribers
        delivery_count = 0
        for subscription_id in matching_subscriptions:
            try:
                callback = self.subscriber_callbacks[subscription_id]
                
                # Apply content filter if specified
                subscription = self.subscriptions[subscription_id]
                if subscription.content_filter and not subscription.content_filter(message):
                    continue
                
                # Deliver message asynchronously
                asyncio.create_task(self._deliver_message(callback, message))
                
                # Update subscription stats
                subscription.message_count += 1
                subscription.last_message_at = datetime.utcnow()
                
                delivery_count += 1
                
            except Exception as e:
                print(f"Error delivering message to subscription {subscription_id}: {e}")
        
        return delivery_count
    
    def _find_matching_subscriptions(self, message: TopicMessage) -> List[str]:
        """Find subscriptions that match the message topic"""
        
        matching_subscriptions = []
        
        for subscription_id, subscription in self.subscriptions.items():
            if not subscription.is_active:
                continue
            
            if self._topic_matches_subscription(message.topic, subscription):
                matching_subscriptions.append(subscription_id)
        
        return matching_subscriptions
    
    def _topic_matches_subscription(self, topic: str, subscription: Subscription) -> bool:
        """Check if topic matches subscription pattern"""
        
        if subscription.subscription_type == SubscriptionType.EXACT_MATCH:
            return topic == subscription.topic_pattern
        
        elif subscription.subscription_type == SubscriptionType.WILDCARD:
            pattern = self.wildcard_patterns.get(subscription.id)
            return pattern and pattern.match(topic) is not None
        
        elif subscription.subscription_type == SubscriptionType.REGEX:
            pattern = self.regex_patterns.get(subscription.id)
            return pattern and pattern.match(topic) is not None
        
        elif subscription.subscription_type == SubscriptionType.CONTENT_FILTER:
            # Content filtering is applied during delivery, so all topics match initially
            return True
        
        return False
    
    async def _deliver_message(self, callback: Callable[[TopicMessage], None], message: TopicMessage) -> None:
        """Deliver message to subscriber callback"""
        
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(message)
            else:
                callback(message)
                
        except Exception as e:
            print(f"Error in subscriber callback: {e}")
    
    def get_topic_stats(self) -> Dict[str, Any]:
        """Get comprehensive topic and subscription statistics"""
        
        active_subscriptions = [s for s in self.subscriptions.values() if s.is_active]
        
        subscription_by_type = {}
        for sub in active_subscriptions:
            sub_type = sub.subscription_type.value
            subscription_by_type[sub_type] = subscription_by_type.get(sub_type, 0) + 1
        
        return {
            'total_topics': len(self.topics),
            'total_subscriptions': len(active_subscriptions),
            'subscription_by_type': subscription_by_type,
            'topics': list(self.topics),
            'subscriptions': [
                {
                    'id': sub.id,
                    'subscriber_id': sub.subscriber_id,
                    'topic_pattern': sub.topic_pattern,
                    'type': sub.subscription_type.value,
                    'message_count': sub.message_count,
                    'last_message_at': sub.last_message_at.isoformat() if sub.last_message_at else None
                }
                for sub in active_subscriptions
            ]
        }

class ContentBasedRouter:
    """Advanced content-based message routing"""
    
    def __init__(self, topic_manager: TopicManager):
        self.topic_manager = topic_manager
        self.routing_rules: List[Callable[[TopicMessage], Optional[str]]] = []
    
    def add_routing_rule(self, rule: Callable[[TopicMessage], Optional[str]]) -> None:
        """Add content-based routing rule"""
        self.routing_rules.append(rule)
    
    async def route_message(self, message: TopicMessage) -> List[str]:
        """Route message based on content and return target topics"""
        
        target_topics = [message.topic]  # Always include original topic
        
        # Apply routing rules
        for rule in self.routing_rules:
            try:
                additional_topic = rule(message)
                if additional_topic and additional_topic not in target_topics:
                    target_topics.append(additional_topic)
            except Exception as e:
                print(f"Error in routing rule: {e}")
        
        return target_topics
    
    async def publish_with_routing(
        self, 
        topic: str, 
        payload: Dict[str, Any], 
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, int]:
        """Publish message with content-based routing"""
        
        message = TopicMessage(topic=topic, payload=payload, headers=headers or {})
        
        # Determine target topics
        target_topics = await self.route_message(message)
        
        # Publish to each target topic
        delivery_results = {}
        for target_topic in target_topics:
            message.topic = target_topic
            delivery_count = await self.topic_manager.publish(target_topic, payload, headers)
            delivery_results[target_topic] = delivery_count
        
        return delivery_results

# Example content-based routing rules
def priority_based_routing(message: TopicMessage) -> Optional[str]:
    """Route high-priority messages to priority topic"""
    
    priority = message.headers.get('priority', 'normal')
    
    if priority == 'high':
        return f"{message.topic}.priority"
    
    return None

def geographic_routing(message: TopicMessage) -> Optional[str]:
    """Route messages based on geographic region"""
    
    region = message.payload.get('region')
    
    if region:
        return f"{message.topic}.region.{region}"
    
    return None

def size_based_routing(message: TopicMessage) -> Optional[str]:
    """Route large messages to dedicated topic"""
    
    message_size = len(json.dumps(message.payload))
    
    if message_size > 1024 * 1024:  # 1MB
        return f"{message.topic}.large"
    
    return None
```

This expanded Architecture Messaging document now includes comprehensive implementations of message queue patterns, publish-subscribe systems, ordering guarantees, persistence mechanisms, and advanced routing strategies. Each pattern is demonstrated with production-ready code examples that can be adapted for real-world messaging architectures.