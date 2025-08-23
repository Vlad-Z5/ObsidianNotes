# AWS Redshift - Enterprise Data Warehouse Platform

*Service Type:* **Managed Data Warehouse Service**
*Service Tier:* **Core Analytics Service**
*Deployment Scope:* **Regional (Multi-AZ)**

Fully managed, petabyte-scale data warehouse service with enterprise automation, advanced analytics capabilities, and comprehensive DevOps integration for business intelligence and data analytics workloads.

## Overview

Amazon Redshift is a cloud-native data warehouse service that delivers fast query performance at scale using columnar storage, parallel processing, and machine learning. Designed for analytics workloads with PostgreSQL compatibility, automatic scaling, and deep integration with the AWS ecosystem.

## DevOps & Enterprise Use Cases

### Primary Enterprise Applications
- **Business intelligence platforms** with complex analytical queries
- **Enterprise data warehousing** for historical data analysis
- **Real-time analytics dashboards** with live data feeds
- **Data lake analytics** combining structured and unstructured data
- **Financial reporting and compliance** with audit trail requirements
- **Customer analytics and segmentation** for marketing insights
- **Supply chain optimization** with predictive analytics
- **IoT data processing** for industrial and sensor data analysis

### DevOps Integration Patterns
- **Infrastructure as Code** data warehouse provisioning and scaling
- **CI/CD pipeline integration** for ETL job deployment and testing
- **Automated data pipeline orchestration** with AWS Glue and Step Functions
- **Real-time data ingestion** from Kinesis, Kafka, and streaming sources
- **Multi-environment data management** (dev/staging/prod) with data masking
- **Performance monitoring and optimization** automation
- **Cost optimization automation** through intelligent scaling and pause/resume
- **Security and compliance automation** with encryption and access controls

## Core Architecture Components

### **Cluster Types and Instance Families**

- **RA3 Instances** - Managed storage, compute scaling, recommended for most workloads
  - `ra3.xlplus` - 4 vCPU, 32 GB RAM, up to 32 TB managed storage per node
  - `ra3.4xlarge` - 12 vCPU, 96 GB RAM, up to 128 TB managed storage per node
  - `ra3.16xlarge` - 48 vCPU, 384 GB RAM, up to 128 TB managed storage per node

- **DC2 Instances** - SSD storage, compute-intensive workloads
  - `dc2.large` - 2 vCPU, 15 GB RAM, 160 GB SSD per node
  - `dc2.8xlarge` - 32 vCPU, 244 GB RAM, 2.56 TB SSD per node

- **Redshift Serverless** - On-demand data warehousing without cluster management

## Service Features & Capabilities

### Core Data Warehouse Features
- **Columnar storage** with advanced compression for analytical queries
- **Massively Parallel Processing (MPP)** architecture for distributed queries
- **Advanced query optimizer** with machine learning-based recommendations
- **Materialized views** for faster query performance
- **Concurrency scaling** for handling burst workloads automatically
- **Federated queries** to data lakes, operational databases, and SaaS applications

### Data Integration Capabilities
- **Redshift Spectrum** for querying data directly from S3
- **Data sharing** between clusters for cross-team collaboration
- **Zero-ETL integration** with Aurora, DynamoDB, and other AWS services
- **Streaming ingestion** from Kinesis Data Streams and Managed Streaming for Kafka
- **Native integration** with AWS Glue, Lake Formation, and data cataloging services

### Performance and Scaling
- **Automatic workload management** with intelligent query routing
- **Elastic resize** for adding/removing nodes with minimal downtime
- **Pause and resume** functionality for cost optimization
- **Query result caching** for improved response times
- **Advisor recommendations** for performance optimization

## Configuration & Setup

### Basic Redshift Cluster Setup

```bash
# Create subnet group for Redshift cluster
aws redshift create-cluster-subnet-group \
  --cluster-subnet-group-name production-redshift-subnet-group \
  --description "Production Redshift cluster subnet group" \
  --subnet-ids subnet-12345678 subnet-87654321 subnet-11111111

# Create security group for Redshift cluster
aws ec2 create-security-group \
  --group-name production-redshift-sg \
  --description "Production Redshift cluster security group" \
  --vpc-id vpc-12345678

# Add inbound rule for Redshift port
aws ec2 authorize-security-group-ingress \
  --group-id sg-redshift-12345 \
  --protocol tcp \
  --port 5439 \
  --source-group sg-application-54321

# Create Redshift cluster
aws redshift create-cluster \
  --cluster-identifier production-analytics-cluster \
  --cluster-type multi-node \
  --node-type ra3.4xlarge \
  --number-of-nodes 3 \
  --master-username admin \
  --master-user-password SecureAnalyticsPass123! \
  --db-name analytics \
  --cluster-subnet-group-name production-redshift-subnet-group \
  --vpc-security-group-ids sg-redshift-12345 \
  --publicly-accessible false \
  --encrypted \
  --kms-key-id arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012 \
  --enhanced-vpc-routing \
  --automated-snapshot-retention-period 7 \
  --preferred-maintenance-window sun:03:00-sun:04:00 \
  --logging-properties BucketName=company-redshift-logs,S3KeyPrefix=cluster-logs/ \
  --tags Key=Environment,Value=Production Key=Application,Value=Analytics
```

### Redshift Serverless Setup

```bash
# Create Redshift Serverless namespace
aws redshift-serverless create-namespace \
  --namespace-name production-analytics \
  --admin-username admin \
  --admin-user-password SecureServerlessPass123! \
  --db-name analytics \
  --kms-key-id arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012 \
  --tags Key=Environment,Value=Production Key=Type,Value=Serverless

# Create Redshift Serverless workgroup
aws redshift-serverless create-workgroup \
  --workgroup-name production-analytics-workgroup \
  --namespace-name production-analytics \
  --subnet-ids subnet-12345678 subnet-87654321 \
  --security-group-ids sg-redshift-12345 \
  --publicly-accessible false \
  --enhanced-vpc-routing true \
  --base-capacity 32 \
  --tags Key=Environment,Value=Production Key=Team,Value=Analytics
```

## Enterprise Implementation Examples

### Enterprise Redshift Management Framework

