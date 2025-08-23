# AWS SQS: Enterprise Message Queuing & Asynchronous Processing Platform

> **Service Type:** Application Integration | **Scope:** Regional | **Serverless:** Yes

## Overview

Amazon Simple Queue Service (SQS) is a fully managed message queuing service that enables reliable, scalable, and cost-effective decoupling of microservices, distributed systems, and serverless applications. It provides enterprise-grade message delivery guarantees, supports both standard and FIFO queuing patterns, and integrates seamlessly with AWS services to build resilient, event-driven architectures at any scale.

## Core Architecture Components

- **Standard Queues:** High-throughput, at-least-once delivery with best-effort ordering
- **FIFO Queues:** Exactly-once processing with strict first-in-first-out message ordering
- **Dead Letter Queues:** Automated handling of failed messages for debugging and reprocessing
- **Message Attributes:** Structured metadata for filtering, routing, and processing logic
- **Visibility Timeout:** Configurable message locking during processing to prevent duplication
- **Long Polling:** Efficient message retrieval that reduces empty responses and costs
- **Batch Operations:** High-performance APIs for sending and receiving multiple messages
- **Integration Points:** Native integration with Lambda, SNS, EventBridge, and other AWS services

## DevOps & Enterprise Use Cases

### Microservices Communication & Decoupling
- **Service-to-Service Messaging:** Asynchronous communication between distributed microservices
- **Event-Driven Architecture:** Reliable event processing with guaranteed message delivery
- **API Rate Limiting:** Queue management for backend processing to prevent service overload
- **Service Mesh Integration:** Message queuing layer for complex service interdependencies

### DevOps Automation & CI/CD
- **Build Pipeline Coordination:** Queue-based job distribution across build agents and environments
- **Deployment Orchestration:** Sequential and parallel deployment task management
- **Infrastructure Automation:** Automated provisioning and configuration management workflows
- **Monitoring & Alerting:** Queue-based alert processing and incident response automation

### Data Processing & Analytics
- **ETL Pipeline Management:** Reliable data transformation job queuing and processing
- **Batch Processing Workflows:** Large-scale data processing with fault tolerance and retry mechanisms
- **Real-time Analytics:** Stream processing coordination for data ingestion and analysis
- **Log Processing:** Centralized log collection and processing from distributed applications

### Enterprise Integration & Legacy Systems
- **Legacy System Integration:** Bridge between modern cloud services and existing enterprise applications
- **Cross-Account Communication:** Secure message passing between different AWS accounts and organizational units
- **Partner System Integration:** Reliable message exchange with external business partners
- **Compliance & Audit Workflows:** Message queuing for regulatory reporting and audit trail processing

## Queue Types Comparison

|Feature|Standard Queue|FIFO Queue|
|---|---|---|
|**Throughput**|Nearly unlimited TPS|300 TPS (3,000 with batching)|
|**Message Order**|Best-effort ordering|Strict FIFO order|
|**Delivery**|At-least-once|Exactly-once processing|
|**Duplicates**|Possible|Prevented by deduplication|
|**Naming**|Any valid name|Must end with `.fifo`|
|**Use Case**|High throughput, eventual consistency|Order-critical applications|

## Enterprise Implementation Examples

### Example 1: E-commerce Order Processing Pipeline

**Business Requirement:** Process 50,000+ orders per hour with guaranteed order sequence, inventory management, payment processing, and shipping coordination across multiple microservices.

**Implementation Steps:**

1. **FIFO Queue Architecture Setup**
   ```bash
   # Create order processing FIFO queue
   aws sqs create-queue \
     --queue-name order-processing-pipeline.fifo \
     --attributes '{
       "FifoQueue": "true",
       "ContentBasedDeduplication": "true",
       "MessageRetentionPeriod": "1209600",
       "VisibilityTimeoutSeconds": "300",
       "RedrivePolicy": "{\"deadLetterTargetArn\":\"arn:aws:sqs:us-east-1:123456789012:order-processing-dlq.fifo\",\"maxReceiveCount\":3}"
     }' \
     --tags Key=Environment,Value=Production Key=Service,Value=OrderProcessing
   ```

