# AWS Athena - Enterprise Serverless Analytics Platform

Interactive query service for analyzing data in S3 using standard SQL, built on Presto, enhanced with enterprise automation, cost optimization, and advanced analytics capabilities.

## Core Features & Types

- **Serverless Queries:** Pay per query execution
- **Federated Queries:** Query across multiple data sources
- **Standard SQL support with ANSI SQL compliance**
- **Integration with AWS Glue Data Catalog**
- **Support for various data formats** (Parquet, ORC, JSON, CSV, Avro)
- **Columnar storage optimization** for performance
- **JDBC/ODBC connectivity** for BI tools
- **Workgroups** for query organization and cost control

## Enterprise Analytics Automation Framework

```python
import json
import boto3
import pandas as pd
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from botocore.exceptions import ClientError
import time

class QueryStatus(Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING" 
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class DataFormat(Enum):
    PARQUET = "PARQUET"
    ORC = "ORC"
    JSON = "JSON"
    CSV = "CSV"
    AVRO = "AVRO"

class CompressionType(Enum):
    GZIP = "GZIP"
    SNAPPY = "SNAPPY"
    LZO = "LZO"
    UNCOMPRESSED = "UNCOMPRESSED"

@dataclass
class QueryExecution:
    query_id: str
    query: str
    status: QueryStatus
    execution_time_ms: Optional[int] = None
    data_scanned_bytes: Optional[int] = None
    result_location: Optional[str] = None
    cost_estimate: Optional[float] = None
    workgroup: Optional[str] = None

@dataclass
class TablePartition:
    partition_key: str
    partition_value: str
    location: str
    size_bytes: int = 0

@dataclass
class AnalyticsTable:
    database: str
    table_name: str
    location: str
    data_format: DataFormat
    compression: CompressionType
    columns: List[Dict[str, str]] = field(default_factory=list)
    partitions: List[TablePartition] = field(default_factory=list)
    lifecycle_policy: Optional[Dict[str, Any]] = None

class EnterpriseAthenaManager:
    """
    Enterprise AWS Athena manager with automated query optimization,
    cost control, and advanced analytics capabilities.
    """
    
    def __init__(self, region: str = 'us-east-1', workgroup: str = 'primary'):
        self.athena = boto3.client('athena', region_name=region)
        self.glue = boto3.client('glue', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.workgroup = workgroup
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger('AthenaManager')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def execute_optimized_query(self, 
                               query: str, 
                               result_location: str,
                               enable_cost_optimization: bool = True) -> QueryExecution:
        """Execute query with automatic optimization and cost control"""
        try:
            # Optimize query if enabled
            if enable_cost_optimization:
                query = self._optimize_query(query)
            
            # Execute query
            response = self.athena.start_query_execution(
                QueryString=query,
                WorkGroup=self.workgroup,
                ResultConfiguration={
                    'OutputLocation': result_location,
                    'EncryptionConfiguration': {
                        'EncryptionOption': 'SSE_S3'
                    }
                }
            )
            
            query_id = response['QueryExecutionId']
            
            # Monitor execution
            execution = self._monitor_query_execution(query_id)
            
            # Calculate cost estimate
            if execution.data_scanned_bytes:
                execution.cost_estimate = self._calculate_query_cost(execution.data_scanned_bytes)
            
            self.logger.info(f"Query executed: {query_id}, Cost: ${execution.cost_estimate:.4f}")
            return execution
            
        except ClientError as e:
            self.logger.error(f"Error executing query: {str(e)}")
            raise

    def _optimize_query(self, query: str) -> str:
        """Apply automatic query optimizations"""
        optimizations = []
        
        # Add LIMIT if not present and query doesn't have aggregations
        if 'LIMIT' not in query.upper() and not any(agg in query.upper() 
                                                   for agg in ['COUNT', 'SUM', 'AVG', 'GROUP BY']):
            query += ' LIMIT 10000'
            optimizations.append('Added LIMIT clause')
        
        # Suggest partition pruning
        if 'WHERE' in query.upper() and 'year=' not in query.lower():
            self.logger.warning("Consider adding partition filters (e.g., year=2024) for better performance")
        
        # Log optimizations applied
        if optimizations:
            self.logger.info(f"Applied optimizations: {', '.join(optimizations)}")
        
        return query

    def _monitor_query_execution(self, query_id: str) -> QueryExecution:
        """Monitor query execution until completion"""
        while True:
            response = self.athena.get_query_execution(QueryExecutionId=query_id)
            execution_details = response['QueryExecution']
            
            status = QueryStatus(execution_details['Status']['State'])
            
            if status in [QueryStatus.SUCCEEDED, QueryStatus.FAILED, QueryStatus.CANCELLED]:
                execution = QueryExecution(
                    query_id=query_id,
                    query=execution_details['Query'],
                    status=status,
                    execution_time_ms=execution_details['Statistics'].get('EngineExecutionTimeInMillis'),
                    data_scanned_bytes=execution_details['Statistics'].get('DataScannedInBytes'),
                    result_location=execution_details.get('ResultConfiguration', {}).get('OutputLocation'),
                    workgroup=execution_details.get('WorkGroup')
                )
                return execution
            
            time.sleep(2)  # Wait before checking again

    def _calculate_query_cost(self, data_scanned_bytes: int) -> float:
        """Calculate query cost based on data scanned"""
        # Athena pricing: $5.00 per TB of data scanned
        tb_scanned = data_scanned_bytes / (1024 ** 4)  # Convert to TB
        return tb_scanned * 5.00

    def create_optimized_table(self, table_config: AnalyticsTable) -> Dict[str, Any]:
        """Create optimized table with best practices"""
        try:
            # Create database if not exists
            try:
                self.glue.create_database(DatabaseInput={'Name': table_config.database})
            except ClientError as e:
                if 'AlreadyExistsException' not in str(e):
                    raise
            
            # Prepare table input
            table_input = {
                'Name': table_config.table_name,
                'StorageDescriptor': {
                    'Columns': table_config.columns,
                    'Location': table_config.location,
                    'InputFormat': self._get_input_format(table_config.data_format),
                    'OutputFormat': self._get_output_format(table_config.data_format),
                    'SerdeInfo': {
                        'SerializationLibrary': self._get_serde_library(table_config.data_format)
                    },
                    'Compressed': table_config.compression != CompressionType.UNCOMPRESSED,
                    'Parameters': {
                        'compression.type': table_config.compression.value.lower()
                    }
                },
                'PartitionKeys': [
                    {'Name': 'year', 'Type': 'string'},
                    {'Name': 'month', 'Type': 'string'},
                    {'Name': 'day', 'Type': 'string'}
                ] if table_config.partitions else [],
                'TableType': 'EXTERNAL_TABLE',
                'Parameters': {
                    'classification': table_config.data_format.value.lower(),
                    'has_encrypted_data': 'false'
                }
            }
            
            # Create table
            self.glue.create_table(
                DatabaseName=table_config.database,
                TableInput=table_input
            )
            
            # Add partitions if provided
            if table_config.partitions:
                self._add_table_partitions(table_config)
            
            self.logger.info(f"Created optimized table: {table_config.database}.{table_config.table_name}")
            
            return {
                'database': table_config.database,
                'table': table_config.table_name,
                'location': table_config.location,
                'status': 'created'
            }
            
        except ClientError as e:
            self.logger.error(f"Error creating table: {str(e)}")
            raise

    def _get_input_format(self, data_format: DataFormat) -> str:
        """Get input format for table creation"""
        formats = {
            DataFormat.PARQUET: 'org.apache.hadoop.mapred.TextInputFormat',
            DataFormat.ORC: 'org.apache.hadoop.mapred.TextInputFormat',
            DataFormat.JSON: 'org.apache.hadoop.mapred.TextInputFormat',
            DataFormat.CSV: 'org.apache.hadoop.mapred.TextInputFormat',
            DataFormat.AVRO: 'org.apache.hadoop.mapred.TextInputFormat'
        }
        return formats.get(data_format, 'org.apache.hadoop.mapred.TextInputFormat')

    def _get_output_format(self, data_format: DataFormat) -> str:
        """Get output format for table creation"""
        formats = {
            DataFormat.PARQUET: 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat',
            DataFormat.ORC: 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat',
            DataFormat.JSON: 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat',
            DataFormat.CSV: 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat',
            DataFormat.AVRO: 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
        }
        return formats.get(data_format, 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat')

    def _get_serde_library(self, data_format: DataFormat) -> str:
        """Get SerDe library for table creation"""
        serdes = {
            DataFormat.PARQUET: 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe',
            DataFormat.ORC: 'org.apache.hadoop.hive.ql.io.orc.OrcSerde',
            DataFormat.JSON: 'org.openx.data.jsonserde.JsonSerDe',
            DataFormat.CSV: 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe',
            DataFormat.AVRO: 'org.apache.hadoop.hive.serde2.avro.AvroSerDe'
        }
        return serdes.get(data_format, 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe')

    def _add_table_partitions(self, table_config: AnalyticsTable) -> None:
        """Add partitions to table"""
        partition_inputs = []
        
        for partition in table_config.partitions:
            partition_input = {
                'Values': [partition.partition_value],
                'StorageDescriptor': {
                    'Columns': table_config.columns,
                    'Location': partition.location,
                    'InputFormat': self._get_input_format(table_config.data_format),
                    'OutputFormat': self._get_output_format(table_config.data_format),
                    'SerdeInfo': {
                        'SerializationLibrary': self._get_serde_library(table_config.data_format)
                    }
                }
            }
            partition_inputs.append(partition_input)
        
        # Batch create partitions
        for i in range(0, len(partition_inputs), 100):  # Glue limit: 100 partitions per batch
            batch = partition_inputs[i:i+100]
            self.glue.batch_create_partition(
                DatabaseName=table_config.database,
                TableName=table_config.table_name,
                PartitionInputList=batch
            )

    def run_analytical_workload(self, queries: List[str], output_location: str) -> Dict[str, Any]:
        """Run analytical workload with performance monitoring"""
        try:
            workload_start = datetime.utcnow()
            executions = []
            total_cost = 0.0
            total_data_scanned = 0
            
            for i, query in enumerate(queries):
                self.logger.info(f"Executing query {i+1}/{len(queries)}")
                
                execution = self.execute_optimized_query(
                    query=query,
                    result_location=f"{output_location}/query_{i+1}/"
                )
                
                executions.append(execution)
                if execution.cost_estimate:
                    total_cost += execution.cost_estimate
                if execution.data_scanned_bytes:
                    total_data_scanned += execution.data_scanned_bytes
            
            workload_duration = (datetime.utcnow() - workload_start).total_seconds()
            
            results = {
                'workload_id': f"workload_{int(workload_start.timestamp())}",
                'queries_executed': len(queries),
                'successful_queries': len([e for e in executions if e.status == QueryStatus.SUCCEEDED]),
                'failed_queries': len([e for e in executions if e.status == QueryStatus.FAILED]),
                'total_duration_seconds': workload_duration,
                'total_cost': total_cost,
                'total_data_scanned_gb': total_data_scanned / (1024**3),
                'average_cost_per_query': total_cost / len(queries) if queries else 0,
                'executions': [self._serialize_execution(e) for e in executions]
            }
            
            # Send metrics to CloudWatch
            self._publish_workload_metrics(results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error running analytical workload: {str(e)}")
            raise

    def _serialize_execution(self, execution: QueryExecution) -> Dict[str, Any]:
        """Serialize query execution for JSON output"""
        return {
            'query_id': execution.query_id,
            'status': execution.status.value,
            'execution_time_ms': execution.execution_time_ms,
            'data_scanned_bytes': execution.data_scanned_bytes,
            'cost_estimate': execution.cost_estimate,
            'workgroup': execution.workgroup
        }

    def _publish_workload_metrics(self, results: Dict[str, Any]) -> None:
        """Publish workload metrics to CloudWatch"""
        try:
            metric_data = [
                {
                    'MetricName': 'QueriesExecuted',
                    'Value': results['queries_executed'],
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'WorkloadCost',
                    'Value': results['total_cost'],
                    'Unit': 'None'
                },
                {
                    'MetricName': 'DataScannedGB',
                    'Value': results['total_data_scanned_gb'],
                    'Unit': 'None'
                },
                {
                    'MetricName': 'WorkloadDuration',
                    'Value': results['total_duration_seconds'],
                    'Unit': 'Seconds'
                }
            ]
            
            self.cloudwatch.put_metric_data(
                Namespace='AWS/Athena/Analytics',
                MetricData=metric_data
            )
            
        except Exception as e:
            self.logger.warning(f"Error publishing metrics: {str(e)}")

# Practical Real-World Examples

def create_web_analytics_pipeline():
    """Create web analytics data pipeline with Athena"""
    
    manager = EnterpriseAthenaManager(workgroup='analytics-team')
    
    # Create web logs table
    web_logs_table = AnalyticsTable(
        database='web_analytics',
        table_name='access_logs',
        location='s3://company-logs/web-access-logs/',
        data_format=DataFormat.PARQUET,
        compression=CompressionType.SNAPPY,
        columns=[
            {'Name': 'timestamp', 'Type': 'timestamp'},
            {'Name': 'ip_address', 'Type': 'string'},
            {'Name': 'user_agent', 'Type': 'string'},
            {'Name': 'request_uri', 'Type': 'string'},
            {'Name': 'status_code', 'Type': 'int'},
            {'Name': 'response_size', 'Type': 'bigint'},
            {'Name': 'response_time', 'Type': 'double'},
            {'Name': 'referer', 'Type': 'string'}
        ]
    )
    
    table_result = manager.create_optimized_table(web_logs_table)
    print(f"Created table: {table_result}")
    
    # Run analytics queries
    analytics_queries = [
        """
        SELECT 
            DATE_TRUNC('hour', timestamp) as hour,
            COUNT(*) as requests,
            COUNT(DISTINCT ip_address) as unique_visitors,
            AVG(response_time) as avg_response_time
        FROM web_analytics.access_logs 
        WHERE year = '2024' AND month = '01'
        GROUP BY DATE_TRUNC('hour', timestamp)
        ORDER BY hour
        """,
        """
        SELECT 
            request_uri,
            COUNT(*) as hits,
            COUNT(DISTINCT ip_address) as unique_visitors
        FROM web_analytics.access_logs 
        WHERE year = '2024' AND month = '01'
            AND status_code = 200
        GROUP BY request_uri
        ORDER BY hits DESC
        LIMIT 20
        """,
        """
        SELECT 
            status_code,
            COUNT(*) as error_count,
            COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as error_percentage
        FROM web_analytics.access_logs 
        WHERE year = '2024' AND month = '01'
            AND status_code >= 400
        GROUP BY status_code
        ORDER BY error_count DESC
        """
    ]
    
    workload_results = manager.run_analytical_workload(
        queries=analytics_queries,
        output_location='s3://company-analytics/web-reports/'
    )
    
    print(f"Analytics workload completed:")
    print(f"- Queries executed: {workload_results['queries_executed']}")
    print(f"- Total cost: ${workload_results['total_cost']:.4f}")
    print(f"- Data scanned: {workload_results['total_data_scanned_gb']:.2f} GB")
    
    return workload_results

def create_sales_analytics_dashboard():
    """Create sales analytics dashboard queries"""
    
    manager = EnterpriseAthenaManager(workgroup='sales-analytics')
    
    # Sales analytics queries
    sales_queries = [
        """
        -- Daily Sales Performance
        SELECT 
            DATE(order_date) as date,
            COUNT(*) as orders,
            SUM(total_amount) as revenue,
            AVG(total_amount) as avg_order_value,
            COUNT(DISTINCT customer_id) as unique_customers
        FROM sales.orders 
        WHERE year = '2024' AND month = '01'
        GROUP BY DATE(order_date)
        ORDER BY date
        """,
        """
        -- Top Products by Revenue
        SELECT 
            p.product_name,
            p.category,
            SUM(oi.quantity) as units_sold,
            SUM(oi.quantity * oi.unit_price) as revenue
        FROM sales.order_items oi
        JOIN sales.products p ON oi.product_id = p.product_id
        WHERE oi.year = '2024' AND oi.month = '01'
        GROUP BY p.product_name, p.category
        ORDER BY revenue DESC
        LIMIT 50
        """,
        """
        -- Customer Segmentation Analysis
        SELECT 
            CASE 
                WHEN total_spent >= 1000 THEN 'VIP'
                WHEN total_spent >= 500 THEN 'Premium'
                WHEN total_spent >= 100 THEN 'Regular'
                ELSE 'New'
            END as customer_segment,
            COUNT(*) as customer_count,
            AVG(total_spent) as avg_spent,
            SUM(total_spent) as segment_revenue
        FROM (
            SELECT 
                customer_id,
                SUM(total_amount) as total_spent
            FROM sales.orders 
            WHERE year = '2024'
            GROUP BY customer_id
        ) customer_totals
        GROUP BY 
            CASE 
                WHEN total_spent >= 1000 THEN 'VIP'
                WHEN total_spent >= 500 THEN 'Premium'
                WHEN total_spent >= 100 THEN 'Regular'
                ELSE 'New'
            END
        ORDER BY segment_revenue DESC
        """
    ]
    
    return manager.run_analytical_workload(
        queries=sales_queries,
        output_location='s3://company-analytics/sales-dashboard/'
    )

def create_iot_sensor_analysis():
    """Create IoT sensor data analysis pipeline"""
    
    manager = EnterpriseAthenaManager(workgroup='iot-analytics')
    
    # Create IoT sensor data table
    sensor_table = AnalyticsTable(
        database='iot_data',
        table_name='sensor_readings',
        location='s3://company-iot/sensor-data/',
        data_format=DataFormat.PARQUET,
        compression=CompressionType.SNAPPY,
        columns=[
            {'Name': 'device_id', 'Type': 'string'},
            {'Name': 'timestamp', 'Type': 'timestamp'},
            {'Name': 'temperature', 'Type': 'double'},
            {'Name': 'humidity', 'Type': 'double'},
            {'Name': 'pressure', 'Type': 'double'},
            {'Name': 'battery_level', 'Type': 'double'},
            {'Name': 'location_lat', 'Type': 'double'},
            {'Name': 'location_lon', 'Type': 'double'}
        ]
    )
    
    table_result = manager.create_optimized_table(sensor_table)
    
    # IoT analytics queries
    iot_queries = [
        """
        -- Device Health Monitoring
        SELECT 
            device_id,
            COUNT(*) as reading_count,
            AVG(battery_level) as avg_battery,
            MIN(battery_level) as min_battery,
            MAX(timestamp) as last_reading
        FROM iot_data.sensor_readings 
        WHERE year = '2024' AND month = '01'
        GROUP BY device_id
        HAVING AVG(battery_level) < 20 OR MAX(timestamp) < current_timestamp - INTERVAL '1' DAY
        ORDER BY avg_battery ASC
        """,
        """
        -- Environmental Monitoring Alerts
        SELECT 
            DATE_TRUNC('hour', timestamp) as hour,
            AVG(temperature) as avg_temp,
            AVG(humidity) as avg_humidity,
            COUNT(*) as reading_count,
            COUNT(CASE WHEN temperature > 30 THEN 1 END) as high_temp_alerts
        FROM iot_data.sensor_readings 
        WHERE year = '2024' AND month = '01'
        GROUP BY DATE_TRUNC('hour', timestamp)
        HAVING AVG(temperature) > 25 OR AVG(humidity) > 80
        ORDER BY hour
        """
    ]
    
    return manager.run_analytical_workload(
        queries=iot_queries,
        output_location='s3://company-analytics/iot-reports/'
    )
```