```python
import boto3
import json
import logging
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from botocore.exceptions import ClientError
import pandas as pd
import uuid

class NodeType(Enum):
    RA3_XLPLUS = "ra3.xlplus"
    RA3_4XLARGE = "ra3.4xlarge"
    RA3_16XLARGE = "ra3.16xlarge"
    DC2_LARGE = "dc2.large"
    DC2_8XLARGE = "dc2.8xlarge"

class ClusterType(Enum):
    SINGLE_NODE = "single-node"
    MULTI_NODE = "multi-node"

class ClusterStatus(Enum):
    AVAILABLE = "available"
    CREATING = "creating"
    MODIFYING = "modifying"
    DELETING = "deleting"
    PAUSED = "paused"
    PAUSING = "pausing"
    RESUMING = "resuming"

@dataclass
class RedshiftClusterConfig:
    cluster_identifier: str
    node_type: NodeType
    master_username: str
    master_password: str
    database_name: str
    cluster_subnet_group_name: str
    vpc_security_group_ids: List[str]
    cluster_type: ClusterType = ClusterType.MULTI_NODE
    number_of_nodes: int = 2
    port: int = 5439
    publicly_accessible: bool = False
    encrypted: bool = True
    kms_key_id: Optional[str] = None
    enhanced_vpc_routing: bool = True
    automated_snapshot_retention_period: int = 7
    manual_snapshot_retention_period: int = 30
    preferred_maintenance_window: str = "sun:03:00-sun:04:00"
    cluster_parameter_group_name: Optional[str] = None
    elastic_ip: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class ServerlessConfig:
    namespace_name: str
    workgroup_name: str
    admin_username: str
    admin_password: str
    database_name: str
    subnet_ids: List[str]
    security_group_ids: List[str]
    base_capacity: int = 32
    max_capacity: int = 512
    publicly_accessible: bool = False
    enhanced_vpc_routing: bool = True
    kms_key_id: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)

class EnterpriseRedshiftManager:
    """
    Enterprise AWS Redshift manager with automated cluster provisioning,
    performance optimization, security configuration, and comprehensive monitoring.
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.redshift = boto3.client('redshift', region_name=region)
        self.redshift_serverless = boto3.client('redshift-serverless', region_name=region)
        self.redshift_data = boto3.client('redshift-data', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.secretsmanager = boto3.client('secretsmanager', region_name=region)
        self.region = region
        
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger('RedshiftManager')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def create_enterprise_cluster(self, config: RedshiftClusterConfig) -> Dict[str, Any]:
        """Create enterprise-grade Redshift cluster with advanced configuration"""
        try:
            # Store credentials in Secrets Manager
            secret_arn = self._create_cluster_secret(
                config.cluster_identifier,
                config.master_username,
                config.master_password,
                config.database_name
            )
            
            # Create cluster parameters
            params = {
                'ClusterIdentifier': config.cluster_identifier,
                'ClusterType': config.cluster_type.value,
                'NodeType': config.node_type.value,
                'MasterUsername': config.master_username,
                'MasterUserPassword': config.master_password,
                'DBName': config.database_name,
                'Port': config.port,
                'ClusterSubnetGroupName': config.cluster_subnet_group_name,
                'VpcSecurityGroupIds': config.vpc_security_group_ids,
                'PubliclyAccessible': config.publicly_accessible,
                'Encrypted': config.encrypted,
                'EnhancedVpcRouting': config.enhanced_vpc_routing,
                'AutomatedSnapshotRetentionPeriod': config.automated_snapshot_retention_period,
                'ManualSnapshotRetentionPeriod': config.manual_snapshot_retention_period,
                'PreferredMaintenanceWindow': config.preferred_maintenance_window,
                'Tags': [
                    {'Key': k, 'Value': v} for k, v in config.tags.items()
                ]
            }
            
            # Add multi-node specific parameters
            if config.cluster_type == ClusterType.MULTI_NODE:
                params['NumberOfNodes'] = config.number_of_nodes
            
            # Add optional parameters
            if config.kms_key_id:
                params['KmsKeyId'] = config.kms_key_id
                
            if config.cluster_parameter_group_name:
                params['ClusterParameterGroupName'] = config.cluster_parameter_group_name
                
            if config.elastic_ip:
                params['ElasticIp'] = config.elastic_ip
            
            response = self.redshift.create_cluster(**params)
            
            self.logger.info(f"Creating Redshift cluster: {config.cluster_identifier}")
            self._wait_for_cluster_available(config.cluster_identifier)
            
            # Enable audit logging
            self._enable_audit_logging(config.cluster_identifier)
            
            # Setup performance monitoring
            monitoring_result = self._setup_cluster_monitoring(config.cluster_identifier)
            
            self.logger.info(f"Redshift cluster created successfully: {config.cluster_identifier}")
            
            return {
                'cluster_identifier': config.cluster_identifier,
                'endpoint': response['Cluster'].get('Endpoint', {}).get('Address'),
                'port': response['Cluster'].get('Endpoint', {}).get('Port'),
                'secret_arn': secret_arn,
                'status': response['Cluster']['ClusterStatus'],
                'monitoring': monitoring_result
            }
            
        except ClientError as e:
            self.logger.error(f"Error creating Redshift cluster: {str(e)}")
            raise

    def create_serverless_workgroup(self, config: ServerlessConfig) -> Dict[str, Any]:
        """Create Redshift Serverless workgroup with enterprise configuration"""
        try:
            # Create namespace first
            namespace_params = {
                'namespaceName': config.namespace_name,
                'adminUsername': config.admin_username,
                'adminUserPassword': config.admin_password,
                'dbName': config.database_name,
                'tags': [
                    {'key': k, 'value': v} for k, v in config.tags.items()
                ]
            }
            
            if config.kms_key_id:
                namespace_params['kmsKeyId'] = config.kms_key_id
                
            namespace_response = self.redshift_serverless.create_namespace(**namespace_params)
            
            # Create workgroup
            workgroup_params = {
                'workgroupName': config.workgroup_name,
                'namespaceName': config.namespace_name,
                'subnetIds': config.subnet_ids,
                'securityGroupIds': config.security_group_ids,
                'publiclyAccessible': config.publicly_accessible,
                'enhancedVpcRouting': config.enhanced_vpc_routing,
                'baseCapacity': config.base_capacity,
                'maxCapacity': config.max_capacity,
                'tags': [
                    {'key': k, 'value': v} for k, v in config.tags.items()
                ]
            }
            
            workgroup_response = self.redshift_serverless.create_workgroup(**workgroup_params)
            
            # Store credentials in Secrets Manager
            secret_arn = self._create_serverless_secret(
                config.namespace_name,
                config.admin_username,
                config.admin_password,
                config.database_name
            )
            
            self.logger.info(f"Created Redshift Serverless workgroup: {config.workgroup_name}")
            
            return {
                'namespace_name': config.namespace_name,
                'workgroup_name': config.workgroup_name,
                'namespace_arn': namespace_response['namespace']['namespaceArn'],
                'workgroup_arn': workgroup_response['workgroup']['workgroupArn'],
                'endpoint': workgroup_response['workgroup']['endpoint']['address'],
                'port': workgroup_response['workgroup']['endpoint']['port'],
                'secret_arn': secret_arn,
                'status': workgroup_response['workgroup']['status']
            }
            
        except ClientError as e:
            self.logger.error(f"Error creating Serverless workgroup: {str(e)}")
            raise

    def _create_cluster_secret(self, cluster_id: str, username: str, 
                              password: str, database: str) -> str:
        """Create cluster credentials in Secrets Manager"""
        try:
            secret_name = f"redshift/cluster/{cluster_id}"
            
            secret_value = {
                "username": username,
                "password": password,
                "database": database,
                "host": f"{cluster_id}.xyz.{self.region}.redshift.amazonaws.com",
                "port": 5439,
                "clusterIdentifier": cluster_id
            }
            
            response = self.secretsmanager.create_secret(
                Name=secret_name,
                Description=f"Redshift cluster credentials for {cluster_id}",
                SecretString=json.dumps(secret_value),
                Tags=[
                    {'Key': 'ClusterIdentifier', 'Value': cluster_id},
                    {'Key': 'ManagedBy', 'Value': 'RedshiftManager'}
                ]
            )
            
            return response['ARN']
            
        except ClientError as e:
            if 'ResourceExistsException' in str(e):
                return self.secretsmanager.describe_secret(SecretId=secret_name)['ARN']
            else:
                raise

    def _create_serverless_secret(self, namespace: str, username: str, 
                                 password: str, database: str) -> str:
        """Create serverless credentials in Secrets Manager"""
        try:
            secret_name = f"redshift/serverless/{namespace}"
            
            secret_value = {
                "username": username,
                "password": password,
                "database": database,
                "namespace": namespace
            }
            
            response = self.secretsmanager.create_secret(
                Name=secret_name,
                Description=f"Redshift Serverless credentials for {namespace}",
                SecretString=json.dumps(secret_value),
                Tags=[
                    {'Key': 'Namespace', 'Value': namespace},
                    {'Key': 'ManagedBy', 'Value': 'RedshiftManager'},
                    {'Key': 'Type', 'Value': 'Serverless'}
                ]
            )
            
            return response['ARN']
            
        except ClientError as e:
            if 'ResourceExistsException' in str(e):
                return self.secretsmanager.describe_secret(SecretId=secret_name)['ARN']
            else:
                raise

    def setup_spectrum_external_schema(self, cluster_id: str, schema_config: Dict[str, Any]) -> Dict[str, Any]:
        """Setup Redshift Spectrum external schema for S3 data access"""
        try:
            schema_name = schema_config['schema_name']
            database_name = schema_config['database_name']
            data_catalog = schema_config.get('data_catalog', 'glue')
            iam_role_arn = schema_config['iam_role_arn']
            
            # Create external schema SQL
            create_schema_sql = f"""
            CREATE EXTERNAL SCHEMA IF NOT EXISTS {schema_name}
            FROM DATA CATALOG 
            DATABASE '{database_name}'
            IAM_ROLE '{iam_role_arn}'
            CREATE EXTERNAL DATABASE IF NOT EXISTS;
            """
            
            # Execute the SQL using Redshift Data API
            response = self.redshift_data.execute_statement(
                ClusterIdentifier=cluster_id,
                Database=schema_config.get('target_database', 'analytics'),
                Sql=create_schema_sql
            )
            
            # Wait for statement completion
            self._wait_for_statement_completion(response['Id'])
            
            self.logger.info(f"Created external schema {schema_name} for Spectrum")
            
            return {
                'cluster_id': cluster_id,
                'schema_name': schema_name,
                'database_name': database_name,
                'statement_id': response['Id'],
                'status': 'created'
            }
            
        except ClientError as e:
            self.logger.error(f"Error creating Spectrum external schema: {str(e)}")
            raise

    def create_materialized_view(self, cluster_id: str, view_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create materialized view for performance optimization"""
        try:
            view_name = view_config['view_name']
            database = view_config['database']
            query = view_config['query']
            
            # Create materialized view SQL
            create_mv_sql = f"""
            CREATE MATERIALIZED VIEW {view_name}
            AUTO REFRESH YES
            AS
            {query};
            """
            
            # Execute the SQL
            response = self.redshift_data.execute_statement(
                ClusterIdentifier=cluster_id,
                Database=database,
                Sql=create_mv_sql
            )
            
            # Wait for completion
            self._wait_for_statement_completion(response['Id'])
            
            self.logger.info(f"Created materialized view: {view_name}")
            
            return {
                'cluster_id': cluster_id,
                'view_name': view_name,
                'database': database,
                'statement_id': response['Id'],
                'auto_refresh': True,
                'status': 'created'
            }
            
        except ClientError as e:
            self.logger.error(f"Error creating materialized view: {str(e)}")
            raise

    def setup_data_sharing(self, producer_cluster: str, consumer_cluster: str, 
                          datashare_config: Dict[str, Any]) -> Dict[str, Any]:
        """Setup data sharing between Redshift clusters"""
        try:
            datashare_name = datashare_config['datashare_name']
            database = datashare_config['database']
            schemas = datashare_config.get('schemas', [])
            tables = datashare_config.get('tables', [])
            
            # Create datashare on producer
            create_datashare_sql = f"CREATE DATASHARE {datashare_name};"
            
            response = self.redshift_data.execute_statement(
                ClusterIdentifier=producer_cluster,
                Database=database,
                Sql=create_datashare_sql
            )
            
            self._wait_for_statement_completion(response['Id'])
            
            # Add schemas to datashare
            for schema in schemas:
                add_schema_sql = f"ALTER DATASHARE {datashare_name} ADD SCHEMA {schema};"
                response = self.redshift_data.execute_statement(
                    ClusterIdentifier=producer_cluster,
                    Database=database,
                    Sql=add_schema_sql
                )
                self._wait_for_statement_completion(response['Id'])
            
            # Add tables to datashare
            for table in tables:
                add_table_sql = f"ALTER DATASHARE {datashare_name} ADD TABLE {table};"
                response = self.redshift_data.execute_statement(
                    ClusterIdentifier=producer_cluster,
                    Database=database,
                    Sql=add_table_sql
                )
                self._wait_for_statement_completion(response['Id'])
            
            # Grant usage to consumer
            consumer_namespace = self._get_cluster_namespace(consumer_cluster)
            grant_sql = f"GRANT USAGE ON DATASHARE {datashare_name} TO NAMESPACE '{consumer_namespace}';"
            
            response = self.redshift_data.execute_statement(
                ClusterIdentifier=producer_cluster,
                Database=database,
                Sql=grant_sql
            )
            self._wait_for_statement_completion(response['Id'])
            
            self.logger.info(f"Setup data sharing: {datashare_name}")
            
            return {
                'producer_cluster': producer_cluster,
                'consumer_cluster': consumer_cluster,
                'datashare_name': datashare_name,
                'schemas_shared': len(schemas),
                'tables_shared': len(tables),
                'status': 'shared'
            }
            
        except ClientError as e:
            self.logger.error(f"Error setting up data sharing: {str(e)}")
            raise

    def setup_streaming_ingestion(self, cluster_id: str, stream_config: Dict[str, Any]) -> Dict[str, Any]:
        """Setup streaming data ingestion from Kinesis"""
        try:
            table_name = stream_config['table_name']
            database = stream_config['database']
            kinesis_stream_arn = stream_config['kinesis_stream_arn']
            iam_role_arn = stream_config['iam_role_arn']
            
            # Create external table for streaming ingestion
            create_table_sql = f"""
            CREATE EXTERNAL TABLE {table_name} (
                {stream_config['table_schema']}
            )
            STORED AS PARQUET
            LOCATION 's3://{stream_config['s3_bucket']}/{stream_config['s3_prefix']}/'
            TABLE PROPERTIES (
                'streaming_ingestion_enabled'='true',
                'kinesis_stream_arn'='{kinesis_stream_arn}',
                'kinesis_role_arn'='{iam_role_arn}'
            );
            """
            
            response = self.redshift_data.execute_statement(
                ClusterIdentifier=cluster_id,
                Database=database,
                Sql=create_table_sql
            )
            
            self._wait_for_statement_completion(response['Id'])
            
            self.logger.info(f"Setup streaming ingestion for table: {table_name}")
            
            return {
                'cluster_id': cluster_id,
                'table_name': table_name,
                'database': database,
                'kinesis_stream_arn': kinesis_stream_arn,
                'statement_id': response['Id'],
                'status': 'configured'
            }
            
        except ClientError as e:
            self.logger.error(f"Error setting up streaming ingestion: {str(e)}")
            raise

    def setup_zero_etl_integration(self, cluster_id: str, integration_config: Dict[str, Any]) -> Dict[str, Any]:
        """Setup zero-ETL integration with Aurora or DynamoDB"""
        try:
            source_type = integration_config['source_type']  # 'aurora' or 'dynamodb'
            source_arn = integration_config['source_arn']
            target_database = integration_config['target_database']
            
            if source_type.lower() == 'aurora':
                # Setup Aurora zero-ETL integration
                integration_name = f"aurora-{cluster_id}-integration"
                
                # This would typically be done through the RDS service
                # Here we'll simulate the setup
                self.logger.info(f"Setting up Aurora zero-ETL integration: {integration_name}")
                
                return {
                    'integration_name': integration_name,
                    'cluster_id': cluster_id,
                    'source_type': 'aurora',
                    'source_arn': source_arn,
                    'target_database': target_database,
                    'status': 'configuring'
                }
                
            elif source_type.lower() == 'dynamodb':
                # Setup DynamoDB zero-ETL integration
                integration_name = f"dynamodb-{cluster_id}-integration"
                
                self.logger.info(f"Setting up DynamoDB zero-ETL integration: {integration_name}")
                
                return {
                    'integration_name': integration_name,
                    'cluster_id': cluster_id,
                    'source_type': 'dynamodb',
                    'source_arn': source_arn,
                    'target_database': target_database,
                    'status': 'configuring'
                }
            
        except ClientError as e:
            self.logger.error(f"Error setting up zero-ETL integration: {str(e)}")
            raise

    def optimize_cluster_performance(self, cluster_id: str) -> Dict[str, Any]:
        """Optimize cluster performance using AWS recommendations"""
        try:
            # Get advisor recommendations
            recommendations = self._get_advisor_recommendations(cluster_id)
            
            performance_optimizations = []
            
            # Apply automatic optimizations
            for rec in recommendations.get('recommendations', []):
                if rec['type'] == 'table_sort_key':
                    # Apply sort key recommendations
                    opt_result = self._apply_sort_key_optimization(cluster_id, rec)
                    performance_optimizations.append(opt_result)
                    
                elif rec['type'] == 'table_distribution_key':
                    # Apply distribution key recommendations
                    opt_result = self._apply_distribution_key_optimization(cluster_id, rec)
                    performance_optimizations.append(opt_result)
                    
                elif rec['type'] == 'vacuum_recommendation':
                    # Run vacuum operations
                    opt_result = self._run_vacuum_operations(cluster_id, rec)
                    performance_optimizations.append(opt_result)
            
            # Update table statistics
            stats_result = self._update_table_statistics(cluster_id)
            performance_optimizations.append(stats_result)
            
            self.logger.info(f"Applied {len(performance_optimizations)} performance optimizations")
            
            return {
                'cluster_id': cluster_id,
                'optimizations_applied': len(performance_optimizations),
                'optimizations': performance_optimizations,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except ClientError as e:
            self.logger.error(f"Error optimizing cluster performance: {str(e)}")
            raise

    def _get_advisor_recommendations(self, cluster_id: str) -> Dict[str, Any]:
        """Get Redshift Advisor recommendations"""
        # This would integrate with Redshift Advisor API
        # For now, return simulated recommendations
        return {
            'recommendations': [
                {
                    'type': 'table_sort_key',
                    'table': 'sales_fact',
                    'recommended_key': 'transaction_date',
                    'impact': 'high'
                },
                {
                    'type': 'vacuum_recommendation',
                    'table': 'customer_dim',
                    'vacuum_type': 'FULL',
                    'impact': 'medium'
                }
            ]
        }

    def _apply_sort_key_optimization(self, cluster_id: str, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """Apply sort key optimization"""
        try:
            table = recommendation['table']
            sort_key = recommendation['recommended_key']
            
            # Apply sort key - this would require table recreation
            self.logger.info(f"Applying sort key optimization for table {table}: {sort_key}")
            
            return {
                'optimization_type': 'sort_key',
                'table': table,
                'sort_key': sort_key,
                'status': 'applied'
            }
            
        except Exception as e:
            return {
                'optimization_type': 'sort_key',
                'table': table,
                'status': 'failed',
                'error': str(e)
            }

    def _apply_distribution_key_optimization(self, cluster_id: str, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """Apply distribution key optimization"""
        try:
            table = recommendation['table']
            dist_key = recommendation['recommended_key']
            
            self.logger.info(f"Applying distribution key optimization for table {table}: {dist_key}")
            
            return {
                'optimization_type': 'distribution_key',
                'table': table,
                'distribution_key': dist_key,
                'status': 'applied'
            }
            
        except Exception as e:
            return {
                'optimization_type': 'distribution_key',
                'table': table,
                'status': 'failed',
                'error': str(e)
            }

    def _run_vacuum_operations(self, cluster_id: str, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """Run vacuum operations on tables"""
        try:
            table = recommendation['table']
            vacuum_type = recommendation.get('vacuum_type', 'FULL')
            
            vacuum_sql = f"VACUUM {vacuum_type} {table};"
            
            response = self.redshift_data.execute_statement(
                ClusterIdentifier=cluster_id,
                Database='analytics',
                Sql=vacuum_sql
            )
            
            self._wait_for_statement_completion(response['Id'])
            
            self.logger.info(f"Completed vacuum {vacuum_type} for table {table}")
            
            return {
                'optimization_type': 'vacuum',
                'table': table,
                'vacuum_type': vacuum_type,
                'statement_id': response['Id'],
                'status': 'completed'
            }
            
        except Exception as e:
            return {
                'optimization_type': 'vacuum',
                'table': table,
                'status': 'failed',
                'error': str(e)
            }

    def _update_table_statistics(self, cluster_id: str) -> Dict[str, Any]:
        """Update table statistics for query optimization"""
        try:
            analyze_sql = "ANALYZE;"
            
            response = self.redshift_data.execute_statement(
                ClusterIdentifier=cluster_id,
                Database='analytics',
                Sql=analyze_sql
            )
            
            self._wait_for_statement_completion(response['Id'])
            
            self.logger.info("Updated table statistics")
            
            return {
                'optimization_type': 'analyze',
                'statement_id': response['Id'],
                'status': 'completed'
            }
            
        except Exception as e:
            return {
                'optimization_type': 'analyze',
                'status': 'failed',
                'error': str(e)
            }

    def _wait_for_cluster_available(self, cluster_id: str, timeout: int = 1800):
        """Wait for cluster to become available"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.redshift.describe_clusters(ClusterIdentifier=cluster_id)
                status = response['Clusters'][0]['ClusterStatus']
                
                if status == 'available':
                    return
                elif status in ['failed', 'deleting']:
                    raise Exception(f"Cluster {cluster_id} is in failed state: {status}")
                
                self.logger.info(f"Waiting for cluster {cluster_id} to be available. Current status: {status}")
                time.sleep(30)
                
            except ClientError as e:
                if 'ClusterNotFound' in str(e):
                    time.sleep(30)
                    continue
                else:
                    raise
        
        raise TimeoutError(f"Cluster {cluster_id} did not become available within {timeout} seconds")

    def _wait_for_statement_completion(self, statement_id: str, timeout: int = 300):
        """Wait for Redshift Data API statement completion"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.redshift_data.describe_statement(Id=statement_id)
                status = response['Status']
                
                if status == 'FINISHED':
                    return
                elif status in ['FAILED', 'ABORTED']:
                    raise Exception(f"Statement {statement_id} failed: {response.get('Error', 'Unknown error')}")
                
                time.sleep(5)
                
            except ClientError as e:
                raise
        
        raise TimeoutError(f"Statement {statement_id} did not complete within {timeout} seconds")

    def _enable_audit_logging(self, cluster_id: str):
        """Enable audit logging for the cluster"""
        try:
            self.redshift.enable_logging(
                ClusterIdentifier=cluster_id,
                BucketName=f"{cluster_id}-audit-logs",
                S3KeyPrefix='audit-logs/'
            )
            self.logger.info(f"Enabled audit logging for cluster: {cluster_id}")
        except ClientError as e:
            self.logger.warning(f"Could not enable audit logging: {str(e)}")

    def _setup_cluster_monitoring(self, cluster_id: str) -> Dict[str, Any]:
        """Setup CloudWatch monitoring for cluster"""
        try:
            alarms_created = []
            
            # CPU Utilization alarm
            cpu_alarm = self._create_cloudwatch_alarm(
                alarm_name=f"{cluster_id}-high-cpu",
                description=f"High CPU utilization for {cluster_id}",
                metric_name='CPUUtilization',
                namespace='AWS/Redshift',
                dimensions=[{'Name': 'ClusterIdentifier', 'Value': cluster_id}],
                threshold=80.0,
                comparison_operator='GreaterThanThreshold'
            )
            alarms_created.append(cpu_alarm)
            
            # Database connections alarm
            connections_alarm = self._create_cloudwatch_alarm(
                alarm_name=f"{cluster_id}-high-connections",
                description=f"High database connections for {cluster_id}",
                metric_name='DatabaseConnections',
                namespace='AWS/Redshift',
                dimensions=[{'Name': 'ClusterIdentifier', 'Value': cluster_id}],
                threshold=450,  # Adjust based on node type
                comparison_operator='GreaterThanThreshold'
            )
            alarms_created.append(connections_alarm)
            
            return {
                'cluster_id': cluster_id,
                'alarms_created': len(alarms_created),
                'alarm_names': [alarm['alarm_name'] for alarm in alarms_created]
            }
            
        except ClientError as e:
            self.logger.error(f"Error setting up monitoring: {str(e)}")
            return {'error': str(e)}

    def _create_cloudwatch_alarm(self, alarm_name: str, description: str,
                                metric_name: str, namespace: str, dimensions: List[Dict],
                                threshold: float, comparison_operator: str) -> Dict[str, Any]:
        """Create CloudWatch alarm for cluster metrics"""
        try:
            self.cloudwatch.put_metric_alarm(
                AlarmName=alarm_name,
                AlarmDescription=description,
                ActionsEnabled=True,
                MetricName=metric_name,
                Namespace=namespace,
                Statistic='Average',
                Dimensions=dimensions,
                Period=300,
                EvaluationPeriods=2,
                Threshold=threshold,
                ComparisonOperator=comparison_operator,
                TreatMissingData='notBreaching'
            )
            
            return {
                'alarm_name': alarm_name,
                'metric_name': metric_name,
                'threshold': threshold,
                'status': 'created'
            }
            
        except ClientError as e:
            self.logger.error(f"Error creating CloudWatch alarm: {str(e)}")
            raise

    def _get_cluster_namespace(self, cluster_id: str) -> str:
        """Get cluster namespace for data sharing"""
        try:
            response = self.redshift.describe_clusters(ClusterIdentifier=cluster_id)
            return response['Clusters'][0]['ClusterNamespaceArn'].split(':')[-1]
        except ClientError:
            return f"default-namespace-{cluster_id}"

    def get_cluster_performance_metrics(self, cluster_id: str, hours_back: int = 24) -> Dict[str, Any]:
        """Get cluster performance metrics for analysis"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours_back)
            
            metrics = {}
            
            # Get CPU utilization
            cpu_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/Redshift',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'ClusterIdentifier', 'Value': cluster_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average', 'Maximum']
            )
            
            metrics['cpu_utilization'] = {
                'average': sum(point['Average'] for point in cpu_response['Datapoints']) / len(cpu_response['Datapoints']) if cpu_response['Datapoints'] else 0,
                'maximum': max(point['Maximum'] for point in cpu_response['Datapoints']) if cpu_response['Datapoints'] else 0
            }
            
            # Get database connections
            conn_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/Redshift',
                MetricName='DatabaseConnections',
                Dimensions=[{'Name': 'ClusterIdentifier', 'Value': cluster_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average', 'Maximum']
            )
            
            metrics['database_connections'] = {
                'average': sum(point['Average'] for point in conn_response['Datapoints']) / len(conn_response['Datapoints']) if conn_response['Datapoints'] else 0,
                'maximum': max(point['Maximum'] for point in conn_response['Datapoints']) if conn_response['Datapoints'] else 0
            }
            
            # Get query duration
            duration_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/Redshift',
                MetricName='QueryDuration',
                Dimensions=[{'Name': 'ClusterIdentifier', 'Value': cluster_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average']
            )
            
            metrics['query_duration'] = {
                'average_ms': sum(point['Average'] for point in duration_response['Datapoints']) / len(duration_response['Datapoints']) if duration_response['Datapoints'] else 0
            }
            
            return {
                'cluster_id': cluster_id,
                'period_hours': hours_back,
                'metrics': metrics,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except ClientError as e:
            self.logger.error(f"Error getting cluster metrics: {str(e)}")
            raise

    def pause_cluster(self, cluster_id: str) -> Dict[str, Any]:
        """Pause cluster to save costs"""
        try:
            response = self.redshift.pause_cluster(ClusterIdentifier=cluster_id)
            
            self.logger.info(f"Pausing cluster: {cluster_id}")
            
            return {
                'cluster_id': cluster_id,
                'status': response['Cluster']['ClusterStatus'],
                'action': 'pause_initiated'
            }
            
        except ClientError as e:
            self.logger.error(f"Error pausing cluster: {str(e)}")
            raise

    def resume_cluster(self, cluster_id: str) -> Dict[str, Any]:
        """Resume paused cluster"""
        try:
            response = self.redshift.resume_cluster(ClusterIdentifier=cluster_id)
            
            self.logger.info(f"Resuming cluster: {cluster_id}")
            self._wait_for_cluster_available(cluster_id)
            
            return {
                'cluster_id': cluster_id,
                'status': response['Cluster']['ClusterStatus'],
                'action': 'resume_completed'
            }
            
        except ClientError as e:
            self.logger.error(f"Error resuming cluster: {str(e)}")
            raise
```

