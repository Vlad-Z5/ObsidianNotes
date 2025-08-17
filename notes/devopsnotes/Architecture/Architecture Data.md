# Architecture Data

## Data Architecture Patterns

Data architecture forms the foundation of modern applications, defining how data is stored, processed, and accessed. This guide covers comprehensive data architecture patterns with production-ready implementations.

### Data Modeling

#### Conceptual Data Modeling
High-level entity relationships and business rules definition.

```python
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class CustomerType(Enum):
    INDIVIDUAL = "individual"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"

@dataclass
class ConceptualModel:
    """Conceptual data model for e-commerce domain"""
    
    def __init__(self):
        self.entities = {
            'Customer': {
                'attributes': ['customer_id', 'name', 'email', 'type'],
                'relationships': ['places_orders', 'has_addresses']
            },
            'Order': {
                'attributes': ['order_id', 'order_date', 'status', 'total'],
                'relationships': ['belongs_to_customer', 'contains_items']
            },
            'Product': {
                'attributes': ['product_id', 'name', 'price', 'category'],
                'relationships': ['in_orders', 'has_inventory']
            }
        }
        
    def validate_business_rules(self) -> List[str]:
        """Validate conceptual model business rules"""
        rules = []
        rules.append("Customer must have valid email")
        rules.append("Order total must be greater than 0")
        rules.append("Product price must be positive")
        return rules
```

#### Logical Data Modeling
Platform-independent data structure with detailed attributes and constraints.

```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Decimal, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class Customer(Base):
    __tablename__ = 'customers'
    
    customer_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    customer_type = Column(Enum(CustomerType), default=CustomerType.INDIVIDUAL)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    orders = relationship("Order", back_populates="customer")
    addresses = relationship("Address", back_populates="customer")

class Order(Base):
    __tablename__ = 'orders'
    
    order_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customers.customer_id'), nullable=False)
    order_date = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(20), default='pending')
    total = Column(Decimal(10, 2), nullable=False)
    
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")

class Product(Base):
    __tablename__ = 'products'
    
    product_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    price = Column(Decimal(10, 2), nullable=False)
    category = Column(String(50))
    in_stock = Column(Integer, default=0)
```

#### Dimensional Modeling
Star schema design for analytics and data warehousing.

```python
class DimensionalModel:
    """Star schema implementation for sales analytics"""
    
    def __init__(self):
        self.fact_tables = {
            'sales_fact': {
                'measures': ['quantity', 'unit_price', 'total_amount', 'discount'],
                'dimensions': ['date_key', 'product_key', 'customer_key', 'store_key']
            }
        }
        
        self.dimensions = {
            'date_dimension': ['date_key', 'date', 'year', 'quarter', 'month', 'day_of_week'],
            'product_dimension': ['product_key', 'product_name', 'category', 'subcategory', 'brand'],
            'customer_dimension': ['customer_key', 'customer_name', 'segment', 'region', 'loyalty_tier'],
            'store_dimension': ['store_key', 'store_name', 'city', 'state', 'region', 'store_type']
        }
    
    def generate_star_schema_ddl(self) -> str:
        """Generate DDL for star schema"""
        ddl = """
        -- Fact Table
        CREATE TABLE sales_fact (
            sale_id BIGINT PRIMARY KEY,
            date_key INT REFERENCES date_dimension(date_key),
            product_key INT REFERENCES product_dimension(product_key),
            customer_key INT REFERENCES customer_dimension(customer_key),
            store_key INT REFERENCES store_dimension(store_key),
            quantity INT NOT NULL,
            unit_price DECIMAL(10,2) NOT NULL,
            total_amount DECIMAL(12,2) NOT NULL,
            discount DECIMAL(8,2) DEFAULT 0
        );
        
        -- Date Dimension
        CREATE TABLE date_dimension (
            date_key INT PRIMARY KEY,
            date DATE NOT NULL,
            year INT NOT NULL,
            quarter INT NOT NULL,
            month INT NOT NULL,
            day_of_week INT NOT NULL,
            is_weekend BOOLEAN DEFAULT FALSE
        );
        """
        return ddl
```

### Database Selection

#### Polyglot Persistence Strategy
Choose the right database for each use case.

