# AWS Kinesis: Enterprise Real-Time Data Streaming & Analytics Platform

> **Service Type:** Analytics | **Scope:** Regional | **Serverless:** Yes

## Overview

AWS Kinesis is a comprehensive managed platform for real-time data streaming, processing, and analytics that enables organizations to collect, process, and analyze massive volumes of streaming data in real-time. The platform consists of four integrated services—Data Streams, Data Firehose, Data Analytics, and Video Streams—providing end-to-end capabilities for building scalable, enterprise-grade streaming applications that support real-time decision making, operational intelligence, and advanced analytics workflows with seamless integration into the broader AWS ecosystem.

## Core Architecture Components

- **Data Streams:** Massively scalable, real-time data ingestion service with configurable retention and shard-based architecture for high-throughput streaming
- **Data Firehose:** Fully managed delivery service for streaming data to data lakes, data warehouses, and analytics services with automatic scaling and transformation
- **Data Analytics:** SQL and Apache Flink-based stream processing service for real-time analytics, windowing functions, and complex event processing
- **Video Streams:** Secure video ingestion and processing service for live streaming applications with machine learning integration capabilities
- **Integration Framework:** Native connectivity with Lambda, S3, Redshift, OpenSearch, and third-party analytics platforms for comprehensive data pipelines
- **Producer/Consumer SDKs:** Multi-language client libraries with automatic retry, checkpointing, and load balancing for resilient stream processing
- **Security & Compliance:** End-to-end encryption, VPC endpoints, IAM integration, and audit logging for enterprise security requirements

## DevOps & Enterprise Use Cases

### Real-Time Analytics & Business Intelligence
- **Live Dashboard Analytics:** Real-time KPI monitoring and business metrics visualization with sub-second latency for operational dashboards
- **Financial Trading Systems:** High-frequency market data processing, algorithmic trading signals, and risk management analytics
- **E-commerce Personalization:** Real-time recommendation engines, dynamic pricing optimization, and customer behavior analytics
- **IoT & Sensor Data Processing:** Industrial IoT telemetry, smart city infrastructure monitoring, and predictive maintenance analytics

### Data Engineering & ETL Pipelines
- **Streaming ETL Workflows:** Continuous data transformation, enrichment, and loading into data warehouses and data lakes
- **Multi-Source Data Integration:** Real-time aggregation of data from applications, databases, logs, and external APIs into unified data streams
- **Data Lake Ingestion:** High-volume data ingestion to S3 with automatic partitioning, compression, and format conversion for analytics optimization
- **Change Data Capture (CDC):** Real-time database replication, data synchronization, and event sourcing architectures

### Operational Intelligence & Monitoring
- **Application Log Analytics:** Real-time log processing, anomaly detection, and operational alerting for application monitoring
- **Security Event Processing:** SIEM integration, threat detection, and security incident response automation
- **Infrastructure Monitoring:** System metrics aggregation, performance monitoring, and automated scaling decisions
- **Clickstream Analytics:** User behavior tracking, conversion funnel analysis, and real-time A/B testing

### Machine Learning & AI Integration
- **Real-Time Feature Engineering:** Streaming feature computation for ML models, feature stores, and online inference pipelines
- **Anomaly Detection Systems:** Continuous monitoring for fraud detection, system anomalies, and business process deviations
- **Computer Vision Processing:** Real-time video analysis, object detection, and automated video content moderation
- **Natural Language Processing:** Real-time text analysis, sentiment analysis, and content classification from streaming data

## Service Features & Capabilities

### Data Streams Features
- **Scalable Architecture:** Shard-based partitioning with automatic scaling from single streams to millions of records per second
- **Flexible Retention:** Configurable data retention from 24 hours to 365 days for replay and reprocessing capabilities
- **Enhanced Fan-Out:** Dedicated throughput for multiple consumers with HTTP/2 push delivery and reduced latency
- **Server-Side Encryption:** Automatic data encryption at rest using AWS KMS with configurable key management

### Data Firehose Capabilities
- **Automatic Scaling:** Fully managed service that automatically scales to handle gigabytes of streaming data per hour
- **Format Conversion:** Built-in data transformation from JSON to optimized columnar formats (Parquet, ORC) for analytics performance
- **Error Handling:** Comprehensive error handling with failed records routing, retry mechanisms, and backup configurations
- **Compression & Optimization:** Multiple compression algorithms (GZIP, Snappy, ZIP) for storage cost optimization

### Analytics & Processing
- **SQL Analytics:** Standard SQL queries on streaming data with sliding windows, aggregations, and real-time joins
- **Apache Flink Integration:** Advanced stream processing with stateful computations, complex event processing, and exactly-once semantics
- **Time-Based Windows:** Tumbling, sliding, and session windows for temporal analytics and event correlation
- **Machine Learning Integration:** Built-in functions for anomaly detection, hotspot detection, and statistical analysis

## Configuration & Setup

### Basic Configuration
```bash
# Create Kinesis Data Stream
aws kinesis create-stream \
  --stream-name "enterprise-data-stream" \
  --shard-count 10 \
  --tags Key=Environment,Value=Production Key=Application,Value=Analytics

# Enable server-side encryption
aws kinesis enable-stream-encryption \
  --stream-name "enterprise-data-stream" \
  --encryption-type KMS \
  --key-id "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012"

# Create Data Firehose delivery stream
aws firehose create-delivery-stream \
  --delivery-stream-name "enterprise-delivery-stream" \
  --extended-s3-destination-configuration '{
    "RoleARN": "arn:aws:iam::123456789012:role/firehose_delivery_role",
    "BucketARN": "arn:aws:s3:::enterprise-data-lake",
    "Prefix": "year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/",
    "BufferingHints": {
      "SizeInMBs": 128,
      "IntervalInSeconds": 60
    },
    "CompressionFormat": "GZIP",
    "DataFormatConversionConfiguration": {
      "Enabled": true,
      "OutputFormatConfiguration": {
        "Serializer": {
          "ParquetSerDe": {}
        }
      }
    }
  }'

# Configure stream for enhanced fan-out
aws kinesis register-stream-consumer \
  --stream-arn "arn:aws:kinesis:us-east-1:123456789012:stream/enterprise-data-stream" \
  --consumer-name "real-time-analytics-consumer"
```

### Advanced Configuration
```bash
# Enterprise multi-stream setup with auto-scaling
stream_configs=(
  "user-events:5:UserEvents"
  "transaction-data:10:TransactionProcessing" 
  "sensor-telemetry:20:IoTTelemetry"
  "application-logs:15:LogAnalytics"
)

for config in "${stream_configs[@]}"; do
  IFS=':' read -r stream_name shard_count purpose <<< "$config"
  
  # Create stream with specific configuration
  aws kinesis create-stream \
    --stream-name "$stream_name" \
    --shard-count "$shard_count" \
    --stream-mode-details StreamMode=ON_DEMAND \
    --tags Key=Purpose,Value="$purpose" Key=Environment,Value=Production
  
  # Wait for stream to become active
  aws kinesis wait stream-exists --stream-name "$stream_name"
  
  # Enable encryption and monitoring
  aws kinesis enable-stream-encryption \
    --stream-name "$stream_name" \
    --encryption-type KMS \
    --key-id alias/kinesis-encryption-key
  
  # Put retention policy
  aws kinesis increase-stream-retention-period \
    --stream-name "$stream_name" \
    --retention-period-hours 168  # 7 days
done

# Create Kinesis Analytics application
aws kinesisanalytics create-application \
  --application-name "enterprise-stream-analytics" \
  --application-description "Real-time analytics for enterprise streaming data" \
  --inputs '[
    {
      "NamePrefix": "SOURCE_SQL_STREAM",
      "KinesisStreamsInput": {
        "ResourceARN": "arn:aws:kinesis:us-east-1:123456789012:stream/user-events",
        "RoleARN": "arn:aws:iam::123456789012:role/kinesis-analytics-role"
      },
      "InputSchema": {
        "RecordColumns": [
          {
            "Name": "user_id",
            "SqlType": "VARCHAR(32)",
            "Mapping": "$.user_id"
          },
          {
            "Name": "event_time", 
            "SqlType": "TIMESTAMP",
            "Mapping": "$.timestamp"
          },
          {
            "Name": "event_type",
            "SqlType": "VARCHAR(64)", 
            "Mapping": "$.event_type"
          }
        ],
        "RecordFormat": {
          "RecordFormatType": "JSON"
        }
      }
    }
  ]'
```

## Enterprise Implementation Examples

### Example 1: Real-Time E-commerce Analytics Platform

**Business Requirement:** Build a comprehensive real-time analytics platform for a global e-commerce company processing 100M+ daily events, enabling real-time personalization, fraud detection, and operational dashboards with sub-second latency requirements.

**Implementation Steps:**
1. **Multi-Stream Architecture Setup**
   ```bash
   # Create specialized streams for different event types
   event_streams=(
     "user-interactions:50:UserBehavior"
     "transaction-events:30:PaymentProcessing"
     "inventory-updates:20:InventoryManagement" 
     "fraud-signals:10:SecurityMonitoring"
   )

   for stream_config in "${event_streams[@]}"; do
     IFS=':' read -r stream_name shard_count category <<< "$stream_config"
     
     aws kinesis create-stream \
       --stream-name "$stream_name" \
       --shard-count "$shard_count" \
       --tags Key=Category,Value="$category" Key=CriticalityLevel,Value=High
     
     # Enable enhanced fan-out for low latency
     aws kinesis register-stream-consumer \
       --stream-arn "arn:aws:kinesis:us-east-1:123456789012:stream/$stream_name" \
       --consumer-name "${category,,}-processor"
   done
   ```