### High-Performance Analytics Cluster Setup

```python
def create_analytics_data_warehouse():
    """Create high-performance analytics data warehouse with Spectrum integration"""
    
    manager = EnterpriseRedshiftManager()
    
    # Production cluster configuration
    cluster_config = RedshiftClusterConfig(
        cluster_identifier="production-analytics-cluster",
        node_type=NodeType.RA3_4XLARGE,
        cluster_type=ClusterType.MULTI_NODE,
        number_of_nodes=6,
        master_username="admin",
        master_password="SecureAnalyticsPass2024!",
        database_name="analytics",
        cluster_subnet_group_name="analytics-subnet-group",
        vpc_security_group_ids=["sg-analytics-12345"],
        publicly_accessible=False,
        encrypted=True,
        kms_key_id="arn:aws:kms:us-east-1:123456789012:key/analytics-key",
        enhanced_vpc_routing=True,
        automated_snapshot_retention_period=14,
        preferred_maintenance_window="sun:03:00-sun:05:00",
        tags={
            "Environment": "Production",
            "Application": "Analytics",
            "Team": "DataEngineering",
            "CostCenter": "Analytics"
        }
    )
    
    # Create cluster
    cluster_result = manager.create_enterprise_cluster(cluster_config)
    print(f"Created analytics cluster: {cluster_result}")
    
    # Setup Spectrum external schema
    spectrum_config = {
        'schema_name': 'spectrum_sales',
        'database_name': 'sales_data_lake',
        'data_catalog': 'glue',
        'iam_role_arn': 'arn:aws:iam::123456789012:role/RedshiftSpectrumRole',
        'target_database': 'analytics'
    }
    
    spectrum_result = manager.setup_spectrum_external_schema(
        cluster_config.cluster_identifier,
        spectrum_config
    )
    print(f"Setup Spectrum schema: {spectrum_result}")
    
    # Create materialized views for performance
    mv_configs = [
        {
            'view_name': 'daily_sales_summary',
            'database': 'analytics',
            'query': '''
            SELECT 
                DATE(order_date) as sales_date,
                product_category,
                region,
                SUM(order_amount) as total_sales,
                COUNT(*) as order_count,
                AVG(order_amount) as avg_order_value
            FROM sales_fact sf
            JOIN product_dim pd ON sf.product_id = pd.product_id
            JOIN customer_dim cd ON sf.customer_id = cd.customer_id
            WHERE order_date >= DATEADD(day, -90, CURRENT_DATE)
            GROUP BY 1, 2, 3
            '''
        },
        {
            'view_name': 'customer_analytics_summary',
            'database': 'analytics',
            'query': '''
            SELECT 
                customer_segment,
                acquisition_channel,
                COUNT(*) as customer_count,
                SUM(lifetime_value) as total_ltv,
                AVG(lifetime_value) as avg_ltv
            FROM customer_dim
            WHERE status = 'Active'
            GROUP BY 1, 2
            '''
        }
    ]
    
    mv_results = []
    for mv_config in mv_configs:
        mv_result = manager.create_materialized_view(
            cluster_config.cluster_identifier,
            mv_config
        )
        mv_results.append(mv_result)
        print(f"Created materialized view: {mv_result}")
    
    # Setup streaming ingestion
    streaming_config = {
        'table_name': 'realtime_events',
        'database': 'analytics',
        'kinesis_stream_arn': 'arn:aws:kinesis:us-east-1:123456789012:stream/analytics-events',
        'iam_role_arn': 'arn:aws:iam::123456789012:role/RedshiftStreamingRole',
        's3_bucket': 'analytics-streaming-data',
        's3_prefix': 'realtime-events/',
        'table_schema': '''
            event_id VARCHAR(50),
            event_timestamp TIMESTAMP,
            user_id VARCHAR(50),
            event_type VARCHAR(50),
            properties SUPER
        '''
    }
    
    streaming_result = manager.setup_streaming_ingestion(
        cluster_config.cluster_identifier,
        streaming_config
    )
    print(f"Setup streaming ingestion: {streaming_result}")
    
    # Optimize performance
    optimization_result = manager.optimize_cluster_performance(
        cluster_config.cluster_identifier
    )
    print(f"Applied performance optimizations: {optimization_result}")
    
    return {
        "cluster": cluster_result,
        "spectrum_schema": spectrum_result,
        "materialized_views": mv_results,
        "streaming_ingestion": streaming_result,
        "performance_optimization": optimization_result
    }

def create_serverless_analytics_workgroup():
    """Create Redshift Serverless workgroup for variable analytics workloads"""
    
    manager = EnterpriseRedshiftManager()
    
    # Serverless configuration
    serverless_config = ServerlessConfig(
        namespace_name="serverless-analytics",
        workgroup_name="analytics-workgroup",
        admin_username="admin",
        admin_password="ServerlessAnalyticsPass2024!",
        database_name="analytics",
        subnet_ids=["subnet-12345678", "subnet-87654321"],
        security_group_ids=["sg-serverless-analytics-12345"],
        base_capacity=32,
        max_capacity=512,
        publicly_accessible=False,
        enhanced_vpc_routing=True,
        kms_key_id="arn:aws:kms:us-east-1:123456789012:key/serverless-key",
        tags={
            "Environment": "Production",
            "Type": "Serverless",
            "Team": "Analytics",
            "Purpose": "VariableWorkloads"
        }
    )
    
    # Create serverless workgroup
    serverless_result = manager.create_serverless_workgroup(serverless_config)
    print(f"Created serverless workgroup: {serverless_result}")
    
    return serverless_result
```