## DevOps Integration Patterns

### Infrastructure as Code (Terraform)

```hcl
# athena_infrastructure.tf
resource "aws_athena_workgroup" "analytics_workgroup" {
  name = "enterprise-analytics"
  
  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics        = true
    bytes_scanned_cutoff_per_query    = 1000000000  # 1GB limit
    
    result_configuration {
      output_location = "s3://${aws_s3_bucket.athena_results.bucket}/results/"
      
      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }
  }
  
  tags = {
    Environment = var.environment
    Team        = "Analytics"
  }
}

resource "aws_s3_bucket" "athena_results" {
  bucket = "company-athena-results-${random_id.bucket_suffix.hex}"
}

resource "aws_athena_named_query" "top_products" {
  name      = "TopProductsByRevenue"
  workgroup = aws_athena_workgroup.analytics_workgroup.name
  database  = "sales"
  
  query = <<-EOT
    SELECT 
      product_name,
      SUM(revenue) as total_revenue
    FROM sales.product_sales 
    WHERE year = '${formatdate("YYYY", timestamp())}'
    GROUP BY product_name
    ORDER BY total_revenue DESC
    LIMIT 10
  EOT
}
```

### CI/CD Pipeline Integration

```yaml
# .github/workflows/athena-analytics.yml
name: Athena Analytics Pipeline

on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM
  workflow_dispatch:

jobs:
  run-analytics:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        role-to-assume: ${{ secrets.AWS_ATHENA_ROLE }}
        aws-region: us-east-1
    
    - name: Run Daily Analytics
      run: |
        python scripts/daily_analytics.py \
          --workgroup analytics-team \
          --output-location s3://company-analytics/daily-reports/ \
          --cost-limit 50.00
    
    - name: Generate Reports
      run: |
        python scripts/generate_dashboard.py \
          --input-location s3://company-analytics/daily-reports/ \
          --output-format html
```

