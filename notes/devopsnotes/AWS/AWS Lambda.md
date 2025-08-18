# AWS Lambda

> **Service Type:** Serverless Compute | **Tier:** CI/CD and Automation | **Global/Regional:** Regional

## Overview

AWS Lambda is a serverless compute service that runs code in response to events without requiring server management. It automatically scales from zero to thousands of concurrent executions and enables event-driven architectures that are fundamental to modern DevOps practices.

## DevOps Use Cases

### Infrastructure Automation
- **Auto Scaling triggers** based on custom business logic and metrics
- **Infrastructure provisioning** using CloudFormation custom resources
- **Configuration management** automated deployment and updates
- **Cost optimization** by automatically stopping/starting non-production resources

### CI/CD Pipeline Integration
- **Build notifications** sending Slack/Teams alerts on build status
- **Deployment automation** triggering deployments based on git events
- **Testing automation** running integration tests after deployments
- **Approval workflows** custom approval logic for production deployments

### Event-Driven Operations
- **Security automation** responding to CloudTrail security events
- **Log processing** real-time log analysis and alerting
- **Backup automation** scheduled backups and lifecycle management
- **Compliance monitoring** automated compliance checks and reporting

### API and Webhook Integration
- **Webhook endpoints** for third-party service integrations
- **API backends** for internal tools and dashboards
- **Microservice communication** event-based service coordination
- **External API integrations** connecting to SaaS platforms and tools

### Data Processing and Analytics
- **Log aggregation** processing logs from multiple sources
- **Metrics transformation** converting raw data to actionable insights
- **Real-time analytics** processing streaming data for immediate insights
- **ETL operations** data transformation and loading pipelines

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

## Practical CLI Examples

### Function Management

```bash
# Create function with zip file
aws lambda create-function \
  --function-name MyAutomationFunction \
  --runtime python3.9 \
  --role arn:aws:iam::123456789012:role/lambda-execution-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://function.zip \
  --timeout 300 \
  --memory-size 256 \
  --environment Variables='{ENVIRONMENT=production,LOG_LEVEL=INFO}' \
  --tags Project=DevOps,Team=Infrastructure

# Update function code
aws lambda update-function-code \
  --function-name MyAutomationFunction \
  --zip-file fileb://updated-function.zip

# Update function configuration
aws lambda update-function-configuration \
  --function-name MyAutomationFunction \
  --timeout 600 \
  --memory-size 512 \
  --environment Variables='{ENVIRONMENT=production,LOG_LEVEL=DEBUG,SNS_TOPIC=arn:aws:sns:us-west-2:123456789012:alerts}'

# Invoke function synchronously
aws lambda invoke \
  --function-name MyAutomationFunction \
  --payload '{"action": "backup", "target": "database"}' \
  --cli-binary-format raw-in-base64-out \
  response.json

# Invoke function asynchronously
aws lambda invoke \
  --function-name MyAutomationFunction \
  --invocation-type Event \
  --payload '{"action": "cleanup", "environment": "staging"}' \
  --cli-binary-format raw-in-base64-out \
  response.json
```

### Version and Alias Management

```bash
# Publish version
aws lambda publish-version \
  --function-name MyAutomationFunction \
  --description "Stable release v1.2.3"

# Create alias pointing to version
aws lambda create-alias \
  --function-name MyAutomationFunction \
  --name PROD \
  --function-version 5 \
  --description "Production alias"

# Update alias with traffic shifting
aws lambda update-alias \
  --function-name MyAutomationFunction \
  --name PROD \
  --function-version 6 \
  --routing-config AdditionalVersionWeights='{5=0.1}'
```

### Event Source Mapping

```bash
# Create SQS trigger
aws lambda create-event-source-mapping \
  --function-name MyAutomationFunction \
  --event-source-arn arn:aws:sqs:us-west-2:123456789012:automation-queue \
  --batch-size 10 \
  --maximum-batching-window-in-seconds 5

# Create DynamoDB Streams trigger
aws lambda create-event-source-mapping \
  --function-name MyAutomationFunction \
  --event-source-arn arn:aws:dynamodb:us-west-2:123456789012:table/MyTable/stream/2024-01-15T00:00:00.000 \
  --starting-position LATEST \
  --batch-size 100

# Create S3 trigger (via S3 API)
aws s3api put-bucket-notification-configuration \
  --bucket my-automation-bucket \
  --notification-configuration '{
    "LambdaConfigurations": [{
      "Id": "ProcessNewFiles",
      "LambdaFunctionArn": "arn:aws:lambda:us-west-2:123456789012:function:MyAutomationFunction",
      "Events": ["s3:ObjectCreated:*"],
      "Filter": {
        "Key": {
          "FilterRules": [{
            "Name": "prefix",
            "Value": "uploads/"
          }]
        }
      }
    }]
  }'
```

