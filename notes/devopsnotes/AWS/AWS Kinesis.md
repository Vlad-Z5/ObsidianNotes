AWS Kinesis is a platform for real-time data streaming and analytics on AWS.

## Kinesis Services Comparison

|Service|Purpose|Use Case|Data Retention|
|---|---|---|---|
|**Data Streams**|Real-time streaming|Custom processing, replay|1 day - 1 year|
|**Data Firehose**|Batch delivery|ETL to storage/analytics|No storage|
|**Data Analytics**|Stream processing|SQL on streaming data|Query results only|
|**Video Streams**|Video processing|Live video analysis|Configurable|

---

## Kinesis Data Streams

### Core Concepts

- **Stream** - Collection of shards for data records
- **Shard** - Unit of capacity (1 MB/s or 1000 records/s ingestion)
- **Record** - Data unit with partition key, sequence number, data blob
- **Partition Key** - Determines which shard receives the record
- **Sequence Number** - Unique identifier per shard

### Capacity & Limits

|Specification|Limit|
|---|---|
|**Record Size**|Max 1 MB|
|**Partition Key**|Max 256 bytes|
|**Shard Ingestion**|1 MB/s or 1,000 records/s|
|**Shard Read**|2 MB/s or 5 reads/s|
|**Retention**|1 day (default) - 1 year|
|**Shards per Stream**|No limit (soft limit ~500)|

### Shard Management

#### Scaling Operations

```
Shard Splitting  - Increase capacity (1 shard → 2 shards)
Shard Merging    - Decrease capacity (2 shards → 1 shard)
Auto Scaling     - Automatic shard management
```

#### Partition Key Strategy

- **Even Distribution** - Prevents hot shards
- **Sequential** - Maintains order within partition
- **Random** - Maximum throughput distribution

### Consumer Types

#### Shared Fan-Out (Pull Model)

- **Classic** - 2 MB/s per shard shared across consumers
- **Polling** - GetRecords API calls
- **Cost Effective** - Lower cost, higher latency

#### Enhanced Fan-Out (Push Model)

- **Dedicated** - 2 MB/s per consumer per shard
- **HTTP/2 Push** - SubscribeToShard API
- **Lower Latency** - ~70ms average
- **Higher Cost** - Pay per consumer-shard hour

---

## Kinesis Data Firehose

### Delivery Destinations

#### Storage

- **S3** - Most common, supports partitioning
- **Redshift** - Via S3 with COPY command
- **OpenSearch** - Real-time search and analytics

#### Analytics & Monitoring

- **Splunk** - Log analysis platform
- **Datadog** - Monitoring and analytics
- **New Relic** - Application monitoring
- **HTTP Endpoints** - Custom destinations

### Data Transformation

|Feature|Description|Use Case|
|---|---|---|
|**Format Conversion**|JSON → Parquet/ORC|Analytics optimization|
|**Compression**|GZIP, SNAPPY, ZIP|Storage cost reduction|
|**Lambda Processing**|Custom transformation|Data enrichment/filtering|
|**Dynamic Partitioning**|S3 prefix based on data|Query performance|

### Buffering Configuration

#### Buffer Conditions (OR Logic)

- **Size** - 1 MB to 128 MB
- **Time** - 60 seconds to 900 seconds
- **Trigger** - Whichever condition met first

#### Error Handling

- **Error Output Prefix** - Failed records location
- **Processing Configuration** - Retry duration
- **Backup Configuration** - All records backup

---

## Kinesis Data Analytics

### Application Types

#### SQL Applications

- **Real-time SQL** - ANSI SQL queries on streams
- **Windowing** - Tumbling, sliding, session windows
- **Built-in Functions** - Aggregations, string manipulation

#### Apache Flink Applications

- **Flink Runtime** - Java/Scala applications
- **Advanced Processing** - Complex event processing
- **State Management** - Checkpointing and recovery

### SQL Windowing Functions

```sql
-- Tumbling Window (non-overlapping)
WINDOWED BY RANGE INTERVAL '5' MINUTE

-- Sliding Window (overlapping)  
WINDOWED BY RANGE INTERVAL '5' MINUTE PRECEDING

-- Session Window (activity-based)
WINDOWED BY SESSION INTERVAL '10' MINUTE
```