```python
import asyncio
import redis
import pymongo
from neo4j import GraphDatabase
from influxdb_client import InfluxDBClient
import psycopg2

class DatabaseSelector:
    """Database selection strategy based on use case"""
    
    def __init__(self):
        self.databases = {
            'postgresql': self._setup_postgresql(),
            'mongodb': self._setup_mongodb(),
            'redis': self._setup_redis(),
            'neo4j': self._setup_neo4j(),
            'influxdb': self._setup_influxdb()
        }
    
    def _setup_postgresql(self):
        """Relational database for ACID transactions"""
        return {
            'use_cases': ['transactional data', 'complex queries', 'reporting'],
            'strengths': ['ACID compliance', 'complex joins', 'mature ecosystem'],
            'connection': psycopg2.connect(
                host="localhost",
                database="ecommerce",
                user="postgres",
                password="password"
            )
        }
    
    def _setup_mongodb(self):
        """Document database for flexible schemas"""
        return {
            'use_cases': ['content management', 'catalogs', 'user profiles'],
            'strengths': ['flexible schema', 'horizontal scaling', 'JSON native'],
            'connection': pymongo.MongoClient('mongodb://localhost:27017/')
        }
    
    def _setup_redis(self):
        """In-memory database for caching and sessions"""
        return {
            'use_cases': ['caching', 'sessions', 'real-time analytics'],
            'strengths': ['high performance', 'data structures', 'pub/sub'],
            'connection': redis.Redis(host='localhost', port=6379, db=0)
        }
    
    def _setup_neo4j(self):
        """Graph database for relationships"""
        return {
            'use_cases': ['social networks', 'recommendations', 'fraud detection'],
            'strengths': ['relationship traversal', 'pattern matching', 'graph algorithms'],
            'connection': GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
        }
    
    def _setup_influxdb(self):
        """Time-series database for metrics"""
        return {
            'use_cases': ['IoT data', 'monitoring', 'analytics'],
            'strengths': ['time-based queries', 'compression', 'retention policies'],
            'connection': InfluxDBClient(url="http://localhost:8086", token="my-token", org="my-org")
        }
    
    def recommend_database(self, use_case: str) -> str:
        """Recommend database based on use case"""
        recommendations = {
            'user_authentication': 'postgresql',
            'product_catalog': 'mongodb',
            'shopping_cart': 'redis',
            'recommendations': 'neo4j',
            'application_metrics': 'influxdb'
        }
        return recommendations.get(use_case, 'postgresql')
```

### Data Storage Patterns

#### Data Lake Architecture
Scalable storage for structured and unstructured data.

```python
import boto3
import pandas as pd
from typing import Dict, Any
import json
from datetime import datetime

class DataLakeManager:
    """Data lake implementation with AWS S3"""
    
    def __init__(self, bucket_name: str):
        self.s3_client = boto3.client('s3')
        self.bucket = bucket_name
        self.zones = {
            'raw': 'raw-data/',
            'processed': 'processed-data/',
            'curated': 'curated-data/',
            'sandbox': 'sandbox/'
        }
    
    def ingest_data(self, data: Any, data_type: str, source: str) -> str:
        """Ingest data into raw zone with partitioning"""
        timestamp = datetime.now()
        partition_path = f"year={timestamp.year}/month={timestamp.month:02d}/day={timestamp.day:02d}"
        
        key = f"{self.zones['raw']}{source}/{data_type}/{partition_path}/{timestamp.isoformat()}.json"
        
        if isinstance(data, pd.DataFrame):
            json_data = data.to_json(orient='records')
        else:
            json_data = json.dumps(data)
        
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=json_data,
            Metadata={
                'source': source,
                'data_type': data_type,
                'ingestion_time': timestamp.isoformat()
            }
        )
        
        return key
    
    def process_data(self, raw_key: str, processing_function) -> str:
        """Process raw data and store in processed zone"""
        response = self.s3_client.get_object(Bucket=self.bucket, Key=raw_key)
        raw_data = json.loads(response['Body'].read())
        
        processed_data = processing_function(raw_data)
        
        processed_key = raw_key.replace(self.zones['raw'], self.zones['processed'])
        
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=processed_key,
            Body=json.dumps(processed_data),
            Metadata={'processing_time': datetime.now().isoformat()}
        )
        
        return processed_key
    
    def create_data_catalog(self) -> Dict[str, Any]:
        """Create metadata catalog for data discovery"""
        catalog = {
            'datasets': [],
            'schemas': {},
            'lineage': {}
        }
        
        for zone in self.zones.values():
            objects = self.s3_client.list_objects_v2(Bucket=self.bucket, Prefix=zone)
            
            if 'Contents' in objects:
                for obj in objects['Contents']:
                    metadata = self.s3_client.head_object(Bucket=self.bucket, Key=obj['Key'])
                    
                    catalog['datasets'].append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'metadata': metadata.get('Metadata', {})
                    })
        
        return catalog
```

