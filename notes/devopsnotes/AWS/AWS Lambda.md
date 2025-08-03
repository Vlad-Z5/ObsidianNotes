# AWS Lambda Quick Reference

## Core Concepts

- **Function** - Code that runs in response to events
- **Event** - JSON document that triggers function execution
- **Context** - Runtime information (request ID, time remaining, etc.)
- **Handler** - Entry point method in your code

## Supported Runtimes

|Language|Runtime Examples|
|---|---|
|**Python**|python3.9, python3.10, python3.11, python3.12|
|**Node.js**|nodejs18.x, nodejs20.x|
|**Java**|java8.al2, java11, java17, java21|
|**Go**|provided.al2 (custom runtime)|
|**Ruby**|ruby3.2|
|**.NET**|dotnet6, dotnet8|
|**Custom**|provided.al2, provided.al2023|

## Event Sources & Triggers

### Synchronous (Request-Response)

- **API Gateway** - REST/HTTP APIs
- **Application Load Balancer** - HTTP requests
- **Lambda Function URLs** - Direct HTTPS endpoint
- **AWS CLI/SDK** - Direct invocation

### Asynchronous (Fire-and-Forget)

- **S3** - Object events (create, delete, restore)
- **SNS** - Message publication
- **EventBridge** - Custom/scheduled events
- **CloudWatch Logs** - Log stream events
- **SES** - Email events

### Stream-Based (Poll-Based)

- **DynamoDB Streams** - Table changes
- **Kinesis Data Streams** - Real-time data
- **SQS** - Message queues (standard/FIFO)
- **MSK/Kafka** - Message streaming

## Execution Environment

### Limits & Configuration

|Setting|Range|Default|
|---|---|---|
|**Memory**|128 MB - 10,240 MB|128 MB|
|**Timeout**|1 sec - 15 min|3 sec|
|**Ephemeral Storage**|512 MB - 10,240 MB|512 MB|
|**Environment Variables**|0 - 4 KB total|-|
|**Layers**|0 - 5 per function|-|

### Runtime Lifecycle

1. **Init Phase** - Download code, start runtime, run init code
2. **Invoke Phase** - Run handler function
3. **Shutdown Phase** - Runtime shuts down (after inactivity)

## Concurrency Models

### Types

- **Unreserved** - Shared pool (default 1000 limit)
- **Reserved** - Dedicated capacity for function
- **Provisioned** - Pre-initialized execution environments

### Scaling Behavior

- **Initial Burst** - 1000 (us-west-2, us-east-1, eu-west-1) or 500 concurrent executions
- **Gradual Scale** - +500/min after initial burst
- **Cold Start** - New execution environment initialization delay

## Deployment Methods

### Code Packaging

|Method|Size Limit|Use Case|
|---|---|---|
|**Zip Archive**|50 MB (zipped), 250 MB (unzipped)|Small functions|
|**Container Image**|10 GB|Large dependencies|
|**Lambda Layers**|50 MB per layer|Shared libraries|

### Deployment Options

```
Console Upload    - Direct zip/container upload
AWS CLI          - aws lambda update-function-code
SAM              - Serverless Application Model
CDK              - Cloud Development Kit
Terraform        - Infrastructure as Code
```

## Versions & Aliases

### Versions

- **$LATEST** - Mutable, latest version
- **Numbered** - Immutable snapshots (1, 2, 3...)
- **Qualified ARN** - Includes version number

### Aliases

- **Pointer** - Points to specific version
- **Traffic Shifting** - Weighted routing between versions
- **Blue/Green** - Safe deployment pattern

## Networking & Security

### VPC Configuration

- **Subnets** - Private subnets recommended
- **Security Groups** - Control traffic
- **NAT Gateway** - Internet access from private subnet
- **ENI** - Elastic Network Interface creation overhead

### IAM & Permissions

- **Execution Role** - Permissions Lambda assumes
- **Resource Policy** - Who can invoke function
- **Environment Variables** - Plain text or encrypted

## Error Handling & Retry

### Invocation Types

|Type|Retry Behavior|Error Handling|
|---|---|---|
|**Synchronous**|No automatic retry|Return error to caller|
|**Asynchronous**|2 automatic retries|Dead Letter Queue (DLQ)|
|**Stream-based**|Retry until success/expiry|Configurable retry attempts|

### Dead Letter Queues

- **SQS** - Failed async invocations
- **SNS** - Failed async invocations
- **Destinations** - Success/failure routing

## Monitoring & Observability

### CloudWatch Metrics

```
Duration         - Execution time
Invocations      - Number of invocations
Errors           - Number of errors
Throttles        - Number of throttled invocations
ConcurrentExecutions - Concurrent executions
```

### Logging

- **CloudWatch Logs** - Automatic log group creation
- **Structured Logging** - JSON format recommended
- **X-Ray Tracing** - Distributed tracing support

## Pricing Model

### Cost Components

- **Requests** - $0.20 per 1M requests
- **Compute Time** - Price per GB-second
- **Provisioned Concurrency** - $0.0000041667 per GB-second

## Performance Optimization

### Cold Start Mitigation

- **Provisioned Concurrency** - Pre-warmed environments
- **Smaller Packages** - Faster download/initialization
- **Connection Reuse** - Initialize outside handler
- **Lambda SnapStart** - Java performance improvement

### Best Practices

```
Minimize Package Size    - Remove unused dependencies
Reuse Connections      - Database, HTTP clients
Use Environment Variables - Configuration management
Implement Proper Logging - Structured, searchable logs
Handle Timeouts        - Graceful degradation
```

## Integration Patterns

### API Gateway + Lambda

```
REST API     - Traditional REST endpoints
HTTP API     - Lower latency, lower cost
WebSocket    - Real-time bidirectional communication
```

### Event-Driven Architecture

```
S3 → Lambda           - File processing
DynamoDB → Lambda     - Change data capture  
SNS → Lambda          - Fan-out messaging
SQS → Lambda          - Queue processing
EventBridge → Lambda  - Event routing
```

## Common Use Cases

- **API Backends** - Serverless REST/GraphQL APIs
- **Data Processing** - ETL, image/video processing
- **Real-time Analytics** - Stream processing
- **Automation** - Infrastructure automation, backups
- **Webhooks** - Third-party integrations
- **Scheduled Tasks** - Cron-like functionality
- **Authentication** - Custom authorizers