## Core Concepts

- **Table** - Collection of items (rows)
- **Item** - Record with attributes (max 400KB)
- **Attribute** - Key-value pair (name + value + type)
- **Primary Key** - Partition Key (PK) or Composite (PK + Sort Key)

## Capacity Modes

|Mode|Scaling|Pricing|Use Case|
|---|---|---|---|
|**On-Demand**|Automatic|Pay-per-request|Unpredictable traffic|
|**Provisioned**|Manual/Auto|RCU/WCU based|Predictable traffic|

## Key Types

- **Partition Key (PK)** - Determines item location, must be unique for simple PK
- **Sort Key (SK)** - Optional, enables range queries, PK+SK must be unique
- **Composite Key** - PK + SK combination

## Secondary Indexes

### Global Secondary Index (GSI)

- Different PK/SK from base table
- Eventually consistent reads only
- Has own provisioned throughput
- Can be created/deleted anytime
- Max 20 per table

### Local Secondary Index (LSI)

- Same PK as base table, different SK
- Strongly/eventually consistent reads
- Shares table's provisioned throughput
- Must be created at table creation
- Max 10 per table
- 10GB limit per partition key value

## Data Types

### Scalar

- **String (S)** - UTF-8 text
- **Number (N)** - Numeric values
- **Binary (B)** - Binary data
- **Boolean (BOOL)** - true/false
- **Null (NULL)** - null value

### Document

- **Map (M)** - Nested attributes `{attr1: value1}`
- **List (L)** - Ordered collection `[value1, value2]`

### Set

- **String Set (SS)** - Set of strings
- **Number Set (NS)** - Set of numbers
- **Binary Set (BS)** - Set of binary values

## Operations

### Item Operations

```
PutItem      - Create/replace item
GetItem      - Retrieve single item
UpdateItem   - Modify item attributes
DeleteItem   - Remove item
```

### Query Operations

```
Query        - Find items by PK (+ optional SK condition)
Scan         - Examine entire table/index
BatchGetItem - Retrieve up to 100 items
BatchWriteItem - Put/delete up to 25 items
```

## Consistency Models

- **Eventually Consistent** - Default, may not reflect recent writes
- **Strongly Consistent** - Returns most up-to-date data (not available for GSI)

## Advanced Features

### DynamoDB Streams

- Capture data modification events
- 24-hour retention
- Near real-time processing
- Triggers Lambda functions

### Global Tables

- Multi-region, multi-master replication
- Eventually consistent across regions
- Automatic conflict resolution

### Transactions

- **TransactWriteItems** - Up to 25 write operations
- **TransactGetItems** - Up to 25 read operations
- ACID compliance across multiple items

### PartiQL

- SQL-compatible query language
- SELECT, INSERT, UPDATE, DELETE operations
- Works with complex nested data

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

## Backup & Recovery

### Backup Types

- **On-Demand** - Manual backups, retained until deleted
- **Point-in-Time Recovery (PITR)** - Continuous backups (35 days)

### Global Tables Backup

- Cross-region replication
- Independent backup policies per region

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

### Cost Optimization

- Choose appropriate capacity mode
- Use reserved capacity for predictable workloads
- Implement efficient pagination
- Consider item size and query patterns

## Monitoring

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
  
## DynamoDB Accelerator (DAX)

In-memory cache for DynamoDB, default TTL 5 minutes