### Monitoring and Debugging

```bash
# Get function metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=MyAutomationFunction \
  --start-time 2024-01-15T00:00:00Z \
  --end-time 2024-01-15T23:59:59Z \
  --period 3600 \
  --statistics Average,Maximum

# Get recent logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/MyAutomationFunction \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --filter-pattern 'ERROR'

# Enable X-Ray tracing
aws lambda update-function-configuration \
  --function-name MyAutomationFunction \
  --tracing-config Mode=Active
```

## DevOps Automation Scripts

### Deployment Notification Function

```python
# deploy-notification.py - Slack notification for deployments
import json
import boto3
import urllib3
import os

def lambda_handler(event, context):
    """Send deployment notifications to Slack"""
    
    # Parse CodePipeline event
    detail = event.get('detail', {})
    pipeline_name = detail.get('pipeline', 'Unknown')
    execution_id = detail.get('execution-id', 'Unknown')
    state = detail.get('state', 'Unknown')
    
    # Color coding for Slack
    colors = {
        'SUCCEEDED': 'good',
        'FAILED': 'danger',
        'STARTED': 'warning'
    }
    
    # Slack webhook URL from environment variable
    slack_webhook = os.environ['SLACK_WEBHOOK_URL']
    
    # Construct message
    message = {
        'attachments': [{
            'color': colors.get(state, 'warning'),
            'title': f'Deployment {state}',
            'fields': [
                {
                    'title': 'Pipeline',
                    'value': pipeline_name,
                    'short': True
                },
                {
                    'title': 'Execution ID',
                    'value': execution_id,
                    'short': True
                },
                {
                    'title': 'Status',
                    'value': state,
                    'short': True
                }
            ],
            'footer': 'AWS CodePipeline',
            'ts': context.aws_request_id
        }]
    }
    
    # Send to Slack
    http = urllib3.PoolManager()
    response = http.request('POST', slack_webhook,
                          body=json.dumps(message),
                          headers={'Content-Type': 'application/json'})
    
    return {
        'statusCode': 200,
        'body': json.dumps(f'Notification sent: {state}')
    }
```

### Infrastructure Automation Function

```python
# infrastructure-automation.py - Auto-scaling and cost optimization
import json
import boto3
import os
from datetime import datetime, timezone

def lambda_handler(event, context):
    """Automate infrastructure scaling and cost optimization"""
    
    ec2 = boto3.client('ec2')
    autoscaling = boto3.client('autoscaling')
    sns = boto3.client('sns')
    
    # Get environment from event or default
    environment = event.get('environment', 'staging')
    action = event.get('action', 'check')
    
    if action == 'scale_down_staging':
        return scale_down_staging_resources(ec2, autoscaling, sns)
    elif action == 'scale_up_staging':
        return scale_up_staging_resources(ec2, autoscaling, sns)
    elif action == 'cleanup_old_snapshots':
        return cleanup_old_snapshots(ec2, sns)
    else:
        return check_resource_utilization(ec2, sns)

def scale_down_staging_resources(ec2, autoscaling, sns):
    """Scale down staging resources for cost savings"""
    
    results = []
    
    # Stop EC2 instances tagged for automatic scaling
    response = ec2.describe_instances(
        Filters=[
            {'Name': 'tag:Environment', 'Values': ['staging']},
            {'Name': 'tag:AutoScale', 'Values': ['true']},
            {'Name': 'instance-state-name', 'Values': ['running']}
        ]
    )
    
    instance_ids = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_ids.append(instance['InstanceId'])
    
    if instance_ids:
        ec2.stop_instances(InstanceIds=instance_ids)
        results.append(f"Stopped {len(instance_ids)} staging instances")
    
    # Scale down Auto Scaling Groups
    asg_response = autoscaling.describe_auto_scaling_groups()
    for asg in asg_response['AutoScalingGroups']:
        for tag in asg.get('Tags', []):
            if tag['Key'] == 'Environment' and tag['Value'] == 'staging':
                autoscaling.update_auto_scaling_group(
                    AutoScalingGroupName=asg['AutoScalingGroupName'],
                    MinSize=0,
                    DesiredCapacity=0
                )
                results.append(f"Scaled down ASG: {asg['AutoScalingGroupName']}")
    
    # Send notification
    if results:
        sns.publish(
            TopicArn=os.environ['SNS_TOPIC_ARN'],
            Message=f"Staging resources scaled down:\n" + "\n".join(results),
            Subject="Infrastructure Automation: Staging Scale Down"
        )
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'action': 'scale_down_staging',
            'results': results
        })
    }

def cleanup_old_snapshots(ec2, sns):
    """Clean up EBS snapshots older than 30 days"""
    
    from datetime import timedelta
    
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
    
    # Get snapshots owned by this account
    response = ec2.describe_snapshots(OwnerIds=['self'])
    
    deleted_snapshots = []
    for snapshot in response['Snapshots']:
        start_time = snapshot['StartTime']
        if start_time < cutoff_date:
            # Check if snapshot is tagged for retention
            tags = {tag['Key']: tag['Value'] for tag in snapshot.get('Tags', [])}
            if tags.get('Retention') != 'permanent':
                try:
                    ec2.delete_snapshot(SnapshotId=snapshot['SnapshotId'])
                    deleted_snapshots.append(snapshot['SnapshotId'])
                except Exception as e:
                    print(f"Failed to delete {snapshot['SnapshotId']}: {str(e)}")
    
    # Send notification
    if deleted_snapshots:
        sns.publish(
            TopicArn=os.environ['SNS_TOPIC_ARN'],
            Message=f"Deleted {len(deleted_snapshots)} old snapshots:\n" + "\n".join(deleted_snapshots),
            Subject="Infrastructure Automation: Snapshot Cleanup"
        )
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'action': 'cleanup_old_snapshots',
            'deleted_count': len(deleted_snapshots),
            'snapshot_ids': deleted_snapshots
        })
    }
```