2. **Multi-Service Processing Implementation**
   ```python
   import boto3
   import json
   import hashlib
   from typing import Dict, Any, List
   from datetime import datetime
   
   class EnterpriseOrderProcessor:
       def __init__(self):
           self.sqs = boto3.client('sqs')
           self.order_queue_url = 'https://sqs.us-east-1.amazonaws.com/123456789012/order-processing-pipeline.fifo'
           self.inventory_queue_url = 'https://sqs.us-east-1.amazonaws.com/123456789012/inventory-updates.fifo'
           self.payment_queue_url = 'https://sqs.us-east-1.amazonaws.com/123456789012/payment-processing.fifo'
           
       def process_order_placement(self, order_data: Dict[str, Any]):
           """Process new order with guaranteed sequence"""
           
           # Generate message group ID for customer-specific ordering
           group_id = f"customer-{order_data['customer_id']}"
           
           # Create order processing message
           order_message = {
               'event_type': 'order_placed',
               'order_id': order_data['order_id'],
               'customer_id': order_data['customer_id'],
               'items': order_data['items'],
               'total_amount': order_data['total_amount'],
               'timestamp': datetime.utcnow().isoformat(),
               'processing_stage': 'validation'
           }
           
           # Send to order processing queue with deduplication
           response = self.sqs.send_message(
               QueueUrl=self.order_queue_url,
               MessageBody=json.dumps(order_message),
               MessageGroupId=group_id,
               MessageDeduplicationId=f"order-{order_data['order_id']}-{int(datetime.utcnow().timestamp())}",
               MessageAttributes={
                   'event_type': {'StringValue': 'order_placed', 'DataType': 'String'},
                   'customer_tier': {'StringValue': order_data.get('customer_tier', 'standard'), 'DataType': 'String'},
                   'order_priority': {'StringValue': str(order_data.get('priority', 1)), 'DataType': 'Number'}
               }
           )
           
           return response['MessageId']
       
       def process_order_workflow(self):
           """Process orders from queue with enterprise error handling"""
           
           while True:
               try:
                   # Long polling for efficient message retrieval
                   response = self.sqs.receive_message(
                       QueueUrl=self.order_queue_url,
                       MaxNumberOfMessages=10,
                       WaitTimeSeconds=20,
                       MessageAttributeNames=['All'],
                       AttributeNames=['All']
                   )
                   
                   messages = response.get('Messages', [])
                   
                   for message in messages:
                       try:
                           order_data = json.loads(message['Body'])
                           
                           # Process based on current stage
                           if order_data['processing_stage'] == 'validation':
                               self.validate_order(order_data, message)
                           elif order_data['processing_stage'] == 'inventory_check':
                               self.check_inventory(order_data, message)
                           elif order_data['processing_stage'] == 'payment_processing':
                               self.process_payment(order_data, message)
                           elif order_data['processing_stage'] == 'fulfillment':
                               self.initiate_fulfillment(order_data, message)
                               
                           # Delete message after successful processing
                           self.sqs.delete_message(
                               QueueUrl=self.order_queue_url,
                               ReceiptHandle=message['ReceiptHandle']
                           )
                           
                       except Exception as processing_error:
                           print(f"Order processing failed: {processing_error}")
                           # Message will return to queue for retry
                           
               except Exception as polling_error:
                   print(f"Polling error: {polling_error}")
                   time.sleep(5)  # Brief delay before retry
       
       def validate_order(self, order_data: Dict[str, Any], message: Dict[str, Any]):
           """Validate order and proceed to inventory check"""
           
           # Perform order validation logic
           if self.is_valid_order(order_data):
               # Update processing stage and send to next step
               order_data['processing_stage'] = 'inventory_check'
               order_data['validation_timestamp'] = datetime.utcnow().isoformat()
               
               self.sqs.send_message(
                   QueueUrl=self.order_queue_url,
                   MessageBody=json.dumps(order_data),
                   MessageGroupId=f"customer-{order_data['customer_id']}",
                   MessageDeduplicationId=f"order-{order_data['order_id']}-inventory-{int(datetime.utcnow().timestamp())}"
               )
           else:
               # Send to validation failure queue for manual review
               self.handle_validation_failure(order_data)
   ```

