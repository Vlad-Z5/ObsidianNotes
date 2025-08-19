# AWS QuickSight - Enterprise BI & Analytics Platform

Cloud-native business intelligence service for data visualization and insights, enhanced with enterprise automation, advanced analytics capabilities, and comprehensive DevOps integration.

## Core Features & Components

- **Standard & Enterprise Editions** with advanced ML insights
- **Interactive dashboards** with real-time data visualization
- **ML-powered insights** and anomaly detection capabilities
- **SPICE (Super-fast, Parallel, In-memory Calculation Engine)** for performance
- **Mobile app support** and embedding capabilities
- **Auto-scaling architecture** for thousands of concurrent users
- **Row-level security (RLS)** and advanced permissions
- **Multi-source data connections** with automated refresh
- **Pay-per-session pricing** model with cost optimization
- **Paginated reports** for operational reporting
- **Q&A natural language queries** with machine learning

## Enterprise BI & Analytics Automation Framework

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

class DataSourceType(Enum):
    REDSHIFT = "REDSHIFT"
    RDS = "RDS"
    ATHENA = "ATHENA"
    S3 = "S3"
    SNOWFLAKE = "SNOWFLAKE"
    SALESFORCE = "SALESFORCE"
    JIRA = "JIRA"
    GITHUB = "GITHUB"
    SERVICENOW = "SERVICENOW"
    DATABRICKS = "DATABRICKS"

class ResourceStatus(Enum):
    CREATION_IN_PROGRESS = "CREATION_IN_PROGRESS"
    CREATION_SUCCESSFUL = "CREATION_SUCCESSFUL"
    CREATION_FAILED = "CREATION_FAILED"
    UPDATE_IN_PROGRESS = "UPDATE_IN_PROGRESS"
    UPDATE_SUCCESSFUL = "UPDATE_SUCCESSFUL"
    UPDATE_FAILED = "UPDATE_FAILED"
    DELETED = "DELETED"

class DashboardVersion(Enum):
    PUBLISHED = "PUBLISHED"
    DRAFT = "DRAFT"

class UserRole(Enum):
    ADMIN = "ADMIN"
    AUTHOR = "AUTHOR"
    READER = "READER"

@dataclass
class QuickSightDataSource:
    data_source_id: str
    name: str
    type: DataSourceType
    connection_properties: Dict[str, Any]
    credentials: Optional[Dict[str, Any]] = None
    permissions: List[Dict[str, Any]] = field(default_factory=list)
    ssl_properties: Optional[Dict[str, bool]] = None
    vpc_connection_properties: Optional[Dict[str, str]] = None
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class QuickSightDataSet:
    data_set_id: str
    name: str
    physical_table_map: Dict[str, Any]
    logical_table_map: Optional[Dict[str, Any]] = None
    import_mode: str = "SPICE"
    column_groups: List[Dict[str, Any]] = field(default_factory=list)
    field_folders: Dict[str, Any] = field(default_factory=dict)
    permissions: List[Dict[str, Any]] = field(default_factory=list)
    row_level_permission_data_set: Optional[Dict[str, Any]] = None
    column_level_permission_rules: List[Dict[str, Any]] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class QuickSightAnalysis:
    analysis_id: str
    name: str
    definition: Dict[str, Any]
    theme_arn: Optional[str] = None
    permissions: List[Dict[str, Any]] = field(default_factory=list)
    source_entity: Optional[Dict[str, Any]] = None
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class QuickSightDashboard:
    dashboard_id: str
    name: str
    definition: Optional[Dict[str, Any]] = None
    source_entity: Optional[Dict[str, Any]] = None
    theme_arn: Optional[str] = None
    permissions: List[Dict[str, Any]] = field(default_factory=list)
    dashboard_publish_options: Optional[Dict[str, Any]] = None
    tags: Dict[str, str] = field(default_factory=dict)

