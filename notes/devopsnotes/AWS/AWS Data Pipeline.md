# AWS Data Pipeline - Enterprise ETL Orchestration Platform

Web service for orchestrating and automating data movement and transformation, enhanced with enterprise automation, advanced scheduling, and comprehensive DevOps integration.

## Core Features & Components

- **Pipeline Activities:** EMR, Hive, Pig, SQL, Shell commands, Lambda functions
- **Schedule-based execution:** Time-based and cron-based scheduling
- **Event-driven processing:** Triggered by data availability or external events
- **Visual pipeline designer** with drag-and-drop interface
- **Built-in retry logic and error handling** with exponential backoff
- **Integration capabilities:** EMR, RDS, S3, Redshift, DynamoDB, and third-party systems
- **Precondition checking** before execution with data validation
- **SNS notifications** for pipeline status and error alerts
- **Template library** for common ETL patterns
- **Resource management** with automatic scaling and cost optimization

## Enterprise ETL Orchestration Framework

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

class PipelineState(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"
    PAUSED = "PAUSED"

class ActivityType(Enum):
    EMR_ACTIVITY = "EmrActivity"
    HIVE_ACTIVITY = "HiveActivity"
    PIG_ACTIVITY = "PigActivity"
    SQL_ACTIVITY = "SqlActivity"
    SHELL_COMMAND = "ShellCommandActivity"
    COPY_ACTIVITY = "CopyActivity"
    LAMBDA_ACTIVITY = "LambdaActivity"

class ScheduleType(Enum):
    CRON = "cron"
    TIMESERIES = "timeSeries"
    ONDEMAND = "ondemand"

@dataclass
class PipelineActivity:
    activity_id: str
    activity_type: ActivityType
    name: str
    input_data: Optional[str] = None
    output_data: Optional[str] = None
    schedule: Optional[Dict[str, Any]] = None
    retry_delay: str = "15 Minutes"
    maximum_retries: int = 3
    on_fail: Optional[str] = None
    on_success: Optional[str] = None
    depends_on: List[str] = field(default_factory=list)

@dataclass
class DataNode:
    node_id: str
    node_type: str  # S3DataNode, SqlDataNode, DynamoDBDataNode, etc.
    table_name: Optional[str] = None
    s3_location: Optional[str] = None
    sql_query: Optional[str] = None
    select_query: Optional[str] = None
    database: Optional[str] = None

@dataclass
class ETLPipeline:
    pipeline_id: str
    name: str
    description: str
    activities: List[PipelineActivity] = field(default_factory=list)
    data_nodes: List[DataNode] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    schedule: Optional[Dict[str, Any]] = None
    pipeline_tags: Dict[str, str] = field(default_factory=dict)

class EnterpriseDataPipelineManager:
    """
    Enterprise AWS Data Pipeline manager with automated ETL orchestration,
    advanced scheduling, and comprehensive monitoring capabilities.
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.datapipeline = boto3.client('datapipeline', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.emr = boto3.client('emr', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger('DataPipelineManager')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def create_etl_pipeline(self, pipeline_config: ETLPipeline) -> Dict[str, Any]:
        """Create comprehensive ETL pipeline with enterprise features"""
        try:
            # Create pipeline
            response = self.datapipeline.create_pipeline(
                name=pipeline_config.name,
                uniqueId=pipeline_config.pipeline_id,
                description=pipeline_config.description,
                tags=[
                    {'key': k, 'value': v} 
                    for k, v in pipeline_config.pipeline_tags.items()
                ]
            )
            
            pipeline_id = response['pipelineId']
            
            # Build pipeline definition
            pipeline_definition = self._build_pipeline_definition(pipeline_config)
            
            # Put pipeline definition
            self.datapipeline.put_pipeline_definition(
                pipelineId=pipeline_id,
                pipelineObjects=pipeline_definition
            )
            
            # Validate pipeline
            validation_response = self.datapipeline.validate_pipeline_definition(
                pipelineId=pipeline_id,
                pipelineObjects=pipeline_definition
            )
            
            if validation_response.get('errored'):
                raise Exception(f"Pipeline validation failed: {validation_response.get('validationErrors', [])}")
            
            self.logger.info(f"Created ETL pipeline: {pipeline_id}")
            
            return {
                'pipeline_id': pipeline_id,
                'pipeline_name': pipeline_config.name,
                'status': 'created',
                'validation_warnings': validation_response.get('validationWarnings', [])
            }
            
        except ClientError as e:
            self.logger.error(f"Error creating ETL pipeline: {str(e)}")
            raise

    def _build_pipeline_definition(self, config: ETLPipeline) -> List[Dict[str, Any]]:
        """Build comprehensive pipeline definition"""
        pipeline_objects = []
        
        # Add default objects
        pipeline_objects.extend([
            {
                'id': 'Default',
                'name': 'Default',
                'fields': [
                    {'key': 'type', 'stringValue': 'Default'},
                    {'key': 'scheduleType', 'stringValue': 'cron'},
                    {'key': 'schedule', 'refValue': 'DefaultSchedule'},
                    {'key': 'pipelineLogUri', 'stringValue': 's3://data-pipeline-logs/'},
                    {'key': 'resourceRole', 'stringValue': 'DataPipelineDefaultResourceRole'},
                    {'key': 'role', 'stringValue': 'DataPipelineDefaultRole'},
                    {'key': 'failureAndRerunMode', 'stringValue': 'CASCADE'}
                ]
            },
            {
                'id': 'DefaultSchedule',
                'name': 'Every day at 2 AM',
                'fields': [
                    {'key': 'type', 'stringValue': 'Schedule'},
                    {'key': 'period', 'stringValue': '1 days'},
                    {'key': 'startDateTime', 'stringValue': datetime.utcnow().strftime('%Y-%m-%dT02:00:00')},
                    {'key': 'occurrences', 'stringValue': '1'}
                ]
            }
        ])
        
        # Add custom schedule if provided
        if config.schedule:
            schedule_obj = {
                'id': 'CustomSchedule',
                'name': 'Custom Schedule',
                'fields': [
                    {'key': 'type', 'stringValue': 'Schedule'}
                ]
            }
            
            for key, value in config.schedule.items():
                schedule_obj['fields'].append({'key': key, 'stringValue': str(value)})
            
            pipeline_objects.append(schedule_obj)
        
        # Add data nodes
        for data_node in config.data_nodes:
            node_obj = self._create_data_node_object(data_node)
            pipeline_objects.append(node_obj)
        
        # Add activities
        for activity in config.activities:
            activity_obj = self._create_activity_object(activity)
            pipeline_objects.append(activity_obj)
        
        return pipeline_objects

    def _create_data_node_object(self, data_node: DataNode) -> Dict[str, Any]:
        """Create data node object for pipeline definition"""
        fields = [
            {'key': 'type', 'stringValue': data_node.node_type}
        ]
        
        if data_node.s3_location:
            fields.append({'key': 'filePath', 'stringValue': data_node.s3_location})
        
        if data_node.table_name:
            fields.append({'key': 'tableName', 'stringValue': data_node.table_name})
        
        if data_node.database:
            fields.append({'key': 'database', 'refValue': data_node.database})
        
        if data_node.select_query:
            fields.append({'key': 'selectQuery', 'stringValue': data_node.select_query})
        
        return {
            'id': data_node.node_id,
            'name': data_node.node_id,
            'fields': fields
        }

    def _create_activity_object(self, activity: PipelineActivity) -> Dict[str, Any]:
        """Create activity object for pipeline definition"""
        fields = [
            {'key': 'type', 'stringValue': activity.activity_type.value},
            {'key': 'retryDelay', 'stringValue': activity.retry_delay},
            {'key': 'maximumRetries', 'stringValue': str(activity.maximum_retries)}
        ]
        
        if activity.input_data:
            fields.append({'key': 'input', 'refValue': activity.input_data})
        
        if activity.output_data:
            fields.append({'key': 'output', 'refValue': activity.output_data})
        
        if activity.depends_on:
            fields.append({'key': 'dependsOn', 'refValue': ','.join(activity.depends_on)})
        
        if activity.on_fail:
            fields.append({'key': 'onFail', 'refValue': activity.on_fail})
        
        if activity.on_success:
            fields.append({'key': 'onSuccess', 'refValue': activity.on_success})
        
        # Add activity-specific configurations
        if activity.activity_type == ActivityType.EMR_ACTIVITY:
            fields.extend([
                {'key': 'emrCluster', 'refValue': 'EmrClusterForProcessing'},
                {'key': 'step', 'stringValue': '/home/hadoop/contrib/streaming/hadoop-streaming.jar'}
            ])
        elif activity.activity_type == ActivityType.SQL_ACTIVITY:
            fields.extend([
                {'key': 'database', 'refValue': 'SqlDatabase'},
                {'key': 'script', 'stringValue': 'SELECT * FROM source_table'}
            ])
        
        return {
            'id': activity.activity_id,
            'name': activity.name,
            'fields': fields
        }

    def activate_pipeline(self, pipeline_id: str, start_timestamp: Optional[str] = None) -> Dict[str, Any]:
        """Activate pipeline with monitoring setup"""
        try:
            params = {'pipelineId': pipeline_id}
            if start_timestamp:
                params['startTimestamp'] = start_timestamp
            
            self.datapipeline.activate_pipeline(**params)
            
            # Setup CloudWatch monitoring
            self._setup_pipeline_monitoring(pipeline_id)
            
            self.logger.info(f"Activated pipeline: {pipeline_id}")
            
            return {
                'pipeline_id': pipeline_id,
                'status': 'activated',
                'activation_time': datetime.utcnow().isoformat()
            }
            
        except ClientError as e:
            self.logger.error(f"Error activating pipeline: {str(e)}")
            raise

    def _setup_pipeline_monitoring(self, pipeline_id: str) -> None:
        """Setup comprehensive pipeline monitoring"""
        try:
            # Create CloudWatch alarms for pipeline health
            self.cloudwatch.put_metric_alarm(
                AlarmName=f'DataPipeline-{pipeline_id}-Failed',
                ComparisonOperator='GreaterThanThreshold',
                EvaluationPeriods=1,
                MetricName='PipelineExecutionFailed',
                Namespace='AWS/DataPipeline',
                Period=300,
                Statistic='Sum',
                Threshold=0.0,
                ActionsEnabled=True,
                AlarmActions=[
                    f'arn:aws:sns:us-east-1:123456789012:datapipeline-alerts'
                ],
                AlarmDescription=f'Alert when pipeline {pipeline_id} fails',
                Dimensions=[
                    {
                        'Name': 'PipelineId',
                        'Value': pipeline_id
                    }
                ]
            )
            
        except Exception as e:
            self.logger.warning(f"Error setting up monitoring: {str(e)}")

    def monitor_pipeline_execution(self, pipeline_id: str, timeout_minutes: int = 60) -> Dict[str, Any]:
        """Monitor pipeline execution with detailed status tracking"""
        try:
            start_time = datetime.utcnow()
            timeout_time = start_time + timedelta(minutes=timeout_minutes)
            
            execution_history = []
            
            while datetime.utcnow() < timeout_time:
                # Get pipeline status
                status_response = self.datapipeline.describe_pipelines(
                    pipelineIds=[pipeline_id]
                )
                
                if not status_response.get('pipelineDescriptionList'):
                    raise Exception(f"Pipeline {pipeline_id} not found")
                
                pipeline_desc = status_response['pipelineDescriptionList'][0]
                current_state = pipeline_desc.get('pipelineState', 'UNKNOWN')
                
                # Get object runs
                objects_response = self.datapipeline.query_objects(
                    pipelineId=pipeline_id,
                    sphere='INSTANCE'
                )
                
                if objects_response.get('ids'):
                    # Get detailed object status
                    objects_detail = self.datapipeline.describe_objects(
                        pipelineId=pipeline_id,
                        objectIds=objects_response['ids'][:10]  # Limit to first 10
                    )
                    
                    # Track execution progress
                    for obj in objects_detail.get('pipelineObjects', []):
                        obj_id = obj.get('id')
                        obj_fields = {field['key']: field.get('stringValue', field.get('refValue')) 
                                    for field in obj.get('fields', [])}
                        
                        execution_history.append({
                            'object_id': obj_id,
                            'status': obj_fields.get('@status', 'UNKNOWN'),
                            'type': obj_fields.get('type'),
                            'timestamp': datetime.utcnow().isoformat()
                        })
                
                # Check if pipeline is complete
                if current_state in ['FINISHED', 'FAILED', 'CANCELED']:
                    break
                
                time.sleep(30)  # Check every 30 seconds
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            results = {
                'pipeline_id': pipeline_id,
                'final_state': current_state,
                'duration_seconds': duration,
                'execution_history': execution_history,
                'monitoring_completed': datetime.utcnow().isoformat()
            }
            
            # Publish execution metrics
            self._publish_execution_metrics(results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error monitoring pipeline: {str(e)}")
            raise

    def _publish_execution_metrics(self, execution_results: Dict[str, Any]) -> None:
        """Publish pipeline execution metrics to CloudWatch"""
        try:
            metric_data = [
                {
                    'MetricName': 'PipelineExecutionDuration',
                    'Value': execution_results['duration_seconds'],
                    'Unit': 'Seconds',
                    'Dimensions': [
                        {
                            'Name': 'PipelineId',
                            'Value': execution_results['pipeline_id']
                        }
                    ]
                },
                {
                    'MetricName': 'PipelineExecutionCount',
                    'Value': 1,
                    'Unit': 'Count',
                    'Dimensions': [
                        {
                            'Name': 'PipelineId',
                            'Value': execution_results['pipeline_id']
                        },
                        {
                            'Name': 'Status',
                            'Value': execution_results['final_state']
                        }
                    ]
                }
            ]
            
            self.cloudwatch.put_metric_data(
                Namespace='AWS/DataPipeline/Enterprise',
                MetricData=metric_data
            )
            
        except Exception as e:
            self.logger.warning(f"Error publishing metrics: {str(e)}")

    def run_data_warehouse_etl(self, source_config: Dict[str, Any], 
                              target_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run comprehensive data warehouse ETL pipeline"""
        try:
            # Create data warehouse ETL pipeline
            warehouse_pipeline = ETLPipeline(
                pipeline_id=f"warehouse-etl-{int(datetime.utcnow().timestamp())}",
                name="Data Warehouse ETL Pipeline",
                description="Automated data warehouse loading with transformation",
                schedule={
                    'period': '1 days',
                    'startDateTime': (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:00:00')
                },
                pipeline_tags={
                    'Environment': 'production',
                    'Purpose': 'data-warehouse',
                    'Owner': 'data-engineering'
                }
            )
            
            # Add data nodes
            source_data = DataNode(
                node_id="SourceData",
                node_type="S3DataNode",
                s3_location=source_config['s3_location']
            )
            
            target_data = DataNode(
                node_id="TargetWarehouse",
                node_type="RedshiftDataNode" if target_config.get('type') == 'redshift' else "SqlDataNode",
                database="DataWarehouse",
                table_name=target_config['table_name']
            )
            
            warehouse_pipeline.data_nodes.extend([source_data, target_data])
            
            # Add ETL activities
            extract_activity = PipelineActivity(
                activity_id="ExtractData",
                activity_type=ActivityType.SQL_ACTIVITY,
                name="Extract Source Data",
                input_data="SourceData",
                retry_delay="10 Minutes",
                maximum_retries=2
            )
            
            transform_activity = PipelineActivity(
                activity_id="TransformData",
                activity_type=ActivityType.EMR_ACTIVITY,
                name="Transform Data with Spark",
                input_data="SourceData",
                output_data="TransformedData",
                depends_on=["ExtractData"],
                retry_delay="15 Minutes",
                maximum_retries=3
            )
            
            load_activity = PipelineActivity(
                activity_id="LoadData",
                activity_type=ActivityType.COPY_ACTIVITY,
                name="Load to Data Warehouse",
                input_data="TransformedData",
                output_data="TargetWarehouse",
                depends_on=["TransformData"],
                retry_delay="5 Minutes",
                maximum_retries=2
            )
            
            warehouse_pipeline.activities.extend([
                extract_activity, transform_activity, load_activity
            ])
            
            # Create and activate pipeline
            pipeline_result = self.create_etl_pipeline(warehouse_pipeline)
            activation_result = self.activate_pipeline(pipeline_result['pipeline_id'])
            
            # Monitor execution
            execution_result = self.monitor_pipeline_execution(
                pipeline_result['pipeline_id'],
                timeout_minutes=120
            )
            
            return {
                'pipeline_creation': pipeline_result,
                'activation': activation_result,
                'execution': execution_result
            }
            
        except Exception as e:
            self.logger.error(f"Error running data warehouse ETL: {str(e)}")
            raise

# Practical Real-World Examples

def create_daily_sales_etl():
    """Create daily sales data ETL pipeline"""
    
    manager = EnterpriseDataPipelineManager()
    
    # Configure sales ETL pipeline
    sales_pipeline = ETLPipeline(
        pipeline_id="daily-sales-etl-v1",
        name="Daily Sales Data ETL",
        description="Extract daily sales data, transform for analytics, and load to data warehouse",
        schedule={
            'period': '1 days',
            'startDateTime': datetime.utcnow().replace(hour=2, minute=0).strftime('%Y-%m-%dT%H:%M:%S'),
            'occurrences': '365'  # Run for a year
        },
        pipeline_tags={
            'Department': 'Sales',
            'DataType': 'Transactional',
            'Frequency': 'Daily'
        }
    )
    
    # Data nodes
    raw_sales_data = DataNode(
        node_id="RawSalesData",
        node_type="S3DataNode",
        s3_location="s3://company-sales-data/raw/#{format(@scheduledStartTime, 'yyyy/MM/dd')}/"
    )
    
    processed_sales_data = DataNode(
        node_id="ProcessedSalesData",
        node_type="S3DataNode",
        s3_location="s3://company-analytics/processed-sales/#{format(@scheduledStartTime, 'yyyy/MM/dd')}/"
    )
    
    sales_warehouse = DataNode(
        node_id="SalesWarehouse",
        node_type="RedshiftDataNode",
        database="SalesAnalytics",
        table_name="daily_sales_facts"
    )
    
    sales_pipeline.data_nodes.extend([raw_sales_data, processed_sales_data, sales_warehouse])
    
    # Activities
    validate_data = PipelineActivity(
        activity_id="ValidateRawData",
        activity_type=ActivityType.SHELL_COMMAND,
        name="Validate Raw Sales Data",
        input_data="RawSalesData"
    )
    
    process_sales = PipelineActivity(
        activity_id="ProcessSalesData",
        activity_type=ActivityType.EMR_ACTIVITY,
        name="Process Sales Data with Spark",
        input_data="RawSalesData",
        output_data="ProcessedSalesData",
        depends_on=["ValidateRawData"],
        retry_delay="20 Minutes",
        maximum_retries=2
    )
    
    load_to_warehouse = PipelineActivity(
        activity_id="LoadToWarehouse",
        activity_type=ActivityType.COPY_ACTIVITY,
        name="Load to Sales Data Warehouse",
        input_data="ProcessedSalesData",
        output_data="SalesWarehouse",
        depends_on=["ProcessSalesData"]
    )
    
    sales_pipeline.activities.extend([validate_data, process_sales, load_to_warehouse])
    
    # Create and run pipeline
    pipeline_result = manager.create_etl_pipeline(sales_pipeline)
    activation_result = manager.activate_pipeline(pipeline_result['pipeline_id'])
    
    print(f"Created daily sales ETL pipeline:")
    print(f"- Pipeline ID: {pipeline_result['pipeline_id']}")
    print(f"- Status: {activation_result['status']}")
    
    return pipeline_result

def create_log_analysis_pipeline():
    """Create log analysis ETL pipeline"""
    
    manager = EnterpriseDataPipelineManager()
    
    # Configure log analysis pipeline
    log_pipeline = ETLPipeline(
        pipeline_id="log-analysis-etl-v1",
        name="Web Logs Analysis Pipeline",
        description="Process web access logs for analytics and monitoring",
        schedule={
            'period': '1 hours',
            'startDateTime': datetime.utcnow().replace(minute=0, second=0).strftime('%Y-%m-%dT%H:%M:%S')
        }
    )
    
    # Data sources and targets
    raw_logs = DataNode(
        node_id="WebAccessLogs",
        node_type="S3DataNode",
        s3_location="s3://company-logs/web-access/#{format(@scheduledStartTime, 'yyyy/MM/dd/HH')}/"
    )
    
    processed_logs = DataNode(
        node_id="ProcessedLogs",
        node_type="S3DataNode",
        s3_location="s3://company-analytics/processed-logs/#{format(@scheduledStartTime, 'yyyy/MM/dd/HH')}/"
    )
    
    log_pipeline.data_nodes.extend([raw_logs, processed_logs])
    
    # Processing activities
    parse_logs = PipelineActivity(
        activity_id="ParseWebLogs",
        activity_type=ActivityType.EMR_ACTIVITY,
        name="Parse and Clean Web Logs",
        input_data="WebAccessLogs",
        output_data="ProcessedLogs"
    )
    
    generate_metrics = PipelineActivity(
        activity_id="GenerateMetrics",
        activity_type=ActivityType.LAMBDA_ACTIVITY,
        name="Generate Real-time Metrics",
        input_data="ProcessedLogs",
        depends_on=["ParseWebLogs"]
    )
    
    log_pipeline.activities.extend([parse_logs, generate_metrics])
    
    return manager.create_etl_pipeline(log_pipeline)

def create_ml_data_pipeline():
    """Create machine learning data preparation pipeline"""
    
    manager = EnterpriseDataPipelineManager()
    
    # Configure ML data pipeline
    ml_pipeline = ETLPipeline(
        pipeline_id="ml-data-prep-v1",
        name="ML Training Data Pipeline",
        description="Prepare and feature engineer data for machine learning models",
        schedule={
            'period': '1 days',
            'startDateTime': datetime.utcnow().replace(hour=1, minute=0).strftime('%Y-%m-%dT%H:%M:%S')
        }
    )
    
    # Data sources
    customer_data = DataNode(
        node_id="CustomerData",
        node_type="SqlDataNode",
        database="CustomerDB",
        select_query="SELECT * FROM customers WHERE updated_date >= '#{format(@scheduledStartTime, 'yyyy-MM-dd')}'"
    )
    
    transaction_data = DataNode(
        node_id="TransactionData",
        node_type="S3DataNode",
        s3_location="s3://company-transactions/daily/#{format(@scheduledStartTime, 'yyyy/MM/dd')}/"
    )
    
    ml_features = DataNode(
        node_id="MLFeatures",
        node_type="S3DataNode",
        s3_location="s3://company-ml/features/#{format(@scheduledStartTime, 'yyyy/MM/dd')}/"
    )
    
    ml_pipeline.data_nodes.extend([customer_data, transaction_data, ml_features])
    
    # Feature engineering activities
    merge_data = PipelineActivity(
        activity_id="MergeCustomerTransaction",
        activity_type=ActivityType.EMR_ACTIVITY,
        name="Merge Customer and Transaction Data",
        input_data="CustomerData,TransactionData",
        output_data="MergedData"
    )
    
    feature_engineering = PipelineActivity(
        activity_id="FeatureEngineering",
        activity_type=ActivityType.EMR_ACTIVITY,
        name="Feature Engineering with Spark ML",
        input_data="MergedData",
        output_data="MLFeatures",
        depends_on=["MergeCustomerTransaction"]
    )
    
    validate_features = PipelineActivity(
        activity_id="ValidateFeatures",
        activity_type=ActivityType.LAMBDA_ACTIVITY,
        name="Validate ML Features",
        input_data="MLFeatures",
        depends_on=["FeatureEngineering"]
    )
    
    ml_pipeline.activities.extend([merge_data, feature_engineering, validate_features])
    
    return manager.create_etl_pipeline(ml_pipeline)

def create_financial_reporting_pipeline():
    """Create financial reporting ETL pipeline"""
    
    manager = EnterpriseDataPipelineManager()
    
    # Monthly financial reporting pipeline
    financial_pipeline = ETLPipeline(
        pipeline_id="monthly-financial-reports-v1",
        name="Monthly Financial Reporting",
        description="Generate monthly financial reports and regulatory compliance data",
        schedule={
            'period': '1 months',
            'startDateTime': datetime.utcnow().replace(day=1, hour=6, minute=0).strftime('%Y-%m-%dT%H:%M:%S')
        }
    )
    
    # Financial data sources
    accounting_data = DataNode(
        node_id="AccountingData",
        node_type="SqlDataNode",
        database="FinancialDB",
        select_query="SELECT * FROM accounting_entries WHERE entry_date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')"
    )
    
    transaction_data = DataNode(
        node_id="TransactionData",
        node_type="SqlDataNode",
        database="PaymentDB",
        select_query="SELECT * FROM transactions WHERE transaction_date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')"
    )
    
    financial_reports = DataNode(
        node_id="FinancialReports",
        node_type="S3DataNode",
        s3_location="s3://company-financial-reports/#{format(@scheduledStartTime, 'yyyy/MM')}/"
    )
    
    financial_pipeline.data_nodes.extend([accounting_data, transaction_data, financial_reports])
    
    # Reporting activities
    reconcile_data = PipelineActivity(
        activity_id="ReconcileFinancialData",
        activity_type=ActivityType.SQL_ACTIVITY,
        name="Reconcile Accounting and Transaction Data",
        input_data="AccountingData,TransactionData"
    )
    
    generate_reports = PipelineActivity(
        activity_id="GenerateFinancialReports",
        activity_type=ActivityType.EMR_ACTIVITY,
        name="Generate Financial Reports",
        input_data="AccountingData,TransactionData",
        output_data="FinancialReports",
        depends_on=["ReconcileFinancialData"]
    )
    
    compliance_check = PipelineActivity(
        activity_id="ComplianceValidation",
        activity_type=ActivityType.LAMBDA_ACTIVITY,
        name="Validate Regulatory Compliance",
        input_data="FinancialReports",
        depends_on=["GenerateFinancialReports"]
    )
    
    financial_pipeline.activities.extend([reconcile_data, generate_reports, compliance_check])
    
    return manager.create_etl_pipeline(financial_pipeline)
```

## DevOps Integration Patterns

### Infrastructure as Code (Terraform)

```hcl
# datapipeline_infrastructure.tf
resource "aws_data_pipeline_pipeline" "etl_pipeline" {
  name = "enterprise-etl-pipeline"
  description = "Enterprise ETL pipeline for data processing"
  
  tags = {
    Environment = var.environment
    Purpose     = "ETL"
    Owner       = "data-engineering"
  }
}

resource "aws_iam_role" "datapipeline_role" {
  name = "DataPipelineRole"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "datapipeline.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "datapipeline_policy" {
  name = "DataPipelineExecutionPolicy"
  role = aws_iam_role.datapipeline_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket",
          "emr:CreateCluster",
          "emr:TerminateCluster",
          "emr:AddJobFlowSteps",
          "rds:CreateDBSnapshot",
          "redshift:CopyClusterSnapshot"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_sns_topic" "pipeline_alerts" {
  name = "datapipeline-alerts"
  
  tags = {
    Purpose = "DataPipeline-Alerts"
  }
}

resource "aws_cloudwatch_log_group" "pipeline_logs" {
  name              = "/aws/datapipeline/enterprise"
  retention_in_days = 30
  
  tags = {
    Environment = var.environment
    Application = "DataPipeline"
  }
}
```

### CI/CD Pipeline Integration

```yaml
# .github/workflows/datapipeline-deployment.yml
name: Data Pipeline Deployment

on:
  push:
    branches: [main]
    paths: ['pipelines/**']
  workflow_dispatch:
    inputs:
      pipeline_environment:
        description: 'Environment to deploy'
        required: true
        type: choice
        options:
          - development
          - staging
          - production

jobs:
  validate-pipeline:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Validate Pipeline Definition
      run: |
        python scripts/validate_pipeline.py \
          --pipeline-config pipelines/config/ \
          --environment ${{ github.event.inputs.pipeline_environment || 'development' }}

  deploy-pipeline:
    needs: validate-pipeline
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        role-to-assume: ${{ secrets.AWS_DATAPIPELINE_ROLE }}
        aws-region: us-east-1
    
    - name: Deploy Data Pipeline
      run: |
        python scripts/deploy_pipeline.py \
          --config-file pipelines/config/etl-pipeline.json \
          --environment ${{ github.event.inputs.pipeline_environment || 'development' }} \
          --auto-activate
    
    - name: Run Pipeline Tests
      run: |
        python scripts/test_pipeline.py \
          --pipeline-id ${{ env.PIPELINE_ID }} \
          --test-data-location s3://test-data/samples/
```

## Practical Use Cases

### 1. Data Warehouse ETL
- **Daily sales data processing** with automated transformation
- **Customer data synchronization** across multiple systems
- **Financial reporting automation** with regulatory compliance
- **Inventory management** with real-time updates

### 2. Analytics Data Preparation
- **Web log analysis** for user behavior insights
- **Marketing campaign effectiveness** measurement
- **Customer segmentation** based on transaction patterns
- **Business intelligence** dashboard data preparation

### 3. Machine Learning Pipelines
- **Feature engineering** for ML model training
- **Data quality validation** and cleansing
- **Model training data** preparation and versioning
- **Prediction result** processing and storage

### 4. Compliance and Auditing
- **Regulatory reporting** automation
- **Data lineage tracking** for audit trails
- **Data retention policy** enforcement
- **Security compliance** monitoring

### 5. Real-time Data Processing
- **Event-driven ETL** triggered by data arrival
- **Stream processing** with batch components
- **IoT data aggregation** and analysis
- **Fraud detection** pipeline automation

## Cost Optimization Strategies

- **Spot instances for EMR clusters** to reduce compute costs
- **S3 lifecycle policies** for automated data archiving
- **Right-sizing resources** based on workload requirements
- **Schedule optimization** to avoid peak usage periods
- **Data compression** and format optimization
- **Incremental processing** to minimize data movement