### Log Processing Function

```python
# log-processor.py - Real-time log analysis and alerting
import json
import boto3
import gzip
import base64
import re
import os

def lambda_handler(event, context):
    """Process CloudWatch Logs and send alerts for errors"""
    
    sns = boto3.client('sns')
    cloudwatch = boto3.client('cloudwatch')
    
    # Decode CloudWatch Logs data
    compressed_payload = base64.b64decode(event['awslogs']['data'])
    uncompressed_payload = gzip.decompress(compressed_payload)
    log_data = json.loads(uncompressed_payload)
    
    error_count = 0
    critical_errors = []
    
    # Process each log event
    for log_event in log_data['logEvents']:
        message = log_event['message']
        timestamp = log_event['timestamp']
        
        # Check for error patterns
        if is_error_message(message):
            error_count += 1
            
            # Check for critical errors
            if is_critical_error(message):
                critical_errors.append({
                    'timestamp': timestamp,
                    'message': message[:500]  # Truncate long messages
                })
    
    # Send CloudWatch metric
    cloudwatch.put_metric_data(
        Namespace='CustomApp/Errors',
        MetricData=[
            {
                'MetricName': 'ErrorCount',
                'Value': error_count,
                'Unit': 'Count',
                'Dimensions': [
                    {
                        'Name': 'LogGroup',
                        'Value': log_data['logGroup']
                    }
                ]
            }
        ]
    )
    
    # Send alert for critical errors
    if critical_errors:
        alert_message = f"Critical errors detected in {log_data['logGroup']}:\n\n"
        for error in critical_errors[:5]:  # Limit to 5 errors
            alert_message += f"Timestamp: {error['timestamp']}\n"
            alert_message += f"Message: {error['message']}\n\n"
        
        sns.publish(
            TopicArn=os.environ['ALERT_TOPIC_ARN'],
            Message=alert_message,
            Subject=f"CRITICAL: Errors in {log_data['logGroup']}"
        )
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'processed_events': len(log_data['logEvents']),
            'error_count': error_count,
            'critical_errors': len(critical_errors)
        })
    }

def is_error_message(message):
    """Check if log message indicates an error"""
    error_patterns = [
        r'\bERROR\b',
        r'\bFAILED\b',
        r'\bEXCEPTION\b',
        r'\b5\d\d\b',  # 5xx HTTP status codes
        r'\bTimeout\b',
        r'\bConnection.*failed\b'
    ]
    
    return any(re.search(pattern, message, re.IGNORECASE) for pattern in error_patterns)

def is_critical_error(message):
    """Check if error is critical and needs immediate attention"""
    critical_patterns = [
        r'\bDatabase.*connection.*failed\b',
        r'\bOut of memory\b',
        r'\bDisk.*full\b',
        r'\bSecurity.*violation\b',
        r'\b50[0-5]\b',  # 500-505 HTTP status codes
        r'\bFatal\b'
    ]
    
    return any(re.search(pattern, message, re.IGNORECASE) for pattern in critical_patterns)
```