3. **Cross-Service Integration with SNS Fan-out**
   ```python
   def setup_cross_service_integration(self):
       """Setup SQS queues for different services with SNS fan-out"""
       
       service_queues = {
           'inventory-service': {
               'queue_name': 'inventory-service-orders',
               'filter_policy': {
                   'event_type': ['order_placed', 'order_cancelled'],
                   'requires_inventory_check': ['true']
               }
           },
           'payment-service': {
               'queue_name': 'payment-service-orders', 
               'filter_policy': {
                   'event_type': ['inventory_confirmed', 'payment_retry'],
                   'payment_required': ['true']
               }
           },
           'shipping-service': {
               'queue_name': 'shipping-service-orders',
               'filter_policy': {
                   'event_type': ['payment_confirmed'],
                   'shipping_required': ['true']
               }
           }
       }
       
       for service, config in service_queues.items():
           # Create service-specific queue
           queue_response = self.sqs.create_queue(
               QueueName=config['queue_name'],
               Attributes={
                   'MessageRetentionPeriod': '1209600',  # 14 days
                   'VisibilityTimeoutSeconds': '300',
                   'RedrivePolicy': json.dumps({
                       'deadLetterTargetArn': f'arn:aws:sqs:us-east-1:123456789012:{service}-dlq',
                       'maxReceiveCount': 3
                   })
               }
           )
           
           # Subscribe queue to SNS topic with filtering
           sns = boto3.client('sns')
           sns.subscribe(
               TopicArn='arn:aws:sns:us-east-1:123456789012:order-events',
               Protocol='sqs',
               Endpoint=queue_response['QueueUrl'],
               Attributes={
                   'FilterPolicy': json.dumps(config['filter_policy'])
               }
           )
   ```

**Expected Outcome:** Process 50,000+ orders/hour with 99.9% processing accuracy, guaranteed order sequence per customer, automated error handling, and comprehensive audit trail.

### Example 2: DevOps Build Pipeline Coordination

**Business Requirement:** Coordinate build, test, and deployment jobs across multiple environments with priority queuing, resource allocation, and failure recovery.

**Implementation Steps:**

