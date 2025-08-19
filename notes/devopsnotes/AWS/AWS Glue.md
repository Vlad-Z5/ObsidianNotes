# AWS Glue - Enterprise Data Catalog & ETL Platform

Fully managed extract, transform, and load (ETL) service for data preparation, enhanced with enterprise automation, advanced data catalog management, and comprehensive DevOps integration.

## Core Features & Components

- **Glue Jobs:** Serverless ETL processing with auto-scaling
- **Glue Crawlers:** Automatic schema discovery and cataloging
- **Glue DataBrew:** Visual data preparation and profiling
- **Data Catalog:** Centralized metadata repository
- **Glue Studio:** Visual ETL job creation and management
- **Data Quality:** Built-in data validation and quality checks
- **Schema Registry:** Schema evolution and version management
- **Job scheduling and monitoring** with CloudWatch integration
- **Data lineage tracking** for compliance and governance
- **Machine learning transforms** for data preparation

## Enterprise Data Catalog & ETL Framework

```python
import json
import boto3
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from botocore.exceptions import ClientError
import time
import uuid

class JobType(Enum):
    PYTHON_SHELL = "pythonshell"
    SPARK = "glueetl"
    STREAMING = "gluestreaming"
    RAY = "glueray"

class CrawlerState(Enum):
    READY = "READY"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"

class JobRunState(Enum):
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"

class ConnectionType(Enum):
    JDBC = "JDBC"
    KAFKA = "KAFKA"
    MONGODB = "MONGODB"
    NETWORK = "NETWORK"
    MARKETPLACE = "MARKETPLACE"
    CUSTOM = "CUSTOM"

@dataclass
class GlueTable:
    database_name: str
    table_name: str
    location: str
    input_format: str
    output_format: str
    serde_info: Dict[str, Any]
    columns: List[Dict[str, str]] = field(default_factory=list)
    partition_keys: List[Dict[str, str]] = field(default_factory=list)
    table_type: str = "EXTERNAL_TABLE"
    parameters: Dict[str, str] = field(default_factory=dict)

@dataclass
class CrawlerConfig:
    crawler_name: str
    database_name: str
    targets: Dict[str, Any]
    role: str
    schedule: Optional[str] = None
    table_prefix: Optional[str] = None
    schema_change_policy: Optional[Dict[str, str]] = None
    recrawl_policy: Optional[Dict[str, str]] = None
    lineage_configuration: Optional[Dict[str, str]] = None

@dataclass
class ETLJob:
    job_name: str
    role: str
    command: Dict[str, Any]
    description: Optional[str] = None
    log_uri: Optional[str] = None
    execution_property: Optional[Dict[str, int]] = None
    default_arguments: Dict[str, str] = field(default_factory=dict)
    non_overridable_arguments: Dict[str, str] = field(default_factory=dict)
    connections: List[str] = field(default_factory=list)
    max_retries: int = 0
    timeout: int = 2880  # 48 hours in minutes
    max_capacity: Optional[float] = None
    worker_type: Optional[str] = None
    number_of_workers: Optional[int] = None
    security_configuration: Optional[str] = None
    notification_property: Optional[Dict[str, int]] = None
    glue_version: str = "3.0"

class EnterpriseGlueManager:
    """
    Enterprise AWS Glue manager with automated data catalog management,
    ETL job orchestration, and advanced data governance capabilities.
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.glue = boto3.client('glue', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.sts = boto3.client('sts', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger('GlueManager')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def create_data_catalog_database(self, database_name: str, 
                                   description: str = "",
                                   location_uri: Optional[str] = None) -> Dict[str, Any]:
        """Create data catalog database with enterprise metadata"""
        try:
            database_input = {
                'Name': database_name,
                'Description': description or f"Enterprise data catalog database: {database_name}",
                'Parameters': {
                    'created_by': 'enterprise-glue-manager',
                    'created_at': datetime.utcnow().isoformat(),
                    'environment': 'production'
                }
            }
            
            if location_uri:
                database_input['LocationUri'] = location_uri
            
            self.glue.create_database(DatabaseInput=database_input)
            
            self.logger.info(f"Created data catalog database: {database_name}")
            
            return {
                'database_name': database_name,
                'status': 'created',
                'location_uri': location_uri
            }
            
        except ClientError as e:
            if 'AlreadyExistsException' in str(e):
                self.logger.warning(f"Database {database_name} already exists")
                return {'database_name': database_name, 'status': 'exists'}
            else:
                self.logger.error(f"Error creating database: {str(e)}")
                raise

    def create_advanced_crawler(self, crawler_config: CrawlerConfig) -> Dict[str, Any]:
        """Create advanced crawler with enterprise configuration"""
        try:
            # Set default schema change policy
            if not crawler_config.schema_change_policy:
                crawler_config.schema_change_policy = {
                    'UpdateBehavior': 'UPDATE_IN_DATABASE',
                    'DeleteBehavior': 'LOG'
                }
            
            # Set default recrawl policy
            if not crawler_config.recrawl_policy:
                crawler_config.recrawl_policy = {
                    'RecrawlBehavior': 'CRAWL_EVERYTHING'
                }
            
            crawler_params = {
                'Name': crawler_config.crawler_name,
                'Role': crawler_config.role,
                'DatabaseName': crawler_config.database_name,
                'Targets': crawler_config.targets,
                'SchemaChangePolicy': crawler_config.schema_change_policy,
                'RecrawlPolicy': crawler_config.recrawl_policy,
                'Configuration': json.dumps({
                    'Version': 1.0,
                    'CrawlerOutput': {
                        'Partitions': {'AddOrUpdateBehavior': 'InheritFromTable'},
                        'Tables': {'AddOrUpdateBehavior': 'MergeNewColumns'}
                    },
                    'Grouping': {
                        'TableGroupingPolicy': 'CombineCompatibleSchemas'
                    }
                }),
                'Tags': {
                    'Environment': 'production',
                    'ManagedBy': 'enterprise-glue-manager',
                    'Purpose': 'data-catalog'
                }
            }
            
            if crawler_config.schedule:
                crawler_params['Schedule'] = crawler_config.schedule
                
            if crawler_config.table_prefix:
                crawler_params['TablePrefix'] = crawler_config.table_prefix
                
            if crawler_config.lineage_configuration:
                crawler_params['LineageConfiguration'] = crawler_config.lineage_configuration
            
            self.glue.create_crawler(**crawler_params)
            
            self.logger.info(f"Created advanced crawler: {crawler_config.crawler_name}")
            
            return {
                'crawler_name': crawler_config.crawler_name,
                'database_name': crawler_config.database_name,
                'status': 'created'
            }
            
        except ClientError as e:
            self.logger.error(f"Error creating crawler: {str(e)}")
            raise

    def run_crawler_with_monitoring(self, crawler_name: str, 
                                   timeout_minutes: int = 60) -> Dict[str, Any]:
        """Run crawler with comprehensive monitoring"""
        try:
            # Start crawler
            self.glue.start_crawler(Name=crawler_name)
            
            start_time = datetime.utcnow()
            timeout_time = start_time + timedelta(minutes=timeout_minutes)
            
            self.logger.info(f"Started crawler: {crawler_name}")
            
            # Monitor crawler execution
            while datetime.utcnow() < timeout_time:
                response = self.glue.get_crawler(Name=crawler_name)
                crawler_state = CrawlerState(response['Crawler']['State'])
                
                if crawler_state == CrawlerState.READY:
                    # Get crawler metrics
                    metrics = response['Crawler'].get('LastCrawl', {})
                    
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    
                    results = {
                        'crawler_name': crawler_name,
                        'status': 'completed',
                        'duration_seconds': duration,
                        'tables_created': metrics.get('TablesCreated', 0),
                        'tables_updated': metrics.get('TablesUpdated', 0),
                        'tables_deleted': metrics.get('TablesDeleted', 0),
                        'partitions_created': metrics.get('PartitionsCreated', 0),
                        'partitions_updated': metrics.get('PartitionsUpdated', 0),
                        'partitions_deleted': metrics.get('PartitionsDeleted', 0),
                        'last_updated': datetime.utcnow().isoformat()
                    }
                    
                    # Publish crawler metrics
                    self._publish_crawler_metrics(results)
                    
                    self.logger.info(f"Crawler {crawler_name} completed successfully")
                    return results
                
                elif crawler_state in [CrawlerState.RUNNING]:
                    self.logger.info(f"Crawler {crawler_name} is running...")
                    time.sleep(30)
                    continue
                else:
                    raise Exception(f"Crawler {crawler_name} in unexpected state: {crawler_state.value}")
            
            raise Exception(f"Crawler {crawler_name} timed out after {timeout_minutes} minutes")
            
        except ClientError as e:
            self.logger.error(f"Error running crawler: {str(e)}")
            raise

    def create_enterprise_etl_job(self, job_config: ETLJob) -> Dict[str, Any]:
        """Create enterprise ETL job with advanced configuration"""
        try:
            # Set default arguments for enterprise features
            default_args = {
                '--enable-metrics': '',
                '--enable-continuous-cloudwatch-log': 'true',
                '--enable-spark-ui': 'true',
                '--spark-event-logs-path': 's3://glue-job-logs/spark-events/',
                '--additional-python-modules': 'great-expectations,pandas==1.5.3',
                '--conf': 'spark.sql.adaptive.enabled=true',
                '--conf': 'spark.sql.adaptive.coalescePartitions.enabled=true',
                '--TempDir': 's3://glue-temp-bucket/temp/',
                '--job-bookmark-option': 'job-bookmark-enable',
                '--job-language': 'python'
            }
            
            # Merge with user-provided arguments
            job_config.default_arguments.update(default_args)
            
            # Prepare job parameters
            job_params = {
                'Name': job_config.job_name,
                'Description': job_config.description,
                'Role': job_config.role,
                'Command': job_config.command,
                'DefaultArguments': job_config.default_arguments,
                'MaxRetries': job_config.max_retries,
                'Timeout': job_config.timeout,
                'GlueVersion': job_config.glue_version,
                'Tags': {
                    'Environment': 'production',
                    'ManagedBy': 'enterprise-glue-manager',
                    'JobType': job_config.command.get('Name', 'unknown')
                }
            }
            
            # Add optional parameters
            if job_config.log_uri:
                job_params['LogUri'] = job_config.log_uri
                
            if job_config.execution_property:
                job_params['ExecutionProperty'] = job_config.execution_property
                
            if job_config.non_overridable_arguments:
                job_params['NonOverridableArguments'] = job_config.non_overridable_arguments
                
            if job_config.connections:
                job_params['Connections'] = {'Connections': job_config.connections}
                
            if job_config.security_configuration:
                job_params['SecurityConfiguration'] = job_config.security_configuration
                
            if job_config.notification_property:
                job_params['NotificationProperty'] = job_config.notification_property
            
            # Set worker configuration
            if job_config.worker_type and job_config.number_of_workers:
                job_params['WorkerType'] = job_config.worker_type
                job_params['NumberOfWorkers'] = job_config.number_of_workers
            elif job_config.max_capacity:
                job_params['MaxCapacity'] = job_config.max_capacity
            
            response = self.glue.create_job(**job_params)
            
            self.logger.info(f"Created ETL job: {job_config.job_name}")
            
            return {
                'job_name': job_config.job_name,
                'job_arn': response.get('Name'),
                'status': 'created'
            }
            
        except ClientError as e:
            self.logger.error(f"Error creating ETL job: {str(e)}")
            raise

    def run_etl_job_with_monitoring(self, job_name: str, 
                                   job_arguments: Optional[Dict[str, str]] = None,
                                   timeout_minutes: int = 120) -> Dict[str, Any]:
        """Run ETL job with comprehensive monitoring"""
        try:
            # Start job run
            run_params = {'JobName': job_name}
            if job_arguments:
                run_params['Arguments'] = job_arguments
            
            response = self.glue.start_job_run(**run_params)
            job_run_id = response['JobRunId']
            
            start_time = datetime.utcnow()
            timeout_time = start_time + timedelta(minutes=timeout_minutes)
            
            self.logger.info(f"Started ETL job run: {job_name} (Run ID: {job_run_id})")
            
            # Monitor job execution
            while datetime.utcnow() < timeout_time:
                response = self.glue.get_job_run(JobName=job_name, RunId=job_run_id)
                job_run = response['JobRun']
                
                job_state = JobRunState(job_run['JobRunState'])
                
                if job_state in [JobRunState.SUCCEEDED, JobRunState.FAILED, 
                               JobRunState.STOPPED, JobRunState.TIMEOUT]:
                    
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    
                    results = {
                        'job_name': job_name,
                        'job_run_id': job_run_id,
                        'status': job_state.value,
                        'duration_seconds': duration,
                        'started_on': job_run.get('StartedOn').isoformat() if job_run.get('StartedOn') else None,
                        'completed_on': job_run.get('CompletedOn').isoformat() if job_run.get('CompletedOn') else None,
                        'execution_time': job_run.get('ExecutionTime'),
                        'max_capacity': job_run.get('MaxCapacity'),
                        'worker_type': job_run.get('WorkerType'),
                        'number_of_workers': job_run.get('NumberOfWorkers'),
                        'log_group_name': job_run.get('LogGroupName'),
                        'error_message': job_run.get('ErrorMessage')
                    }
                    
                    # Publish job metrics
                    self._publish_job_metrics(results)
                    
                    if job_state == JobRunState.SUCCEEDED:
                        self.logger.info(f"ETL job {job_name} completed successfully")
                    else:
                        self.logger.error(f"ETL job {job_name} failed with state: {job_state.value}")
                    
                    return results
                
                elif job_state in [JobRunState.STARTING, JobRunState.RUNNING]:
                    self.logger.info(f"ETL job {job_name} is {job_state.value.lower()}...")
                    time.sleep(30)
                    continue
                else:
                    self.logger.warning(f"ETL job {job_name} in state: {job_state.value}")
                    time.sleep(30)
            
            raise Exception(f"ETL job {job_name} timed out after {timeout_minutes} minutes")
            
        except ClientError as e:
            self.logger.error(f"Error running ETL job: {str(e)}")
            raise

    def create_data_quality_ruleset(self, database_name: str, table_name: str,
                                   quality_rules: List[str]) -> Dict[str, Any]:
        """Create data quality ruleset for table validation"""
        try:
            ruleset_name = f"{database_name}_{table_name}_quality_rules"
            
            # Prepare data quality rules
            dqdl_rules = "\n".join([
                f"Rules = [{', '.join(quality_rules)}]"
            ])
            
            response = self.glue.create_data_quality_ruleset(
                Name=ruleset_name,
                Description=f"Data quality rules for {database_name}.{table_name}",
                Ruleset=dqdl_rules,
                TargetTable={
                    'TableName': table_name,
                    'DatabaseName': database_name
                },
                Tags={
                    'Environment': 'production',
                    'ManagedBy': 'enterprise-glue-manager',
                    'Purpose': 'data-quality'
                }
            )
            
            self.logger.info(f"Created data quality ruleset: {ruleset_name}")
            
            return {
                'ruleset_name': ruleset_name,
                'database_name': database_name,
                'table_name': table_name,
                'rules_count': len(quality_rules),
                'status': 'created'
            }
            
        except ClientError as e:
            self.logger.error(f"Error creating data quality ruleset: {str(e)}")
            raise

    def run_data_catalog_discovery(self, s3_paths: List[str], 
                                  database_name: str) -> Dict[str, Any]:
        """Run comprehensive data catalog discovery for multiple S3 paths"""
        try:
            discovery_results = []
            
            for i, s3_path in enumerate(s3_paths):
                crawler_name = f"discovery-crawler-{database_name}-{i+1}"
                
                # Create crawler for this S3 path
                crawler_config = CrawlerConfig(
                    crawler_name=crawler_name,
                    database_name=database_name,
                    targets={
                        'S3Targets': [{'Path': s3_path}]
                    },
                    role='arn:aws:iam::123456789012:role/GlueServiceRole',
                    schema_change_policy={
                        'UpdateBehavior': 'UPDATE_IN_DATABASE',
                        'DeleteBehavior': 'LOG'
                    },
                    recrawl_policy={
                        'RecrawlBehavior': 'CRAWL_NEW_FOLDERS_ONLY'
                    }
                )
                
                # Create and run crawler
                self.create_advanced_crawler(crawler_config)
                crawler_result = self.run_crawler_with_monitoring(crawler_name)
                
                discovery_results.append({
                    's3_path': s3_path,
                    'crawler_name': crawler_name,
                    'result': crawler_result
                })
                
                # Clean up temporary crawler
                try:
                    self.glue.delete_crawler(Name=crawler_name)
                except:
                    pass
            
            # Aggregate results
            total_tables = sum(result['result']['tables_created'] + 
                             result['result']['tables_updated'] 
                             for result in discovery_results)
            
            return {
                'database_name': database_name,
                'paths_processed': len(s3_paths),
                'total_tables_discovered': total_tables,
                'discovery_results': discovery_results,
                'status': 'completed'
            }
            
        except Exception as e:
            self.logger.error(f"Error running data catalog discovery: {str(e)}")
            raise

    def _publish_crawler_metrics(self, results: Dict[str, Any]) -> None:
        """Publish crawler metrics to CloudWatch"""
        try:
            metric_data = [
                {
                    'MetricName': 'CrawlerDuration',
                    'Value': results['duration_seconds'],
                    'Unit': 'Seconds',
                    'Dimensions': [
                        {
                            'Name': 'CrawlerName',
                            'Value': results['crawler_name']
                        }
                    ]
                },
                {
                    'MetricName': 'TablesCreated',
                    'Value': results['tables_created'],
                    'Unit': 'Count',
                    'Dimensions': [
                        {
                            'Name': 'CrawlerName',
                            'Value': results['crawler_name']
                        }
                    ]
                },
                {
                    'MetricName': 'TablesUpdated',
                    'Value': results['tables_updated'],
                    'Unit': 'Count',
                    'Dimensions': [
                        {
                            'Name': 'CrawlerName',
                            'Value': results['crawler_name']
                        }
                    ]
                }
            ]
            
            self.cloudwatch.put_metric_data(
                Namespace='AWS/Glue/Enterprise',
                MetricData=metric_data
            )
            
        except Exception as e:
            self.logger.warning(f"Error publishing crawler metrics: {str(e)}")

    def _publish_job_metrics(self, results: Dict[str, Any]) -> None:
        """Publish job metrics to CloudWatch"""
        try:
            metric_data = [
                {
                    'MetricName': 'JobDuration',
                    'Value': results['duration_seconds'],
                    'Unit': 'Seconds',
                    'Dimensions': [
                        {
                            'Name': 'JobName',
                            'Value': results['job_name']
                        }
                    ]
                },
                {
                    'MetricName': 'JobExecution',
                    'Value': 1,
                    'Unit': 'Count',
                    'Dimensions': [
                        {
                            'Name': 'JobName',
                            'Value': results['job_name']
                        },
                        {
                            'Name': 'Status',
                            'Value': results['status']
                        }
                    ]
                }
            ]
            
            if results.get('execution_time'):
                metric_data.append({
                    'MetricName': 'JobExecutionTime',
                    'Value': results['execution_time'],
                    'Unit': 'Seconds',
                    'Dimensions': [
                        {
                            'Name': 'JobName',
                            'Value': results['job_name']
                        }
                    ]
                })
            
            self.cloudwatch.put_metric_data(
                Namespace='AWS/Glue/Enterprise',
                MetricData=metric_data
            )
            
        except Exception as e:
            self.logger.warning(f"Error publishing job metrics: {str(e)}")

# Practical Real-World Examples

def create_data_lake_etl_pipeline():
    """Create comprehensive data lake ETL pipeline"""
    
    manager = EnterpriseGlueManager()
    
    # Create data catalog database
    database_result = manager.create_data_catalog_database(
        database_name="enterprise_data_lake",
        description="Enterprise data lake catalog",
        location_uri="s3://company-data-lake/"
    )
    print(f"Created database: {database_result}")
    
    # Create crawler for raw data discovery
    raw_data_crawler = CrawlerConfig(
        crawler_name="raw-data-discovery-crawler",
        database_name="enterprise_data_lake",
        targets={
            'S3Targets': [
                {'Path': 's3://company-data-lake/raw/sales/'},
                {'Path': 's3://company-data-lake/raw/customers/'},
                {'Path': 's3://company-data-lake/raw/products/'}
            ]
        },
        role="arn:aws:iam::123456789012:role/GlueServiceRole",
        schedule="cron(0 2 * * ? *)",  # Daily at 2 AM
        table_prefix="raw_",
        schema_change_policy={
            'UpdateBehavior': 'UPDATE_IN_DATABASE',
            'DeleteBehavior': 'LOG'
        }
    )
    
    crawler_result = manager.create_advanced_crawler(raw_data_crawler)
    print(f"Created crawler: {crawler_result}")
    
    # Run crawler to discover schema
    discovery_result = manager.run_crawler_with_monitoring("raw-data-discovery-crawler")
    print(f"Discovery completed: {discovery_result}")
    
    # Create ETL job for data transformation
    transformation_job = ETLJob(
        job_name="data-lake-transformation",
        role="arn:aws:iam::123456789012:role/GlueServiceRole",
        command={
            'Name': 'glueetl',
            'ScriptLocation': 's3://glue-scripts/data-lake-transformation.py',
            'PythonVersion': '3'
        },
        description="Transform raw data lake files to optimized format",
        default_arguments={
            '--input_database': 'enterprise_data_lake',
            '--output_location': 's3://company-data-lake/processed/',
            '--output_format': 'parquet',
            '--compression': 'snappy'
        },
        worker_type="G.1X",
        number_of_workers=10,
        max_retries=2,
        timeout=120
    )
    
    job_result = manager.create_enterprise_etl_job(transformation_job)
    print(f"Created ETL job: {job_result}")
    
    # Run ETL job
    job_execution = manager.run_etl_job_with_monitoring(
        "data-lake-transformation",
        job_arguments={'--date': datetime.utcnow().strftime('%Y-%m-%d')}
    )
    print(f"ETL job execution: {job_execution}")
    
    return {
        'database': database_result,
        'crawler': crawler_result,
        'discovery': discovery_result,
        'job': job_result,
        'execution': job_execution
    }

def create_streaming_etl_pipeline():
    """Create real-time streaming ETL pipeline"""
    
    manager = EnterpriseGlueManager()
    
    # Create streaming ETL job
    streaming_job = ETLJob(
        job_name="real-time-streaming-etl",
        role="arn:aws:iam::123456789012:role/GlueServiceRole",
        command={
            'Name': 'gluestreaming',
            'ScriptLocation': 's3://glue-scripts/streaming-etl.py',
            'PythonVersion': '3'
        },
        description="Real-time streaming ETL for IoT data processing",
        default_arguments={
            '--kafka_bootstrap_servers': 'kafka.company.com:9092',
            '--kafka_topic': 'iot-sensor-data',
            '--output_location': 's3://company-streaming-data/processed/',
            '--checkpoint_location': 's3://glue-checkpoints/streaming-etl/',
            '--window_size': '5 minutes',
            '--watermark_delay': '2 minutes'
        },
        worker_type="G.1X",
        number_of_workers=5,
        glue_version="3.0"
    )
    
    job_result = manager.create_enterprise_etl_job(streaming_job)
    
    # Create data quality rules for streaming data
    quality_rules = [
        "ColumnCount > 5",
        "IsComplete \"sensor_id\"",
        "IsComplete \"timestamp\"", 
        "ColumnValues \"temperature\" between -50 and 100",
        "ColumnValues \"humidity\" between 0 and 100",
        "Freshness \"timestamp\" <= 5 minutes"
    ]
    
    quality_result = manager.create_data_quality_ruleset(
        database_name="iot_streaming_data",
        table_name="sensor_readings",
        quality_rules=quality_rules
    )
    
    return {
        'streaming_job': job_result,
        'data_quality': quality_result
    }

def create_data_warehouse_etl():
    """Create data warehouse ETL pipeline"""
    
    manager = EnterpriseGlueManager()
    
    # Create database for analytics
    analytics_db = manager.create_data_catalog_database(
        database_name="analytics_warehouse",
        description="Analytics data warehouse catalog"
    )
    
    # Create ETL job for data warehouse loading
    warehouse_job = ETLJob(
        job_name="warehouse-etl-pipeline",
        role="arn:aws:iam::123456789012:role/GlueServiceRole",
        command={
            'Name': 'glueetl',
            'ScriptLocation': 's3://glue-scripts/warehouse-etl.py',
            'PythonVersion': '3'
        },
        description="ETL pipeline for populating analytics data warehouse",
        default_arguments={
            '--source_database': 'enterprise_data_lake',
            '--target_connection': 'redshift-connection',
            '--target_schema': 'analytics',
            '--batch_size': '10000',
            '--enable_data_lineage': 'true'
        },
        connections=['redshift-connection'],
        worker_type="G.2X",
        number_of_workers=20,
        max_retries=3,
        timeout=240
    )
    
    job_result = manager.create_enterprise_etl_job(warehouse_job)
    
    # Create crawler for warehouse tables
    warehouse_crawler = CrawlerConfig(
        crawler_name="warehouse-schema-crawler",
        database_name="analytics_warehouse",
        targets={
            'JdbcTargets': [{
                'ConnectionName': 'redshift-connection',
                'Path': 'analytics/%'
            }]
        },
        role="arn:aws:iam::123456789012:role/GlueServiceRole",
        schedule="cron(0 6 * * ? *)"  # Daily at 6 AM
    )
    
    crawler_result = manager.create_advanced_crawler(warehouse_crawler)
    
    return {
        'database': analytics_db,
        'etl_job': job_result,
        'crawler': crawler_result
    }

def create_ml_feature_engineering_pipeline():
    """Create machine learning feature engineering pipeline"""
    
    manager = EnterpriseGlueManager()
    
    # Create ML features database
    ml_db = manager.create_data_catalog_database(
        database_name="ml_features",
        description="Machine learning feature store"
    )
    
    # Create feature engineering job
    feature_job = ETLJob(
        job_name="ml-feature-engineering",
        role="arn:aws:iam::123456789012:role/GlueServiceRole",
        command={
            'Name': 'glueetl',
            'ScriptLocation': 's3://glue-scripts/ml-feature-engineering.py',
            'PythonVersion': '3'
        },
        description="ML feature engineering and preparation pipeline",
        default_arguments={
            '--source_database': 'enterprise_data_lake',
            '--feature_store_location': 's3://ml-feature-store/',
            '--feature_group_prefix': 'customer_features',
            '--enable_feature_validation': 'true',
            '--spark_sql_adaptive_enabled': 'true'
        },
        worker_type="G.2X",
        number_of_workers=15,
        max_retries=2,
        timeout=180
    )
    
    job_result = manager.create_enterprise_etl_job(feature_job)
    
    # Create data quality rules for ML features
    ml_quality_rules = [
        "IsComplete \"customer_id\"",
        "IsUnique \"customer_id\"",
        "ColumnValues \"age\" between 18 and 120",
        "ColumnValues \"income\" >= 0",
        "ColumnDataType \"purchase_frequency\" = \"DECIMAL\"",
        "ColumnNamesMatchPattern \".*_feature$\"",
        "RowCount > 1000"
    ]
    
    quality_result = manager.create_data_quality_ruleset(
        database_name="ml_features",
        table_name="customer_features",
        quality_rules=ml_quality_rules
    )
    
    return {
        'database': ml_db,
        'feature_job': job_result,
        'data_quality': quality_result
    }

def create_compliance_data_pipeline():
    """Create compliance and audit data pipeline"""
    
    manager = EnterpriseGlueManager()
    
    # Create compliance database
    compliance_db = manager.create_data_catalog_database(
        database_name="compliance_audit",
        description="Compliance and audit data catalog"
    )
    
    # Create compliance ETL job
    compliance_job = ETLJob(
        job_name="compliance-data-processing",
        role="arn:aws:iam::123456789012:role/GlueServiceRole",
        command={
            'Name': 'glueetl',
            'ScriptLocation': 's3://glue-scripts/compliance-processing.py',
            'PythonVersion': '3'
        },
        description="Process data for compliance and audit requirements",
        default_arguments={
            '--enable_data_lineage': 'true',
            '--enable_encryption': 'true',
            '--pii_detection': 'true',
            '--retention_days': '2555',  # 7 years
            '--audit_log_location': 's3://compliance-audit-logs/'
        },
        security_configuration="compliance-security-config",
        worker_type="G.1X",
        number_of_workers=8,
        max_retries=1,
        timeout=360
    )
    
    job_result = manager.create_enterprise_etl_job(compliance_job)
    
    # Create strict data quality rules for compliance
    compliance_quality_rules = [
        "IsComplete \"transaction_id\"",
        "IsUnique \"transaction_id\"",
        "IsComplete \"timestamp\"",
        "IsComplete \"user_id\"",
        "ColumnDataType \"amount\" = \"DECIMAL\"",
        "ColumnValues \"amount\" > 0",
        "CustomSql \"SELECT COUNT(*) FROM primary WHERE timestamp >= CURRENT_DATE - INTERVAL '1' DAY\" > 0"
    ]
    
    quality_result = manager.create_data_quality_ruleset(
        database_name="compliance_audit",
        table_name="financial_transactions",
        quality_rules=compliance_quality_rules
    )
    
    return {
        'database': compliance_db,
        'compliance_job': job_result,
        'data_quality': quality_result
    }
```