2. **Real-Time Analytics Processing Framework**
   ```python
   import boto3
   import json
   import logging
   from datetime import datetime, timedelta
   from typing import Dict, List, Any, Optional
   from dataclasses import dataclass, field
   import asyncio
   import uuid
   from decimal import Decimal
   
   @dataclass
   class StreamEvent:
       event_id: str
       user_id: str
       session_id: str
       event_type: str
       timestamp: datetime
       properties: Dict[str, Any] = field(default_factory=dict)
       source_stream: str = ""
   
   @dataclass 
   class AnalyticsMetrics:
       total_events: int = 0
       unique_users: int = 0
       conversion_rate: float = 0.0
       revenue: Decimal = Decimal('0.0')
       fraud_score: float = 0.0
       anomaly_count: int = 0
   
   class EcommerceStreamProcessor:
       """
       Enterprise e-commerce real-time stream processing with advanced analytics,
       fraud detection, and personalization features.
       """
       
       def __init__(self, region: str = 'us-east-1'):
           self.kinesis = boto3.client('kinesis', region_name=region)
           self.firehose = boto3.client('firehose', region_name=region)
           self.analytics = boto3.client('kinesisanalytics', region_name=region)
           self.dynamodb = boto3.client('dynamodb', region_name=region)
           self.cloudwatch = boto3.client('cloudwatch', region_name=region)
           self.region = region
           self.logger = self._setup_logging()
           
           # Real-time state management
           self.user_sessions = {}
           self.fraud_patterns = {}
           self.conversion_funnel = {}
           
       def _setup_logging(self) -> logging.Logger:
           logger = logging.getLogger('EcommerceStreamProcessor')
           logger.setLevel(logging.INFO)
           if not logger.handlers:
               handler = logging.StreamHandler()
               formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
               handler.setFormatter(formatter)
               logger.addHandler(handler)
           return logger
       
       def setup_real_time_analytics(self) -> Dict[str, Any]:
           """Setup comprehensive real-time analytics infrastructure"""
           try:
               analytics_queries = {
                   'user_behavior_analysis': """
                       CREATE STREAM "user_behavior_stream" AS
                       SELECT 
                           user_id,
                           event_type,
                           COUNT(*) as event_count,
                           AVG(CASE WHEN event_type = 'purchase' THEN properties.amount ELSE 0 END) as avg_purchase,
                           ROWTIME_TO_TIMESTAMP(ROWTIME) as window_time
                       FROM SOURCE_SQL_STREAM_001
                       WHERE event_type IN ('view', 'add_to_cart', 'purchase')
                       GROUP BY user_id, event_type, 
                                RANGE_WINDOW(INTERVAL '5' MINUTE)
                   """,
                   
                   'fraud_detection': """
                       CREATE STREAM "fraud_alerts_stream" AS
                       SELECT 
                           user_id,
                           session_id,
                           COUNT(*) as transaction_count,
                           SUM(properties.amount) as total_amount,
                           CASE 
                               WHEN COUNT(*) > 10 AND SUM(properties.amount) > 5000 THEN 'HIGH_RISK'
                               WHEN COUNT(*) > 5 AND SUM(properties.amount) > 2000 THEN 'MEDIUM_RISK'
                               ELSE 'LOW_RISK'
                           END as fraud_score
                       FROM SOURCE_SQL_STREAM_001
                       WHERE event_type = 'purchase'
                       GROUP BY user_id, session_id,
                                RANGE_WINDOW(INTERVAL '1' MINUTE)
                       HAVING COUNT(*) > 3 OR SUM(properties.amount) > 1000
                   """,
                   
                   'conversion_funnel': """
                       CREATE STREAM "conversion_metrics_stream" AS
                       SELECT 
                           properties.product_category as category,
                           COUNT(CASE WHEN event_type = 'view' THEN 1 END) as views,
                           COUNT(CASE WHEN event_type = 'add_to_cart' THEN 1 END) as cart_adds,
                           COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) as purchases,
                           (COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) * 100.0) / 
                           NULLIF(COUNT(CASE WHEN event_type = 'view' THEN 1 END), 0) as conversion_rate
                       FROM SOURCE_SQL_STREAM_001
                       GROUP BY properties.product_category,
                                RANGE_WINDOW(INTERVAL '10' MINUTE)
                   """
               }
               
               # Create analytics applications for each query
               created_applications = []
               for app_name, query in analytics_queries.items():
                   try:
                       app_response = self.analytics.create_application(
                           ApplicationName=f'ecommerce-{app_name}',
                           ApplicationDescription=f'Real-time analytics for {app_name}',
                           Inputs=[{
                               'NamePrefix': 'SOURCE_SQL_STREAM',
                               'KinesisStreamsInput': {
                                   'ResourceARN': 'arn:aws:kinesis:us-east-1:123456789012:stream/user-interactions',
                                   'RoleARN': 'arn:aws:iam::123456789012:role/kinesis-analytics-role'
                               },
                               'InputSchema': self._get_input_schema()
                           }]
                       )
                       
                       # Add SQL query to application
                       self.analytics.add_application_input_processing_configuration(
                           ApplicationName=f'ecommerce-{app_name}',
                           CurrentApplicationVersionId=app_response['ApplicationSummary']['ApplicationVersionId'],
                           InputProcessingConfiguration={
                               'InputLambdaProcessor': {
                                   'ResourceARN': f'arn:aws:lambda:us-east-1:123456789012:function:process-{app_name}',
                                   'RoleARN': 'arn:aws:iam::123456789012:role/kinesis-analytics-role'
                               }
                           }
                       )
                       
                       created_applications.append({
                           'application_name': f'ecommerce-{app_name}',
                           'application_arn': app_response['ApplicationSummary']['ApplicationARN'],
                           'query_type': app_name,
                           'status': 'created'
                       })
                       
                       self.logger.info(f"Created analytics application: ecommerce-{app_name}")
                       
                   except Exception as app_error:
                       self.logger.error(f"Failed to create application {app_name}: {str(app_error)}")
                       created_applications.append({
                           'application_name': f'ecommerce-{app_name}',
                           'query_type': app_name,
                           'status': 'error',
                           'error': str(app_error)
                       })
               
               return {
                   'analytics_applications': created_applications,
                   'total_applications': len(created_applications),
                   'successful_applications': len([app for app in created_applications if app['status'] == 'created']),
                   'real_time_processing': 'enabled'
               }
               
           except Exception as e:
               self.logger.error(f"Analytics setup failed: {str(e)}")
               raise
       
       def process_real_time_events(self, stream_name: str, max_records: int = 1000) -> Dict[str, Any]:
           """Process real-time events with advanced analytics and fraud detection"""
           try:
               # Get shard iterator for the stream
               stream_description = self.kinesis.describe_stream(StreamName=stream_name)
               shard_id = stream_description['StreamDescription']['Shards'][0]['ShardId']
               
               shard_iterator_response = self.kinesis.get_shard_iterator(
                   StreamName=stream_name,
                   ShardId=shard_id,
                   ShardIteratorType='LATEST'
               )
               
               shard_iterator = shard_iterator_response['ShardIterator']
               
               # Process records in real-time
               processing_stats = {
                   'total_processed': 0,
                   'fraud_alerts': 0,
                   'conversion_events': 0,
                   'user_segments_updated': 0,
                   'anomalies_detected': 0
               }
               
               while processing_stats['total_processed'] < max_records:
                   records_response = self.kinesis.get_records(
                       ShardIterator=shard_iterator,
                       Limit=100
                   )
                   
                   records = records_response.get('Records', [])
                   if not records:
                       break
                   
                   # Process each record
                   for record in records:
                       try:
                           # Decode and parse event data
                           event_data = json.loads(record['Data'])
                           stream_event = StreamEvent(
                               event_id=event_data.get('event_id', str(uuid.uuid4())),
                               user_id=event_data['user_id'],
                               session_id=event_data.get('session_id', ''),
                               event_type=event_data['event_type'],
                               timestamp=datetime.fromisoformat(event_data['timestamp']),
                               properties=event_data.get('properties', {}),
                               source_stream=stream_name
                           )
                           
                           # Real-time fraud detection
                           if self._detect_fraud(stream_event):
                               processing_stats['fraud_alerts'] += 1
                               self._send_fraud_alert(stream_event)
                           
                           # Conversion tracking
                           if stream_event.event_type in ['purchase', 'signup']:
                               processing_stats['conversion_events'] += 1
                               self._update_conversion_metrics(stream_event)
                           
                           # User segmentation updates
                           self._update_user_segments(stream_event)
                           processing_stats['user_segments_updated'] += 1
                           
                           # Anomaly detection
                           if self._detect_anomalies(stream_event):
                               processing_stats['anomalies_detected'] += 1
                           
                           processing_stats['total_processed'] += 1
                           
                       except Exception as record_error:
                           self.logger.warning(f"Failed to process record: {str(record_error)}")
                           continue
                   
                   # Update shard iterator for next batch
                   shard_iterator = records_response.get('NextShardIterator')
                   if not shard_iterator:
                       break
               
               # Publish processing metrics
               self._publish_processing_metrics(processing_stats)
               
               return {
                   'processing_statistics': processing_stats,
                   'stream_name': stream_name,
                   'processing_timestamp': datetime.utcnow().isoformat(),
                   'real_time_insights': self._generate_real_time_insights()
               }
               
           except Exception as e:
               self.logger.error(f"Real-time processing failed: {str(e)}")
               raise
       
       def setup_personalization_engine(self) -> Dict[str, Any]:
           """Setup real-time personalization engine using streaming data"""
           try:
               # Create personalization delivery streams
               personalization_streams = [
                   'user-recommendations',
                   'dynamic-pricing', 
                   'content-optimization',
                   'marketing-campaigns'
               ]
               
               created_streams = []
               for stream_name in personalization_streams:
                   try:
                       firehose_response = self.firehose.create_delivery_stream(
                           DeliveryStreamName=f'{stream_name}-delivery',
                           DeliveryStreamType='DirectPut',
                           ExtendedS3DestinationConfiguration={
                               'RoleARN': 'arn:aws:iam::123456789012:role/firehose-personalization-role',
                               'BucketARN': 'arn:aws:s3:::ecommerce-personalization-data',
                               'Prefix': f'{stream_name}/year=!{{timestamp:yyyy}}/month=!{{timestamp:MM}}/day=!{{timestamp:dd}}/',
                               'BufferingHints': {
                                   'SizeInMBs': 64,
                                   'IntervalInSeconds': 60
                               },
                               'CompressionFormat': 'GZIP',
                               'ProcessingConfiguration': {
                                   'Enabled': True,
                                   'Processors': [{
                                       'Type': 'Lambda',
                                       'Parameters': [{
                                           'ParameterName': 'LambdaArn',
                                           'ParameterValue': f'arn:aws:lambda:us-east-1:123456789012:function:enrich-{stream_name}-data'
                                       }]
                                   }]
                               },
                               'DynamicPartitioning': {
                                   'Enabled': True
                               },
                               'ProcessingConfiguration': {
                                   'Enabled': True,
                                   'Processors': [{
                                       'Type': 'MetadataExtraction',
                                       'Parameters': [{
                                           'ParameterName': 'MetadataExtractionQuery',
                                           'ParameterValue': '{user_segment:.user_segment}'
                                       }]
                                   }]
                               }
                           }
                       )
                       
                       created_streams.append({
                           'stream_name': f'{stream_name}-delivery',
                           'stream_arn': firehose_response['DeliveryStreamARN'],
                           'purpose': stream_name.replace('-', ' ').title(),
                           'status': 'created'
                       })
                       
                   except Exception as stream_error:
                       self.logger.warning(f"Failed to create stream {stream_name}: {str(stream_error)}")
                       created_streams.append({
                           'stream_name': f'{stream_name}-delivery', 
                           'purpose': stream_name.replace('-', ' ').title(),
                           'status': 'error',
                           'error': str(stream_error)
                       })
               
               return {
                   'personalization_streams': created_streams,
                   'total_streams': len(created_streams),
                   'successful_streams': len([s for s in created_streams if s['status'] == 'created']),
                   'personalization_engine': 'active'
               }
               
           except Exception as e:
               self.logger.error(f"Personalization engine setup failed: {str(e)}")
               raise
       
       def _detect_fraud(self, event: StreamEvent) -> bool:
           """Advanced fraud detection using streaming patterns"""
           try:
               user_id = event.user_id
               current_time = event.timestamp
               
               # Initialize user fraud tracking
               if user_id not in self.fraud_patterns:
                   self.fraud_patterns[user_id] = {
                       'transaction_count': 0,
                       'total_amount': Decimal('0.0'),
                       'last_transaction': current_time,
                       'velocity_score': 0.0
                   }
               
               user_fraud = self.fraud_patterns[user_id]
               
               # High-frequency transaction detection
               time_diff = (current_time - user_fraud['last_transaction']).total_seconds()
               if time_diff < 30 and event.event_type == 'purchase':  # 30 seconds
                   user_fraud['velocity_score'] += 10
               
               # High-value transaction detection
               if event.event_type == 'purchase':
                   amount = Decimal(str(event.properties.get('amount', 0)))
                   user_fraud['transaction_count'] += 1
                   user_fraud['total_amount'] += amount
                   user_fraud['last_transaction'] = current_time
                   
                   # Unusual amount patterns
                   if amount > Decimal('5000'):  # High-value transaction
                       user_fraud['velocity_score'] += 20
                   
                   # Rapid successive transactions
                   if user_fraud['transaction_count'] > 5 and time_diff < 300:  # 5 transactions in 5 minutes
                       user_fraud['velocity_score'] += 15
               
               # Geographic anomalies (if location data available)
               if 'location' in event.properties:
                   location = event.properties['location']
                   if self._is_geographic_anomaly(user_id, location):
                       user_fraud['velocity_score'] += 25
               
               # Device fingerprint anomalies
               if 'device_id' in event.properties:
                   if self._is_device_anomaly(user_id, event.properties['device_id']):
                       user_fraud['velocity_score'] += 15
               
               # Determine if fraud threshold exceeded
               return user_fraud['velocity_score'] > 50
               
           except Exception as e:
               self.logger.warning(f"Fraud detection error: {str(e)}")
               return False
       
       def _generate_real_time_insights(self) -> Dict[str, Any]:
           """Generate real-time business insights from processed data"""
           try:
               insights = {
                   'user_engagement': {
                       'active_sessions': len(self.user_sessions),
                       'avg_session_duration': self._calculate_avg_session_duration(),
                       'bounce_rate': self._calculate_bounce_rate()
                   },
                   'conversion_metrics': {
                       'current_conversion_rate': self._get_current_conversion_rate(),
                       'top_converting_categories': self._get_top_converting_categories(),
                       'revenue_per_visitor': self._calculate_revenue_per_visitor()
                   },
                   'fraud_analytics': {
                       'high_risk_users': len([u for u, data in self.fraud_patterns.items() if data['velocity_score'] > 50]),
                       'blocked_transactions': self._get_blocked_transaction_count(),
                       'fraud_prevention_savings': self._calculate_fraud_savings()
                   },
                   'real_time_trends': {
                       'trending_products': self._get_trending_products(),
                       'geographic_hotspots': self._get_geographic_hotspots(),
                       'peak_traffic_indicators': self._analyze_traffic_patterns()
                   }
               }
               
               return insights
               
           except Exception as e:
               self.logger.warning(f"Insights generation error: {str(e)}")
               return {}
       
       def _get_input_schema(self) -> Dict[str, Any]:
           """Define input schema for Kinesis Analytics"""
           return {
               'RecordColumns': [
                   {'Name': 'event_id', 'SqlType': 'VARCHAR(64)', 'Mapping': '$.event_id'},
                   {'Name': 'user_id', 'SqlType': 'VARCHAR(32)', 'Mapping': '$.user_id'}, 
                   {'Name': 'session_id', 'SqlType': 'VARCHAR(64)', 'Mapping': '$.session_id'},
                   {'Name': 'event_type', 'SqlType': 'VARCHAR(32)', 'Mapping': '$.event_type'},
                   {'Name': 'timestamp', 'SqlType': 'TIMESTAMP', 'Mapping': '$.timestamp'},
                   {'Name': 'properties', 'SqlType': 'VARCHAR(2048)', 'Mapping': '$.properties'}
               ],
               'RecordFormat': {'RecordFormatType': 'JSON'},
               'RecordEncoding': 'UTF-8'
           }
   
   # Usage example
   processor = EcommerceStreamProcessor()
   analytics_result = processor.setup_real_time_analytics()
   processing_result = processor.process_real_time_events('user-interactions', max_records=5000)
   personalization_result = processor.setup_personalization_engine()
   ```

