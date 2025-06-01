Amazon Simple Notification Service (SNS) is a fully managed pub/sub messaging service for decoupling applications and enabling fan-out messaging to multiple subscribers.

## Core Concepts

|Component|Description|
|---|---|
|**Topic**|Communication channel for messages|
|**Publisher**|Application that sends messages to topic|
|**Subscriber**|Endpoint that receives messages from topic|
|**Message**|Data sent through SNS (up to 256KB)|
|**Subscription**|Configuration linking topic to endpoint|

---

## Topic Types

### Standard Topics

|Feature|Description|
|---|---|
|**Throughput**|Nearly unlimited TPS|
|**Message Order**|Best-effort ordering|
|**Delivery**|At-least-once delivery|
|**Duplicates**|Possible duplicate delivery|
|**Use Case**|High throughput, eventual consistency|

### FIFO Topics

|Feature|Description|
|---|---|
|**Throughput**|300 TPS (3,000 with batching)|
|**Message Order**|Strict FIFO order|
|**Delivery**|Exactly-once delivery|
|**Duplicates**|Prevented by deduplication|
|**Naming**|Must end with `.fifo`|
|**Use Case**|Order-critical applications|
|**SQS FIFO Only**|Can only fan-out to SQS FIFO queues|

---

## Supported Protocols & Endpoints

### HTTP/HTTPS

|Feature|Details|
|---|---|
|**URL Format**|Must be publicly accessible|
|**Confirmation**|Requires subscription confirmation|
|**Retry Policy**|Configurable with exponential backoff|
|**Timeout**|15 seconds default|
|**Message Format**|JSON with SNS metadata|

### Email/Email-JSON

|Type|Use Case|Format|
|---|---|---|
|**Email**|Human notifications|Plain text subject + body|
|**Email-JSON**|Application processing|Full JSON message structure|

### SMS

|Feature|Details|
|---|---|
|**Geographic Coverage**|200+ countries|
|**Message Length**|160 characters (GSM), 70 (Unicode)|
|**Delivery Receipt**|Optional delivery confirmations|
|**Opt-out**|Automatic STOP/START handling|
|**Pricing**|Varies by destination country|

### SQS Integration

|Feature|Benefit|
|---|---|
|**Fan-out Pattern**|One SNS → Multiple SQS queues|
|**Decoupling**|Asynchronous processing|
|**Reliability**|Message persistence in SQS|
|**Filtering**|Message filtering per subscription|
|**Cross-Account**|Different AWS accounts|

### Lambda

|Feature|Details|
|---|---|
|**Invocation**|Asynchronous execution|
|**Retry**|Automatic retries on failure|
|**Dead Letter Queue**|Failed invocation handling|
|**Concurrency**|Scales automatically|
|**Cross-Account**|Support for cross-account functions|

### Mobile Push Notifications

|Platform|Service|Use Case|
|---|---|---|
|**iOS**|Apple Push Notification Service (APNs)|iPhone, iPad apps|
|**Android**|Firebase Cloud Messaging (FCM)|Android apps|
|**Amazon**|Amazon Device Messaging (ADM)|Kindle Fire apps|
|**Windows**|Windows Push Notification Services (WNS)|Windows apps|
|**Baidu**|Baidu Cloud Push|Chinese Android market|

---

## Message Structure

### Standard Message Format

```json
{
  "Type": "Notification",
  "MessageId": "unique-message-id",
  "TopicArn": "arn:aws:sns:region:account:topic-name",
  "Subject": "Optional message subject",
  "Message": "Message content",
  "Timestamp": "2023-01-01T12:00:00.000Z",
  "SignatureVersion": "1",
  "Signature": "signature-string",
  "SigningCertURL": "certificate-url",
  "UnsubscribeURL": "unsubscribe-url"
}
```

### Message Attributes

|Attribute Type|Data Types|Use Case|
|---|---|---|
|**String**|UTF-8 text|Simple metadata|
|**Number**|Numeric values|Counters, IDs|
|**Binary**|Base64 encoded|Small binary data|
|**String.Array**|JSON array of strings|Multiple values|

---

## Message Filtering

### Filter Policies

- **JSON-based** - Define filtering criteria per subscription
- **Attribute Matching** - Filter on message attributes
- **Logical Operators** - AND, OR, NOT operations
- **Comparison Operators** - Numeric and string comparisons

### Filter Policy Examples

