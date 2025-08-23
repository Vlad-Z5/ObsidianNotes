# AWS DynamoDB

## Overview

AWS DynamoDB is a fully managed NoSQL database service that provides fast and predictable performance with seamless scalability. It supports both document and key-value data models, offers built-in security, backup and restore, and in-memory caching capabilities.

### Core Concepts

- **Table** - Collection of items (rows)
- **Item** - Record with attributes (max 400KB)
- **Attribute** - Key-value pair (name + value + type)
- **Primary Key** - Partition Key (PK) or Composite (PK + Sort Key)

### Capacity Modes

|Mode|Scaling|Pricing|Use Case|
|---|---|---|---|
|**On-Demand**|Automatic|Pay-per-request|Unpredictable traffic|
|**Provisioned**|Manual/Auto|RCU/WCU based|Predictable traffic|

## Core Architecture Components

### Key Types

- **Partition Key (PK)** - Determines item location, must be unique for simple PK
- **Sort Key (SK)** - Optional, enables range queries, PK+SK must be unique
- **Composite Key** - PK + SK combination

### Secondary Indexes

#### Global Secondary Index (GSI)

- Different PK/SK from base table
- Eventually consistent reads only
- Has own provisioned throughput
- Can be created/deleted anytime
- Max 20 per table

#### Local Secondary Index (LSI)

- Same PK as base table, different SK
- Strongly/eventually consistent reads
- Shares table's provisioned throughput
- Must be created at table creation
- Max 10 per table
- 10GB limit per partition key value

## DevOps & Enterprise Use Cases

### Application Development
- **Microservices Data Store** - Independent data persistence per service
- **Session Management** - High-performance user session storage
- **Real-time Analytics** - Fast data ingestion and querying
- **Content Management** - Flexible schema for diverse content types

### Enterprise Integration
- **Event Sourcing** - Immutable event log with DynamoDB Streams
- **CQRS Implementation** - Separate read/write models with GSI
- **Multi-tenant Applications** - Partition key-based tenant isolation
- **Global Applications** - Global Tables for multi-region deployment

### DevOps Automation
```python
import boto3
from datetime import datetime

def deploy_dynamodb_table(table_name, environment):
    dynamodb = boto3.resource('dynamodb')
    
    table_config = {
        'TableName': f"{table_name}-{environment}",
        'KeySchema': [
            {'AttributeName': 'pk', 'KeyType': 'HASH'},
            {'AttributeName': 'sk', 'KeyType': 'RANGE'}
        ],
        'AttributeDefinitions': [
            {'AttributeName': 'pk', 'AttributeType': 'S'},
            {'AttributeName': 'sk', 'AttributeType': 'S'}
        ],
        'BillingMode': 'PAY_PER_REQUEST',
        'Tags': [
            {'Key': 'Environment', 'Value': environment},
            {'Key': 'DeployedAt', 'Value': datetime.now().isoformat()}
        ]
    }
    
    table = dynamodb.create_table(**table_config)
    table.wait_until_exists()
    return table
```

## Service Features & Capabilities

### Data Types

#### Scalar
- **String (S)** - UTF-8 text
- **Number (N)** - Numeric values
- **Binary (B)** - Binary data
- **Boolean (BOOL)** - true/false
- **Null (NULL)** - null value

#### Document
- **Map (M)** - Nested attributes `{attr1: value1}`
- **List (L)** - Ordered collection `[value1, value2]`

#### Set
- **String Set (SS)** - Set of strings
- **Number Set (NS)** - Set of numbers
- **Binary Set (BS)** - Set of binary values

### Operations

#### Item Operations
```
PutItem      - Create/replace item
GetItem      - Retrieve single item
UpdateItem   - Modify item attributes
DeleteItem   - Remove item
```

#### Query Operations
```
Query        - Find items by PK (+ optional SK condition)
Scan         - Examine entire table/index
BatchGetItem - Retrieve up to 100 items
BatchWriteItem - Put/delete up to 25 items
```

### Consistency Models
- **Eventually Consistent** - Default, may not reflect recent writes
- **Strongly Consistent** - Returns most up-to-date data (not available for GSI)

### Advanced Features

#### DynamoDB Streams
- Capture data modification events
- 24-hour retention
- Near real-time processing
- Triggers Lambda functions

#### Global Tables
- Multi-region, multi-master replication
- Eventually consistent across regions
- Automatic conflict resolution

#### Transactions
- **TransactWriteItems** - Up to 25 write operations
- **TransactGetItems** - Up to 25 read operations
- ACID compliance across multiple items