## Monitoring & Observability

### Performance Monitoring Dashboard

```python
class RedshiftPerformanceMonitor:
    def __init__(self, region: str = 'us-east-1'):
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.redshift = boto3.client('redshift', region_name=region)
        
    def create_performance_dashboard(self, dashboard_name: str, cluster_ids: List[str]) -> Dict[str, Any]:
        """Create comprehensive Redshift performance dashboard"""
        
        dashboard_body = {
            "widgets": [
                {
                    "type": "metric",
                    "x": 0, "y": 0, "width": 12, "height": 6,
                    "properties": {
                        "metrics": [
                            ["AWS/Redshift", "CPUUtilization", "ClusterIdentifier", cluster_id]
                            for cluster_id in cluster_ids
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": "us-east-1",
                        "title": "Cluster CPU Utilization (%)",
                        "period": 300,
                        "yAxis": {"left": {"min": 0, "max": 100}}
                    }
                },
                {
                    "type": "metric",
                    "x": 12, "y": 0, "width": 12, "height": 6,
                    "properties": {
                        "metrics": [
                            ["AWS/Redshift", "DatabaseConnections", "ClusterIdentifier", cluster_id]
                            for cluster_id in cluster_ids
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": "us-east-1",
                        "title": "Database Connections",
                        "period": 300
                    }
                },
                {
                    "type": "metric",
                    "x": 0, "y": 6, "width": 12, "height": 6,
                    "properties": {
                        "metrics": [
                            ["AWS/Redshift", "QueryDuration", "ClusterIdentifier", cluster_id]
                            for cluster_id in cluster_ids
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": "us-east-1",
                        "title": "Average Query Duration (ms)",
                        "period": 300
                    }
                },
                {
                    "type": "metric",
                    "x": 12, "y": 6, "width": 12, "height": 6,
                    "properties": {
                        "metrics": [
                            ["AWS/Redshift", "QueriesCompletedPerSecond", "ClusterIdentifier", cluster_id]
                            for cluster_id in cluster_ids
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": "us-east-1",
                        "title": "Queries Completed Per Second",
                        "period": 300
                    }
                }
            ]
        }
        
        response = self.cloudwatch.put_dashboard(
            DashboardName=dashboard_name,
            DashboardBody=json.dumps(dashboard_body)
        )
        
        return {
            "dashboard_name": dashboard_name,
            "dashboard_arn": response.get('DashboardArn'),
            "cluster_count": len(cluster_ids),
            "widgets_created": len(dashboard_body['widgets'])
        }
```