class EnterpriseQuickSightManager:
    """
    Enterprise AWS QuickSight manager with automated BI dashboard creation,
    advanced analytics capabilities, and comprehensive data governance.
    """
    
    def __init__(self, region: str = 'us-east-1', account_id: Optional[str] = None):
        self.quicksight = boto3.client('quicksight', region_name=region)
        self.sts = boto3.client('sts', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        
        # Get account ID if not provided
        if not account_id:
            account_id = self.sts.get_caller_identity()['Account']
        self.account_id = account_id
        
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger('QuickSightManager')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def create_enterprise_data_source(self, datasource_config: QuickSightDataSource) -> Dict[str, Any]:
        """Create enterprise data source with advanced configuration"""
        try:
            # Prepare data source parameters
            params = {
                'AwsAccountId': self.account_id,
                'DataSourceId': datasource_config.data_source_id,
                'Name': datasource_config.name,
                'Type': datasource_config.type.value,
                'DataSourceParameters': self._build_data_source_parameters(
                    datasource_config.type, 
                    datasource_config.connection_properties
                ),
                'Tags': [
                    {'Key': k, 'Value': v} 
                    for k, v in datasource_config.tags.items()
                ]
            }
            
            # Add optional configurations
            if datasource_config.credentials:
                params['Credentials'] = datasource_config.credentials
                
            if datasource_config.permissions:
                params['Permissions'] = datasource_config.permissions
                
            if datasource_config.ssl_properties:
                params['SslProperties'] = datasource_config.ssl_properties
                
            if datasource_config.vpc_connection_properties:
                params['VpcConnectionProperties'] = datasource_config.vpc_connection_properties
            
            response = self.quicksight.create_data_source(**params)
            
            self.logger.info(f"Created data source: {datasource_config.data_source_id}")
            
            return {
                'data_source_id': datasource_config.data_source_id,
                'arn': response.get('Arn'),
                'creation_status': response.get('CreationStatus'),
                'request_id': response.get('RequestId')
            }
            
        except ClientError as e:
            self.logger.error(f"Error creating data source: {str(e)}")
            raise

    def _build_data_source_parameters(self, ds_type: DataSourceType, 
                                    connection_props: Dict[str, Any]) -> Dict[str, Any]:
        """Build data source parameters based on type"""
        if ds_type == DataSourceType.REDSHIFT:
            return {
                'RedshiftParameters': {
                    'Host': connection_props['host'],
                    'Port': connection_props.get('port', 5439),
                    'Database': connection_props['database'],
                    'ClusterId': connection_props.get('cluster_id')
                }
            }
        elif ds_type == DataSourceType.RDS:
            return {
                'RdsParameters': {
                    'InstanceId': connection_props['instance_id'],
                    'Database': connection_props['database']
                }
            }
        elif ds_type == DataSourceType.ATHENA:
            return {
                'AthenaParameters': {
                    'WorkGroup': connection_props.get('work_group', 'primary'),
                    'RoleArn': connection_props.get('role_arn')
                }
            }
        elif ds_type == DataSourceType.S3:
            return {
                'S3Parameters': {
                    'ManifestFileLocation': {
                        'Bucket': connection_props['bucket'],
                        'Key': connection_props['manifest_key']
                    },
                    'RoleArn': connection_props.get('role_arn')
                }
            }
        elif ds_type == DataSourceType.SNOWFLAKE:
            return {
                'SnowflakeParameters': {
                    'Host': connection_props['host'],
                    'Database': connection_props['database'],
                    'Warehouse': connection_props['warehouse']
                }
            }
        else:
            return connection_props

    def create_enterprise_dataset(self, dataset_config: QuickSightDataSet) -> Dict[str, Any]:
        """Create enterprise dataset with advanced features"""
        try:
            params = {
                'AwsAccountId': self.account_id,
                'DataSetId': dataset_config.data_set_id,
                'Name': dataset_config.name,
                'PhysicalTableMap': dataset_config.physical_table_map,
                'ImportMode': dataset_config.import_mode,
                'Tags': [
                    {'Key': k, 'Value': v} 
                    for k, v in dataset_config.tags.items()
                ]
            }
            
            # Add optional configurations
            if dataset_config.logical_table_map:
                params['LogicalTableMap'] = dataset_config.logical_table_map
                
            if dataset_config.column_groups:
                params['ColumnGroups'] = dataset_config.column_groups
                
            if dataset_config.field_folders:
                params['FieldFolders'] = dataset_config.field_folders
                
            if dataset_config.permissions:
                params['Permissions'] = dataset_config.permissions
                
            if dataset_config.row_level_permission_data_set:
                params['RowLevelPermissionDataSet'] = dataset_config.row_level_permission_data_set
                
            if dataset_config.column_level_permission_rules:
                params['ColumnLevelPermissionRules'] = dataset_config.column_level_permission_rules
            
            response = self.quicksight.create_data_set(**params)
            
            self.logger.info(f"Created dataset: {dataset_config.data_set_id}")
            
            return {
                'data_set_id': dataset_config.data_set_id,
                'arn': response.get('Arn'),
                'creation_status': response.get('CreationStatus'),
                'request_id': response.get('RequestId')
            }
            
        except ClientError as e:
            self.logger.error(f"Error creating dataset: {str(e)}")
            raise

    def create_advanced_analysis(self, analysis_config: QuickSightAnalysis) -> Dict[str, Any]:
        """Create advanced analysis with rich visualizations"""
        try:
            params = {
                'AwsAccountId': self.account_id,
                'AnalysisId': analysis_config.analysis_id,
                'Name': analysis_config.name,
                'Definition': analysis_config.definition,
                'Tags': [
                    {'Key': k, 'Value': v} 
                    for k, v in analysis_config.tags.items()
                ]
            }
            
            # Add optional configurations
            if analysis_config.theme_arn:
                params['ThemeArn'] = analysis_config.theme_arn
                
            if analysis_config.permissions:
                params['Permissions'] = analysis_config.permissions
                
            if analysis_config.source_entity:
                params['SourceEntity'] = analysis_config.source_entity
            
            response = self.quicksight.create_analysis(**params)
            
            self.logger.info(f"Created analysis: {analysis_config.analysis_id}")
            
            return {
                'analysis_id': analysis_config.analysis_id,
                'arn': response.get('Arn'),
                'creation_status': response.get('CreationStatus'),
                'request_id': response.get('RequestId')
            }
            
        except ClientError as e:
            self.logger.error(f"Error creating analysis: {str(e)}")
            raise

    def create_executive_dashboard(self, dashboard_config: QuickSightDashboard) -> Dict[str, Any]:
        """Create executive dashboard with enterprise features"""
        try:
            params = {
                'AwsAccountId': self.account_id,
                'DashboardId': dashboard_config.dashboard_id,
                'Name': dashboard_config.name,
                'Tags': [
                    {'Key': k, 'Value': v} 
                    for k, v in dashboard_config.tags.items()
                ]
            }
            
            # Add definition or source entity
            if dashboard_config.definition:
                params['Definition'] = dashboard_config.definition
            elif dashboard_config.source_entity:
                params['SourceEntity'] = dashboard_config.source_entity
            else:
                raise ValueError("Either definition or source_entity must be provided")
            
            # Add optional configurations
            if dashboard_config.theme_arn:
                params['ThemeArn'] = dashboard_config.theme_arn
                
            if dashboard_config.permissions:
                params['Permissions'] = dashboard_config.permissions
                
            if dashboard_config.dashboard_publish_options:
                params['DashboardPublishOptions'] = dashboard_config.dashboard_publish_options
            
            response = self.quicksight.create_dashboard(**params)
            
            self.logger.info(f"Created dashboard: {dashboard_config.dashboard_id}")
            
            return {
                'dashboard_id': dashboard_config.dashboard_id,
                'arn': response.get('Arn'),
                'creation_status': response.get('CreationStatus'),
                'dashboard_url': self._get_dashboard_url(dashboard_config.dashboard_id),
                'request_id': response.get('RequestId')
            }
            
        except ClientError as e:
            self.logger.error(f"Error creating dashboard: {str(e)}")
            raise

    def _get_dashboard_url(self, dashboard_id: str) -> str:
        """Generate dashboard URL"""
        return f"https://quicksight.aws.amazon.com/sn/dashboards/{dashboard_id}"

    def setup_user_management(self, users: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Setup enterprise user management with roles and permissions"""
        try:
            created_users = []
            
            for user_config in users:
                try:
                    # Register user
                    response = self.quicksight.register_user(
                        AwsAccountId=self.account_id,
                        Namespace='default',
                        IdentityType='QUICKSIGHT',
                        Email=user_config['email'],
                        UserRole=user_config['role'],
                        UserName=user_config.get('username', user_config['email']),
                        SessionName=user_config.get('session_name'),
                        CustomPermissionsName=user_config.get('custom_permissions_name')
                    )
                    
                    created_users.append({
                        'email': user_config['email'],
                        'username': response.get('User', {}).get('UserName'),
                        'arn': response.get('User', {}).get('Arn'),
                        'role': user_config['role'],
                        'status': 'created'
                    })
                    
                    self.logger.info(f"Created user: {user_config['email']}")
                    
                except ClientError as e:
                    if 'ResourceExistsException' in str(e):
                        created_users.append({
                            'email': user_config['email'],
                            'status': 'already_exists'
                        })
                    else:
                        self.logger.error(f"Error creating user {user_config['email']}: {str(e)}")
                        created_users.append({
                            'email': user_config['email'],
                            'status': 'failed',
                            'error': str(e)
                        })
            
            return {
                'total_users': len(users),
                'created_users': len([u for u in created_users if u['status'] == 'created']),
                'existing_users': len([u for u in created_users if u['status'] == 'already_exists']),
                'failed_users': len([u for u in created_users if u['status'] == 'failed']),
                'users': created_users
            }
            
        except Exception as e:
            self.logger.error(f"Error setting up user management: {str(e)}")
            raise

    def setup_automated_refresh(self, dataset_id: str, 
                               refresh_schedule: Dict[str, Any]) -> Dict[str, Any]:
        """Setup automated data refresh for datasets"""
        try:
            response = self.quicksight.create_refresh_schedule(
                AwsAccountId=self.account_id,
                DataSetId=dataset_id,
                Schedule={
                    'ScheduleId': f"{dataset_id}-refresh-schedule",
                    'ScheduleFrequency': refresh_schedule,
                    'StartAfterDateTime': datetime.utcnow(),
                    'RefreshType': 'FULL_REFRESH'
                }
            )
            
            self.logger.info(f"Created refresh schedule for dataset: {dataset_id}")
            
            return {
                'dataset_id': dataset_id,
                'schedule_id': response.get('ScheduleId'),
                'arn': response.get('Arn'),
                'status': 'created'
            }
            
        except ClientError as e:
            self.logger.error(f"Error creating refresh schedule: {str(e)}")
            raise

    def create_row_level_security(self, dataset_id: str, 
                                 rls_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create row-level security configuration"""
        try:
            # Update dataset with RLS configuration
            response = self.quicksight.update_data_set(
                AwsAccountId=self.account_id,
                DataSetId=dataset_id,
                Name=rls_config['dataset_name'],
                PhysicalTableMap=rls_config['physical_table_map'],
                RowLevelPermissionDataSet={
                    'Namespace': 'default',
                    'Arn': rls_config['permission_dataset_arn'],
                    'PermissionPolicy': rls_config.get('permission_policy', 'GRANT_ACCESS'),
                    'FormatVersion': rls_config.get('format_version', 'VERSION_1'),
                    'Status': rls_config.get('status', 'ENABLED')
                }
            )
            
            self.logger.info(f"Configured RLS for dataset: {dataset_id}")
            
            return {
                'dataset_id': dataset_id,
                'rls_status': 'configured',
                'request_id': response.get('RequestId')
            }
            
        except ClientError as e:
            self.logger.error(f"Error configuring RLS: {str(e)}")
            raise

    def generate_embed_url(self, dashboard_id: str, user_arn: str, 
                          session_lifetime_minutes: int = 600) -> Dict[str, Any]:
        """Generate dashboard embed URL for applications"""
        try:
            response = self.quicksight.generate_embed_url_for_registered_user(
                AwsAccountId=self.account_id,
                UserArn=user_arn,
                SessionLifetimeInMinutes=session_lifetime_minutes,
                ExperienceConfiguration={
                    'Dashboard': {
                        'InitialDashboardId': dashboard_id,
                        'FeatureConfigurations': {
                            'StatePersistence': {
                                'Enabled': True
                            }
                        }
                    }
                },
                AllowedDomains=['https://company.com', 'https://app.company.com']
            )
            
            self.logger.info(f"Generated embed URL for dashboard: {dashboard_id}")
            
            return {
                'dashboard_id': dashboard_id,
                'embed_url': response['EmbedUrl'],
                'request_id': response.get('RequestId'),
                'expires_in_minutes': session_lifetime_minutes
            }
            
        except ClientError as e:
            self.logger.error(f"Error generating embed URL: {str(e)}")
            raise

    def monitor_dashboard_usage(self, dashboard_ids: List[str], 
                               days_back: int = 30) -> Dict[str, Any]:
        """Monitor dashboard usage and performance metrics"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days_back)
            
            usage_metrics = []
            
            for dashboard_id in dashboard_ids:
                try:
                    # Get dashboard sessions (this would typically use CloudWatch or custom metrics)
                    sessions_metric = self.cloudwatch.get_metric_statistics(
                        Namespace='AWS/QuickSight',
                        MetricName='SessionCount',
                        Dimensions=[
                            {
                                'Name': 'DashboardId',
                                'Value': dashboard_id
                            }
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=86400,  # Daily
                        Statistics=['Sum']
                    )
                    
                    # Get dashboard views
                    views_metric = self.cloudwatch.get_metric_statistics(
                        Namespace='AWS/QuickSight',
                        MetricName='ViewCount',
                        Dimensions=[
                            {
                                'Name': 'DashboardId',
                                'Value': dashboard_id
                            }
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=86400,  # Daily
                        Statistics=['Sum']
                    )
                    
                    total_sessions = sum(point['Sum'] for point in sessions_metric['Datapoints'])
                    total_views = sum(point['Sum'] for point in views_metric['Datapoints'])
                    
                    usage_metrics.append({
                        'dashboard_id': dashboard_id,
                        'total_sessions': total_sessions,
                        'total_views': total_views,
                        'avg_daily_sessions': total_sessions / days_back,
                        'avg_daily_views': total_views / days_back,
                        'period_days': days_back
                    })
                    
                except Exception as e:
                    self.logger.warning(f"Error getting metrics for dashboard {dashboard_id}: {str(e)}")
                    usage_metrics.append({
                        'dashboard_id': dashboard_id,
                        'error': str(e)
                    })
            
            return {
                'monitoring_period_days': days_back,
                'dashboards_monitored': len(dashboard_ids),
                'usage_metrics': usage_metrics,
                'report_generated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error monitoring dashboard usage: {str(e)}")
            raise

# Practical Real-World Examples

def create_executive_kpi_dashboard():
    """Create executive KPI dashboard with real-time metrics"""
    
    manager = EnterpriseQuickSightManager()
    
    # Create Redshift data source
    redshift_datasource = QuickSightDataSource(
        data_source_id="executive-redshift-ds",
        name="Executive Analytics Redshift",
        type=DataSourceType.REDSHIFT,
        connection_properties={
            'host': 'analytics-cluster.xyz.us-east-1.redshift.amazonaws.com',
            'port': 5439,
            'database': 'analytics',
            'cluster_id': 'analytics-cluster'
        },
        credentials={
            'CredentialPair': {
                'Username': 'analytics_user',
                'Password': 'SecurePassword123!'
            }
        },
        tags={
            'Department': 'Executive',
            'Environment': 'Production',
            'CostCenter': 'Analytics'
        }
    )
    
    ds_result = manager.create_enterprise_data_source(redshift_datasource)
    print(f"Created data source: {ds_result}")
    
    # Create executive KPI dataset
    kpi_dataset = QuickSightDataSet(
        data_set_id="executive-kpi-dataset",
        name="Executive KPI Metrics",
        physical_table_map={
            'executive_kpis': {
                'RelationalTable': {
                    'DataSourceArn': ds_result['arn'],
                    'Catalog': 'analytics',
                    'Schema': 'executive',
                    'Name': 'kpi_metrics',
                    'InputColumns': [
                        {'Name': 'date', 'Type': 'DATETIME'},
                        {'Name': 'revenue', 'Type': 'DECIMAL'},
                        {'Name': 'profit_margin', 'Type': 'DECIMAL'},
                        {'Name': 'customer_count', 'Type': 'INTEGER'},
                        {'Name': 'market_share', 'Type': 'DECIMAL'},
                        {'Name': 'employee_satisfaction', 'Type': 'DECIMAL'},
                        {'Name': 'operational_efficiency', 'Type': 'DECIMAL'}
                    ]
                }
            }
        },
        import_mode="SPICE",
        tags={
            'Dashboard': 'Executive',
            'RefreshFrequency': 'Hourly'
        }
    )
    
    dataset_result = manager.create_enterprise_dataset(kpi_dataset)
    print(f"Created dataset: {dataset_result}")
    
    # Create executive dashboard
    executive_dashboard = QuickSightDashboard(
        dashboard_id="executive-kpi-dashboard",
        name="Executive KPI Dashboard",
        definition={
            'DataSetIdentifierDeclarations': [
                {
                    'DataSetArn': dataset_result['arn'],
                    'Identifier': 'executive_kpis'
                }
            ],
            'Sheets': [
                {
                    'SheetId': 'executive-overview',
                    'Name': 'Executive Overview',
                    'Visuals': [
                        {
                            'BarChartVisual': {
                                'VisualId': 'revenue-trend',
                                'Title': {'Visibility': 'VISIBLE', 'Label': 'Revenue Trend'},
                                'FieldWells': {
                                    'BarChartAggregatedFieldWells': {
                                        'Category': [{'DateDimensionField': {'FieldId': 'date', 'Column': {'DataSetIdentifier': 'executive_kpis', 'ColumnName': 'date'}}}],
                                        'Values': [{'NumericalMeasureField': {'FieldId': 'revenue', 'Column': {'DataSetIdentifier': 'executive_kpis', 'ColumnName': 'revenue'}}}]
                                    }
                                }
                            }
                        },
                        {
                            'KPIVisual': {
                                'VisualId': 'profit-margin-kpi',
                                'Title': {'Visibility': 'VISIBLE', 'Label': 'Profit Margin'},
                                'FieldWells': {
                                    'Values': [{'NumericalMeasureField': {'FieldId': 'profit_margin', 'Column': {'DataSetIdentifier': 'executive_kpis', 'ColumnName': 'profit_margin'}}}]
                                }
                            }
                        },
                        {
                            'GaugeChartVisual': {
                                'VisualId': 'efficiency-gauge',
                                'Title': {'Visibility': 'VISIBLE', 'Label': 'Operational Efficiency'},
                                'FieldWells': {
                                    'Values': [{'NumericalMeasureField': {'FieldId': 'operational_efficiency', 'Column': {'DataSetIdentifier': 'executive_kpis', 'ColumnName': 'operational_efficiency'}}}]
                                }
                            }
                        }
                    ]
                }
            ]
        },
        permissions=[
            {
                'Principal': f'arn:aws:quicksight:us-east-1:123456789012:group/default/Executives',
                'Actions': ['quicksight:DescribeDashboard', 'quicksight:ListDashboardVersions', 'quicksight:QueryDashboard']
            }
        ],
        tags={
            'Department': 'Executive',
            'Audience': 'C-Level'
        }
    )
    
    dashboard_result = manager.create_executive_dashboard(executive_dashboard)
    print(f"Created dashboard: {dashboard_result}")
    
    # Setup automated refresh
    refresh_schedule = {
        'RefreshType': 'FULL_REFRESH',
        'TimeOfTheDay': '06:00',
        'Timezone': 'America/New_York'
    }
    
    refresh_result = manager.setup_automated_refresh(
        dataset_result['data_set_id'], 
        refresh_schedule
    )
    print(f"Setup refresh schedule: {refresh_result}")
    
    return {
        'data_source': ds_result,
        'dataset': dataset_result,
        'dashboard': dashboard_result,
        'refresh_schedule': refresh_result
    }

def create_sales_analytics_dashboard():
    """Create comprehensive sales analytics dashboard"""
    
    manager = EnterpriseQuickSightManager()
    
    # Create Athena data source for sales data
    athena_datasource = QuickSightDataSource(
        data_source_id="sales-athena-ds",
        name="Sales Analytics Athena",
        type=DataSourceType.ATHENA,
        connection_properties={
            'work_group': 'sales-analytics',
            'role_arn': 'arn:aws:iam::123456789012:role/QuickSightAthenaRole'
        },
        tags={
            'Department': 'Sales',
            'DataType': 'Transactional'
        }
    )
    
    ds_result = manager.create_enterprise_data_source(athena_datasource)
    
    # Create sales dataset with multiple tables
    sales_dataset = QuickSightDataSet(
        data_set_id="sales-analytics-dataset",
        name="Sales Analytics Dataset",
        physical_table_map={
            'sales_transactions': {
                'RelationalTable': {
                    'DataSourceArn': ds_result['arn'],
                    'Catalog': 'sales_catalog',
                    'Schema': 'sales',
                    'Name': 'transactions',
                    'InputColumns': [
                        {'Name': 'transaction_id', 'Type': 'STRING'},
                        {'Name': 'date', 'Type': 'DATETIME'},
                        {'Name': 'customer_id', 'Type': 'STRING'},
                        {'Name': 'product_id', 'Type': 'STRING'},
                        {'Name': 'amount', 'Type': 'DECIMAL'},
                        {'Name': 'quantity', 'Type': 'INTEGER'},
                        {'Name': 'sales_rep', 'Type': 'STRING'},
                        {'Name': 'region', 'Type': 'STRING'}
                    ]
                }
            },
            'products': {
                'RelationalTable': {
                    'DataSourceArn': ds_result['arn'],
                    'Catalog': 'sales_catalog',
                    'Schema': 'sales',
                    'Name': 'products',
                    'InputColumns': [
                        {'Name': 'product_id', 'Type': 'STRING'},
                        {'Name': 'product_name', 'Type': 'STRING'},
                        {'Name': 'category', 'Type': 'STRING'},
                        {'Name': 'cost', 'Type': 'DECIMAL'},
                        {'Name': 'list_price', 'Type': 'DECIMAL'}
                    ]
                }
            }
        },
        logical_table_map={
            'sales_with_products': {
                'Alias': 'Sales with Product Details',
                'DataTransforms': [
                    {
                        'ProjectOperation': {
                            'ProjectedColumns': [
                                'transaction_id', 'date', 'customer_id', 'amount', 
                                'quantity', 'sales_rep', 'region', 'product_name', 
                                'category', 'list_price'
                            ]
                        }
                    },
                    {
                        'CreateColumnsOperation': {
                            'Columns': [
                                {
                                    'ColumnName': 'profit',
                                    'ColumnId': 'profit',
                                    'Expression': 'amount - (quantity * cost)'
                                },
                                {
                                    'ColumnName': 'profit_margin',
                                    'ColumnId': 'profit_margin', 
                                    'Expression': '(amount - (quantity * cost)) / amount * 100'
                                }
                            ]
                        }
                    }
                ],
                'Source': {
                    'JoinInstruction': {
                        'LeftOperand': 'sales_transactions',
                        'RightOperand': 'products',
                        'Type': 'INNER',
                        'OnClause': 'sales_transactions.product_id = products.product_id'
                    }
                }
            }
        },
        row_level_permission_data_set={
            'Namespace': 'default',
            'Arn': 'arn:aws:quicksight:us-east-1:123456789012:dataset/sales-rls-dataset',
            'PermissionPolicy': 'GRANT_ACCESS'
        },
        tags={
            'Department': 'Sales',
            'DataSensitivity': 'Confidential'
        }
    )
    
    dataset_result = manager.create_enterprise_dataset(sales_dataset)
    
    # Create comprehensive sales dashboard
    sales_dashboard = QuickSightDashboard(
        dashboard_id="sales-analytics-dashboard",
        name="Sales Analytics Dashboard",
        definition={
            'DataSetIdentifierDeclarations': [
                {
                    'DataSetArn': dataset_result['arn'],
                    'Identifier': 'sales_data'
                }
            ],
            'Sheets': [
                {
                    'SheetId': 'sales-overview',
                    'Name': 'Sales Overview',
                    'Visuals': [
                        {
                            'LineChartVisual': {
                                'VisualId': 'sales-trend',
                                'Title': {'Visibility': 'VISIBLE', 'Label': 'Sales Trend Over Time'},
                                'FieldWells': {
                                    'LineChartAggregatedFieldWells': {
                                        'Category': [{'DateDimensionField': {'FieldId': 'date', 'Column': {'DataSetIdentifier': 'sales_data', 'ColumnName': 'date'}}}],
                                        'Values': [{'NumericalMeasureField': {'FieldId': 'amount', 'Column': {'DataSetIdentifier': 'sales_data', 'ColumnName': 'amount'}, 'AggregationFunction': {'SimpleNumericalAggregation': 'SUM'}}}]
                                    }
                                }
                            }
                        },
                        {
                            'BarChartVisual': {
                                'VisualId': 'sales-by-region',
                                'Title': {'Visibility': 'VISIBLE', 'Label': 'Sales by Region'},
                                'FieldWells': {
                                    'BarChartAggregatedFieldWells': {
                                        'Category': [{'CategoricalDimensionField': {'FieldId': 'region', 'Column': {'DataSetIdentifier': 'sales_data', 'ColumnName': 'region'}}}],
                                        'Values': [{'NumericalMeasureField': {'FieldId': 'amount', 'Column': {'DataSetIdentifier': 'sales_data', 'ColumnName': 'amount'}, 'AggregationFunction': {'SimpleNumericalAggregation': 'SUM'}}}]
                                    }
                                }
                            }
                        },
                        {
                            'PieChartVisual': {
                                'VisualId': 'sales-by-category',
                                'Title': {'Visibility': 'VISIBLE', 'Label': 'Sales by Product Category'},
                                'FieldWells': {
                                    'PieChartAggregatedFieldWells': {
                                        'Category': [{'CategoricalDimensionField': {'FieldId': 'category', 'Column': {'DataSetIdentifier': 'sales_data', 'ColumnName': 'category'}}}],
                                        'Values': [{'NumericalMeasureField': {'FieldId': 'amount', 'Column': {'DataSetIdentifier': 'sales_data', 'ColumnName': 'amount'}, 'AggregationFunction': {'SimpleNumericalAggregation': 'SUM'}}}]
                                    }
                                }
                            }
                        }
                    ]
                },
                {
                    'SheetId': 'performance-analysis',
                    'Name': 'Performance Analysis',
                    'Visuals': [
                        {
                            'TableVisual': {
                                'VisualId': 'top-performers',
                                'Title': {'Visibility': 'VISIBLE', 'Label': 'Top Sales Representatives'},
                                'FieldWells': {
                                    'TableAggregatedFieldWells': {
                                        'GroupBy': [{'CategoricalDimensionField': {'FieldId': 'sales_rep', 'Column': {'DataSetIdentifier': 'sales_data', 'ColumnName': 'sales_rep'}}}],
                                        'Values': [
                                            {'NumericalMeasureField': {'FieldId': 'total_sales', 'Column': {'DataSetIdentifier': 'sales_data', 'ColumnName': 'amount'}, 'AggregationFunction': {'SimpleNumericalAggregation': 'SUM'}}},
                                            {'NumericalMeasureField': {'FieldId': 'avg_profit_margin', 'Column': {'DataSetIdentifier': 'sales_data', 'ColumnName': 'profit_margin'}, 'AggregationFunction': {'SimpleNumericalAggregation': 'AVERAGE'}}}
                                        ]
                                    }
                                }
                            }
                        }
                    ]
                }
            ]
        },
        permissions=[
            {
                'Principal': f'arn:aws:quicksight:us-east-1:123456789012:group/default/SalesManagers',
                'Actions': ['quicksight:DescribeDashboard', 'quicksight:ListDashboardVersions', 'quicksight:QueryDashboard']
            },
            {
                'Principal': f'arn:aws:quicksight:us-east-1:123456789012:group/default/SalesReps',
                'Actions': ['quicksight:DescribeDashboard', 'quicksight:QueryDashboard']
            }
        ],
        tags={
            'Department': 'Sales',
            'Audience': 'Sales-Team'
        }
    )
    
    dashboard_result = manager.create_executive_dashboard(sales_dashboard)
    
    return {
        'data_source': ds_result,
        'dataset': dataset_result,
        'dashboard': dashboard_result
    }

def create_financial_reporting_dashboard():
    """Create financial reporting dashboard with compliance features"""
    
    manager = EnterpriseQuickSightManager()
    
    # Create S3 data source for financial data
    s3_datasource = QuickSightDataSource(
        data_source_id="financial-s3-ds",
        name="Financial Reporting S3",
        type=DataSourceType.S3,
        connection_properties={
            'bucket': 'company-financial-data',
            'manifest_key': 'financial-reports/manifest.json',
            'role_arn': 'arn:aws:iam::123456789012:role/QuickSightS3Role'
        },
        tags={
            'Department': 'Finance',
            'Compliance': 'SOX'
        }
    )
    
    ds_result = manager.create_enterprise_data_source(s3_datasource)
    
    # Create financial dataset with strict data governance
    financial_dataset = QuickSightDataSet(
        data_set_id="financial-reporting-dataset",
        name="Financial Reporting Dataset",
        physical_table_map={
            'financial_statements': {
                'S3Source': {
                    'DataSourceArn': ds_result['arn'],
                    'InputColumns': [
                        {'Name': 'account_id', 'Type': 'STRING'},
                        {'Name': 'account_name', 'Type': 'STRING'},
                        {'Name': 'account_type', 'Type': 'STRING'},
                        {'Name': 'period', 'Type': 'DATETIME'},
                        {'Name': 'amount', 'Type': 'DECIMAL'},
                        {'Name': 'currency', 'Type': 'STRING'},
                        {'Name': 'subsidiary', 'Type': 'STRING'},
                        {'Name': 'department', 'Type': 'STRING'}
                    ]
                }
            }
        },
        column_level_permission_rules=[
            {
                'Principals': [f'arn:aws:quicksight:us-east-1:123456789012:group/default/FinanceViewers'],
                'ColumnNames': ['account_name', 'period', 'amount', 'currency']
            },
            {
                'Principals': [f'arn:aws:quicksight:us-east-1:123456789012:group/default/FinanceManagers'],
                'ColumnNames': ['*']
            }
        ],
        tags={
            'Department': 'Finance',
            'DataClassification': 'Restricted',
            'Compliance': 'SOX-Compliant'
        }
    )
    
    dataset_result = manager.create_enterprise_dataset(financial_dataset)
    
    # Create financial dashboard with compliance controls
    financial_dashboard = QuickSightDashboard(
        dashboard_id="financial-reporting-dashboard",
        name="Financial Reporting Dashboard",
        definition={
            'DataSetIdentifierDeclarations': [
                {
                    'DataSetArn': dataset_result['arn'],
                    'Identifier': 'financial_data'
                }
            ],
            'Sheets': [
                {
                    'SheetId': 'income-statement',
                    'Name': 'Income Statement',
                    'Visuals': [
                        {
                            'TableVisual': {
                                'VisualId': 'income-statement-table',
                                'Title': {'Visibility': 'VISIBLE', 'Label': 'Income Statement'},
                                'FieldWells': {
                                    'TableAggregatedFieldWells': {
                                        'GroupBy': [
                                            {'CategoricalDimensionField': {'FieldId': 'account_name', 'Column': {'DataSetIdentifier': 'financial_data', 'ColumnName': 'account_name'}}},
                                            {'DateDimensionField': {'FieldId': 'period', 'Column': {'DataSetIdentifier': 'financial_data', 'ColumnName': 'period'}}}
                                        ],
                                        'Values': [
                                            {'NumericalMeasureField': {'FieldId': 'amount', 'Column': {'DataSetIdentifier': 'financial_data', 'ColumnName': 'amount'}, 'AggregationFunction': {'SimpleNumericalAggregation': 'SUM'}}}
                                        ]
                                    }
                                }
                            }
                        }
                    ]
                },
                {
                    'SheetId': 'balance-sheet',
                    'Name': 'Balance Sheet',
                    'Visuals': [
                        {
                            'BarChartVisual': {
                                'VisualId': 'balance-sheet-chart',
                                'Title': {'Visibility': 'VISIBLE', 'Label': 'Balance Sheet Summary'},
                                'FieldWells': {
                                    'BarChartAggregatedFieldWells': {
                                        'Category': [{'CategoricalDimensionField': {'FieldId': 'account_type', 'Column': {'DataSetIdentifier': 'financial_data', 'ColumnName': 'account_type'}}}],
                                        'Values': [{'NumericalMeasureField': {'FieldId': 'amount', 'Column': {'DataSetIdentifier': 'financial_data', 'ColumnName': 'amount'}, 'AggregationFunction': {'SimpleNumericalAggregation': 'SUM'}}}]
                                    }
                                }
                            }
                        }
                    ]
                }
            ]
        },
        permissions=[
            {
                'Principal': f'arn:aws:quicksight:us-east-1:123456789012:group/default/CFO',
                'Actions': ['quicksight:DescribeDashboard', 'quicksight:ListDashboardVersions', 'quicksight:QueryDashboard', 'quicksight:UpdateDashboard']
            },
            {
                'Principal': f'arn:aws:quicksight:us-east-1:123456789012:group/default/FinanceManagers',
                'Actions': ['quicksight:DescribeDashboard', 'quicksight:QueryDashboard']
            }
        ],
        tags={
            'Department': 'Finance',
            'Compliance': 'SOX',
            'AuditRequired': 'true'
        }
    )
    
    dashboard_result = manager.create_executive_dashboard(financial_dashboard)
    
    # Setup row-level security for financial data
    rls_config = {
        'dataset_name': 'Financial Reporting Dataset',
        'physical_table_map': financial_dataset.physical_table_map,
        'permission_dataset_arn': 'arn:aws:quicksight:us-east-1:123456789012:dataset/financial-permissions',
        'permission_policy': 'GRANT_ACCESS',
        'status': 'ENABLED'
    }
    
    rls_result = manager.create_row_level_security(
        dataset_result['data_set_id'],
        rls_config
    )
    
    return {
        'data_source': ds_result,
        'dataset': dataset_result,
        'dashboard': dashboard_result,
        'row_level_security': rls_result
    }

def create_operational_monitoring_dashboard():
    """Create operational monitoring dashboard for IT and DevOps"""
    
    manager = EnterpriseQuickSightManager()
    
    # Create multiple data sources for operational data
    datasources = []
    
    # CloudWatch metrics via Athena
    cloudwatch_ds = QuickSightDataSource(
        data_source_id="cloudwatch-athena-ds",
        name="CloudWatch Metrics Athena",
        type=DataSourceType.ATHENA,
        connection_properties={
            'work_group': 'operations',
            'role_arn': 'arn:aws:iam::123456789012:role/QuickSightAthenaRole'
        },
        tags={'DataSource': 'CloudWatch', 'Team': 'DevOps'}
    )
    
    cw_result = manager.create_enterprise_data_source(cloudwatch_ds)
    datasources.append(cw_result)
    
    # Application logs from S3
    logs_ds = QuickSightDataSource(
        data_source_id="application-logs-s3-ds",
        name="Application Logs S3",
        type=DataSourceType.S3,
        connection_properties={
            'bucket': 'company-application-logs',
            'manifest_key': 'processed-logs/manifest.json',
            'role_arn': 'arn:aws:iam::123456789012:role/QuickSightS3Role'
        },
        tags={'DataSource': 'ApplicationLogs', 'Team': 'DevOps'}
    )
    
    logs_result = manager.create_enterprise_data_source(logs_ds)
    datasources.append(logs_result)
    
    # Create operational dataset
    ops_dataset = QuickSightDataSet(
        data_set_id="operational-monitoring-dataset",
        name="Operational Monitoring Dataset",
        physical_table_map={
            'infrastructure_metrics': {
                'RelationalTable': {
                    'DataSourceArn': cw_result['arn'],
                    'Catalog': 'operations_catalog',
                    'Schema': 'cloudwatch',
                    'Name': 'infrastructure_metrics',
                    'InputColumns': [
                        {'Name': 'timestamp', 'Type': 'DATETIME'},
                        {'Name': 'metric_name', 'Type': 'STRING'},
                        {'Name': 'metric_value', 'Type': 'DECIMAL'},
                        {'Name': 'service_name', 'Type': 'STRING'},
                        {'Name': 'instance_id', 'Type': 'STRING'},
                        {'Name': 'region', 'Type': 'STRING'}
                    ]
                }
            },
            'application_errors': {
                'S3Source': {
                    'DataSourceArn': logs_result['arn'],
                    'InputColumns': [
                        {'Name': 'timestamp', 'Type': 'DATETIME'},
                        {'Name': 'application', 'Type': 'STRING'},
                        {'Name': 'error_type', 'Type': 'STRING'},
                        {'Name': 'error_count', 'Type': 'INTEGER'},
                        {'Name': 'severity', 'Type': 'STRING'},
                        {'Name': 'environment', 'Type': 'STRING'}
                    ]
                }
            }
        },
        import_mode="SPICE",
        tags={'Team': 'DevOps', 'Purpose': 'Monitoring'}
    )
    
    dataset_result = manager.create_enterprise_dataset(ops_dataset)
    
    # Create operational dashboard
    ops_dashboard = QuickSightDashboard(
        dashboard_id="operational-monitoring-dashboard",
        name="Operational Monitoring Dashboard",
        definition={
            'DataSetIdentifierDeclarations': [
                {
                    'DataSetArn': dataset_result['arn'],
                    'Identifier': 'ops_data'
                }
            ],
            'Sheets': [
                {
                    'SheetId': 'infrastructure-health',
                    'Name': 'Infrastructure Health',
                    'Visuals': [
                        {
                            'LineChartVisual': {
                                'VisualId': 'cpu-utilization',
                                'Title': {'Visibility': 'VISIBLE', 'Label': 'CPU Utilization Over Time'},
                                'FieldWells': {
                                    'LineChartAggregatedFieldWells': {
                                        'Category': [{'DateDimensionField': {'FieldId': 'timestamp', 'Column': {'DataSetIdentifier': 'ops_data', 'ColumnName': 'timestamp'}}}],
                                        'Values': [{'NumericalMeasureField': {'FieldId': 'cpu_metric', 'Column': {'DataSetIdentifier': 'ops_data', 'ColumnName': 'metric_value'}}}],
                                        'Colors': [{'CategoricalDimensionField': {'FieldId': 'service_name', 'Column': {'DataSetIdentifier': 'ops_data', 'ColumnName': 'service_name'}}}]
                                    }
                                }
                            }
                        },
                        {
                            'GaugeChartVisual': {
                                'VisualId': 'system-health-gauge',
                                'Title': {'Visibility': 'VISIBLE', 'Label': 'Overall System Health'},
                                'FieldWells': {
                                    'Values': [{'NumericalMeasureField': {'FieldId': 'health_score', 'Column': {'DataSetIdentifier': 'ops_data', 'ColumnName': 'metric_value'}}}]
                                }
                            }
                        }
                    ]
                },
                {
                    'SheetId': 'error-analysis',
                    'Name': 'Error Analysis',
                    'Visuals': [
                        {
                            'BarChartVisual': {
                                'VisualId': 'errors-by-application',
                                'Title': {'Visibility': 'VISIBLE', 'Label': 'Errors by Application'},
                                'FieldWells': {
                                    'BarChartAggregatedFieldWells': {
                                        'Category': [{'CategoricalDimensionField': {'FieldId': 'application', 'Column': {'DataSetIdentifier': 'ops_data', 'ColumnName': 'application'}}}],
                                        'Values': [{'NumericalMeasureField': {'FieldId': 'error_count', 'Column': {'DataSetIdentifier': 'ops_data', 'ColumnName': 'error_count'}}}]
                                    }
                                }
                            }
                        }
                    ]
                }
            ]
        },
        permissions=[
            {
                'Principal': f'arn:aws:quicksight:us-east-1:123456789012:group/default/DevOpsTeam',
                'Actions': ['quicksight:DescribeDashboard', 'quicksight:ListDashboardVersions', 'quicksight:QueryDashboard']
            },
            {
                'Principal': f'arn:aws:quicksight:us-east-1:123456789012:group/default/ITManagers',
                'Actions': ['quicksight:DescribeDashboard', 'quicksight:QueryDashboard']
            }
        ],
        tags={'Team': 'DevOps', 'Purpose': 'Monitoring'}
    )
    
    dashboard_result = manager.create_executive_dashboard(ops_dashboard)
    
    # Setup automated refresh every 15 minutes
    refresh_schedule = {
        'RefreshType': 'INCREMENTAL_REFRESH',
        'TimeOfTheDay': '00:00',
        'Timezone': 'UTC'
    }
    
    refresh_result = manager.setup_automated_refresh(
        dataset_result['data_set_id'],
        refresh_schedule
    )
    
    return {
        'data_sources': datasources,
        'dataset': dataset_result,
        'dashboard': dashboard_result,
        'refresh_schedule': refresh_result
    }
```

## DevOps Integration Patterns

### Infrastructure as Code (Terraform)

```hcl
# quicksight_infrastructure.tf
resource "aws_quicksight_data_source" "enterprise_redshift" {
  data_source_id = "enterprise-redshift-source"
  name           = "Enterprise Redshift Analytics"
  type           = "REDSHIFT"
  
  aws_account_id = var.aws_account_id
  
  data_source_parameters {
    redshift {
      host      = aws_redshift_cluster.analytics.endpoint
      port      = aws_redshift_cluster.analytics.port
      database  = aws_redshift_cluster.analytics.database_name
    }
  }
  
  credentials {
    credential_pair {
      username = var.redshift_username
      password = var.redshift_password
    }
  }
  
  permission {
    principal = "arn:aws:quicksight:${var.aws_region}:${var.aws_account_id}:group/default/Analysts"
    actions = [
      "quicksight:DescribeDataSource",
      "quicksight:DescribeDataSourcePermissions",
      "quicksight:PassDataSource",
      "quicksight:UpdateDataSource",
      "quicksight:UpdateDataSourcePermissions"
    ]
  }
  
  tags = {
    Environment = var.environment
    Department  = "Analytics"
    Purpose     = "EnterpriseBI"
  }
}

resource "aws_quicksight_data_set" "enterprise_kpis" {
  data_set_id = "enterprise-kpi-dataset"
  name        = "Enterprise KPI Dataset"
  
  aws_account_id = var.aws_account_id
  import_mode    = "SPICE"
  
  physical_table_map {
    physical_table_id = "kpi-table"
    relational_table {
      data_source_arn = aws_quicksight_data_source.enterprise_redshift.arn
      catalog         = "analytics"
      schema          = "kpis"
      name            = "enterprise_metrics"
      
      input_columns {
        name = "date"
        type = "DATETIME"
      }
      
      input_columns {
        name = "revenue"
        type = "DECIMAL"
      }
      
      input_columns {
        name = "profit_margin"
        type = "DECIMAL"
      }
      
      input_columns {
        name = "customer_count"
        type = "INTEGER"
      }
    }
  }
  
  refresh_properties {
    refresh_configuration {
      incremental_refresh {
        lookback_window {
          column_name = "date"
          size        = 1
          size_unit   = "DAY"
        }
      }
    }
  }
  
  tags = {
    Environment = var.environment
    Department  = "Executive"
    DataType    = "KPIs"
  }
}

resource "aws_quicksight_dashboard" "executive_dashboard" {
  dashboard_id   = "executive-kpi-dashboard"
  name           = "Executive KPI Dashboard"
  version_description = "Executive dashboard for key performance indicators"
  
  aws_account_id = var.aws_account_id
  
  source_entity {
    source_template {
      data_set_references {
        data_set_arn         = aws_quicksight_data_set.enterprise_kpis.arn
        data_set_placeholder = "kpi_data"
      }
      arn = aws_quicksight_template.executive_template.arn
    }
  }
  
  dashboard_publish_options {
    ad_hoc_filtering_option {
      availability_status = "ENABLED"
    }
    export_to_csv_option {
      availability_status = "ENABLED"
    }
    sheet_controls_option {
      visibility_state = "EXPANDED"
    }
  }
  
  permission {
    principal = "arn:aws:quicksight:${var.aws_region}:${var.aws_account_id}:group/default/Executives"
    actions = [
      "quicksight:DescribeDashboard",
      "quicksight:ListDashboardVersions",
      "quicksight:QueryDashboard"
    ]
  }
  
  tags = {
    Environment = var.environment
    Department  = "Executive"
    Audience    = "C-Level"
  }
}

resource "aws_quicksight_refresh_schedule" "daily_refresh" {
  data_set_id = aws_quicksight_data_set.enterprise_kpis.data_set_id
  aws_account_id = var.aws_account_id
  
  schedule {
    schedule_id       = "daily-morning-refresh"
    refresh_type      = "FULL_REFRESH"
    start_after_date_time = "2024-01-01T06:00:00.000Z"
    
    schedule_frequency {
      interval = "DAILY"
      time_of_the_day = "06:00"
      timezone = "America/New_York"
    }
  }
}
```

### CI/CD Pipeline Integration

```yaml
# .github/workflows/quicksight-deployment.yml
name: QuickSight BI Deployment

on:
  push:
    branches: [main]
    paths: ['quicksight/**']
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
  validate-definitions:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Validate Dashboard Definitions
      run: |
        python scripts/validate_quicksight_definitions.py \
          --definitions-dir quicksight/definitions/ \
          --environment ${{ github.event.inputs.environment || 'development' }}

  deploy-data-sources:
    needs: validate-definitions
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        role-to-assume: ${{ secrets.AWS_QUICKSIGHT_ROLE }}
        aws-region: us-east-1
    
    - name: Deploy Data Sources
      run: |
        python scripts/deploy_quicksight_datasources.py \
          --config-file quicksight/config/datasources.json \
          --environment ${{ github.event.inputs.environment || 'development' }}

  deploy-datasets:
    needs: deploy-data-sources
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        role-to-assume: ${{ secrets.AWS_QUICKSIGHT_ROLE }}
        aws-region: us-east-1
    
    - name: Deploy Datasets
      run: |
        python scripts/deploy_quicksight_datasets.py \
          --config-file quicksight/config/datasets.json \
          --environment ${{ github.event.inputs.environment || 'development' }}

  deploy-dashboards:
    needs: deploy-datasets
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        role-to-assume: ${{ secrets.AWS_QUICKSIGHT_ROLE }}
        aws-region: us-east-1
    
    - name: Deploy Dashboards
      run: |
        python scripts/deploy_quicksight_dashboards.py \
          --config-file quicksight/config/dashboards.json \
          --environment ${{ github.event.inputs.environment || 'development' }}
    
    - name: Test Dashboard Functionality
      run: |
        python scripts/test_quicksight_dashboards.py \
          --environment ${{ github.event.inputs.environment || 'development' }} \
          --test-queries quicksight/tests/
```

## Practical Use Cases

### 1. Executive KPI Monitoring
- **Real-time business metrics** with automated alerts
- **C-level dashboards** with strategic insights
- **Performance tracking** across departments
- **Trend analysis** and forecasting capabilities

### 2. Sales Analytics Platform
- **Sales performance tracking** with regional breakdowns
- **Customer segmentation** and behavior analysis
- **Product performance** and profitability insights
- **Sales team performance** monitoring

### 3. Financial Reporting & Compliance
- **Automated financial statements** with audit trails
- **Regulatory compliance** dashboards
- **Budget vs. actual** analysis and variance reporting
- **Cash flow monitoring** and forecasting

### 4. Operational Monitoring
- **Infrastructure health** dashboards
- **Application performance** monitoring
- **Error tracking** and alert systems
- **Capacity planning** and resource optimization

### 5. Customer Analytics
- **Customer journey** visualization
- **Churn prediction** and retention analysis
- **Product usage** patterns and adoption metrics
- **Customer satisfaction** tracking

## Advanced Features

- **ML-powered insights** with anomaly detection
- **Natural language queries** with Q&A
- **Embedded analytics** for applications
- **Row-level security** for data governance
- **SPICE acceleration** for fast queries
- **Mobile optimization** for executives

## Cost Optimization

- **Pay-per-session pricing** for occasional users
- **SPICE optimization** for frequently accessed data
- **Data source efficiency** with query optimization
- **User role management** to control access costs
- **Automated refresh scheduling** during off-peak hours
- **Resource monitoring** and usage analytics