#### PartiQL
- SQL-compatible query language
- SELECT, INSERT, UPDATE, DELETE operations
- Works with complex nested data

#### DynamoDB Accelerator (DAX)
- In-memory cache for DynamoDB
- Default TTL 5 minutes
- Microsecond latency for cached reads

## Configuration & Setup

### Table Creation
```python
import boto3

def create_table_with_gsi():
    dynamodb = boto3.resource('dynamodb')
    
    table = dynamodb.create_table(
        TableName='UserProfiles',
        KeySchema=[
            {'AttributeName': 'userId', 'KeyType': 'HASH'},
            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'userId', 'AttributeType': 'S'},
            {'AttributeName': 'timestamp', 'AttributeType': 'S'},
            {'AttributeName': 'email', 'AttributeType': 'S'}
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'EmailIndex',
                'KeySchema': [{'AttributeName': 'email', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'},
                'BillingMode': 'PAY_PER_REQUEST'
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    
    table.wait_until_exists()
    return table
```

### Capacity Planning
```python
def configure_auto_scaling(table_name):
    autoscaling = boto3.client('application-autoscaling')
    
    # Register scalable target
    autoscaling.register_scalable_target(
        ServiceNamespace='dynamodb',
        ResourceId=f'table/{table_name}',
        ScalableDimension='dynamodb:table:ReadCapacityUnits',
        MinCapacity=5,
        MaxCapacity=40000
    )
    
    # Create scaling policy
    autoscaling.put_scaling_policy(
        PolicyName=f'{table_name}-read-scaling-policy',
        ServiceNamespace='dynamodb',
        ResourceId=f'table/{table_name}',
        ScalableDimension='dynamodb:table:ReadCapacityUnits',
        PolicyType='TargetTrackingScaling',
        TargetTrackingScalingPolicyConfiguration={
            'TargetValue': 70.0,
            'PredefinedMetricSpecification': {
                'PredefinedMetricType': 'DynamoDBReadCapacityUtilization'
            }
        }
    )
```

## Enterprise Implementation Examples

### Single Table Design Pattern
```python
class SingleTableDesign:
    def __init__(self, table_name):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
    
    def create_user(self, user_id, email, name):
        return self.table.put_item(
            Item={
                'pk': f'USER#{user_id}',
                'sk': f'PROFILE#{user_id}',
                'type': 'user',
                'email': email,
                'name': name,
                'created_at': datetime.now().isoformat()
            }
        )
    
    def create_order(self, user_id, order_id, total):
        return self.table.put_item(
            Item={
                'pk': f'USER#{user_id}',
                'sk': f'ORDER#{order_id}',
                'type': 'order',
                'total': total,
                'status': 'pending',
                'created_at': datetime.now().isoformat()
            }
        )
    
    def get_user_orders(self, user_id):
        response = self.table.query(
            KeyConditionExpression=Key('pk').eq(f'USER#{user_id}') & 
                                 Key('sk').begins_with('ORDER#')
        )
        return response['Items']
```

### Event Sourcing Implementation
```python
class EventStore:
    def __init__(self, table_name):
        self.table = boto3.resource('dynamodb').Table(table_name)
    
    def append_event(self, aggregate_id, event_type, event_data):
        timestamp = datetime.now().isoformat()
        event_id = str(uuid.uuid4())
        
        self.table.put_item(
            Item={
                'pk': f'AGGREGATE#{aggregate_id}',
                'sk': f'EVENT#{timestamp}#{event_id}',
                'event_type': event_type,
                'event_data': event_data,
                'timestamp': timestamp,
                'version': self._get_next_version(aggregate_id)
            }
        )
    
    def get_events(self, aggregate_id, from_version=0):
        response = self.table.query(
            KeyConditionExpression=Key('pk').eq(f'AGGREGATE#{aggregate_id}'),
            FilterExpression=Attr('version').gte(from_version),
            ScanIndexForward=True
        )
        return response['Items']
```

## Monitoring & Observability

### CloudWatch Metrics
- `ConsumedReadCapacityUnits`
- `ConsumedWriteCapacityUnits`
- `ThrottledRequests`
- `UserErrors`
- `SystemErrors`

### DynamoDB Insights
- Performance metrics and recommendations
- Contributor Insights for top keys
- Hot partition detection