**Expected Outcome:** Real-time e-commerce analytics platform processing 100M+ daily events with <100ms latency, 40% improvement in conversion rates through personalization, 60% reduction in fraud losses, and comprehensive operational dashboards for business intelligence.

### Example 2: IoT Industrial Monitoring & Predictive Analytics

**Business Requirement:** Implement enterprise IoT data processing for a manufacturing company with 10,000+ sensors, enabling predictive maintenance, quality control, and operational efficiency optimization with real-time alerting and automated response capabilities.

**Implementation Steps:**
1. **Industrial IoT Data Pipeline Architecture**
   ```bash
   # Create IoT-specific streams with different priorities
   iot_streams=(
     "sensor-telemetry:100:CriticalTelemetry"
     "machine-status:50:EquipmentMonitoring"
     "quality-metrics:30:QualityControl" 
     "environmental-data:20:EnvironmentMonitoring"
     "maintenance-logs:10:MaintenancePlanning"
   )

   for stream_config in "${iot_streams[@]}"; do
     IFS=':' read -r stream_name shard_count category <<< "$stream_config"
     
     # Create stream optimized for IoT workloads
     aws kinesis create-stream \
       --stream-name "$stream_name" \
       --shard-count "$shard_count" \
       --stream-mode-details StreamMode=ON_DEMAND \
       --tags Key=IoTCategory,Value="$category" Key=DataType,Value=TimeSeries
     
     # Configure retention for compliance and analysis
     aws kinesis increase-stream-retention-period \
       --stream-name "$stream_name" \
       --retention-period-hours 8760  # 365 days for compliance
   done
   ```