1. **Priority Queue System Setup**
   ```python
   class DevOpsPipelineManager:
       def __init__(self):
           self.sqs = boto3.client('sqs')
           self.queue_configs = {
               'critical': {
                   'queue_name': 'devops-critical-jobs',
                   'visibility_timeout': 1800,  # 30 minutes
                   'retention_period': 345600  # 4 days
               },
               'high': {
                   'queue_name': 'devops-high-priority-jobs', 
                   'visibility_timeout': 900,   # 15 minutes
                   'retention_period': 259200  # 3 days
               },
               'normal': {
                   'queue_name': 'devops-normal-jobs',
                   'visibility_timeout': 600,   # 10 minutes
                   'retention_period': 172800  # 2 days
               }
           }
           
       def create_pipeline_queues(self):
           """Create priority-based pipeline queues"""
           
           for priority, config in self.queue_configs.items():
               # Create main queue
               queue_response = self.sqs.create_queue(
                   QueueName=config['queue_name'],
                   Attributes={
                       'MessageRetentionPeriod': str(config['retention_period']),
                       'VisibilityTimeoutSeconds': str(config['visibility_timeout']),
                       'ReceiveMessageWaitTimeSeconds': '20',  # Long polling
                       'RedrivePolicy': json.dumps({
                           'deadLetterTargetArn': f'arn:aws:sqs:us-east-1:123456789012:{config["queue_name"]}-dlq',
                           'maxReceiveCount': 3
                       })
                   },
                   Tags={
                       'Environment': 'Production',
                       'Service': 'DevOpsPipeline',
                       'Priority': priority
                   }
               )
               
               # Create corresponding dead letter queue
               dlq_response = self.sqs.create_queue(
                   QueueName=f'{config["queue_name"]}-dlq',
                   Attributes={
                       'MessageRetentionPeriod': str(config['retention_period'] * 2)  # Longer retention for DLQ
                   }
               )
       
       def queue_build_job(self, job_data: Dict[str, Any]):
           """Queue build job with appropriate priority"""
           
           priority = self.determine_job_priority(job_data)
           queue_name = self.queue_configs[priority]['queue_name']
           queue_url = f'https://sqs.us-east-1.amazonaws.com/123456789012/{queue_name}'
           
           build_message = {
               'job_id': job_data['job_id'],
               'repository': job_data['repository'],
               'branch': job_data['branch'],
               'commit_sha': job_data['commit_sha'],
               'build_type': job_data['build_type'],
               'target_environment': job_data.get('target_environment', 'development'),
               'requester': job_data['requester'],
               'timestamp': datetime.utcnow().isoformat(),
               'estimated_duration': job_data.get('estimated_duration', 300)
           }
           
           response = self.sqs.send_message(
               QueueUrl=queue_url,
               MessageBody=json.dumps(build_message),
               MessageAttributes={
                   'priority': {'StringValue': priority, 'DataType': 'String'},
                   'build_type': {'StringValue': job_data['build_type'], 'DataType': 'String'},
                   'environment': {'StringValue': job_data.get('target_environment', 'development'), 'DataType': 'String'},
                   'estimated_duration': {'StringValue': str(job_data.get('estimated_duration', 300)), 'DataType': 'Number'}
               }
           )
           
           return response['MessageId']
   ```

**Expected Outcome:** Coordinate 1,000+ daily builds with priority-based processing, 95% first-time success rate, automated retry mechanisms, and detailed build analytics.

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

## Monitoring & Observability

### Key Metrics to Monitor

| Metric | Description | Threshold | Action |
|--------|-------------|-----------|---------|
| **ApproximateNumberOfMessages** | Messages available in queue | >1,000 per queue | Scale consumers or investigate processing delays |
| **ApproximateAgeOfOldestMessage** | Age of oldest unprocessed message | >300 seconds | Check consumer health and scaling |
| **NumberOfEmptyReceives** | Polling calls returning no messages | >50% of calls | Enable long polling to reduce costs |
| **ApproximateNumberOfMessagesNotVisible** | Messages being processed | >queue depth * 0.8 | Monitor for stuck messages or long processing |

### Advanced Monitoring Implementation