### Backup Automation Function

```python
# backup-automation.py - Automated backup management
import json
import boto3
import os
from datetime import datetime, timedelta

def lambda_handler(event, context):
    """Automate backups for EC2 instances and RDS databases"""
    
    ec2 = boto3.client('ec2')
    rds = boto3.client('rds')
    sns = boto3.client('sns')
    
    backup_type = event.get('backup_type', 'all')
    environment = event.get('environment', 'production')
    
    results = []
    
    if backup_type in ['all', 'ec2']:
        ec2_results = backup_ec2_instances(ec2, environment)
        results.extend(ec2_results)
    
    if backup_type in ['all', 'rds']:
        rds_results = backup_rds_instances(rds, environment)
        results.extend(rds_results)
    
    # Clean up old backups
    cleanup_results = cleanup_old_backups(ec2, rds)
    results.extend(cleanup_results)
    
    # Send notification
    if results:
        message = f"Backup automation completed for {environment}:\n\n" + "\n".join(results)
        sns.publish(
            TopicArn=os.environ['SNS_TOPIC_ARN'],
            Message=message,
            Subject=f"Backup Report: {environment}"
        )
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'backup_type': backup_type,
            'environment': environment,
            'results': results
        })
    }

def backup_ec2_instances(ec2, environment):
    """Create snapshots of EC2 instances"""
    results = []
    
    # Get instances tagged for backup
    response = ec2.describe_instances(
        Filters=[
            {'Name': 'tag:Environment', 'Values': [environment]},
            {'Name': 'tag:Backup', 'Values': ['true']},
            {'Name': 'instance-state-name', 'Values': ['running', 'stopped']}
        ]
    )
    
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            instance_name = next((tag['Value'] for tag in instance.get('Tags', []) 
                                if tag['Key'] == 'Name'), instance_id)
            
            # Create snapshots of all EBS volumes
            for device in instance.get('BlockDeviceMappings', []):
                volume_id = device['Ebs']['VolumeId']
                
                snapshot = ec2.create_snapshot(
                    VolumeId=volume_id,
                    Description=f"Automated backup of {instance_name} ({instance_id}) - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                
                # Tag the snapshot
                ec2.create_tags(
                    Resources=[snapshot['SnapshotId']],
                    Tags=[
                        {'Key': 'Name', 'Value': f"{instance_name}-backup-{datetime.now().strftime('%Y%m%d')}"},
                        {'Key': 'Environment', 'Value': environment},
                        {'Key': 'InstanceId', 'Value': instance_id},
                        {'Key': 'VolumeId', 'Value': volume_id},
                        {'Key': 'AutomatedBackup', 'Value': 'true'},
                        {'Key': 'CreatedBy', 'Value': 'lambda-backup-automation'}
                    ]
                )
                
                results.append(f"Created snapshot {snapshot['SnapshotId']} for {instance_name}")
    
    return results

def backup_rds_instances(rds, environment):
    """Create snapshots of RDS instances"""
    results = []
    
    # Get RDS instances
    response = rds.describe_db_instances()
    
    for db_instance in response['DBInstances']:
        # Check if instance should be backed up
        db_identifier = db_instance['DBInstanceIdentifier']
        
        # Get tags to check environment and backup settings
        tags_response = rds.list_tags_for_resource(
            ResourceName=db_instance['DBInstanceArn']
        )
        
        tags = {tag['Key']: tag['Value'] for tag in tags_response['TagList']}
        
        if tags.get('Environment') == environment and tags.get('Backup') == 'true':
            snapshot_id = f"{db_identifier}-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            rds.create_db_snapshot(
                DBSnapshotIdentifier=snapshot_id,
                DBInstanceIdentifier=db_identifier
            )
            
            results.append(f"Created RDS snapshot {snapshot_id} for {db_identifier}")
    
    return results

def cleanup_old_backups(ec2, rds):
    """Remove backups older than retention period"""
    results = []
    retention_days = int(os.environ.get('BACKUP_RETENTION_DAYS', '7'))
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    
    # Clean up old EBS snapshots
    snapshots = ec2.describe_snapshots(OwnerIds=['self'])
    for snapshot in snapshots['Snapshots']:
        tags = {tag['Key']: tag['Value'] for tag in snapshot.get('Tags', [])}
        
        if (tags.get('AutomatedBackup') == 'true' and 
            snapshot['StartTime'].replace(tzinfo=None) < cutoff_date):
            
            ec2.delete_snapshot(SnapshotId=snapshot['SnapshotId'])
            results.append(f"Deleted old snapshot {snapshot['SnapshotId']}")
    
    # Clean up old RDS snapshots
    db_snapshots = rds.describe_db_snapshots(SnapshotType='manual')
    for snapshot in db_snapshots['DBSnapshots']:
        if (snapshot['DBSnapshotIdentifier'].endswith('-backup-') and
            snapshot['SnapshotCreateTime'].replace(tzinfo=None) < cutoff_date):
            
            rds.delete_db_snapshot(
                DBSnapshotIdentifier=snapshot['DBSnapshotIdentifier']
            )
            results.append(f"Deleted old RDS snapshot {snapshot['DBSnapshotIdentifier']}")
    
    return results
```

