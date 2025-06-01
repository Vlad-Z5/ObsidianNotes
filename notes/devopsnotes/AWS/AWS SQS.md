Amazon Simple Queue Service (SQS) is a fully managed message queuing service for decoupling and scaling microservices, distributed systems, and serverless applications.

## Queue Types Comparison

|Feature|Standard Queue|FIFO Queue|
|---|---|---|
|**Throughput**|Nearly unlimited TPS|300 TPS (3,000 with batching)|
|**Message Order**|Best-effort ordering|Strict FIFO order|
|**Delivery**|At-least-once|Exactly-once processing|
|**Duplicates**|Possible|Prevented by deduplication|
|**Naming**|Any valid name|Must end with `.fifo`|
|**Use Case**|High throughput, eventual consistency|Order-critical applications|

---

## Core Concepts

### Message Lifecycle

1. **Producer** sends message to queue
2. **Message** stored redundantly across multiple servers
3. **Consumer** polls queue for messages
4. **Visibility Timeout** hides message from other consumers
5. **Consumer** processes message and deletes it
6. **Message** permanently removed from queue

### Key Terminology

|Term|Definition|
|---|---|
|**Message**|Unit of data sent through queue (up to 256KB)|
|**Queue**|Temporary repository for messages|
|**Producer**|Component that sends messages|
|**Consumer**|Component that receives and processes messages|
|**Receipt Handle**|Temporary identifier for message processing|

---

## Configuration Parameters

### Message Settings

|Parameter|Range|Default|Description|
|---|---|---|---|
|**Message Retention**|1 minute - 14 days|4 days|How long messages stay in queue|
|**Message Size**|1 byte - 256 KB|-|Size per message|
|**Delivery Delay**|0 - 15 minutes|0 seconds|Delay before message available|
|**Receive Message Wait Time**|0 - 20 seconds|0 seconds|Long polling duration|

### Queue Settings

|Parameter|Range|Default|Description|
|---|---|---|---|
|**Visibility Timeout**|0 seconds - 12 hours|30 seconds|Message invisible duration|
|**Max Receive Count**|1 - 1,000|-|Retries before DLQ|
|**Content-Based Deduplication**|Enable/Disable|Disabled|FIFO duplicate detection|

---

## Message Attributes

### System Attributes

```
MessageId                    - Unique message identifier
ReceiptHandle               - Temporary processing handle  
MD5OfBody                   - Message body checksum
Body                        - Message content
Attributes.SenderId         - Sender's AWS account ID
Attributes.SentTimestamp    - Message send time
Attributes.ApproximateReceiveCount - Delivery attempt count
```

### Custom Attributes

- **Data Types** - String, Number, Binary
- **Maximum** - 10 custom attributes per message
- **Size Limit** - Name + value ≤ 256KB (counts toward message size)

### Extended Client Library

- **S3 Integration** - Store large messages (>256KB) in S3
- **Automatic Handling** - Library manages S3 storage/retrieval
- **Pointer Message** - SQS contains S3 object reference
- **Size Limit** - Up to 2GB via S3

---

## Polling Mechanisms

### Short Polling (Default)

- **Behavior** - Returns immediately (even if queue empty)
- **Sampling** - Queries subset of servers
- **Empty Responses** - May return no messages when messages exist
- **Cost** - Higher due to frequent empty responses
- **Use Case** - Immediate response required

### Long Polling (Recommended)

- **Behavior** - Waits for messages up to WaitTimeSeconds
- **Sampling** - Queries all servers
- **Efficiency** - Eliminates empty responses
- **Configuration** - Set ReceiveMessageWaitTimeSeconds (1-20)
- **Benefits** - Lower cost, reduced API calls, faster message delivery

```
Recommended Setting: 20 seconds (maximum)
```

---

## FIFO Queue Features

### Message Deduplication

#### Deduplication Methods

|Method|Description|Use Case|
|---|---|---|
|**Message Deduplication ID**|Explicit dedup token|Custom logic|
|**Content-Based**|SHA-256 hash of body|Simple deduplication|

#### Deduplication Scope

- **Time Window** - 5 minutes
- **Behavior** - Duplicate messages rejected within window
- **Token Length** - Up to 128 characters

### Message Grouping

- **Group ID** - Logical grouping of messages
- **Ordering** - FIFO within each group
- **Parallelism** - Different groups processed in parallel
- **Throughput** - 300 TPS per group

```
Example Groups:
- user-123 (user-specific operations)
- order-456 (order processing workflow)
- payment-789 (payment transactions)
```

---

## Dead Letter Queues (DLQ)

### Configuration

- **Max Receive Count** - Failed processing threshold (1-1,000)
- **DLQ Target** - Must be same type (Standard/FIFO)
- **Retention** - Typically longer than source queue
- **Redrive Policy** - Automatic message movement

### Message Flow

```
Source Queue → Processing Failure → Retry (Max Count) → DLQ
```

### Best Practices

- **Separate DLQ** - One DLQ per source queue
- **Extended Retention** - 14 days for analysis
- **Monitoring** - CloudWatch alarms on DLQ depth
- **Redrive** - Process messages back to source after fixing issues

### Redrive to Source

- **Feature** - Move messages from DLQ back to source
- **Use Case** - After fixing processing issues
- **Configuration** - Set maxReceiveCount for redrive

---

## Security & Access Control

### IAM Policies

#### Queue-Level Permissions