## DevOps Integration Patterns

### Infrastructure as Code (Terraform)

```hcl
# glue_infrastructure.tf
resource "aws_glue_catalog_database" "enterprise_database" {
  name         = "enterprise-data-catalog"
  description  = "Enterprise data catalog for analytics"
  
  create_table_default_permission {
    permissions = ["ALL"]
    
    principal {
      data_lake_principal_identifier = "IAM_ALLOWED_PRINCIPALS"
    }
  }
  
  target_database {
    catalog_id    = data.aws_caller_identity.current.account_id
    database_name = aws_glue_catalog_database.enterprise_database.name
  }
}

resource "aws_glue_crawler" "data_lake_crawler" {
  database_name = aws_glue_catalog_database.enterprise_database.name
  name          = "enterprise-data-lake-crawler"
  role          = aws_iam_role.glue_service_role.arn
  
  s3_target {
    path = "s3://${aws_s3_bucket.data_lake.bucket}/raw/"
  }
  
  s3_target {
    path = "s3://${aws_s3_bucket.data_lake.bucket}/processed/"
  }
  
  schema_change_policy {
    update_behavior = "UPDATE_IN_DATABASE"
    delete_behavior = "LOG"
  }
  
  recrawl_policy {
    recrawl_behavior = "CRAWL_NEW_FOLDERS_ONLY"
  }
  
  configuration = jsonencode({
    Version = 1.0
    CrawlerOutput = {
      Partitions = {
        AddOrUpdateBehavior = "InheritFromTable"
      }
      Tables = {
        AddOrUpdateBehavior = "MergeNewColumns"
      }
    }
    Grouping = {
      TableGroupingPolicy = "CombineCompatibleSchemas"
    }
  })
  
  schedule = "cron(0 2 * * ? *)"
  
  tags = {
    Environment = var.environment
    Purpose     = "DataCatalog"
  }
}

resource "aws_glue_job" "etl_job" {
  name     = "enterprise-etl-job"
  role_arn = aws_iam_role.glue_service_role.arn
  
  command {
    script_location = "s3://${aws_s3_bucket.glue_scripts.bucket}/etl-job.py"
    python_version  = "3"
    name           = "glueetl"
  }
  
  default_arguments = {
    "--job-bookmark-option"                     = "job-bookmark-enable"
    "--enable-metrics"                          = ""
    "--enable-continuous-cloudwatch-log"       = "true"
    "--enable-spark-ui"                         = "true"
    "--spark-event-logs-path"                   = "s3://${aws_s3_bucket.glue_logs.bucket}/spark-events/"
    "--additional-python-modules"               = "great-expectations,pandas==1.5.3"
    "--TempDir"                                = "s3://${aws_s3_bucket.glue_temp.bucket}/temp/"
  }
  
  execution_property {
    max_concurrent_runs = 3
  }
  
  worker_type       = "G.2X"
  number_of_workers = 10
  max_retries       = 2
  timeout           = 2880
  glue_version      = "3.0"
  
  tags = {
    Environment = var.environment
    JobType     = "ETL"
  }
}

resource "aws_glue_data_quality_ruleset" "data_quality_rules" {
  name        = "enterprise-data-quality-rules"
  description = "Enterprise data quality validation rules"
  
  ruleset = <<-EOT
    Rules = [
      IsComplete "id",
      IsUnique "id", 
      ColumnCount > 5,
      RowCount > 100,
      ColumnDataType "timestamp" = "TIMESTAMP",
      ColumnValues "status" in ["active", "inactive", "pending"]
    ]
  EOT
  
  target_table {
    database_name = aws_glue_catalog_database.enterprise_database.name
    table_name    = "processed_data"
  }
  
  tags = {
    Environment = var.environment
    Purpose     = "DataQuality"
  }
}
```