```python
import boto3
import json
from datetime import datetime, timedelta

class SQSMonitoringManager:
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
        self.sqs = boto3.client('sqs')
        
    def create_queue_monitoring_dashboard(self, queue_names: list):
        """Create comprehensive SQS monitoring dashboard"""
        
        dashboard_body = {
            "widgets": [
                {
                    "type": "metric",
                    "properties": {
                        "metrics": [
                            ["AWS/SQS", "ApproximateNumberOfMessages", "QueueName", queue_name]
                            for queue_name in queue_names
                        ],
                        "period": 300,
                        "stat": "Average",
                        "region": "us-east-1",
                        "title": "Queue Depth - Messages Available"
                    }
                },
                {
                    "type": "metric", 
                    "properties": {
                        "metrics": [
                            ["AWS/SQS", "ApproximateAgeOfOldestMessage", "QueueName", queue_name]
                            for queue_name in queue_names
                        ],
                        "period": 300,
                        "stat": "Maximum",
                        "region": "us-east-1",
                        "title": "Message Age - Processing Latency"
                    }
                }
            ]
        }
        
        self.cloudwatch.put_dashboard(
            DashboardName='SQS-Enterprise-Monitoring',
            DashboardBody=json.dumps(dashboard_body)
        )
    
    def setup_queue_alarms(self, queue_name: str, thresholds: dict):
        """Setup comprehensive CloudWatch alarms for queue"""
        
        alarms = [
            {
                'name': f'SQS-{queue_name}-HighQueueDepth',
                'metric': 'ApproximateNumberOfMessages',
                'threshold': thresholds.get('queue_depth', 1000),
                'comparison': 'GreaterThanThreshold',
                'description': f'High queue depth detected in {queue_name}'
            },
            {
                'name': f'SQS-{queue_name}-OldMessages',
                'metric': 'ApproximateAgeOfOldestMessage', 
                'threshold': thresholds.get('message_age', 300),
                'comparison': 'GreaterThanThreshold',
                'description': f'Old messages detected in {queue_name}'
            },
            {
                'name': f'SQS-{queue_name}-DeadLetterQueue',
                'metric': 'ApproximateNumberOfMessages',
                'queue_suffix': '-dlq',
                'threshold': 1,
                'comparison': 'GreaterThanOrEqualToThreshold',
                'description': f'Messages in dead letter queue for {queue_name}'
            }
        ]
        
        for alarm in alarms:
            queue_target = f'{queue_name}{alarm.get("queue_suffix", "")}'
            
            self.cloudwatch.put_metric_alarm(
                AlarmName=alarm['name'],
                ComparisonOperator=alarm['comparison'],
                EvaluationPeriods=2,
                MetricName=alarm['metric'],
                Namespace='AWS/SQS',
                Period=300,
                Statistic='Average',
                Threshold=alarm['threshold'],
                ActionsEnabled=True,
                AlarmActions=[
                    'arn:aws:sns:us-east-1:123456789012:sqs-alerts'
                ],
                AlarmDescription=alarm['description'],
                Dimensions=[
                    {
                        'Name': 'QueueName',
                        'Value': queue_target
                    }
                ],
                Unit='Count'
            )
```

### Common Issues & Solutions

|Issue|Cause|Solution|
|---|---|---|
|**Message Loss**|Not deleting after processing|Implement proper delete logic|
|**Duplicate Processing**|Short visibility timeout|Increase visibility timeout|
|**High Latency**|Short polling|Enable long polling|
|**Poison Messages**|Processing failures|Configure DLQ|
|**Throttling**|High request rate|Implement exponential backoff|

## Security & Compliance

### Security Best Practices
- **Principle of Least Privilege:** Grant minimal required SQS permissions using IAM policies with resource-specific ARNs
- **Enable Encryption:** Use SSE-KMS with customer-managed keys for sensitive message data
- **Access Logging:** Enable CloudTrail for comprehensive SQS API call auditing
- **Network Security:** Use VPC endpoints for private communication between VPC and SQS

### Compliance Frameworks
- **SOC 2 Type II:** SQS supports SOC compliance with encryption, access controls, and audit logging
- **HIPAA Compliance:** Encrypt PHI data using SSE-KMS and implement comprehensive access controls
- **PCI DSS:** Secure payment-related messages with encryption and network isolation
- **GDPR Compliance:** Support data portability and deletion with message retention policies

### Enterprise IAM Policy Example
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes"
      ],
      "Resource": "arn:aws:sqs:us-east-1:123456789012:order-processing-*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "us-east-1"
        },
        "DateLessThan": {
          "aws:RequestTime": "2024-12-31T23:59:59Z"
        },
        "IpAddress": {
          "aws:SourceIp": ["10.0.0.0/16", "192.168.0.0/16"]
        }
      }
    }
  ]
}
```

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