```
sqs:CreateQueue          - Create new queues
sqs:DeleteQueue          - Delete queues  
sqs:GetQueueAttributes   - Retrieve queue metadata
sqs:SetQueueAttributes   - Modify queue settings
sqs:ListQueues          - List account queues
```

#### Message-Level Permissions

```
sqs:SendMessage         - Send messages to queue
sqs:ReceiveMessage      - Receive messages from queue
sqs:DeleteMessage       - Delete processed messages
sqs:ChangeMessageVisibility - Modify visibility timeout
```

### Resource-Based Policies

- **Cross-Account Access** - Allow other AWS accounts
- **Service Integration** - SNS, Lambda, S3 event notifications
- **Condition Keys** - Source IP, request time, etc.

### Encryption

#### Encryption at Rest

- **SSE-SQS** - AWS managed keys (free)
- **SSE-KMS** - Customer managed keys
- **Key Rotation** - Automatic with AWS managed keys

#### Encryption in Transit

- **HTTPS** - All API calls encrypted by default
- **TLS 1.2** - Minimum encryption standard

---

## Monitoring & Troubleshooting

### CloudWatch Metrics

#### Queue Metrics

```
ApproximateNumberOfMessages          - Messages available
ApproximateNumberOfMessagesVisible   - Messages not in flight
ApproximateNumberOfMessagesNotVisible - Messages being processed
NumberOfMessagesSent                 - Messages sent to queue
NumberOfMessagesReceived             - Messages retrieved
NumberOfMessagesDeleted              - Messages deleted
```

#### Performance Metrics

```
ApproximateAgeOfOldestMessage       - Oldest message age
NumberOfEmptyReceives               - Empty polling responses
```

### Common Issues & Solutions

|Issue|Cause|Solution|
|---|---|---|
|**Message Loss**|Not deleting after processing|Implement proper delete logic|
|**Duplicate Processing**|Short visibility timeout|Increase visibility timeout|
|**High Latency**|Short polling|Enable long polling|
|**Poison Messages**|Processing failures|Configure DLQ|
|**Throttling**|High request rate|Implement exponential backoff|

---

## Integration Patterns

### Lambda Integration

```
SQS Queue → Lambda Function (Event Source Mapping)
- Batch Size: 1-10 messages
- Concurrent Executions: Up to 1,000
- Error Handling: Automatic retries + DLQ
```

### SNS-SQS Fan-Out

```
SNS Topic → Multiple SQS Queues → Different Processing Services
- Decoupled microservices
- Parallel processing
- Service-specific filtering
```

### Cross-Service Communication

```
Service A → SQS → Service B
- Asynchronous communication
- Retry mechanism
- Load leveling
```

---

## Performance & Scaling

### Throughput Optimization

#### Standard Queues

- **Concurrent Consumers** - Scale consumers horizontally
- **Batch Operations** - Use SendMessageBatch/ReceiveMessageBatch
- **Multiple Queues** - Distribute load across queues
- **Connection Pooling** - Reuse HTTP connections

#### FIFO Queues

- **Message Groups** - Use multiple groups for parallelism
- **Batching** - Send up to 10 messages per batch
- **High Throughput** - Enable for 3,000 TPS per queue

### Cost Optimization

- **Long Polling** - Reduce empty receives
- **Batching** - Reduce API call count
- **Message Lifecycle** - Set appropriate retention periods
- **Reserved Capacity** - Not available (pay-per-use only)

---

## Pricing Model

### Request Pricing

- **Standard** - $0.40 per million requests (first 1 million free/month)
- **FIFO** - $0.50 per million requests
- **Batch Requests** - Each batch counts as one request

### Data Transfer

- **Within AWS** - Free between SQS and other AWS services in same region
- **Internet** - Standard data transfer rates apply

### Free Tier

- **1 Million Requests** - Per month for Standard queues
- **Perpetual** - Free tier doesn't expire

---

## Best Practices

### Message Design

- **Idempotent Processing** - Handle duplicate messages gracefully
- **Message Size** - Keep messages small, use S3 for large payloads
- **Structured Data** - Use JSON for complex message formats
- **Correlation IDs** - Include tracking identifiers

### Queue Management

- **Naming Convention** - Use descriptive, consistent names
- **Environment Separation** - Separate dev/staging/prod queues
- **Monitoring** - Set up CloudWatch alarms
- **Cleanup** - Delete unused queues to avoid costs

### Consumer Implementation

```python
# Recommended consumer pattern
import boto3
import json

sqs = boto3.client('sqs')
queue_url = 'https://sqs.region.amazonaws.com/account/queue-name'

while True:
    # Long polling
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=20,
        VisibilityTimeoutSeconds=300
    )
    
    messages = response.get('Messages', [])
    for message in messages:
        try:
            # Process message
            process_message(json.loads(message['Body']))
            
            # Delete after successful processing
            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=message['ReceiptHandle']
            )
        except Exception as e:
            # Let message return to queue for retry
            print(f"Processing failed: {e}")
```

### Error Handling

- **Exponential Backoff** - Implement for temporary failures
- **Circuit Breaker** - Prevent cascade failures
- **DLQ Strategy** - Monitor and process failed messages
- **Logging** - Comprehensive error logging for debugging

## Common Use Cases

- **Microservices Decoupling** - Async communication between services
- **Work Queues** - Background job processing
- **Load Leveling** - Smooth traffic spikes
- **Event-Driven Architecture** - React to system events
- **Batch Processing** - Collect and process data in batches
- **Order Processing** - E-commerce transaction workflows
- **Image/Video Processing** - Media processing pipelines
- **Notification Systems** - Reliable message delivery