2. **Predictive Analytics & Anomaly Detection Engine**
   ```python
   import boto3
   import json
   import numpy as np
   from datetime import datetime, timedelta
   from typing import Dict, List, Any, Optional, Tuple
   from dataclasses import dataclass, field
   import statistics
   import logging
   
   @dataclass
   class SensorReading:
       sensor_id: str
       machine_id: str  
       facility_id: str
       timestamp: datetime
       metric_type: str
       value: float
       unit: str
       quality_score: float = 1.0
       anomaly_score: float = 0.0
   
   @dataclass
   class PredictiveMaintenanceAlert:
       machine_id: str
       alert_type: str
       severity: str
       predicted_failure_time: datetime
       confidence_score: float
       recommended_actions: List[str] = field(default_factory=list)
       cost_impact: float = 0.0
   
   class IoTIndustrialProcessor:
       """
       Enterprise IoT industrial data processor with predictive maintenance,
       anomaly detection, and operational intelligence capabilities.
       """
       
       def __init__(self, region: str = 'us-east-1'):
           self.kinesis = boto3.client('kinesis', region_name=region)
           self.firehose = boto3.client('firehose', region_name=region)
           self.timestream = boto3.client('timestream-write', region_name=region)
           self.cloudwatch = boto3.client('cloudwatch', region_name=region)
           self.sns = boto3.client('sns', region_name=region)
           self.region = region
           self.logger = self._setup_logging()
           
           # Real-time analytics state
           self.sensor_baselines = {}
           self.machine_health_scores = {}
           self.anomaly_patterns = {}
           self.maintenance_predictions = {}
           
       def _setup_logging(self) -> logging.Logger:
           logger = logging.getLogger('IoTIndustrialProcessor')
           logger.setLevel(logging.INFO)
           if not logger.handlers:
               handler = logging.StreamHandler()
               formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
               handler.setFormatter(formatter)
               logger.addHandler(handler)
           return logger
       
       def setup_predictive_maintenance_system(self) -> Dict[str, Any]:
           """Setup comprehensive predictive maintenance analytics"""
           try:
               # Create Kinesis Analytics application for predictive maintenance
               maintenance_queries = {
                   'vibration_analysis': """
                       CREATE STREAM "vibration_anomalies" AS
                       SELECT 
                           sensor_id,
                           machine_id,
                           AVG(value) as avg_vibration,
                           STDDEV_POP(value) as vibration_stddev,
                           MAX(value) as peak_vibration,
                           COUNT(*) as reading_count,
                           CASE 
                               WHEN AVG(value) > 10.0 OR STDDEV_POP(value) > 5.0 THEN 'HIGH_RISK'
                               WHEN AVG(value) > 7.0 OR STDDEV_POP(value) > 3.0 THEN 'MEDIUM_RISK'
                               ELSE 'NORMAL'
                           END as risk_level
                       FROM SOURCE_SQL_STREAM_001
                       WHERE metric_type = 'vibration'
                       GROUP BY sensor_id, machine_id, 
                                RANGE_WINDOW(INTERVAL '5' MINUTE)
                       HAVING AVG(value) > 5.0  -- Threshold for attention
                   """,
                   
                   'temperature_trending': """
                       CREATE STREAM "temperature_trends" AS
                       SELECT 
                           machine_id,
                           facility_id,
                           AVG(value) as avg_temp,
                           LAG(AVG(value), 1) OVER (
                               PARTITION BY machine_id 
                               ORDER BY ROWTIME_TO_TIMESTAMP(ROWTIME)
                           ) as prev_avg_temp,
                           (AVG(value) - LAG(AVG(value), 1) OVER (
                               PARTITION BY machine_id 
                               ORDER BY ROWTIME_TO_TIMESTAMP(ROWTIME)
                           )) as temp_change_rate
                       FROM SOURCE_SQL_STREAM_001
                       WHERE metric_type = 'temperature'
                       GROUP BY machine_id, facility_id,
                                RANGE_WINDOW(INTERVAL '10' MINUTE)
                       HAVING ABS(temp_change_rate) > 5.0  -- Rapid temperature changes
                   """,
                   
                   'efficiency_monitoring': """
                       CREATE STREAM "efficiency_metrics" AS
                       SELECT 
                           machine_id,
                           facility_id,
                           SUM(CASE WHEN metric_type = 'production_count' THEN value ELSE 0 END) as total_production,
                           AVG(CASE WHEN metric_type = 'power_consumption' THEN value ELSE 0 END) as avg_power,
                           (SUM(CASE WHEN metric_type = 'production_count' THEN value ELSE 0 END) / 
                            NULLIF(AVG(CASE WHEN metric_type = 'power_consumption' THEN value ELSE 0 END), 0)) as efficiency_ratio,
                           COUNT(DISTINCT sensor_id) as active_sensors
                       FROM SOURCE_SQL_STREAM_001
                       WHERE metric_type IN ('production_count', 'power_consumption')
                       GROUP BY machine_id, facility_id,
                                RANGE_WINDOW(INTERVAL '15' MINUTE)
                   """
               }
               
               # Deploy analytics applications
               deployed_applications = []
               for query_name, sql_query in maintenance_queries.items():
                   try:
                       app_response = self.kinesis.create_application(  # Note: Using Kinesis Analytics v1 for SQL
                           ApplicationName=f'industrial-{query_name}',
                           ApplicationDescription=f'Predictive maintenance: {query_name}',
                           Inputs=[{
                               'NamePrefix': 'SOURCE_SQL_STREAM',
                               'KinesisStreamsInput': {
                                   'ResourceARN': 'arn:aws:kinesis:us-east-1:123456789012:stream/sensor-telemetry',
                                   'RoleARN': 'arn:aws:iam::123456789012:role/kinesis-analytics-industrial-role'
                               },
                               'InputSchema': {
                                   'RecordColumns': [
                                       {'Name': 'sensor_id', 'SqlType': 'VARCHAR(32)', 'Mapping': '$.sensor_id'},
                                       {'Name': 'machine_id', 'SqlType': 'VARCHAR(32)', 'Mapping': '$.machine_id'},
                                       {'Name': 'facility_id', 'SqlType': 'VARCHAR(32)', 'Mapping': '$.facility_id'},
                                       {'Name': 'timestamp', 'SqlType': 'TIMESTAMP', 'Mapping': '$.timestamp'},
                                       {'Name': 'metric_type', 'SqlType': 'VARCHAR(32)', 'Mapping': '$.metric_type'},
                                       {'Name': 'value', 'SqlType': 'DOUBLE', 'Mapping': '$.value'},
                                       {'Name': 'unit', 'SqlType': 'VARCHAR(16)', 'Mapping': '$.unit'}
                                   ],
                                   'RecordFormat': {'RecordFormatType': 'JSON'}
                               }
                           }],
                           Outputs=[{
                               'Name': f'{query_name}_output',
                               'KinesisStreamsOutput': {
                                   'ResourceARN': f'arn:aws:kinesis:us-east-1:123456789012:stream/maintenance-alerts',
                                   'RoleARN': 'arn:aws:iam::123456789012:role/kinesis-analytics-industrial-role'
                               },
                               'DestinationSchema': {'RecordFormatType': 'JSON'}
                           }]
                       )
                       
                       deployed_applications.append({
                           'application_name': f'industrial-{query_name}',
                           'application_arn': app_response['ApplicationSummary']['ApplicationARN'],
                           'query_type': query_name,
                           'status': 'deployed'
                       })
                       
                   except Exception as app_error:
                       self.logger.error(f"Failed to deploy {query_name}: {str(app_error)}")
                       deployed_applications.append({
                           'application_name': f'industrial-{query_name}',
                           'query_type': query_name,
                           'status': 'error',
                           'error': str(app_error)
                       })
               
               return {
                   'predictive_applications': deployed_applications,
                   'total_applications': len(deployed_applications),
                   'successful_deployments': len([app for app in deployed_applications if app['status'] == 'deployed']),
                   'predictive_maintenance': 'active'
               }
               
           except Exception as e:
               self.logger.error(f"Predictive maintenance setup failed: {str(e)}")
               raise
       
       def process_sensor_telemetry(self, stream_name: str, batch_size: int = 500) -> Dict[str, Any]:
           """Process real-time sensor telemetry with anomaly detection"""
           try:
               processing_stats = {
                   'total_readings': 0,
                   'anomalies_detected': 0,
                   'maintenance_alerts': 0,
                   'quality_issues': 0,
                   'efficiency_improvements': 0,
                   'machines_monitored': set()
               }
               
               # Get stream records
               response = self.kinesis.describe_stream(StreamName=stream_name)
               shard_id = response['StreamDescription']['Shards'][0]['ShardId']
               
               iterator_response = self.kinesis.get_shard_iterator(
                   StreamName=stream_name,
                   ShardId=shard_id,
                   ShardIteratorType='LATEST'
               )
               
               shard_iterator = iterator_response['ShardIterator']
               
               # Process records in batches
               while processing_stats['total_readings'] < batch_size:
                   records_response = self.kinesis.get_records(
                       ShardIterator=shard_iterator,
                       Limit=100
                   )
                   
                   records = records_response.get('Records', [])
                   if not records:
                       break
                   
                   for record in records:
                       try:
                           # Parse sensor reading
                           data = json.loads(record['Data'])
                           sensor_reading = SensorReading(
                               sensor_id=data['sensor_id'],
                               machine_id=data['machine_id'],
                               facility_id=data['facility_id'],
                               timestamp=datetime.fromisoformat(data['timestamp']),
                               metric_type=data['metric_type'],
                               value=float(data['value']),
                               unit=data['unit'],
                               quality_score=data.get('quality_score', 1.0)
                           )
                           
                           # Anomaly detection
                           anomaly_score = self._detect_sensor_anomaly(sensor_reading)
                           sensor_reading.anomaly_score = anomaly_score
                           
                           if anomaly_score > 0.8:  # High anomaly threshold
                               processing_stats['anomalies_detected'] += 1
                               self._handle_sensor_anomaly(sensor_reading)
                           
                           # Predictive maintenance analysis
                           maintenance_alert = self._analyze_maintenance_needs(sensor_reading)
                           if maintenance_alert:
                               processing_stats['maintenance_alerts'] += 1
                               self._send_maintenance_alert(maintenance_alert)
                           
                           # Quality control analysis
                           if self._analyze_quality_metrics(sensor_reading):
                               processing_stats['quality_issues'] += 1
                           
                           # Efficiency optimization
                           if self._analyze_efficiency_opportunities(sensor_reading):
                               processing_stats['efficiency_improvements'] += 1
                           
                           # Update machine health tracking
                           self._update_machine_health(sensor_reading)
                           
                           processing_stats['total_readings'] += 1
                           processing_stats['machines_monitored'].add(sensor_reading.machine_id)
                           
                       except Exception as record_error:
                           self.logger.warning(f"Failed to process sensor record: {str(record_error)}")
                           continue
                   
                   # Update iterator
                   shard_iterator = records_response.get('NextShardIterator')
                   if not shard_iterator:
                       break
               
               # Convert set to count for JSON serialization
               processing_stats['machines_monitored'] = len(processing_stats['machines_monitored'])
               
               # Store processed data to TimeStream for time-series analysis
               self._store_to_timestream(processing_stats)
               
               # Generate real-time operational insights
               operational_insights = self._generate_operational_insights()
               
               return {
                   'processing_statistics': processing_stats,
                   'operational_insights': operational_insights,
                   'stream_name': stream_name,
                   'processing_timestamp': datetime.utcnow().isoformat()
               }
               
           except Exception as e:
               self.logger.error(f"Sensor telemetry processing failed: {str(e)}")
               raise
       
       def _detect_sensor_anomaly(self, reading: SensorReading) -> float:
           """Advanced anomaly detection for sensor readings"""
           try:
               sensor_key = f"{reading.sensor_id}_{reading.metric_type}"
               
               # Initialize baseline if not exists
               if sensor_key not in self.sensor_baselines:
                   self.sensor_baselines[sensor_key] = {
                       'values': [],
                       'mean': 0.0,
                       'std': 0.0,
                       'last_update': reading.timestamp
                   }
               
               baseline = self.sensor_baselines[sensor_key]
               baseline['values'].append(reading.value)
               
               # Keep only recent values for baseline (sliding window)
               if len(baseline['values']) > 1000:
                   baseline['values'] = baseline['values'][-500:]
               
               # Calculate statistics if we have enough data
               if len(baseline['values']) >= 30:
                   baseline['mean'] = statistics.mean(baseline['values'])
                   baseline['std'] = statistics.stdev(baseline['values'])
                   
                   # Calculate z-score for anomaly detection
                   if baseline['std'] > 0:
                       z_score = abs(reading.value - baseline['mean']) / baseline['std']
                       
                       # Convert z-score to anomaly probability (0-1)
                       if z_score > 3:  # 3-sigma rule
                           return min(z_score / 5, 1.0)  # Cap at 1.0
                       elif z_score > 2:
                           return z_score / 4
                       else:
                           return 0.0
               
               return 0.0  # Not enough data for anomaly detection
               
           except Exception as e:
               self.logger.warning(f"Anomaly detection error: {str(e)}")
               return 0.0
       
       def _analyze_maintenance_needs(self, reading: SensorReading) -> Optional[PredictiveMaintenanceAlert]:
           """Analyze sensor data for predictive maintenance opportunities"""
           try:
               machine_id = reading.machine_id
               
               # Initialize machine tracking
               if machine_id not in self.maintenance_predictions:
                   self.maintenance_predictions[machine_id] = {
                       'vibration_trend': [],
                       'temperature_trend': [],
                       'efficiency_trend': [],
                       'last_maintenance': datetime.utcnow() - timedelta(days=30),
                       'health_score': 1.0
                   }
               
               machine_data = self.maintenance_predictions[machine_id]
               
               # Track different maintenance indicators
               if reading.metric_type == 'vibration':
                   machine_data['vibration_trend'].append((reading.timestamp, reading.value))
                   if len(machine_data['vibration_trend']) > 100:
                       machine_data['vibration_trend'] = machine_data['vibration_trend'][-50:]
                   
                   # Check for increasing vibration trend
                   if len(machine_data['vibration_trend']) >= 10:
                       recent_values = [v[1] for v in machine_data['vibration_trend'][-10:]]
                       if all(recent_values[i] <= recent_values[i+1] for i in range(len(recent_values)-1)):
                           # Consistently increasing vibration
                           if max(recent_values) > 8.0:  # Threshold
                               return PredictiveMaintenanceAlert(
                                   machine_id=machine_id,
                                   alert_type='BEARING_FAILURE',
                                   severity='HIGH',
                                   predicted_failure_time=datetime.utcnow() + timedelta(days=7),
                                   confidence_score=0.85,
                                   recommended_actions=[
                                       'Schedule bearing inspection',
                                       'Reduce operating speed',
                                       'Plan replacement parts order'
                                   ],
                                   cost_impact=15000.0
                               )
               
               elif reading.metric_type == 'temperature':
                   machine_data['temperature_trend'].append((reading.timestamp, reading.value))
                   if len(machine_data['temperature_trend']) > 100:
                       machine_data['temperature_trend'] = machine_data['temperature_trend'][-50:]
                   
                   # Check for overheating patterns
                   if reading.value > 85.0:  # High temperature threshold
                       return PredictiveMaintenanceAlert(
                           machine_id=machine_id,
                           alert_type='OVERHEATING',
                           severity='MEDIUM',
                           predicted_failure_time=datetime.utcnow() + timedelta(days=14),
                           confidence_score=0.72,
                           recommended_actions=[
                               'Check cooling system',
                               'Clean air filters',
                               'Verify lubricant levels'
                           ],
                           cost_impact=5000.0
                       )
               
               return None
               
           except Exception as e:
               self.logger.warning(f"Maintenance analysis error: {str(e)}")
               return None
       
       def _generate_operational_insights(self) -> Dict[str, Any]:
           """Generate real-time operational insights from processed IoT data"""
           try:
               insights = {
                   'fleet_health': {
                       'total_machines': len(self.machine_health_scores),
                       'healthy_machines': len([m for m, score in self.machine_health_scores.items() if score > 0.8]),
                       'at_risk_machines': len([m for m, score in self.machine_health_scores.items() if 0.5 < score <= 0.8]),
                       'critical_machines': len([m for m, score in self.machine_health_scores.items() if score <= 0.5])
                   },
                   'maintenance_schedule': {
                       'immediate_attention': len([m for m, data in self.maintenance_predictions.items() if self._needs_immediate_attention(data)]),
                       'scheduled_maintenance': len([m for m, data in self.maintenance_predictions.items() if self._needs_scheduled_maintenance(data)]),
                       'optimal_machines': len([m for m, data in self.maintenance_predictions.items() if not self._needs_any_maintenance(data)])
                   },
                   'efficiency_metrics': {
                       'avg_fleet_efficiency': self._calculate_average_fleet_efficiency(),
                       'top_performing_machines': self._get_top_performing_machines(),
                       'efficiency_opportunities': self._identify_efficiency_opportunities()
                   },
                   'cost_projections': {
                       'prevented_downtime_savings': self._calculate_prevented_downtime(),
                       'maintenance_cost_optimization': self._calculate_maintenance_savings(),
                       'energy_efficiency_gains': self._calculate_energy_savings()
                   }
               }
               
               return insights
               
           except Exception as e:
               self.logger.warning(f"Insights generation error: {str(e)}")
               return {}
   
   # Usage example
   iot_processor = IoTIndustrialProcessor()
   maintenance_result = iot_processor.setup_predictive_maintenance_system()
   telemetry_result = iot_processor.process_sensor_telemetry('sensor-telemetry', batch_size=1000)
   ```