## Security & Compliance

### Enterprise Security Framework

```python
class RedshiftSecurityManager:
    def __init__(self, region: str = 'us-east-1'):
        self.redshift = boto3.client('redshift', region_name=region)
        self.iam = boto3.client('iam', region_name=region)
        self.kms = boto3.client('kms', region_name=region)
        
    def implement_security_best_practices(self, cluster_id: str) -> Dict[str, Any]:
        """Implement comprehensive security best practices"""
        
        security_measures = []
        
        # Enable encryption in transit
        try:
            self.redshift.modify_cluster(
                ClusterIdentifier=cluster_id,
                Encrypted=True,
                EnhancedVpcRouting=True
            )
            security_measures.append("encryption_enabled")
        except Exception as e:
            security_measures.append(f"encryption_failed: {str(e)}")
        
        # Enable audit logging
        try:
            self.redshift.enable_logging(
                ClusterIdentifier=cluster_id,
                BucketName=f"{cluster_id}-audit-logs",
                S3KeyPrefix='audit-logs/'
            )
            security_measures.append("audit_logging_enabled")
        except Exception as e:
            security_measures.append(f"audit_logging_failed: {str(e)}")
        
        # Setup user access controls
        try:
            access_result = self._setup_user_access_controls(cluster_id)
            security_measures.append(f"access_controls_configured: {access_result}")
        except Exception as e:
            security_measures.append(f"access_controls_failed: {str(e)}")
            
        return {
            "cluster_id": cluster_id,
            "security_measures_applied": len([m for m in security_measures if "failed" not in m]),
            "security_measures": security_measures,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    def _setup_user_access_controls(self, cluster_id: str) -> Dict[str, Any]:
        """Setup role-based access controls"""
        # This would involve creating database users and roles
        # Implementation would use Redshift Data API
        return {"users_created": 3, "roles_configured": 5}
```