```json
{
  "event_type": ["order_placed", "order_cancelled"],
  "price": [{"numeric": [">", 100]}],
  "region": ["us-east-1", "us-west-2"],
  "customer_type": [{"anything-but": "internal"}]
}
```

### Filter Operators

|Operator|Example|Description|
|---|---|---|
|**Exact Match**|`["red", "blue"]`|String/number equality|
|**Anything-but**|`[{"anything-but": "red"}]`|Exclude specific values|
|**Numeric**|`[{"numeric": [">", 100]}]`|Numeric comparisons|
|**Prefix**|`[{"prefix": "order_"}]`|String prefix matching|
|**Exists**|`[{"exists": true}]`|Attribute presence check|

---

## Delivery Policies & Retry Logic

### HTTP/HTTPS Retry Policy

|Phase|Retries|Backoff|Total Duration|
|---|---|---|---|
|**Immediate**|3 retries|No delay|Immediate|
|**Pre-backoff**|2 retries|1 second|~2 seconds|
|**Backoff**|10 retries|Exponential (1s to 20s)|~5 minutes|
|**Post-backoff**|100,000 retries|20 seconds|~23 days|

### Retry Configuration

```json
{
  "healthyRetryPolicy": {
    "minDelayTarget": 1,
    "maxDelayTarget": 20,
    "numRetries": 3,
    "numMaxDelayRetries": 5,
    "backoffFunction": "exponential"
  }
}
```

### Dead Letter Queues

- **Failed Messages** - Capture undeliverable messages
- **SQS Integration** - Store failed messages for analysis
- **Redrive Policy** - Retry failed messages
- **Debugging** - Analyze delivery failures

---

## FIFO Topics Features

### Message Deduplication

|Method|Description|
|---|---|
|**Content-based**|SHA-256 hash of message body|
|**Message Deduplication ID**|Explicit deduplication token|
|**Time Window**|5-minute deduplication window|

### Message Grouping

- **Group ID** - Logical message grouping
- **Ordering** - FIFO within each group
- **Parallelism** - Different groups processed independently
- **SQS FIFO** - Must subscribe SQS FIFO queues only

---

## Security & Access Control