### CI/CD Pipeline Integration

```yaml
# .github/workflows/glue-etl-deployment.yml
name: Glue ETL Pipeline Deployment

on:
  push:
    branches: [main]
    paths: ['glue/**']
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy'
        required: true
        type: choice
        options:
          - development
          - staging  
          - production

jobs:
  validate-scripts:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install Dependencies
      run: |
        pip install boto3 pyspark great-expectations pytest
    
    - name: Validate ETL Scripts
      run: |
        python scripts/validate_glue_scripts.py \
          --script-directory glue/scripts/ \
          --environment ${{ github.event.inputs.environment || 'development' }}
    
    - name: Run Unit Tests
      run: |
        pytest tests/unit/ -v

  deploy-jobs:
    needs: validate-scripts
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        role-to-assume: ${{ secrets.AWS_GLUE_ROLE }}
        aws-region: us-east-1
    
    - name: Upload Scripts to S3
      run: |
        aws s3 sync glue/scripts/ s3://glue-scripts-${{ github.event.inputs.environment || 'development' }}/
    
    - name: Deploy Glue Jobs
      run: |
        python scripts/deploy_glue_jobs.py \
          --config-file glue/config/jobs.json \
          --environment ${{ github.event.inputs.environment || 'development' }}
    
    - name: Run Integration Tests
      run: |
        python scripts/test_glue_integration.py \
          --job-name enterprise-etl-job-${{ github.event.inputs.environment || 'development' }} \
          --test-data-location s3://test-data/samples/
```