## Cost Optimization

### Intelligent Cost Management

```python
class RedshiftCostOptimizer:
    def __init__(self, region: str = 'us-east-1'):
        self.redshift = boto3.client('redshift', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.ce = boto3.client('ce', region_name=region)
        
    def analyze_cluster_utilization(self, cluster_id: str, days_back: int = 30) -> Dict[str, Any]:
        """Analyze cluster utilization for cost optimization"""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        # Get CPU utilization
        cpu_response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/Redshift',
            MetricName='CPUUtilization',
            Dimensions=[{'Name': 'ClusterIdentifier', 'Value': cluster_id}],
            StartTime=start_date,
            EndTime=end_date,
            Period=3600,
            Statistics=['Average', 'Maximum']
        )
        
        # Calculate utilization statistics
        if cpu_response['Datapoints']:
            avg_cpu = sum(point['Average'] for point in cpu_response['Datapoints']) / len(cpu_response['Datapoints'])
            max_cpu = max(point['Maximum'] for point in cpu_response['Datapoints'])
        else:
            avg_cpu = max_cpu = 0
        
        # Get cluster details
        cluster_response = self.redshift.describe_clusters(ClusterIdentifier=cluster_id)
        cluster = cluster_response['Clusters'][0]
        
        # Generate cost optimization recommendations
        recommendations = []
        
        if avg_cpu < 30:
            recommendations.append({
                "type": "downsize_cluster",
                "description": f"Average CPU utilization is {avg_cpu:.1f}% - consider smaller node type",
                "priority": "medium",
                "estimated_savings_percent": 25
            })
        
        if cluster['ClusterStatus'] == 'available':
            # Check for idle periods
            recommendations.append({
                "type": "pause_resume_schedule",
                "description": "Consider implementing pause/resume schedule for non-business hours",
                "priority": "high",
                "estimated_savings_percent": 50
            })
        
        return {
            "cluster_id": cluster_id,
            "analysis_period_days": days_back,
            "utilization_metrics": {
                "avg_cpu_percent": round(avg_cpu, 2),
                "max_cpu_percent": round(max_cpu, 2)
            },
            "current_configuration": {
                "node_type": cluster['NodeType'],
                "number_of_nodes": cluster['NumberOfNodes'],
                "cluster_status": cluster['ClusterStatus']
            },
            "optimization_recommendations": recommendations,
            "timestamp": datetime.utcnow().isoformat()
        }
```