### Custom Monitoring
```python
def setup_table_monitoring(table_name):
    cloudwatch = boto3.client('cloudwatch')
    
    # Create custom metric for business logic
    cloudwatch.put_metric_data(
        Namespace='DynamoDB/Application',
        MetricData=[
            {
                'MetricName': 'ActiveUsers',
                'Dimensions': [
                    {'Name': 'TableName', 'Value': table_name}
                ],
                'Value': get_active_user_count(),
                'Unit': 'Count'
            }
        ]
    )
    
    # Set up alarm for throttling
    cloudwatch.put_metric_alarm(
        AlarmName=f'{table_name}-ThrottlingAlarm',
        ComparisonOperator='GreaterThanThreshold',
        EvaluationPeriods=2,
        MetricName='UserErrors',
        Namespace='AWS/DynamoDB',
        Period=300,
        Statistic='Sum',
        Threshold=10.0,
        ActionsEnabled=True,
        AlarmActions=['arn:aws:sns:region:account:topic'],
        AlarmDescription='DynamoDB throttling detected',
        Dimensions=[
            {'Name': 'TableName', 'Value': table_name}
        ]
    )
```

## Security & Compliance

### Access Control
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:Query"
            ],
            "Resource": "arn:aws:dynamodb:region:account:table/UserProfiles",
            "Condition": {
                "ForAllValues:StringEquals": {
                    "dynamodb:LeadingKeys": ["${aws:userid}"]
                }
            }
        }
    ]
}
```

### Encryption Configuration
```python
def create_encrypted_table():
    dynamodb = boto3.resource('dynamodb')
    
    table = dynamodb.create_table(
        TableName='SecureUserData',
        # ... other parameters ...
        SSESpecification={
            'Enabled': True,
            'SSEType': 'KMS',
            'KMSMasterKeyId': 'arn:aws:kms:region:account:key/key-id'
        }
    )
    return table
```

### VPC Endpoints
```python
def create_vpc_endpoint():
    ec2 = boto3.client('ec2')
    
    response = ec2.create_vpc_endpoint(
        VpcId='vpc-12345678',
        ServiceName='com.amazonaws.region.dynamodb',
        VpcEndpointType='Gateway',
        RouteTableIds=['rtb-12345678'],
        PolicyDocument=json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "dynamodb:*",
                    "Resource": "*"
                }
            ]
        })
    )
    return response