**Expected Outcome:** Industrial IoT monitoring system processing 10M+ sensor readings daily, 30% reduction in unplanned downtime through predictive maintenance, 25% improvement in operational efficiency, and $2M+ annual savings from optimized maintenance scheduling.

## Monitoring & Observability

### Key Metrics to Monitor
| Metric | Description | Threshold | Action |
|--------|-------------|-----------|--------|
| **Incoming Records** | Records per second ingestion rate | Warning: >80% capacity, Critical: >95% capacity | Scale shards, optimize partition keys |
| **Consumer Lag (Iterator Age)** | Time delay between record production and consumption | Warning: >30s, Critical: >300s | Scale consumers, optimize processing |
| **Read/Write Throttling** | Throttled requests due to capacity limits | Warning: >1%, Critical: >5% | Add shards, implement backoff retry |
| **Error Rate** | Failed processing percentage | Warning: >2%, Critical: >5% | Check error logs, validate data formats |

### CloudWatch Integration
```bash
# Create comprehensive Kinesis dashboard
aws cloudwatch put-dashboard \
  --dashboard-name "Kinesis-Enterprise-Streaming-Dashboard" \
  --dashboard-body '{
    "widgets": [
      {
        "type": "metric",
        "properties": {
          "metrics": [
            ["AWS/Kinesis", "IncomingRecords", "StreamName", "enterprise-data-stream"],
            [".", "OutgoingRecords", ".", "."],
            [".", "IteratorAgeMilliseconds", ".", "."]
          ],
          "period": 300,
          "stat": "Average",
          "region": "us-east-1",
          "title": "Stream Throughput and Consumer Lag"
        }
      },
      {
        "type": "metric",
        "properties": {
          "metrics": [
            ["AWS/KinesisFirehose", "DeliveryToS3.Records", "DeliveryStreamName", "enterprise-delivery-stream"],
            [".", "DeliveryToS3.Success", ".", "."],
            [".", "DeliveryToS3.DataFreshness", ".", "."]
          ],
          "period": 300,
          "stat": "Sum",
          "region": "us-east-1", 
          "title": "Data Delivery Performance"
        }
      }
    ]
  }'

# Set up critical performance alarms
aws cloudwatch put-metric-alarm \
  --alarm-name "Kinesis-HighConsumerLag" \
  --alarm-description "Consumer lag exceeds acceptable threshold" \
  --metric-name "IteratorAgeMilliseconds" \
  --namespace "AWS/Kinesis" \
  --statistic Average \
  --period 300 \
  --threshold 300000 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=StreamName,Value=enterprise-data-stream \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:kinesis-alerts

# Monitor shard-level metrics for capacity planning
aws cloudwatch put-metric-alarm \
  --alarm-name "Kinesis-WriteThrottling" \
  --alarm-description "Write throttling detected on stream" \
  --metric-name "WriteProvisionedThroughputExceeded" \
  --namespace "AWS/Kinesis" \
  --statistic Sum \
  --period 300 \
  --threshold 0 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=StreamName,Value=enterprise-data-stream \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:kinesis-critical-alerts
```