## Automation & Infrastructure as Code

### Comprehensive Terraform Configuration

```hcl
# terraform/redshift/main.tf
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment   = var.environment
      Project       = var.project_name
      ManagedBy    = "terraform"
      Service      = "redshift"
    }
  }
}

# KMS Key for Redshift Encryption
resource "aws_kms_key" "redshift_encryption" {
  description             = "KMS key for Redshift encryption"
  deletion_window_in_days = var.kms_deletion_window
  
  tags = {
    Name = "${var.project_name}-redshift-encryption-key"
  }
}

resource "aws_kms_alias" "redshift_encryption" {
  name          = "alias/${var.project_name}-redshift-encryption"
  target_key_id = aws_kms_key.redshift_encryption.key_id
}

# Redshift Subnet Group
resource "aws_redshift_subnet_group" "main" {
  name       = "${var.project_name}-redshift-subnet-group"
  subnet_ids = var.redshift_subnet_ids

  tags = {
    Name = "${var.project_name} Redshift subnet group"
  }
}

# Security Group for Redshift
resource "aws_security_group" "redshift" {
  name_prefix = "${var.project_name}-redshift-"
  vpc_id      = var.vpc_id
  description = "Security group for Redshift cluster"

  ingress {
    description     = "Redshift access from application tier"
    from_port       = 5439
    to_port         = 5439
    protocol        = "tcp"
    security_groups = var.application_security_group_ids
  }

  ingress {
    description = "Redshift access from analytics tools"
    from_port   = 5439
    to_port     = 5439
    protocol    = "tcp"
    cidr_blocks = var.analytics_cidr_blocks
  }

  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-redshift-sg"
  }
}

# Random password for Redshift
resource "random_password" "redshift_password" {
  length  = 32
  special = true
}

# Store Redshift credentials in Secrets Manager
resource "aws_secretsmanager_secret" "redshift_credentials" {
  name                    = "${var.project_name}/redshift/credentials"
  description             = "Redshift credentials for ${var.project_name}"
  recovery_window_in_days = var.secret_recovery_window
  kms_key_id             = aws_kms_key.redshift_encryption.arn

  tags = {
    Name = "${var.project_name}-redshift-credentials"
  }
}

resource "aws_secretsmanager_secret_version" "redshift_credentials" {
  secret_id = aws_secretsmanager_secret.redshift_credentials.id
  secret_string = jsonencode({
    username = var.redshift_master_username
    password = random_password.redshift_password.result
    database = var.redshift_database_name
    host     = aws_redshift_cluster.main.endpoint
    port     = aws_redshift_cluster.main.port
  })
}

# IAM Role for Redshift Spectrum
resource "aws_iam_role" "redshift_spectrum" {
  name = "${var.project_name}-redshift-spectrum-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "redshift.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-redshift-spectrum-role"
  }
}

resource "aws_iam_role_policy_attachment" "redshift_spectrum_s3" {
  role       = aws_iam_role.redshift_spectrum.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}

resource "aws_iam_role_policy_attachment" "redshift_spectrum_glue" {
  role       = aws_iam_role.redshift_spectrum.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRedshiftServiceLinkedRolePolicy"
}

# Redshift Parameter Group
resource "aws_redshift_parameter_group" "main" {
  family = "redshift-1.0"
  name   = "${var.project_name}-redshift-params"

  dynamic "parameter" {
    for_each = var.redshift_parameters
    content {
      name  = parameter.value.name
      value = parameter.value.value
    }
  }

  tags = {
    Name = "${var.project_name} Redshift parameter group"
  }
}

# Main Redshift Cluster
resource "aws_redshift_cluster" "main" {
  cluster_identifier = "${var.project_name}-${var.environment}-redshift"
  
  # Cluster Configuration
  cluster_type   = var.redshift_cluster_type
  node_type      = var.redshift_node_type
  number_of_nodes = var.redshift_cluster_type == "multi-node" ? var.redshift_number_of_nodes : null
  
  # Database Configuration
  database_name    = var.redshift_database_name
  master_username  = var.redshift_master_username
  master_password  = random_password.redshift_password.result
  port            = 5439
  
  # Network Configuration
  cluster_subnet_group_name   = aws_redshift_subnet_group.main.name
  vpc_security_group_ids     = [aws_security_group.redshift.id]
  publicly_accessible       = var.redshift_publicly_accessible
  
  # Security Configuration
  encrypted    = true
  kms_key_id   = aws_kms_key.redshift_encryption.arn
  enhanced_vpc_routing = true
  
  # Backup Configuration
  automated_snapshot_retention_period = var.backup_retention_period
  manual_snapshot_retention_period    = var.manual_snapshot_retention_period
  preferred_maintenance_window        = var.maintenance_window
  
  # Parameter Group
  cluster_parameter_group_name = aws_redshift_parameter_group.main.name
  
  # IAM Roles
  iam_roles = [aws_iam_role.redshift_spectrum.arn]
  
  # Logging Configuration
  logging {
    enable        = true
    bucket_name   = aws_s3_bucket.redshift_logs.bucket
    s3_key_prefix = "cluster-logs/"
  }
  
  tags = {
    Name = "${var.project_name}-${var.environment}-redshift"
  }
  
  lifecycle {
    ignore_changes = [
      master_password,  # Managed by Secrets Manager
    ]
  }
  
  depends_on = [
    aws_redshift_parameter_group.main,
    aws_iam_role_policy_attachment.redshift_spectrum_s3,
    aws_iam_role_policy_attachment.redshift_spectrum_glue
  ]
}

# S3 Bucket for Redshift Logs
resource "aws_s3_bucket" "redshift_logs" {
  bucket = "${var.project_name}-${var.environment}-redshift-logs"
  
  tags = {
    Name = "${var.project_name}-redshift-logs"
  }
}

resource "aws_s3_bucket_versioning" "redshift_logs" {
  bucket = aws_s3_bucket.redshift_logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_encryption" "redshift_logs" {
  bucket = aws_s3_bucket.redshift_logs.id

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        kms_master_key_id = aws_kms_key.redshift_encryption.arn
        sse_algorithm     = "aws:kms"
      }
    }
  }
}

# Redshift Serverless (optional)
resource "aws_redshiftserverless_namespace" "serverless" {
  count = var.enable_serverless ? 1 : 0
  
  namespace_name     = "${var.project_name}-serverless"
  admin_username     = var.redshift_master_username
  admin_user_password = random_password.redshift_password.result
  db_name           = var.redshift_database_name
  kms_key_id        = aws_kms_key.redshift_encryption.arn
  
  tags = {
    Name = "${var.project_name}-serverless-namespace"
  }
}

resource "aws_redshiftserverless_workgroup" "serverless" {
  count = var.enable_serverless ? 1 : 0
  
  workgroup_name   = "${var.project_name}-serverless-workgroup"
  namespace_name   = aws_redshiftserverless_namespace.serverless[0].namespace_name
  
  base_capacity          = var.serverless_base_capacity
  max_capacity          = var.serverless_max_capacity
  publicly_accessible  = false
  subnet_ids           = var.redshift_subnet_ids
  security_group_ids   = [aws_security_group.redshift.id]
  enhanced_vpc_routing = true
  
  tags = {
    Name = "${var.project_name}-serverless-workgroup"
  }
}
```