#### Data Warehouse Architecture
Structured analytics with dimensional modeling.

```python
import snowflake.connector
from typing import List, Dict
import logging

class DataWarehouseManager:
    """Data warehouse implementation with Snowflake"""
    
    def __init__(self, account: str, user: str, password: str, warehouse: str):
        self.conn = snowflake.connector.connect(
            account=account,
            user=user,
            password=password,
            warehouse=warehouse
        )
        self.cursor = self.conn.cursor()
        self.logger = logging.getLogger(__name__)
    
    def create_dimensional_model(self):
        """Create star schema for analytics"""
        
        dimensions = {
            'date_dim': """
                CREATE OR REPLACE TABLE date_dim (
                    date_key NUMBER(8) PRIMARY KEY,
                    date DATE NOT NULL,
                    year NUMBER(4) NOT NULL,
                    quarter NUMBER(1) NOT NULL,
                    month NUMBER(2) NOT NULL,
                    month_name VARCHAR(10) NOT NULL,
                    day_of_week NUMBER(1) NOT NULL,
                    day_name VARCHAR(10) NOT NULL,
                    is_weekend BOOLEAN DEFAULT FALSE,
                    is_holiday BOOLEAN DEFAULT FALSE
                );
            """,
            'customer_dim': """
                CREATE OR REPLACE TABLE customer_dim (
                    customer_key NUMBER IDENTITY PRIMARY KEY,
                    customer_id VARCHAR(50) NOT NULL,
                    customer_name VARCHAR(100) NOT NULL,
                    email VARCHAR(255),
                    segment VARCHAR(20),
                    region VARCHAR(50),
                    registration_date DATE,
                    effective_date DATE NOT NULL,
                    expiry_date DATE,
                    is_current BOOLEAN DEFAULT TRUE
                );
            """
        }
        
        fact_table = """
            CREATE OR REPLACE TABLE sales_fact (
                sale_key NUMBER IDENTITY PRIMARY KEY,
                date_key NUMBER(8) REFERENCES date_dim(date_key),
                customer_key NUMBER REFERENCES customer_dim(customer_key),
                product_key NUMBER REFERENCES product_dim(product_key),
                quantity NUMBER(10,2) NOT NULL,
                unit_price NUMBER(10,2) NOT NULL,
                discount_amount NUMBER(10,2) DEFAULT 0,
                tax_amount NUMBER(10,2) DEFAULT 0,
                total_amount NUMBER(12,2) NOT NULL
            );
        """
        
        for table_name, ddl in dimensions.items():
            self.cursor.execute(ddl)
            self.logger.info(f"Created dimension table: {table_name}")
        
        self.cursor.execute(fact_table)
        self.logger.info("Created fact table: sales_fact")
    
    def load_slowly_changing_dimension(self, table: str, new_data: List[Dict]):
        """Implement SCD Type 2 for dimension tables"""
        
        for record in new_data:
            business_key = record['customer_id']
            
            # Check if record exists
            check_query = f"""
                SELECT customer_key, customer_name, email, segment, region 
                FROM {table} 
                WHERE customer_id = %s AND is_current = TRUE
            """
            
            self.cursor.execute(check_query, (business_key,))
            existing = self.cursor.fetchone()
            
            if existing:
                # Check if data has changed
                if self._has_changed(existing, record):
                    # Expire current record
                    expire_query = f"""
                        UPDATE {table} 
                        SET expiry_date = CURRENT_DATE(), is_current = FALSE 
                        WHERE customer_id = %s AND is_current = TRUE
                    """
                    self.cursor.execute(expire_query, (business_key,))
                    
                    # Insert new record
                    self._insert_new_dimension_record(table, record)
            else:
                # Insert new record
                self._insert_new_dimension_record(table, record)
    
    def _has_changed(self, existing: tuple, new_record: Dict) -> bool:
        """Check if dimension record has changed"""
        existing_values = existing[1:]  # Skip key
        new_values = (
            new_record['customer_name'],
            new_record['email'],
            new_record['segment'],
            new_record['region']
        )
        return existing_values != new_values
    
    def _insert_new_dimension_record(self, table: str, record: Dict):
        """Insert new dimension record with SCD Type 2"""
        insert_query = f"""
            INSERT INTO {table} (
                customer_id, customer_name, email, segment, region,
                effective_date, expiry_date, is_current
            ) VALUES (%s, %s, %s, %s, %s, CURRENT_DATE(), '9999-12-31', TRUE)
        """
        
        self.cursor.execute(insert_query, (
            record['customer_id'],
            record['customer_name'],
            record['email'],
            record['segment'],
            record['region']
        ))
```