## Practical Use Cases

### 1. Enterprise Data Lake Management
- **Automated schema discovery** for diverse data sources
- **Data catalog governance** with metadata management
- **ETL job orchestration** for data transformation
- **Data quality monitoring** and validation

### 2. Real-time Analytics Pipeline
- **Streaming ETL processing** for live data
- **Real-time data quality** monitoring
- **Event-driven transformations** with triggers
- **Low-latency data processing** for analytics

### 3. Machine Learning Data Preparation
- **Feature engineering** at scale
- **Data preprocessing** for ML models
- **Feature store management** with versioning
- **ML pipeline integration** with SageMaker

### 4. Compliance and Governance
- **Data lineage tracking** for audit trails
- **PII detection and masking** for privacy
- **Regulatory reporting** automation
- **Data retention policy** enforcement

### 5. Multi-source Data Integration
- **Heterogeneous data source** connectivity
- **Schema evolution** management
- **Data format standardization** across sources
- **Cross-platform ETL** processing

## Performance Optimization

- **Optimized Spark configurations** for better performance
- **Dynamic resource allocation** based on workload
- **Columnar storage formats** (Parquet, ORC) for efficiency
- **Partition pruning** for faster queries
- **Job bookmarks** for incremental processing
- **Connection pooling** for database sources

## Cost Management

- **Right-sizing workers** based on data volume
- **Spot instances** for development workloads
- **Job scheduling** during off-peak hours
- **Data lifecycle policies** for storage optimization
- **Resource monitoring** and automated scaling
- **Pay-per-use pricing** model optimization