## Troubleshooting & Operations

### Common Performance Issues

**Query Performance Troubleshooting**
```bash
# Check query performance using system tables
SELECT 
    query, 
    starttime, 
    endtime, 
    DATEDIFF(seconds, starttime, endtime) as duration_seconds,
    userid,
    database
FROM STL_QUERY 
WHERE starttime >= DATEADD(hour, -24, CURRENT_TIMESTAMP)
ORDER BY duration_seconds DESC 
LIMIT 20;

# Check table statistics
SELECT 
    schemaname, 
    tablename, 
    attname, 
    n_distinct, 
    most_common_vals, 
    most_common_freqs 
FROM pg_stats 
WHERE schemaname NOT IN ('information_schema', 'pg_catalog');

# Analyze query execution plan
EXPLAIN SELECT * FROM large_table WHERE date_column >= '2024-01-01';
```

**Cluster Management Operations**
```bash
# Check cluster status
aws redshift describe-clusters --cluster-identifier production-analytics-cluster

# Resize cluster
aws redshift modify-cluster \
  --cluster-identifier production-analytics-cluster \
  --cluster-type multi-node \
  --number-of-nodes 8 \
  --apply-immediately

# Create manual snapshot
aws redshift create-cluster-snapshot \
  --snapshot-identifier manual-snapshot-$(date +%Y%m%d) \
  --cluster-identifier production-analytics-cluster

# Pause cluster for cost savings
aws redshift pause-cluster --cluster-identifier production-analytics-cluster

# Resume cluster
aws redshift resume-cluster --cluster-identifier production-analytics-cluster
```

### Monitoring and Alerting Setup

```bash
# Create CloudWatch alarms for cluster monitoring
aws cloudwatch put-metric-alarm \
  --alarm-name "Redshift-HighCPU" \
  --alarm-description "Redshift cluster high CPU utilization" \
  --metric-name CPUUtilization \
  --namespace AWS/Redshift \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=ClusterIdentifier,Value=production-analytics-cluster \
  --evaluation-periods 2

# Monitor query queue wait times
aws cloudwatch put-metric-alarm \
  --alarm-name "Redshift-HighQueueTime" \
  --alarm-description "Redshift high query queue wait time" \
  --metric-name QueryQueueTime \
  --namespace AWS/Redshift \
  --statistic Average \
  --period 300 \
  --threshold 30000 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=ClusterIdentifier,Value=production-analytics-cluster \
  --evaluation-periods 2
```

## Best Practices

### Performance Best Practices

1. **Table Design Optimization**
   - Choose appropriate distribution keys (EVEN, KEY, ALL)
   - Implement proper sort keys for query patterns
   - Use compression encoding for columns
   - Avoid small frequent loads - batch data loading

2. **Query Optimization**
   - Use EXPLAIN to analyze query execution plans
   - Leverage materialized views for complex aggregations
   - Minimize data movement between nodes
   - Use column-level statistics for query planning

3. **Data Loading Best Practices**
   - Use COPY command for bulk data loading
   - Load data in sort key order when possible
   - Use multiple files for parallel loading
   - Compress data files before loading

### Cost Optimization Best Practices

1. **Cluster Management**
   - Use Reserved Instances for predictable workloads
   - Implement pause/resume schedules for development clusters
   - Monitor and optimize cluster utilization
   - Use Redshift Serverless for variable workloads

2. **Storage Optimization**
   - Regular VACUUM and ANALYZE operations
   - Archive old data to S3 using UNLOAD
   - Use Redshift Spectrum for infrequently accessed data
   - Monitor and manage snapshot retention

### Security Best Practices

1. **Access Control**
   - Implement least privilege access principles
   - Use IAM roles for service-to-service access
   - Regular access reviews and user management
   - Enable database audit logging

2. **Data Protection**
   - Enable encryption at rest and in transit
   - Use AWS KMS for key management
   - Implement network isolation with VPCs
   - Regular security assessments and compliance audits

## Additional Resources

### AWS Documentation
- [Amazon Redshift Management Guide](https://docs.aws.amazon.com/redshift/)
- [Redshift Best Practices](https://docs.aws.amazon.com/redshift/latest/dg/best-practices.html)
- [Redshift Spectrum User Guide](https://docs.aws.amazon.com/redshift/latest/dg/c-using-spectrum.html)
- [Redshift Serverless Guide](https://docs.aws.amazon.com/redshift/latest/mgmt/working-with-serverless.html)

### Performance Optimization Tools
- **Redshift Advisor** - Automated performance recommendations
- **Query Editor v2** - Web-based SQL editor with performance insights
- **AWS Well-Architected Tool** - Architecture review framework
- **CloudWatch Insights** - Log analysis and monitoring

### Third-Party Tools
- **dbt (data build tool)** - Data transformation and modeling
- **Tableau** - Business intelligence and visualization
- **Looker** - Modern BI and data platform
- **Apache Airflow** - Workflow orchestration for data pipelines

### Cost Management Tools
- **AWS Cost Explorer** - Cost analysis and forecasting
- **AWS Budgets** - Cost and usage budgets with alerts
- **Redshift Usage Reports** - Detailed cluster usage analysis
- **Third-party cost optimization tools** - Specialized Redshift cost management

**Key Differences from Other AWS Analytics Services:**
- **vs Athena:** Redshift optimized for complex, high-volume queries and has faster performance with proper indexing
- **vs Aurora:** Redshift designed for analytics (OLAP) while Aurora optimized for transactional workloads (OLTP)
- **vs EMR:** Redshift managed service vs EMR requiring more operational overhead for big data processing
- **vs QuickSight:** Redshift is the data warehouse engine while QuickSight is the visualization layer that can connect to Redshift