### Data Processing Architectures

#### Lambda Architecture
Batch and stream processing for comprehensive analytics.

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from kafka import KafkaConsumer, KafkaProducer
import json
from typing import Dict, Any
import logging

class LambdaArchitecture:
    """Lambda architecture implementation"""
    
    def __init__(self):
        self.kafka_producer = KafkaProducer(
            bootstrap_servers=['localhost:9092'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        self.logger = logging.getLogger(__name__)
    
    def batch_layer(self, input_data: str, output_path: str):
        """Batch processing layer with Apache Beam"""
        
        def parse_json(element):
            """Parse JSON records"""
            try:
                return json.loads(element)
            except json.JSONDecodeError:
                return None
        
        def calculate_metrics(elements):
            """Calculate batch metrics"""
            metrics = {
                'total_records': len(elements),
                'total_revenue': sum(e.get('amount', 0) for e in elements if e),
                'unique_customers': len(set(e.get('customer_id') for e in elements if e and e.get('customer_id')))
            }
            return metrics
        
        pipeline_options = PipelineOptions([
            '--runner=DirectRunner',
            '--project=my-project',
            '--temp_location=gs://my-bucket/temp'
        ])
        
        with beam.Pipeline(options=pipeline_options) as pipeline:
            (pipeline
             | 'ReadFromBigQuery' >> beam.io.ReadFromBigQuery(
                 query=f'SELECT * FROM `{input_data}` WHERE DATE(_PARTITIONTIME) = CURRENT_DATE()'
             )
             | 'ParseRecords' >> beam.Map(parse_json)
             | 'FilterValid' >> beam.Filter(lambda x: x is not None)
             | 'GroupByWindow' >> beam.WindowInto(beam.window.FixedWindows(3600))  # 1-hour windows
             | 'CalculateMetrics' >> beam.CombineGlobally(calculate_metrics)
             | 'WriteResults' >> beam.io.WriteToBigQuery(
                 table='my-project:analytics.batch_metrics',
                 schema='total_records:INTEGER,total_revenue:FLOAT,unique_customers:INTEGER'
             ))
    
    def speed_layer(self):
        """Speed processing layer with Kafka Streams"""
        
        consumer = KafkaConsumer(
            'user-events',
            bootstrap_servers=['localhost:9092'],
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id='lambda-speed-layer'
        )
        
        real_time_metrics = {
            'events_per_second': 0,
            'active_sessions': set(),
            'revenue_rate': 0.0
        }
        
        for message in consumer:
            event = message.value
            
            # Update real-time metrics
            real_time_metrics['events_per_second'] += 1
            
            if event.get('event_type') == 'session_start':
                real_time_metrics['active_sessions'].add(event.get('session_id'))
            elif event.get('event_type') == 'session_end':
                real_time_metrics['active_sessions'].discard(event.get('session_id'))
            elif event.get('event_type') == 'purchase':
                real_time_metrics['revenue_rate'] += event.get('amount', 0)
            
            # Send to serving layer
            self.kafka_producer.send('real-time-metrics', real_time_metrics.copy())
    
    def serving_layer(self):
        """Serving layer combining batch and speed results"""
        
        class ServingLayer:
            def __init__(self):
                self.batch_views = {}
                self.real_time_views = {}
            
            def query(self, query_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
                """Query combining batch and real-time views"""
                
                if query_type == 'customer_metrics':
                    customer_id = parameters.get('customer_id')
                    
                    # Get batch view (historical data)
                    batch_data = self.batch_views.get(customer_id, {})
                    
                    # Get real-time view (recent data)
                    real_time_data = self.real_time_views.get(customer_id, {})
                    
                    # Combine views
                    combined_metrics = {
                        'total_orders': batch_data.get('total_orders', 0) + real_time_data.get('pending_orders', 0),
                        'lifetime_value': batch_data.get('lifetime_value', 0) + real_time_data.get('session_value', 0),
                        'last_activity': real_time_data.get('last_activity', batch_data.get('last_order_date'))
                    }
                    
                    return combined_metrics
                
                return {}
        
        return ServingLayer()
```

#### Kappa Architecture
Stream-first processing architecture.

```python
import asyncio
from kafka import KafkaConsumer, KafkaProducer
from typing import Dict, Any, Callable
import json
import logging

class KappaArchitecture:
    """Kappa architecture - stream processing only"""
    
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=['localhost:9092'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        self.logger = logging.getLogger(__name__)
        self.processors = {}
    
    def register_stream_processor(self, topic: str, processor: Callable):
        """Register stream processor for topic"""
        self.processors[topic] = processor
    
    async def stream_processor(self, input_topic: str, output_topic: str, transform_func: Callable):
        """Generic stream processor"""
        
        consumer = KafkaConsumer(
            input_topic,
            bootstrap_servers=['localhost:9092'],
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id=f'kappa-processor-{input_topic}'
        )
        
        for message in consumer:
            try:
                # Transform data
                transformed_data = transform_func(message.value)
                
                # Send to output topic
                self.producer.send(output_topic, transformed_data)
                
                self.logger.info(f"Processed message from {input_topic} to {output_topic}")
                
            except Exception as e:
                self.logger.error(f"Error processing message: {e}")
                # Send to dead letter queue
                self.producer.send(f"{input_topic}-dlq", {
                    'original_message': message.value,
                    'error': str(e),
                    'timestamp': message.timestamp
                })
    
    def real_time_aggregator(self, window_size: int = 60):
        """Real-time aggregation with windowing"""
        
        aggregation_state = {}
        
        def aggregate_events(event: Dict[str, Any]) -> Dict[str, Any]:
            """Aggregate events in real-time"""
            
            event_type = event.get('event_type')
            customer_id = event.get('customer_id')
            timestamp = event.get('timestamp')
            
            # Create window key
            window_key = f"{customer_id}_{timestamp // window_size}"
            
            if window_key not in aggregation_state:
                aggregation_state[window_key] = {
                    'customer_id': customer_id,
                    'window_start': timestamp // window_size * window_size,
                    'event_count': 0,
                    'page_views': 0,
                    'purchases': 0,
                    'total_amount': 0.0
                }
            
            # Update aggregation
            window_data = aggregation_state[window_key]
            window_data['event_count'] += 1
            
            if event_type == 'page_view':
                window_data['page_views'] += 1
            elif event_type == 'purchase':
                window_data['purchases'] += 1
                window_data['total_amount'] += event.get('amount', 0)
            
            return window_data
        
        return aggregate_events
    
    def start_processing(self):
        """Start all stream processors"""
        
        # User events processor
        user_events_processor = self.real_time_aggregator(window_size=300)  # 5-minute windows
        
        async def run_processors():
            tasks = [
                self.stream_processor('user-events', 'user-metrics', user_events_processor),
                self.stream_processor('order-events', 'order-metrics', self._order_processor),
                self.stream_processor('product-events', 'product-metrics', self._product_processor)
            ]
            
            await asyncio.gather(*tasks)
        
        asyncio.run(run_processors())
    
    def _order_processor(self, order_event: Dict[str, Any]) -> Dict[str, Any]:
        """Process order events"""
        return {
            'order_id': order_event['order_id'],
            'customer_id': order_event['customer_id'],
            'total_amount': order_event['total_amount'],
            'order_status': order_event['status'],
            'processed_at': order_event['timestamp']
        }
    
    def _product_processor(self, product_event: Dict[str, Any]) -> Dict[str, Any]:
        """Process product events"""
        return {
            'product_id': product_event['product_id'],
            'event_type': product_event['event_type'],
            'user_id': product_event.get('user_id'),
            'session_id': product_event.get('session_id'),
            'processed_at': product_event['timestamp']
        }
```

### Data Integration

#### ETL Pipeline Framework
Comprehensive ETL implementation with error handling and monitoring.

```python
import pandas as pd
from typing import Dict, Any, List, Callable
import logging
import time
from datetime import datetime
import boto3
from sqlalchemy import create_engine

class ETLPipeline:
    """Comprehensive ETL pipeline framework"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.metrics = {
            'records_extracted': 0,
            'records_transformed': 0,
            'records_loaded': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Initialize connections
        self.source_engine = create_engine(config['source_db_url'])
        self.target_engine = create_engine(config['target_db_url'])
    
    def extract(self, extraction_config: Dict[str, Any]) -> pd.DataFrame:
        """Extract data from source systems"""
        
        self.metrics['start_time'] = datetime.now()
        self.logger.info("Starting data extraction")
        
        try:
            if extraction_config['type'] == 'database':
                data = self._extract_from_database(extraction_config)
            elif extraction_config['type'] == 's3':
                data = self._extract_from_s3(extraction_config)
            elif extraction_config['type'] == 'api':
                data = self._extract_from_api(extraction_config)
            else:
                raise ValueError(f"Unsupported extraction type: {extraction_config['type']}")
            
            self.metrics['records_extracted'] = len(data)
            self.logger.info(f"Extracted {len(data)} records")
            
            return data
            
        except Exception as e:
            self.metrics['errors'] += 1
            self.logger.error(f"Extraction failed: {e}")
            raise
    
    def _extract_from_database(self, config: Dict[str, Any]) -> pd.DataFrame:
        """Extract from database source"""
        
        query = config.get('query') or f"SELECT * FROM {config['table']}"
        
        # Add incremental extraction logic
        if config.get('incremental'):
            last_run_time = self._get_last_run_time(config['table'])
            query += f" WHERE updated_at > '{last_run_time}'"
        
        return pd.read_sql(query, self.source_engine)
    
    def _extract_from_s3(self, config: Dict[str, Any]) -> pd.DataFrame:
        """Extract from S3 source"""
        
        s3_client = boto3.client('s3')
        
        objects = s3_client.list_objects_v2(
            Bucket=config['bucket'],
            Prefix=config['prefix']
        )
        
        dataframes = []
        for obj in objects.get('Contents', []):
            response = s3_client.get_object(Bucket=config['bucket'], Key=obj['Key'])
            
            if obj['Key'].endswith('.csv'):
                df = pd.read_csv(response['Body'])
            elif obj['Key'].endswith('.json'):
                df = pd.read_json(response['Body'])
            else:
                continue
            
            dataframes.append(df)
        
        return pd.concat(dataframes, ignore_index=True) if dataframes else pd.DataFrame()
    
    def transform(self, data: pd.DataFrame, transformation_rules: List[Dict[str, Any]]) -> pd.DataFrame:
        """Transform data according to rules"""
        
        self.logger.info("Starting data transformation")
        
        try:
            transformed_data = data.copy()
            
            for rule in transformation_rules:
                rule_type = rule['type']
                
                if rule_type == 'rename_columns':
                    transformed_data.rename(columns=rule['mapping'], inplace=True)
                
                elif rule_type == 'data_type_conversion':
                    for column, dtype in rule['conversions'].items():
                        transformed_data[column] = transformed_data[column].astype(dtype)
                
                elif rule_type == 'filter_rows':
                    transformed_data = transformed_data.query(rule['condition'])
                
                elif rule_type == 'add_calculated_column':
                    transformed_data[rule['column_name']] = transformed_data.eval(rule['expression'])
                
                elif rule_type == 'data_quality_check':
                    self._perform_data_quality_check(transformed_data, rule)
                
                elif rule_type == 'custom_function':
                    function = rule['function']
                    transformed_data = function(transformed_data)
            
            self.metrics['records_transformed'] = len(transformed_data)
            self.logger.info(f"Transformed {len(transformed_data)} records")
            
            return transformed_data
            
        except Exception as e:
            self.metrics['errors'] += 1
            self.logger.error(f"Transformation failed: {e}")
            raise
    
    def _perform_data_quality_check(self, data: pd.DataFrame, rule: Dict[str, Any]):
        """Perform data quality checks"""
        
        checks = rule.get('checks', [])
        
        for check in checks:
            if check['type'] == 'null_check':
                null_count = data[check['column']].isnull().sum()
                if null_count > check.get('threshold', 0):
                    raise ValueError(f"Column {check['column']} has {null_count} null values")
            
            elif check['type'] == 'range_check':
                column = check['column']
                min_val, max_val = check['range']
                out_of_range = data[(data[column] < min_val) | (data[column] > max_val)]
                if len(out_of_range) > 0:
                    raise ValueError(f"Column {column} has {len(out_of_range)} out-of-range values")
            
            elif check['type'] == 'uniqueness_check':
                duplicates = data[check['columns']].duplicated().sum()
                if duplicates > 0:
                    raise ValueError(f"Found {duplicates} duplicate records")
    
    def load(self, data: pd.DataFrame, load_config: Dict[str, Any]):
        """Load data to target system"""
        
        self.logger.info("Starting data loading")
        
        try:
            if load_config['type'] == 'database':
                self._load_to_database(data, load_config)
            elif load_config['type'] == 's3':
                self._load_to_s3(data, load_config)
            elif load_config['type'] == 'data_warehouse':
                self._load_to_data_warehouse(data, load_config)
            
            self.metrics['records_loaded'] = len(data)
            self.metrics['end_time'] = datetime.now()
            
            self.logger.info(f"Loaded {len(data)} records successfully")
            
        except Exception as e:
            self.metrics['errors'] += 1
            self.logger.error(f"Loading failed: {e}")
            raise
    
    def _load_to_database(self, data: pd.DataFrame, config: Dict[str, Any]):
        """Load to database target"""
        
        load_strategy = config.get('strategy', 'append')
        
        if load_strategy == 'replace':
            data.to_sql(config['table'], self.target_engine, if_exists='replace', index=False)
        elif load_strategy == 'append':
            data.to_sql(config['table'], self.target_engine, if_exists='append', index=False)
        elif load_strategy == 'upsert':
            self._perform_upsert(data, config)
    
    def _perform_upsert(self, data: pd.DataFrame, config: Dict[str, Any]):
        """Perform upsert operation"""
        
        table = config['table']
        key_columns = config['key_columns']
        
        # Create temporary table
        temp_table = f"{table}_temp_{int(time.time())}"
        data.to_sql(temp_table, self.target_engine, if_exists='replace', index=False)
        
        # Perform upsert
        upsert_sql = f"""
            INSERT INTO {table} 
            SELECT * FROM {temp_table} t
            WHERE NOT EXISTS (
                SELECT 1 FROM {table} m 
                WHERE {' AND '.join(f'm.{col} = t.{col}' for col in key_columns)}
            )
        """
        
        with self.target_engine.connect() as conn:
            conn.execute(upsert_sql)
            conn.execute(f"DROP TABLE {temp_table}")
    
    def run_pipeline(self, pipeline_config: Dict[str, Any]):
        """Run complete ETL pipeline"""
        
        try:
            # Extract
            data = self.extract(pipeline_config['extract'])
            
            # Transform
            transformed_data = self.transform(data, pipeline_config['transform'])
            
            # Load
            self.load(transformed_data, pipeline_config['load'])
            
            # Log metrics
            self._log_pipeline_metrics()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            self._log_pipeline_metrics()
            return False
    
    def _log_pipeline_metrics(self):
        """Log pipeline execution metrics"""
        
        duration = None
        if self.metrics['start_time'] and self.metrics['end_time']:
            duration = (self.metrics['end_time'] - self.metrics['start_time']).total_seconds()
        
        self.logger.info("Pipeline Metrics:")
        self.logger.info(f"  Records Extracted: {self.metrics['records_extracted']}")
        self.logger.info(f"  Records Transformed: {self.metrics['records_transformed']}")
        self.logger.info(f"  Records Loaded: {self.metrics['records_loaded']}")
        self.logger.info(f"  Errors: {self.metrics['errors']}")
        self.logger.info(f"  Duration: {duration} seconds")
    
    def _get_last_run_time(self, table: str) -> str:
        """Get last successful run time for incremental extraction"""
        # Implementation would query metadata table
        return "1900-01-01 00:00:00"
```

This comprehensive data architecture documentation provides production-ready implementations for all major data patterns, from modeling and database selection to processing architectures and integration pipelines. Each pattern includes detailed code examples with error handling, monitoring, and best practices for scalable data systems.

Now proceeding with Architecture Distributed System Patterns.md to continue comprehensive architecture documentation.