```

## Cost Optimization

### Capacity Management
```python
class CostOptimizer:
    def __init__(self):
        self.dynamodb = boto3.client('dynamodb')
        self.cloudwatch = boto3.client('cloudwatch')
    
    def analyze_table_utilization(self, table_name, days=30):
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        metrics = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/DynamoDB',
            MetricName='ConsumedReadCapacityUnits',
            Dimensions=[{'Name': 'TableName', 'Value': table_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Average', 'Maximum']
        )
        
        # Analyze and recommend capacity adjustments
        avg_consumption = sum(d['Average'] for d in metrics['Datapoints']) / len(metrics['Datapoints'])
        max_consumption = max(d['Maximum'] for d in metrics['Datapoints'])
        
        return {
            'average_rcu': avg_consumption,
            'peak_rcu': max_consumption,
            'recommendation': self._get_capacity_recommendation(avg_consumption, max_consumption)
        }
    
    def optimize_gsi_projections(self, table_name):
        # Analyze query patterns and recommend projection optimizations
        table_info = self.dynamodb.describe_table(TableName=table_name)
        gsi_list = table_info['Table'].get('GlobalSecondaryIndexes', [])
        
        recommendations = []
        for gsi in gsi_list:
            if gsi['Projection']['ProjectionType'] == 'ALL':
                recommendations.append(f"Consider KEYS_ONLY projection for {gsi['IndexName']} if full item not needed")
        
        return recommendations
```

## Automation & Infrastructure as Code

### CloudFormation Template
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Parameters:
  Environment:
    Type: String
    Default: dev
    AllowedValues: [dev, staging, prod]

Resources:
  UserProfilesTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub 'UserProfiles-${Environment}'
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: userId
          AttributeType: S
        - AttributeName: email
          AttributeType: S
      KeySchema:
        - AttributeName: userId
          KeyType: HASH
      GlobalSecondaryIndexes:
        - IndexName: EmailIndex
          KeySchema:
            - AttributeName: email
              KeyType: HASH
          Projection:
            ProjectionType: KEYS_ONLY
      PointInTimeRecoverySpecification:
        PointInTimeRecoveryEnabled: true
      SSESpecification:
        SSEEnabled: true
      Tags:
        - Key: Environment
          Value: !Ref Environment
        - Key: Service
          Value: UserManagement
```

### Terraform Configuration
```hcl
resource "aws_dynamodb_table" "user_profiles" {
  name           = "UserProfiles-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "userId"

  attribute {
    name = "userId"
    type = "S"
  }

  attribute {
    name = "email"
    type = "S"
  }

  global_secondary_index {
    name     = "EmailIndex"
    hash_key = "email"
    projection_type = "KEYS_ONLY"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled     = true
    kms_key_id  = aws_kms_key.dynamodb_key.arn
  }

  tags = {
    Environment = var.environment
    Service     = "UserManagement"
  }
}
```

## Performance & Limits

### Throughput
- **RCU** - Read Capacity Unit (4KB strongly consistent, 8KB eventually consistent)
- **WCU** - Write Capacity Unit (1KB per second)
- **Burst Capacity** - Unused capacity accumulated (up to 5 minutes)

### Limits
- Item size: 400KB max
- Attribute name: 64KB max
- Query result: 1MB max
- Batch operations: 16MB max
- GSI per table: 20 max
- LSI per table: 10 max

## Troubleshooting & Operations

### Common Issues

#### Hot Partitions
```python
def detect_hot_partitions(table_name):
    cloudwatch = boto3.client('cloudwatch')
    
    # Check for throttling events
    response = cloudwatch.get_metric_statistics(
        Namespace='AWS/DynamoDB',
        MetricName='ThrottledRequests',
        Dimensions=[{'Name': 'TableName', 'Value': table_name}],
        StartTime=datetime.now() - timedelta(hours=1),
        EndTime=datetime.now(),
        Period=300,
        Statistics=['Sum']
    )
    
    throttled_requests = sum(d['Sum'] for d in response['Datapoints'])
    if throttled_requests > 0:
        print(f"Warning: {throttled_requests} throttled requests detected")
        return True
    return False

def redistribute_partition_keys(old_key):
    # Add random suffix to distribute load
    import hashlib
    hash_suffix = hashlib.md5(old_key.encode()).hexdigest()[:4]
    return f"{old_key}#{hash_suffix}"
```

#### Query Optimization
```python
def optimize_scan_operations(table_name):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    
    # Use parallel scan for large tables
    def parallel_scan(segment, total_segments):
        response = table.scan(
            Segment=segment,
            TotalSegments=total_segments,
            FilterExpression=Attr('status').eq('active')
        )
        return response['Items']
    
    # Execute parallel scans
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(parallel_scan, i, 4) for i in range(4)]
        results = []
        for future in concurrent.futures.as_completed(futures):
            results.extend(future.result())
    
    return results
```

### Backup & Recovery

#### Backup Types
- **On-Demand** - Manual backups, retained until deleted
- **Point-in-Time Recovery (PITR)** - Continuous backups (35 days)

#### Global Tables Backup
- Cross-region replication
- Independent backup policies per region

#### Automated Backup Management
```python
def setup_automated_backups(table_name):
    dynamodb = boto3.client('dynamodb')
    
    # Enable point-in-time recovery
    dynamodb.update_continuous_backups(
        TableName=table_name,
        PointInTimeRecoverySpecification={
            'PointInTimeRecoveryEnabled': True
        }
    )
    
    # Create on-demand backup
    backup_name = f"{table_name}-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    response = dynamodb.create_backup(
        TableName=table_name,
        BackupName=backup_name
    )
    
    return response['BackupDetails']['BackupArn']
```

## Best Practices

### Design Patterns
- **Single Table Design** - Store multiple entity types in one table
- **Hierarchical Data** - Use composite sort keys (USER#123#ORDER#456)
- **Hot Partitions** - Distribute load evenly across partition keys

### Query Optimization
- Use Query over Scan when possible
- Project only needed attributes
- Implement pagination with LastEvaluatedKey
- Use GSI/LSI for alternative access patterns

## Additional Resources

### AWS Documentation
- [DynamoDB Developer Guide](https://docs.aws.amazon.com/dynamodb/latest/developerguide/)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/dynamodb/latest/developerguide/best-practices.html)
- [DynamoDB API Reference](https://docs.aws.amazon.com/dynamodb/latest/APIReference/)

### Tools & SDKs
- **AWS SDK** - Official SDKs for multiple languages
- **NoSQL Workbench** - Visual design tool for DynamoDB
- **DynamoDB Local** - Local development environment

### Learning Resources
- [AWS DynamoDB Workshop](https://amazon-dynamodb-labs.workshop.aws/)
- [DynamoDB Data Modeling Guide](https://docs.aws.amazon.com/dynamodb/latest/developerguide/bp-modeling-nosql.html)
- [Single Table Design Patterns](https://www.alexdebrie.com/posts/dynamodb-single-table/)

### Community Tools
- **Boto3** - Python SDK with extensive DynamoDB support
- **AWS CLI** - Command-line interface for DynamoDB operations
- **Serverless Framework** - Infrastructure as code for DynamoDB