### Data Sources

- **Kinesis Data Streams** - Real-time streaming data
- **Kinesis Data Firehose** - Delivery stream data
- **Reference Data** - S3-based static data joins

---

## Kinesis Video Streams

### Core Components

- **Video Stream** - Resource for live video data
- **Fragment** - Self-contained video chunk
- **Producer** - Device/application sending video
- **Consumer** - Application processing video

### Capabilities

|Feature|Description|
|---|---|
|**Live Streaming**|Real-time video ingestion|
|**Playback**|HLS/DASH streaming protocols|
|**Storage**|Automatic video storage|
|**ML Integration**|Rekognition Video analysis|

---

## Security & Encryption

### Encryption Options

|Type|Data Streams|Data Firehose|Data Analytics|
|---|---|---|---|
|**At Rest**|AWS KMS|AWS KMS|AWS KMS|
|**In Transit**|TLS 1.2|TLS 1.2|TLS 1.2|
|**Client-Side**|Custom|Custom|N/A|

### Access Control

- **IAM Policies** - Service-level permissions
- **Resource Policies** - Cross-account access
- **VPC Endpoints** - Private network access

---

## Monitoring & Troubleshooting

### CloudWatch Metrics

#### Data Streams

```
IncomingRecords          - Records per second
IncomingBytes            - Bytes per second
OutgoingRecords          - Records consumed
IteratorAgeMilliseconds  - Consumer lag
ReadProvisionedThroughputExceeded - Throttling
WriteProvisionedThroughputExceeded - Throttling
```

#### Data Firehose

```
DeliveryToS3.Records     - Records delivered
DeliveryToS3.Success     - Successful deliveries
DeliveryToS3.DataFreshness - Delivery delay
```

### Common Issues

|Problem|Cause|Solution|
|---|---|---|
|**Hot Shards**|Poor partition key|Improve key distribution|
|**Consumer Lag**|Slow processing|Scale consumers/optimize code|
|**Throttling**|Exceed shard limits|Add shards or improve batching|
|**High Latency**|Batch processing|Use enhanced fan-out|

---

## Integration Patterns

### Lambda Integration

```
Data Streams → Lambda    - Real-time processing
Firehose → Lambda       - Data transformation
Analytics → Lambda      - Results processing
```

### Analytics Pipeline

```
Source → Data Streams → Analytics → Firehose → S3 → Athena/QuickSight
```

### Real-time Dashboard

```
IoT → Data Streams → Lambda → ElasticSearch → Kibana
```

---

## Pricing Model

### Data Streams

- **Shard Hour** - $0.015 per shard per hour
- **PUT Payload Units** - $0.014 per million (25KB units)
- **Extended Retention** - $0.023 per shard per hour

### Data Firehose

- **Data Ingested** - $0.029 per GB
- **Format Conversion** - $0.018 per GB
- **VPC Delivery** - Additional $0.01 per hour per AZ

### Data Analytics

- **Kinesis Processing Unit (KPU)** - $0.11 per hour
- **1 KPU** = 1 vCPU + 4GB memory
- **Auto Scaling** - Based on application demand

---

## Best Practices

### Performance Optimization

- **Shard Count** - Plan for peak throughput
- **Partition Keys** - Ensure even distribution
- **Batch Processing** - Use PutRecords for efficiency
- **Consumer Scaling** - Match processing to ingestion rate

### Cost Optimization

- **Right-sizing** - Monitor shard utilization
- **Retention Period** - Set appropriate data retention
- **Compression** - Use Firehose compression features
- **Reserved Capacity** - For predictable workloads

### Reliability

- **Error Handling** - Implement retry logic
- **Checkpointing** - Track processing progress
- **Multi-AZ** - Automatic high availability
- **Backup Strategy** - Consider S3 archival

## Common Use Cases

- **Real-time Analytics** - Dashboard metrics, KPIs
- **IoT Data Processing** - Sensor data aggregation
- **Log Analysis** - Application and system logs
- **Clickstream Analysis** - User behavior tracking
- **Financial Trading** - Market data processing
- **Gaming Leaderboards** - Real-time score updates
- **ML Feature Stores** - Real-time feature engineering