### Topic Policies

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"AWS": "arn:aws:iam::account:root"},
      "Action": "SNS:Publish",
      "Resource": "arn:aws:sns:region:account:topic-name",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "us-east-1"
        }
      }
    }
  ]
}
```

### IAM Permissions

#### Topic Management

```
sns:CreateTopic          - Create new topics
sns:DeleteTopic          - Delete topics
sns:GetTopicAttributes   - Retrieve topic metadata
sns:SetTopicAttributes   - Modify topic settings
sns:ListTopics          - List account topics
```

#### Publishing & Subscribing

```
sns:Publish             - Send messages to topic
sns:Subscribe           - Create subscriptions
sns:Unsubscribe         - Remove subscriptions
sns:ListSubscriptions   - List topic subscriptions
```

### Encryption

#### Server-Side Encryption

- **SSE with AWS KMS** - Customer managed keys
- **Key Policies** - Control access to encryption keys
- **Automatic Decryption** - Transparent for subscribers

#### Message Signing

- **Digital Signatures** - Verify message authenticity
- **Certificate Validation** - Verify SNS origin
- **Signature Verification** - Prevent message tampering

---

## Monitoring & Troubleshooting

### CloudWatch Metrics

#### Publishing Metrics

```
NumberOfMessagesPublished    - Messages sent to topic
NumberOfNotificationsFailed  - Failed deliveries
NumberOfNotificationsDelivered - Successful deliveries
PublishSize                  - Message size distribution
```

#### Subscription Metrics

```
NumberOfNotificationsFailed         - Per-protocol failures
NumberOfNotificationsFilteredOut    - Messages filtered
NumberOfNotificationsDelivered      - Per-protocol successes
```

### Common Issues & Solutions

|Issue|Cause|Solution|
|---|---|---|
|**HTTP 403 Errors**|Invalid topic policy|Update resource-based policy|
|**Message Not Delivered**|Invalid endpoint|Verify endpoint accessibility|
|**Subscription Pending**|Unconfirmed subscription|Confirm via email/HTTP|
|**High Latency**|Retry backoff|Optimize endpoint response time|
|**Message Filtering**|Incorrect filter policy|Validate JSON filter syntax|

---

## Integration Patterns

### Fan-Out Architecture

```
Producer → SNS Topic → Multiple SQS Queues → Different Services
```

### Event-Driven Microservices

```
Order Service → SNS → [Inventory, Payment, Shipping] Services
```

### Multi-Protocol Notifications

```
SNS Topic → [Email, SMS, Mobile Push, Lambda, SQS]
```

### Cross-Account Messaging

```
Account A Publisher → SNS Topic → Account B Subscriber
```

---

## Message Archival & Replay

### Message Archival

- **Kinesis Data Firehose** - Archive all messages to S3
- **Lambda Integration** - Custom archival logic
- **CloudWatch Logs** - Message logging for audit
- **S3 Integration** - Long-term storage

### Message Replay

- **Archive Analysis** - Process historical messages
- **Lambda Replay** - Re-trigger processing functions
- **SQS Redrive** - Replay failed messages from DLQ
- **Custom Solutions** - Application-specific replay logic

---

## Performance & Scaling

### Throughput Optimization

#### Standard Topics

- **Concurrent Publishers** - Scale publishers horizontally
- **Batch Publishing** - Use PublishBatch API (up to 10 messages)
- **Message Attributes** - Optimize filtering performance
- **Regional Distribution** - Multiple topics across regions

#### FIFO Topics

- **Message Groups** - Use multiple groups for parallelism
- **Batching** - Publish up to 10 messages per batch
- **SQS FIFO Integration** - Optimize downstream processing

### Cost Optimization

- **Message Filtering** - Reduce unnecessary deliveries
- **Appropriate Protocols** - Choose cost-effective endpoints
- **Regional Considerations** - SMS pricing varies by region
- **Batch Operations** - Reduce API call costs

---

## Pricing Model

### Publishing

- **Standard** - $0.50 per million requests
- **FIFO** - $0.60 per million requests
- **Mobile Push** - $0.50 per million notifications

### Delivery by Protocol

|Protocol|Price per Million|
|---|---|
|**HTTP/HTTPS**|$0.60|
|**Email/Email-JSON**|$2.00|
|**SMS**|Varies by country ($0.0075 - $0.25+ per message)|
|**SQS**|$0.00 (no additional charge)|
|**Lambda**|$0.00 (Lambda charges apply)|
|**Mobile Push**|$0.50|

### Free Tier

- **1 Million Requests** - SNS requests per month
- **1 Million Notifications** - HTTP, Email, SQS
- **1,000 SMS** - To US phone numbers
- **1 Million Mobile Push** - Notifications

---

## Best Practices

### Topic Design

- **Naming Convention** - Use descriptive, consistent names
- **Topic Granularity** - Balance between specificity and reuse
- **Message Structure** - Consistent JSON schema
- **Versioning Strategy** - Handle schema evolution

### Message Publishing

```python
import boto3
import json

sns = boto3.client('sns')

# Standard message with attributes
response = sns.publish(
    TopicArn='arn:aws:sns:region:account:topic-name',
    Message=json.dumps({
        'event': 'order_placed',
        'order_id': '12345',
        'amount': 99.99
    }),
    MessageAttributes={
        'event_type': {
            'DataType': 'String',
            'StringValue': 'order_placed'
        },
        'priority': {
            'DataType': 'Number',  
            'StringValue': '1'
        }
    }
)
```

### Subscription Management

- **Confirmation Handling** - Automate subscription confirmation
- **Filter Policies** - Use precise filtering to reduce costs
- **Dead Letter Queues** - Handle failed deliveries
- **Monitoring** - Set up CloudWatch alarms

### Error Handling

- **Idempotent Processing** - Handle duplicate messages
- **Graceful Degradation** - Handle endpoint failures
- **Exponential Backoff** - Implement in HTTP endpoints
- **Circuit Breakers** - Prevent cascade failures

### Security

- **Principle of Least Privilege** - Minimal required permissions
- **Resource Policies** - Control topic access
- **Encryption** - Enable for sensitive data
- **Message Signing** - Verify message authenticity

## Common Use Cases

- **Microservices Decoupling** - Event-driven architecture
- **Fan-Out Messaging** - One-to-many communication
- **Real-Time Notifications** - User alerts and updates
- **System Alerts** - Infrastructure monitoring
- **Workflow Orchestration** - Multi-step process coordination
- **Data Pipeline Triggers** - ETL process initiation
- **Mobile App Notifications** - Push notifications to devices
- **Email Campaigns** - Bulk email distribution
- **SMS Notifications** - Text message alerts
- **Cross-System Integration** - Legacy system connectivity