### Custom Monitoring
```python
import boto3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

class KinesisMonitor:
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
        self.kinesis = boto3.client('kinesis')
        self.firehose = boto3.client('firehose')
        
    def publish_custom_metrics(self, stream_name: str, custom_metrics: Dict[str, float]) -> None:
        """Publish custom business metrics to CloudWatch"""
        try:
            metric_data = []
            for metric_name, value in custom_metrics.items():
                metric_data.append({
                    'MetricName': metric_name,
                    'Value': value,
                    'Unit': 'Count',
                    'Dimensions': [
                        {
                            'Name': 'StreamName',
                            'Value': stream_name
                        }
                    ],
                    'Timestamp': datetime.utcnow()
                })
            
            self.cloudwatch.put_metric_data(
                Namespace='Custom/Kinesis',
                MetricData=metric_data
            )
        except Exception as e:
            print(f"Custom metric publication failed: {e}")
            
    def generate_stream_health_report(self, stream_name: str) -> Dict[str, Any]:
        """Generate comprehensive stream health report"""
        try:
            # Get stream description and metrics
            stream_desc = self.kinesis.describe_stream(StreamName=stream_name)
            stream_info = stream_desc['StreamDescription']
            
            # Get recent metrics
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)
            
            metrics_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/Kinesis',
                MetricName='IncomingRecords',
                Dimensions=[{'Name': 'StreamName', 'Value': stream_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Sum', 'Average']
            )
            
            health_report = {
                'stream_name': stream_name,
                'stream_status': stream_info['StreamStatus'],
                'shard_count': len(stream_info['Shards']),
                'retention_period': stream_info['RetentionPeriodHours'],
                'encryption_type': stream_info.get('EncryptionType', 'NONE'),
                'recent_throughput': self._calculate_throughput(metrics_response['Datapoints']),
                'shard_utilization': self._calculate_shard_utilization(stream_name),
                'estimated_cost': self._estimate_stream_cost(stream_info),
                'health_score': self._calculate_health_score(stream_name),
                'recommendations': self._generate_recommendations(stream_name)
            }
            
            return health_report
            
        except Exception as e:
            print(f"Health report generation failed: {e}")
            return {}
    
    def _calculate_shard_utilization(self, stream_name: str) -> Dict[str, float]:
        """Calculate per-shard utilization metrics"""
        try:
            stream_desc = self.kinesis.describe_stream(StreamName=stream_name)
            shards = stream_desc['StreamDescription']['Shards']
            
            utilization_data = {}
            for shard in shards:
                shard_id = shard['ShardId']
                
                # Get shard-level metrics
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(minutes=30)
                
                shard_metrics = self.cloudwatch.get_metric_statistics(
                    Namespace='AWS/Kinesis',
                    MetricName='IncomingRecords',
                    Dimensions=[
                        {'Name': 'StreamName', 'Value': stream_name},
                        {'Name': 'ShardId', 'Value': shard_id}
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,
                    Statistics=['Sum']
                )
                
                if shard_metrics['Datapoints']:
                    avg_records = sum(dp['Sum'] for dp in shard_metrics['Datapoints']) / len(shard_metrics['Datapoints'])
                    utilization_pct = (avg_records / 1000) * 100  # 1000 records/sec capacity
                    utilization_data[shard_id] = min(utilization_pct, 100.0)
                else:
                    utilization_data[shard_id] = 0.0
            
            return utilization_data
            
        except Exception as e:
            print(f"Shard utilization calculation failed: {e}")
            return {}
```

## Security & Compliance

### Security Best Practices
- **Encryption at Rest:** Enable server-side encryption using AWS KMS with customer-managed keys for sensitive streaming data
- **Encryption in Transit:** All data transmission uses TLS 1.2+ with certificate validation for secure streaming endpoints
- **Access Control:** Implement least-privilege IAM policies with resource-based permissions and cross-account access controls
- **VPC Endpoints:** Deploy Kinesis VPC endpoints for private network access without internet gateway routing

### Compliance Frameworks
- **SOC 2 Type II:** Comprehensive audit logging, data retention policies, and automated compliance reporting for streaming data governance
- **HIPAA:** Healthcare data protection with encryption, access logging, and data retention controls for PHI streaming workflows
- **PCI DSS:** Payment card data streaming with tokenization, encryption, and secure transmission for financial transactions
- **GDPR:** Data privacy compliance with consent management, data subject rights, and cross-border data transfer controls

### IAM Policies
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "KinesisStreamAccess",
      "Effect": "Allow",
      "Action": [
        "kinesis:PutRecord",
        "kinesis:PutRecords",
        "kinesis:GetRecords",
        "kinesis:GetShardIterator",
        "kinesis:DescribeStream",
        "kinesis:ListStreams"
      ],
      "Resource": [
        "arn:aws:kinesis:*:*:stream/enterprise-*"
      ],
      "Condition": {
        "StringEquals": {
          "kinesis:StreamName": ["enterprise-data-stream", "enterprise-analytics-stream"]
        }
      }
    },
    {
      "Sid": "FirehoseDeliveryAccess", 
      "Effect": "Allow",
      "Action": [
        "firehose:PutRecord",
        "firehose:PutRecordBatch",
        "firehose:DescribeDeliveryStream"
      ],
      "Resource": [
        "arn:aws:firehose:*:*:deliverystream/enterprise-*"
      ]
    },
    {
      "Sid": "AnalyticsApplicationAccess",
      "Effect": "Allow", 
      "Action": [
        "kinesisanalytics:CreateApplication",
        "kinesisanalytics:DescribeApplication",
        "kinesisanalytics:StartApplication",
        "kinesisanalytics:StopApplication"
      ],
      "Resource": [
        "arn:aws:kinesisanalytics:*:*:application/enterprise-*"
      ]
    }
  ]
}
```

## Cost Optimization

### Pricing Model
- **Data Streams:** $0.015 per shard hour + $0.014 per million PUT payload units (25KB chunks) + $0.023 per shard hour for extended retention
- **Data Firehose:** $0.029 per GB ingested + $0.018 per GB for format conversion + additional charges for VPC delivery and compression
- **Data Analytics:** $0.11 per Kinesis Processing Unit (KPU) hour with auto-scaling based on application demand
- **Video Streams:** $0.0085 per GB ingested + $0.0085 per GB consumed + storage costs for retained video data

### Cost Optimization Strategies
```bash
# Implement shard auto-scaling for cost optimization
aws application-autoscaling register-scalable-target \
  --service-namespace kinesis \
  --resource-id stream/enterprise-data-stream \
  --scalable-dimension kinesis:shard:count \
  --min-capacity 5 \
  --max-capacity 50 \
  --role-arn arn:aws:iam::123456789012:role/application-autoscaling-kinesis-role

# Create scaling policies
aws application-autoscaling put-scaling-policy \
  --service-namespace kinesis \
  --resource-id stream/enterprise-data-stream \
  --scalable-dimension kinesis:shard:count \
  --policy-name "kinesis-scale-out-policy" \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "KinesisStreamIncomingRecords"
    },
    "ScaleOutCooldown": 300,
    "ScaleInCooldown": 900
  }'

# Set up cost monitoring and budget alerts
aws budgets create-budget \
  --account-id 123456789012 \
  --budget '{
    "BudgetName": "Kinesis-Monthly-Budget",
    "BudgetLimit": {
      "Amount": "2000",
      "Unit": "USD"
    },
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST",
    "CostFilters": {
      "Service": ["Amazon Kinesis", "Amazon Kinesis Data Firehose", "Amazon Kinesis Data Analytics"]
    }
  }' \
  --notifications-with-subscribers '[
    {
      "Notification": {
        "NotificationType": "ACTUAL",
        "ComparisonOperator": "GREATER_THAN",
        "Threshold": 80,
        "ThresholdType": "PERCENTAGE"
      },
      "Subscribers": [
        {
          "SubscriptionType": "EMAIL",
          "Address": "devops-team@company.com"
        }
      ]
    }
  ]'

# Optimize Firehose delivery for cost efficiency
aws firehose put-delivery-stream-policy \
  --delivery-stream-name enterprise-delivery-stream \
  --policy '{
    "BufferingHints": {
      "SizeInMBs": 128,
      "IntervalInSeconds": 900
    },
    "CompressionFormat": "GZIP",
    "CloudWatchLogging": {
      "Enabled": false
    }
  }'