### Deployment Script Using AWS CLI

```bash
#!/bin/bash
# deploy-lambda-function.sh - Deploy Lambda function with proper error handling

FUNCTION_NAME=$1
SOURCE_DIR=$2
ENVIRONMENT=${3:-production}

if [ $# -lt 2 ]; then
    echo "Usage: $0 <function-name> <source-directory> [environment]"
    exit 1
fi

echo "Deploying Lambda function: ${FUNCTION_NAME}"

# Build and package function
cd ${SOURCE_DIR}

# Install dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt -t .
fi

# Create deployment package
echo "Creating deployment package..."
zip -r function.zip . -x "*.git*" "*.pyc" "__pycache__/*" "tests/*" "*.md"

# Update function code
echo "Updating function code..."
aws lambda update-function-code \
    --function-name ${FUNCTION_NAME} \
    --zip-file fileb://function.zip

# Wait for update to complete
echo "Waiting for update to complete..."
aws lambda wait function-updated --function-name ${FUNCTION_NAME}

# Publish new version
echo "Publishing new version..."
VERSION=$(aws lambda publish-version \
    --function-name ${FUNCTION_NAME} \
    --description "Deployment $(date -Iseconds)" \
    --query 'Version' \
    --output text)

echo "Published version: ${VERSION}"

# Update alias
ALIAS_NAME=$(echo ${ENVIRONMENT} | tr '[:lower:]' '[:upper:]')
aws lambda update-alias \
    --function-name ${FUNCTION_NAME} \
    --name ${ALIAS_NAME} \
    --function-version ${VERSION}

echo "Updated alias ${ALIAS_NAME} to point to version ${VERSION}"

# Test function
echo "Testing function..."
aws lambda invoke \
    --function-name ${FUNCTION_NAME}:${ALIAS_NAME} \
    --payload '{"test": true}' \
    --cli-binary-format raw-in-base64-out \
    test-response.json

if [ $? -eq 0 ]; then
    echo "Function test successful"
    cat test-response.json
else
    echo "Function test failed"
    exit 1
fi

# Cleanup
rm -f function.zip test-response.json

echo "Deployment completed successfully!"
```

## Best Practices

### Performance Optimization
- **Package Size:** Minimize deployment package size for faster cold starts
- **Memory Allocation:** Right-size memory allocation (affects CPU and cost)
- **Connection Reuse:** Initialize database connections outside the handler
- **Provisioned Concurrency:** Use for latency-sensitive applications

### Security Best Practices
- **IAM Roles:** Use least privilege principle for execution roles
- **Environment Variables:** Encrypt sensitive data using AWS KMS
- **VPC Configuration:** Use private subnets for database access
- **Input Validation:** Always validate and sanitize input data

### Monitoring and Debugging
- **Structured Logging:** Use JSON format for easy parsing and analysis
- **Custom Metrics:** Send business-specific metrics to CloudWatch
- **X-Ray Tracing:** Enable for distributed tracing in complex architectures
- **Error Handling:** Implement proper error handling and retry logic

### Cost Optimization
- **Right-sizing:** Monitor duration and memory usage to optimize configuration
- **Provisioned Concurrency:** Use only when necessary due to additional cost
- **Request Routing:** Use aliases for traffic shifting and canary deployments
- **Lifecycle Management:** Clean up unused versions and aliases