## Practical Use Cases

### 1. Web Analytics Platform
- **Real-time log analysis** for website performance monitoring
- **User behavior tracking** and conversion funnel analysis
- **A/B testing results** and statistical analysis
- **Cost-effective** large-scale log processing

### 2. Business Intelligence Dashboard
- **Sales performance analytics** with real-time insights
- **Customer segmentation** and lifetime value analysis
- **Financial reporting** and revenue forecasting
- **Operational KPI** monitoring and alerting

### 3. IoT Data Analytics
- **Sensor data processing** at scale
- **Predictive maintenance** using historical patterns
- **Environmental monitoring** and alert systems
- **Device performance** optimization

### 4. Financial Data Analysis
- **Risk analytics** and compliance reporting
- **Fraud detection** using transaction patterns
- **Market research** and competitive analysis
- **Regulatory reporting** automation

### 5. Marketing Analytics
- **Campaign performance** measurement
- **Attribution modeling** across channels
- **Customer journey** analysis
- **ROI optimization** for marketing spend

## Cost Optimization Strategies

- **Partition pruning** to reduce data scanned
- **Columnar formats** (Parquet/ORC) for better compression
- **Data lifecycle management** with S3 storage classes
- **Query result caching** to avoid redundant scans
- **Workgroup limits** to control costs
- **Compression algorithms** to reduce storage costs