```

## Automation & Infrastructure as Code

### CloudFormation Template
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Enterprise Kinesis streaming analytics platform'

Parameters:
  EnvironmentName:
    Type: String
    Default: production
    AllowedValues: [development, staging, production]
  
  StreamShardCount:
    Type: Number
    Default: 10
    MinValue: 1
    MaxValue: 200
    Description: Initial number of shards for the data stream
  
  RetentionPeriodHours:
    Type: Number
    Default: 168
    MinValue: 24
    MaxValue: 8760
    Description: Data retention period in hours

Resources:
  # Primary data stream
  EnterpriseDataStream:
    Type: AWS::Kinesis::Stream
    Properties:
      Name: !Sub '${EnvironmentName}-enterprise-data-stream'
      ShardCount: !Ref StreamShardCount
      RetentionPeriodHours: !Ref RetentionPeriodHours
      StreamEncryption:
        EncryptionType: KMS
        KeyId: !Ref StreamEncryptionKey
      Tags:
        - Key: Environment
          Value: !Ref EnvironmentName
        - Key: Service
          Value: Kinesis
        - Key: Purpose
          Value: DataStreaming

  # KMS key for stream encryption
  StreamEncryptionKey:
    Type: AWS::KMS::Key
    Properties:
      Description: !Sub 'Encryption key for ${EnvironmentName} Kinesis streams'
      KeyPolicy:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              AWS: !Sub 'arn:aws:iam::${AWS::AccountId}:root'
            Action: 'kms:*'
            Resource: '*'
          - Effect: Allow
            Principal:
              Service: kinesis.amazonaws.com
            Action:
              - kms:Decrypt
              - kms:GenerateDataKey
            Resource: '*'

  StreamEncryptionKeyAlias:
    Type: AWS::KMS::Alias
    Properties:
      AliasName: !Sub 'alias/${EnvironmentName}-kinesis-key'
      TargetKeyId: !Ref StreamEncryptionKey

  # Data delivery stream to S3
  DataDeliveryStream:
    Type: AWS::KinesisFirehose::DeliveryStream
    Properties:
      DeliveryStreamName: !Sub '${EnvironmentName}-data-delivery-stream'
      DeliveryStreamType: KinesisStreamAsSource
      KinesisStreamSourceConfiguration:
        KinesisStreamARN: !GetAtt EnterpriseDataStream.Arn
        RoleARN: !GetAtt FirehoseDeliveryRole.Arn
      ExtendedS3DestinationConfiguration:
        BucketARN: !GetAtt DataLakeBucket.Arn
        RoleARN: !GetAtt FirehoseDeliveryRole.Arn
        Prefix: !Sub 'data/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/'
        ErrorOutputPrefix: 'errors/'
        BufferingHints:
          IntervalInSeconds: 300
          SizeInMBs: 128
        CompressionFormat: GZIP
        ProcessingConfiguration:
          Enabled: true
          Processors:
            - Type: Lambda
              Parameters:
                - ParameterName: LambdaArn
                  ParameterValue: !GetAtt DataTransformFunction.Arn
        DataFormatConversionConfiguration:
          Enabled: true
          OutputFormatConfiguration:
            Serializer:
              ParquetSerDe: {}
          SchemaConfiguration:
            DatabaseName: !Ref GlueDatabase
            TableName: !Ref GlueTable
            RoleARN: !GetAtt FirehoseDeliveryRole.Arn

  # S3 bucket for data lake
  DataLakeBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub '${EnvironmentName}-enterprise-data-lake-${AWS::AccountId}'
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
      VersioningConfiguration:
        Status: Enabled
      LifecycleConfiguration:
        Rules:
          - Id: DataLifecycleRule
            Status: Enabled
            Transitions:
              - TransitionInDays: 30
                StorageClass: STANDARD_IA
              - TransitionInDays: 90
                StorageClass: GLACIER
              - TransitionInDays: 365
                StorageClass: DEEP_ARCHIVE
      Tags:
        - Key: Environment
          Value: !Ref EnvironmentName
        - Key: Purpose
          Value: DataLake

  # IAM role for Firehose
  FirehoseDeliveryRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub '${EnvironmentName}-firehose-delivery-role'
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: firehose.amazonaws.com
            Action: sts:AssumeRole
      Policies:
        - PolicyName: FirehoseDeliveryRolePolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - s3:AbortMultipartUpload
                  - s3:GetBucketLocation
                  - s3:GetObject
                  - s3:ListBucket
                  - s3:ListBucketMultipartUploads
                  - s3:PutObject
                Resource:
                  - !GetAtt DataLakeBucket.Arn
                  - !Sub '${DataLakeBucket.Arn}/*'
              - Effect: Allow
                Action:
                  - kinesis:DescribeStream
                  - kinesis:GetShardIterator
                  - kinesis:GetRecords
                Resource: !GetAtt EnterpriseDataStream.Arn
              - Effect: Allow
                Action:
                  - lambda:InvokeFunction
                  - lambda:GetFunctionConfiguration
                Resource: !GetAtt DataTransformFunction.Arn

  # Lambda function for data transformation
  DataTransformFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: !Sub '${EnvironmentName}-data-transform'
      Runtime: python3.9
      Handler: index.lambda_handler
      Role: !GetAtt DataTransformRole.Arn
      Timeout: 300
      MemorySize: 512
      Code:
        ZipFile: |
          import json
          import boto3
          import base64
          from datetime import datetime
          
          def lambda_handler(event, context):
              output = []
              
              for record in event['records']:
                  # Decode the data
                  payload = base64.b64decode(record['data'])
                  data = json.loads(payload)
                  
                  # Add processing timestamp
                  data['processed_at'] = datetime.utcnow().isoformat()
                  
                  # Data enrichment and transformation logic here
                  
                  # Encode the data back
                  output_record = {
                      'recordId': record['recordId'],
                      'result': 'Ok',
                      'data': base64.b64encode(
                          json.dumps(data).encode('utf-8')
                      ).decode('utf-8')
                  }
                  output.append(output_record)
              
              return {'records': output}

  DataTransformRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
      Policies:
        - PolicyName: DataTransformPolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - kinesis:DescribeStream
                  - kinesis:GetShardIterator
                  - kinesis:GetRecords
                Resource: !GetAtt EnterpriseDataStream.Arn

  # Glue components for data catalog
  GlueDatabase:
    Type: AWS::Glue::Database
    Properties:
      CatalogId: !Ref AWS::AccountId
      DatabaseInput:
        Name: !Sub '${EnvironmentName}_enterprise_data'
        Description: 'Enterprise data catalog database'

  GlueTable:
    Type: AWS::Glue::Table
    Properties:
      CatalogId: !Ref AWS::AccountId
      DatabaseName: !Ref GlueDatabase
      TableInput:
        Name: streaming_data
        StorageDescriptor:
          Columns:
            - Name: event_id
              Type: string
            - Name: timestamp
              Type: timestamp
            - Name: event_type
              Type: string
            - Name: user_id
              Type: string
            - Name: properties
              Type: struct<amount:double,category:string>
          Location: !Sub 's3://${DataLakeBucket}/data/'
          InputFormat: org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat
          OutputFormat: org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat
          SerdeInfo:
            SerializationLibrary: org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe

Outputs:
  DataStreamArn:
    Description: ARN of the enterprise data stream
    Value: !GetAtt EnterpriseDataStream.Arn
    Export:
      Name: !Sub '${EnvironmentName}-DataStreamArn'
  
  DataStreamName:
    Description: Name of the enterprise data stream
    Value: !Ref EnterpriseDataStream
    Export:
      Name: !Sub '${EnvironmentName}-DataStreamName'
  
  DeliveryStreamArn:
    Description: ARN of the data delivery stream
    Value: !GetAtt DataDeliveryStream.Arn
    Export:
      Name: !Sub '${EnvironmentName}-DeliveryStreamArn'
  
  DataLakeBucketName:
    Description: Name of the data lake S3 bucket
    Value: !Ref DataLakeBucket
    Export:
      Name: !Sub '${EnvironmentName}-DataLakeBucket'
```

### Terraform Configuration
```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# KMS key for encryption
resource "aws_kms_key" "kinesis_encryption" {
  description = "KMS key for Kinesis stream encryption"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Effect = "Allow"
        Principal = {
          Service = "kinesis.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = "*"
      }
    ]
  })
  
  tags = {
    Environment = var.environment
    Service     = "Kinesis"
    Purpose     = "StreamEncryption"
  }
}

resource "aws_kms_alias" "kinesis_encryption" {
  name          = "alias/${var.environment}-kinesis-key"
  target_key_id = aws_kms_key.kinesis_encryption.key_id
}

# Main data stream
resource "aws_kinesis_stream" "enterprise_data_stream" {
  name             = "${var.environment}-enterprise-data-stream"
  shard_count      = var.shard_count
  retention_period = var.retention_period_hours
  
  encryption_type = "KMS"
  kms_key_id      = aws_kms_key.kinesis_encryption.arn
  
  shard_level_metrics = [
    "IncomingRecords",
    "OutgoingRecords"
  ]
  
  tags = {
    Environment = var.environment
    Service     = "Kinesis"
    Purpose     = "DataStreaming"
  }
}

# S3 bucket for data lake
resource "aws_s3_bucket" "data_lake" {
  bucket = "${var.environment}-enterprise-data-lake-${data.aws_caller_identity.current.account_id}"
  
  tags = {
    Environment = var.environment
    Purpose     = "DataLake"
  }
}

resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id
  
  rule {
    id     = "data_lifecycle"
    status = "Enabled"
    
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
    
    transition {
      days          = 90
      storage_class = "GLACIER"
    }
    
    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }
  }
}

# IAM role for Firehose
resource "aws_iam_role" "firehose_delivery_role" {
  name = "${var.environment}-firehose-delivery-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "firehose.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
  
  tags = {
    Environment = var.environment
    Service     = "Kinesis"
  }
}

resource "aws_iam_role_policy" "firehose_delivery_policy" {
  name = "${var.environment}-firehose-delivery-policy"
  role = aws_iam_role.firehose_delivery_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:AbortMultipartUpload",
          "s3:GetBucketLocation",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:ListBucketMultipartUploads",
          "s3:PutObject"
        ]
        Resource = [
          aws_s3_bucket.data_lake.arn,
          "${aws_s3_bucket.data_lake.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "kinesis:DescribeStream",
          "kinesis:GetShardIterator", 
          "kinesis:GetRecords"
        ]
        Resource = aws_kinesis_stream.enterprise_data_stream.arn
      }
    ]
  })
}

# Firehose delivery stream
resource "aws_kinesis_firehose_delivery_stream" "data_delivery" {
  name        = "${var.environment}-data-delivery-stream"
  destination = "extended_s3"
  
  kinesis_source_configuration {
    kinesis_stream_arn = aws_kinesis_stream.enterprise_data_stream.arn
    role_arn          = aws_iam_role.firehose_delivery_role.arn
  }
  
  extended_s3_configuration {
    role_arn   = aws_iam_role.firehose_delivery_role.arn
    bucket_arn = aws_s3_bucket.data_lake.arn
    prefix     = "data/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/"
    error_output_prefix = "errors/"
    
    buffering_size     = 128
    buffering_interval = 300
    compression_format = "GZIP"
    
    data_format_conversion_configuration {
      enabled = true
      
      output_format_configuration {
        serializer {
          parquet_ser_de {}
        }
      }
      
      schema_configuration {
        database_name = aws_glue_catalog_database.enterprise_data.name
        table_name    = aws_glue_catalog_table.streaming_data.name
        role_arn      = aws_iam_role.firehose_delivery_role.arn
      }
    }
  }
  
  tags = {
    Environment = var.environment
    Service     = "Kinesis"
    Purpose     = "DataDelivery"
  }
}

# Glue catalog
resource "aws_glue_catalog_database" "enterprise_data" {
  name        = "${var.environment}_enterprise_data"
  description = "Enterprise data catalog database"
}

resource "aws_glue_catalog_table" "streaming_data" {
  name          = "streaming_data"
  database_name = aws_glue_catalog_database.enterprise_data.name
  
  storage_descriptor {
    location      = "s3://${aws_s3_bucket.data_lake.bucket}/data/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"
    
    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }
    
    columns {
      name = "event_id"
      type = "string"
    }
    
    columns {
      name = "timestamp"
      type = "timestamp"
    }
    
    columns {
      name = "event_type"
      type = "string"
    }
    
    columns {
      name = "user_id"
      type = "string"
    }
    
    columns {
      name = "properties"
      type = "struct<amount:double,category:string>"
    }
  }
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}

# Variables
variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "shard_count" {
  description = "Number of shards for the Kinesis stream"
  type        = number
  default     = 10
}

variable "retention_period_hours" {
  description = "Stream retention period in hours"
  type        = number
  default     = 168
}

# Outputs
output "stream_arn" {
  description = "ARN of the Kinesis stream"
  value       = aws_kinesis_stream.enterprise_data_stream.arn
}

output "stream_name" {
  description = "Name of the Kinesis stream"
  value       = aws_kinesis_stream.enterprise_data_stream.name
}

output "delivery_stream_arn" {
  description = "ARN of the Firehose delivery stream"
  value       = aws_kinesis_firehose_delivery_stream.data_delivery.arn
}

output "data_lake_bucket" {
  description = "S3 bucket name for data lake"
  value       = aws_s3_bucket.data_lake.bucket
}
```

## Troubleshooting & Operations

### Common Issues & Solutions

#### Issue 1: Consumer Lag and Throughput Problems
**Symptoms:** High iterator age, slow data processing, consumer applications falling behind
**Cause:** Insufficient consumer capacity, inefficient processing logic, or shard hotspots
**Solution:**
```bash
# Check consumer lag metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Kinesis \
  --metric-name IteratorAgeMilliseconds \
  --dimensions Name=StreamName,Value=enterprise-data-stream \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T01:00:00Z \
  --period 300 \
  --statistics Average,Maximum

# Scale up shards if necessary
aws kinesis update-shard-count \
  --stream-name enterprise-data-stream \
  --target-shard-count 20 \
  --scaling-type UNIFORM_SCALING

# Enable enhanced fan-out for dedicated throughput
aws kinesis register-stream-consumer \
  --stream-arn arn:aws:kinesis:us-east-1:123456789012:stream/enterprise-data-stream \
  --consumer-name high-priority-processor
```

#### Issue 2: Data Delivery Failures in Firehose
**Symptoms:** Records in error bucket, failed delivery metrics, data loss alerts
**Cause:** Malformed data, insufficient permissions, or destination service issues
**Solution:**
```python
import boto3
import json
from datetime import datetime, timedelta

def diagnose_firehose_issues(delivery_stream_name: str):
    """Diagnose Firehose delivery issues"""
    firehose = boto3.client('firehose')
    cloudwatch = boto3.client('cloudwatch')
    s3 = boto3.client('s3')
    
    try:
        # Get delivery stream description
        stream_desc = firehose.describe_delivery_stream(
            DeliveryStreamName=delivery_stream_name
        )
        
        print(f"Stream Status: {stream_desc['DeliveryStreamDescription']['DeliveryStreamStatus']}")
        
        # Check error metrics
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        error_metrics = cloudwatch.get_metric_statistics(
            Namespace='AWS/KinesisFirehose',
            MetricName='DeliveryToS3.Success',
            Dimensions=[
                {'Name': 'DeliveryStreamName', 'Value': delivery_stream_name}
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=300,
            Statistics=['Sum', 'Average']
        )
        
        if error_metrics['Datapoints']:
            success_rate = sum(dp['Sum'] for dp in error_metrics['Datapoints'])
            print(f"Recent Success Rate: {success_rate}")
            
            if success_rate < 100:
                # Check error records in S3
                config = stream_desc['DeliveryStreamDescription']['Destinations'][0]['ExtendedS3DestinationDescription']
                error_prefix = config.get('ErrorOutputPrefix', 'errors/')
                bucket_name = config['BucketARN'].split(':::')[1]
                
                # List recent error objects
                error_objects = s3.list_objects_v2(
                    Bucket=bucket_name,
                    Prefix=error_prefix,
                    MaxKeys=10
                )
                
                if 'Contents' in error_objects:
                    print(f"Found {len(error_objects['Contents'])} error files")
                    
                    # Analyze first error file
                    first_error = error_objects['Contents'][0]
                    error_content = s3.get_object(
                        Bucket=bucket_name,
                        Key=first_error['Key']
                    )
                    
                    error_data = error_content['Body'].read().decode('utf-8')
                    print(f"Sample Error Data: {error_data[:500]}")
        
        return True
        
    except Exception as e:
        print(f"Diagnosis failed: {e}")
        return False

# Usage
diagnose_firehose_issues('enterprise-delivery-stream')
```

### Performance Optimization

#### Optimization Strategy 1: Shard Management & Scaling
- **Current State Analysis:** Monitor shard utilization, hotspot detection, and throughput patterns across different time periods
- **Optimization Steps:** Implement auto-scaling policies, improve partition key distribution, optimize shard count based on traffic patterns
- **Expected Improvement:** 40% improvement in throughput, reduced hot sharding, optimized cost through dynamic scaling

#### Optimization Strategy 2: Data Processing Efficiency
- **Monitoring Approach:** Track processing latency, batch sizes, error rates, and resource utilization in consumer applications
- **Tuning Parameters:** Optimize batch sizes, implement parallel processing, improve data serialization and compression
- **Validation Methods:** Load testing with realistic data patterns, latency measurement across different throughput levels

## Advanced Implementation Patterns

### Multi-Region Data Streaming
```bash
# Deploy Kinesis across multiple regions with cross-region replication
regions=("us-east-1" "us-west-2" "eu-west-1")

for region in "${regions[@]}"; do
  aws kinesis create-stream \
    --region $region \
    --stream-name "global-enterprise-stream-$region" \
    --shard-count 15 \
    --tags Key=Region,Value=$region Key=GlobalReplication,Value=true
  
  # Set up cross-region replication Lambda
  aws lambda create-function \
    --region $region \
    --function-name "kinesis-cross-region-replicator" \
    --runtime python3.9 \
    --role arn:aws:iam::123456789012:role/kinesis-replication-role \
    --handler index.lambda_handler \
    --zip-file fileb://replication-function.zip
done
```

### Real-Time Event Sourcing Architecture
```yaml
# Event sourcing configuration with Kinesis
EventSourcingArchitecture:
  EventStore:
    Primary: us-east-1
    Replicas: [us-west-2, eu-west-1]
  RetentionPolicy:
    EventStream: 365 days
    SnapshotStream: 2555 days  # 7 years
  ProcessingPatterns:
    EventReplay: enabled
    SnapshotRecovery: enabled
    TimeTravel: enabled
  ComplianceSettings:
    Immutability: enforced
    AuditTrailing: comprehensive
    Encryption: customer_managed_keys
```

## Integration Patterns

### Lambda Event Processing
```python
class KinesisLambdaIntegration:
    def __init__(self, function_arn: str):
        self.lambda_client = boto3.client('lambda')
        self.kinesis_client = boto3.client('kinesis')
        self.function_arn = function_arn
        
    def setup_stream_processing(self, stream_arn: str) -> Dict[str, Any]:
        """Setup Lambda to process Kinesis stream events"""
        try:
            response = self.lambda_client.create_event_source_mapping(
                EventSourceArn=stream_arn,
                FunctionName=self.function_arn,
                StartingPosition='LATEST',
                BatchSize=100,
                MaximumBatchingWindowInSeconds=5,
                ParallelizationFactor=10,
                MaximumRecordAgeInSeconds=60,
                BisectBatchOnFunctionError=True,
                MaximumRetryAttempts=3,
                TumblingWindowInSeconds=10
            )
            
            return {
                'event_source_mapping_uuid': response['UUID'],
                'function_arn': response['FunctionArn'],
                'event_source_arn': response['EventSourceArn'],
                'batch_size': response['BatchSize'],
                'status': 'created'
            }
            
        except Exception as e:
            print(f"Lambda integration setup failed: {e}")
            raise
```

### API Gateway Integration
```bash
# Create API Gateway for Kinesis proxy integration
aws apigateway create-rest-api \
  --name "kinesis-data-ingestion-api" \
  --description "API for streaming data ingestion" \
  --endpoint-configuration types=REGIONAL

# Add Kinesis proxy method
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method POST \
  --authorization-type AWS_IAM \
  --request-parameters method.request.header.X-Amz-Target=true,method.request.header.Content-Type=true

# Configure Kinesis integration
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method POST \
  --type AWS \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:us-east-1:kinesis:action/PutRecord" \
  --credentials "arn:aws:iam::123456789012:role/apigateway-kinesis-role"
```

## Best Practices Summary

### Development & Deployment
1. **Stream Design:** Plan shard count based on peak throughput requirements with 20% headroom for traffic spikes
2. **Partition Strategy:** Use well-distributed partition keys to avoid hot shards and ensure even data distribution
3. **Error Handling:** Implement comprehensive error handling with dead letter queues and retry mechanisms
4. **Data Schema:** Maintain backward-compatible data schemas and implement schema evolution strategies

### Operations & Maintenance
1. **Monitoring Excellence:** Implement comprehensive monitoring of throughput, latency, error rates, and consumer lag
2. **Capacity Planning:** Regular analysis of usage patterns with predictive scaling and cost optimization
3. **Data Retention:** Set appropriate retention periods based on business requirements and compliance needs
4. **Disaster Recovery:** Multi-region deployment with automated failover and data replication

### Security & Governance
1. **Encryption Strategy:** End-to-end encryption with customer-managed KMS keys and secure key rotation
2. **Access Control:** Least-privilege IAM policies with resource-based permissions and audit logging
3. **Data Privacy:** Implement data masking, tokenization, and consent management for sensitive data streams
4. **Compliance Management:** Automated compliance reporting and data retention policies for regulatory requirements

---

## Additional Resources

### AWS Documentation
- [Amazon Kinesis Developer Guide](https://docs.aws.amazon.com/kinesis/latest/dev/)
- [Kinesis Data Streams API Reference](https://docs.aws.amazon.com/kinesis/latest/APIReference/)
- [Kinesis Data Firehose User Guide](https://docs.aws.amazon.com/firehose/latest/dev/)

### Community Resources
- [AWS Kinesis GitHub Samples](https://github.com/aws-samples?q=kinesis)
- [Kinesis Analytics Workshop](https://kinesis-analytics.workshop.aws/)
- [AWS Big Data Blog - Kinesis Posts](https://aws.amazon.com/blogs/big-data/?tag=amazon-kinesis)

### Tools & Utilities
- [AWS CLI Kinesis Commands](https://docs.aws.amazon.com/cli/latest/reference/kinesis/)
- [Kinesis Client Library (KCL)](https://docs.aws.amazon.com/streams/latest/dev/shared-throughput-kcl-consumers.html)
- [Terraform AWS Kinesis Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kinesis_stream)