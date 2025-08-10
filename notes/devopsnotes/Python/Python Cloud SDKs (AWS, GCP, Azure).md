## Cloud SDK Automation with Python

### AWS Boto3 Production Patterns
```python
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from botocore.config import Config
import concurrent.futures
from typing import List, Dict, Optional, Generator

class ProductionAWSManager:
    """Production-ready AWS resource management"""
    
    def __init__(self, region: str = 'us-west-2', profile: Optional[str] = None):
        # Configure retry and timeout settings
        config = Config(
            region_name=region,
            retries={'max_attempts': 3, 'mode': 'adaptive'},
            max_pool_connections=50
        )
        
        self.session = boto3.Session(profile_name=profile)
        self.ec2 = self.session.client('ec2', config=config)
        self.s3 = self.session.client('s3', config=config)
        self.rds = self.session.client('rds', config=config)
        self.lambda_client = self.session.client('lambda', config=config)
        self.cloudwatch = self.session.client('cloudwatch', config=config)
        self.sts = self.session.client('sts', config=config)
        self.logger = logging.getLogger(__name__)
    
    def get_account_id(self) -> str:
        """Get current AWS account ID"""
        try:
            response = self.sts.get_caller_identity()
            return response['Account']
        except ClientError as e:
            self.logger.error(f"Failed to get account ID: {e}")
            return ""
    
    def list_ec2_instances(self, filters: Optional[List[Dict]] = None) -> List[Dict]:
        """List EC2 instances with pagination"""
        instances = []
        
        try:
            paginator = self.ec2.get_paginator('describe_instances')
            
            for page in paginator.paginate(Filters=filters or []):
                for reservation in page['Reservations']:
                    for instance in reservation['Instances']:
                        instances.append({
                            'InstanceId': instance['InstanceId'],
                            'InstanceType': instance['InstanceType'],
                            'State': instance['State']['Name'],
                            'LaunchTime': instance['LaunchTime'],
                            'PrivateIpAddress': instance.get('PrivateIpAddress'),
                            'PublicIpAddress': instance.get('PublicIpAddress'),
                            'Tags': {tag['Key']: tag['Value'] 
                                   for tag in instance.get('Tags', [])},
                            'SecurityGroups': [sg['GroupId'] 
                                             for sg in instance['SecurityGroups']],
                            'VpcId': instance.get('VpcId'),
                            'SubnetId': instance.get('SubnetId')
                        })
            
            return instances
            
        except ClientError as e:
            self.logger.error(f"Failed to list EC2 instances: {e}")
            return []
    
    def batch_start_stop_instances(self, instance_ids: List[str], 
                                  action: str) -> Dict[str, List[str]]:
        """Start or stop multiple instances with batch processing"""
        if action not in ['start', 'stop']:
            raise ValueError("Action must be 'start' or 'stop'")
        
        # Batch instances in groups of 100 (AWS limit)
        batch_size = 100
        successful = []
        failed = []
        
        for i in range(0, len(instance_ids), batch_size):
            batch = instance_ids[i:i + batch_size]
            
            try:
                if action == 'start':
                    response = self.ec2.start_instances(InstanceIds=batch)
                    successful.extend([inst['InstanceId'] 
                                     for inst in response['StartingInstances']])
                else:
                    response = self.ec2.stop_instances(InstanceIds=batch)
                    successful.extend([inst['InstanceId'] 
                                     for inst in response['StoppingInstances']])
                
            except ClientError as e:
                self.logger.error(f"Failed to {action} batch {batch}: {e}")
                failed.extend(batch)
        
        return {'successful': successful, 'failed': failed}
    
    def sync_s3_bucket(self, local_path: str, bucket: str, 
                      s3_prefix: str = '', delete: bool = False) -> bool:
        """Sync local directory to S3 bucket"""
        try:
            import os
            from pathlib import Path
            
            local_path = Path(local_path)
            uploaded_files = []
            
            # Upload files
            for local_file in local_path.rglob('*'):
                if local_file.is_file():
                    relative_path = local_file.relative_to(local_path)
                    s3_key = f"{s3_prefix}/{relative_path}".lstrip('/')
                    
                    try:
                        self.s3.upload_file(
                            str(local_file), bucket, s3_key,
                            ExtraArgs={'ServerSideEncryption': 'AES256'}
                        )
                        uploaded_files.append(s3_key)
                        self.logger.info(f"Uploaded: {s3_key}")
                    
                    except ClientError as e:
                        self.logger.error(f"Failed to upload {s3_key}: {e}")
                        return False
            
            # Delete remote files not in local (if delete=True)
            if delete:
                self._delete_extra_s3_files(bucket, s3_prefix, uploaded_files)
            
            return True
            
        except Exception as e:
            self.logger.error(f"S3 sync failed: {e}")
            return False
    
    def get_rds_performance_insights(self, db_instance_id: str, 
                                   hours: int = 24) -> Dict:
        """Get RDS Performance Insights data"""
        from datetime import datetime, timedelta
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        try:
            pi_client = self.session.client('pi')
            
            # Get resource metrics
            response = pi_client.get_resource_metrics(
                ServiceType='RDS',
                Identifier=db_instance_id,
                MetricQueries=[
                    {
                        'Metric': 'db.CPU.Innodb.rows_read.avg',
                        'GroupBy': {'Group': 'db.wait_event'}
                    },
                    {
                        'Metric': 'db.IO.read_latency.avg'
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                PeriodInSeconds=3600
            )
            
            return response
            
        except ClientError as e:
            self.logger.error(f"Failed to get PI data for {db_instance_id}: {e}")
            return {}
    
    def deploy_lambda_function(self, function_name: str, 
                              zip_file_path: str,
                              runtime: str = 'python3.9',
                              handler: str = 'lambda_function.lambda_handler',
                              environment_vars: Optional[Dict] = None) -> bool:
        """Deploy Lambda function with configuration"""
        try:
            with open(zip_file_path, 'rb') as zip_file:
                zip_content = zip_file.read()
            
            # Check if function exists
            try:
                self.lambda_client.get_function(FunctionName=function_name)
                # Update existing function
                self.lambda_client.update_function_code(
                    FunctionName=function_name,
                    ZipFile=zip_content
                )
                self.logger.info(f"Updated Lambda function: {function_name}")
            
            except self.lambda_client.exceptions.ResourceNotFoundException:
                # Create new function
                self.lambda_client.create_function(
                    FunctionName=function_name,
                    Runtime=runtime,
                    Role=f"arn:aws:iam::{self.get_account_id()}:role/lambda-execution-role",
                    Handler=handler,
                    Code={'ZipFile': zip_content},
                    Environment={
                        'Variables': environment_vars or {}
                    },
                    Timeout=300,
                    MemorySize=512
                )
                self.logger.info(f"Created Lambda function: {function_name}")
            
            return True
            
        except ClientError as e:
            self.logger.error(f"Failed to deploy Lambda function {function_name}: {e}")
            return False
```

### Google Cloud Platform Integration
```python
from google.cloud import compute_v1, storage, monitoring_v3
from google.api_core import exceptions as gcp_exceptions
from google.oauth2 import service_account
import json
from typing import Iterator

class GCPManager:
    """Production GCP resource management"""
    
    def __init__(self, project_id: str, credentials_path: Optional[str] = None):
        self.project_id = project_id
        
        # Initialize credentials
        if credentials_path:
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path
            )
        else:
            credentials = None  # Use default credentials
        
        # Initialize clients
        self.compute_client = compute_v1.InstancesClient(credentials=credentials)
        self.storage_client = storage.Client(
            project=project_id, 
            credentials=credentials
        )
        self.monitoring_client = monitoring_v3.MetricServiceClient(
            credentials=credentials
        )
        self.logger = logging.getLogger(__name__)
    
    def list_compute_instances(self, zone: str) -> List[Dict]:
        """List Compute Engine instances in zone"""
        instances = []
        
        try:
            request = compute_v1.ListInstancesRequest(
                project=self.project_id,
                zone=zone
            )
            
            for instance in self.compute_client.list(request=request):
                instances.append({
                    'name': instance.name,
                    'machine_type': instance.machine_type.split('/')[-1],
                    'status': instance.status,
                    'zone': zone,
                    'internal_ip': instance.network_interfaces[0].network_i_p 
                                 if instance.network_interfaces else None,
                    'external_ip': instance.network_interfaces[0].access_configs[0].nat_i_p
                                 if (instance.network_interfaces and 
                                     instance.network_interfaces[0].access_configs) else None,
                    'labels': dict(instance.labels),
                    'creation_timestamp': instance.creation_timestamp
                })
            
            return instances
            
        except gcp_exceptions.GoogleAPIError as e:
            self.logger.error(f"Failed to list instances in {zone}: {e}")
            return []
    
    def start_stop_instance(self, zone: str, instance_name: str, 
                           action: str) -> bool:
        """Start or stop Compute Engine instance"""
        if action not in ['start', 'stop']:
            raise ValueError("Action must be 'start' or 'stop'")
        
        try:
            if action == 'start':
                request = compute_v1.StartInstanceRequest(
                    project=self.project_id,
                    zone=zone,
                    instance=instance_name
                )
                operation = self.compute_client.start(request=request)
            else:
                request = compute_v1.StopInstanceRequest(
                    project=self.project_id,
                    zone=zone,
                    instance=instance_name
                )
                operation = self.compute_client.stop(request=request)
            
            # Wait for operation to complete
            self._wait_for_operation(operation, zone)
            
            self.logger.info(f"Successfully {action}ed instance {instance_name}")
            return True
            
        except gcp_exceptions.GoogleAPIError as e:
            self.logger.error(f"Failed to {action} instance {instance_name}: {e}")
            return False
    
    def upload_to_gcs(self, bucket_name: str, source_file_path: str, 
                     destination_blob_name: str) -> bool:
        """Upload file to Google Cloud Storage"""
        try:
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(destination_blob_name)
            
            blob.upload_from_filename(source_file_path)
            
            self.logger.info(f"Uploaded {source_file_path} to gs://{bucket_name}/{destination_blob_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to upload to GCS: {e}")
            return False
    
    def get_monitoring_metrics(self, metric_type: str, hours: int = 1) -> List[Dict]:
        """Get monitoring metrics from Stackdriver"""
        from datetime import datetime, timedelta
        from google.cloud.monitoring_v3 import query
        
        try:
            now = datetime.utcnow()
            start_time = now - timedelta(hours=hours)
            
            interval = monitoring_v3.TimeInterval({
                "end_time": {"seconds": int(now.timestamp())},
                "start_time": {"seconds": int(start_time.timestamp())}
            })
            
            client = monitoring_v3.MetricServiceClient()
            project_name = f"projects/{self.project_id}"
            
            request = monitoring_v3.ListTimeSeriesRequest({
                "name": project_name,
                "filter": f'metric.type="{metric_type}"',
                "interval": interval,
                "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL
            })
            
            results = []
            for time_series in client.list_time_series(request=request):
                results.append({
                    'metric': dict(time_series.metric.labels),
                    'resource': dict(time_series.resource.labels),
                    'points': [
                        {
                            'timestamp': point.interval.end_time.seconds,
                            'value': point.value.double_value or point.value.int64_value
                        }
                        for point in time_series.points
                    ]
                })
            
            return results
            
        except gcp_exceptions.GoogleAPIError as e:
            self.logger.error(f"Failed to get metrics {metric_type}: {e}")
            return []
```

### Azure SDK Integration
```python
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.monitor import MonitorManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import AzureError

class AzureManager:
    """Production Azure resource management"""
    
    def __init__(self, subscription_id: str, 
                 tenant_id: Optional[str] = None,
                 client_id: Optional[str] = None,
                 client_secret: Optional[str] = None):
        
        self.subscription_id = subscription_id
        
        # Initialize credentials
        if all([tenant_id, client_id, client_secret]):
            credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
        else:
            credential = DefaultAzureCredential()
        
        # Initialize management clients
        self.compute_client = ComputeManagementClient(
            credential, subscription_id
        )
        self.storage_client = StorageManagementClient(
            credential, subscription_id
        )
        self.monitor_client = MonitorManagementClient(
            credential, subscription_id
        )
        self.resource_client = ResourceManagementClient(
            credential, subscription_id
        )
        
        self.logger = logging.getLogger(__name__)
    
    def list_virtual_machines(self, resource_group: Optional[str] = None) -> List[Dict]:
        """List virtual machines in subscription or resource group"""
        vms = []
        
        try:
            if resource_group:
                vm_list = self.compute_client.virtual_machines.list(resource_group)
            else:
                vm_list = self.compute_client.virtual_machines.list_all()
            
            for vm in vm_list:
                # Get VM instance view for power state
                instance_view = self.compute_client.virtual_machines.instance_view(
                    vm.id.split('/')[4],  # resource group name
                    vm.name
                )
                
                power_state = 'unknown'
                for status in instance_view.statuses:
                    if status.code.startswith('PowerState/'):
                        power_state = status.code.split('/')[-1]
                        break
                
                vms.append({
                    'name': vm.name,
                    'resource_group': vm.id.split('/')[4],
                    'location': vm.location,
                    'vm_size': vm.hardware_profile.vm_size,
                    'power_state': power_state,
                    'os_type': vm.storage_profile.os_disk.os_type.value,
                    'tags': vm.tags or {},
                    'network_interfaces': [nic.id for nic in vm.network_profile.network_interfaces]
                })
            
            return vms
            
        except AzureError as e:
            self.logger.error(f"Failed to list VMs: {e}")
            return []
    
    def start_stop_vm(self, resource_group: str, vm_name: str, 
                     action: str) -> bool:
        """Start or stop Azure VM"""
        if action not in ['start', 'stop']:
            raise ValueError("Action must be 'start' or 'stop'")
        
        try:
            if action == 'start':
                operation = self.compute_client.virtual_machines.begin_start(
                    resource_group, vm_name
                )
            else:
                operation = self.compute_client.virtual_machines.begin_power_off(
                    resource_group, vm_name
                )
            
            # Wait for completion
            result = operation.result()
            
            self.logger.info(f"Successfully {action}ed VM {vm_name}")
            return True
            
        except AzureError as e:
            self.logger.error(f"Failed to {action} VM {vm_name}: {e}")
            return False
    
    def create_storage_account(self, resource_group: str, 
                              account_name: str, 
                              location: str = 'East US') -> bool:
        """Create Azure Storage Account"""
        from azure.mgmt.storage.models import (
            StorageAccountCreateParameters,
            StorageAccountPropertiesCreateParameters,
            Kind,
            Sku,
            SkuName
        )
        
        try:
            storage_params = StorageAccountCreateParameters(
                sku=Sku(name=SkuName.STANDARD_LRS),
                kind=Kind.STORAGE_V2,
                location=location,
                properties=StorageAccountPropertiesCreateParameters(
                    encryption={
                        'services': {
                            'blob': {'enabled': True},
                            'file': {'enabled': True}
                        },
                        'key_source': 'Microsoft.Storage'
                    }
                )
            )
            
            operation = self.storage_client.storage_accounts.begin_create(
                resource_group, account_name, storage_params
            )
            
            result = operation.result()
            
            self.logger.info(f"Created storage account {account_name}")
            return True
            
        except AzureError as e:
            self.logger.error(f"Failed to create storage account {account_name}: {e}")
            return False
    
    def get_resource_metrics(self, resource_uri: str, 
                           metric_names: List[str],
                           hours: int = 1) -> Dict:
        """Get Azure Monitor metrics for resource"""
        from datetime import datetime, timedelta
        
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            metrics_data = self.monitor_client.metrics.list(
                resource_uri=resource_uri,
                timespan=f"{start_time.isoformat()}/{end_time.isoformat()}",
                interval='PT1M',
                metricnames=','.join(metric_names),
                aggregation='Average'
            )
            
            result = {}
            for metric in metrics_data.value:
                result[metric.name.value] = []
                for timeseries in metric.timeseries:
                    for data_point in timeseries.data:
                        if data_point.average is not None:
                            result[metric.name.value].append({
                                'timestamp': data_point.time_stamp.isoformat(),
                                'value': data_point.average
                            })
            
            return result
            
        except AzureError as e:
            self.logger.error(f"Failed to get metrics for {resource_uri}: {e}")
            return {}
```

### Multi-Cloud Resource Manager
```python
from enum import Enum
from typing import Union

class CloudProvider(Enum):
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"

class MultiCloudManager:
    """Unified interface for multi-cloud operations"""
    
    def __init__(self, configs: Dict[CloudProvider, Dict]):
        self.aws = ProductionAWSManager(**configs.get(CloudProvider.AWS, {})) if CloudProvider.AWS in configs else None
        self.gcp = GCPManager(**configs.get(CloudProvider.GCP, {})) if CloudProvider.GCP in configs else None
        self.azure = AzureManager(**configs.get(CloudProvider.AZURE, {})) if CloudProvider.AZURE in configs else None
        self.logger = logging.getLogger(__name__)
    
    def list_all_instances(self) -> Dict[CloudProvider, List[Dict]]:
        """List instances from all configured cloud providers"""
        all_instances = {}
        
        if self.aws:
            all_instances[CloudProvider.AWS] = self.aws.list_ec2_instances()
        
        if self.gcp:
            # Assume we have zones configured
            gcp_instances = []
            for zone in ['us-central1-a', 'us-central1-b']:  # Configure as needed
                gcp_instances.extend(self.gcp.list_compute_instances(zone))
            all_instances[CloudProvider.GCP] = gcp_instances
        
        if self.azure:
            all_instances[CloudProvider.AZURE] = self.azure.list_virtual_machines()
        
        return all_instances
    
    def get_cost_optimization_recommendations(self) -> Dict[CloudProvider, List[str]]:
        """Get cost optimization recommendations across all clouds"""
        recommendations = {}
        
        if self.aws:
            recommendations[CloudProvider.AWS] = self._get_aws_cost_recommendations()
        
        if self.gcp:
            recommendations[CloudProvider.GCP] = self._get_gcp_cost_recommendations()
        
        if self.azure:
            recommendations[CloudProvider.AZURE] = self._get_azure_cost_recommendations()
        
        return recommendations
    
    def _get_aws_cost_recommendations(self) -> List[str]:
        """Get AWS-specific cost recommendations"""
        recommendations = []
        
        # Check for unused EBS volumes
        ec2 = self.aws.ec2
        volumes = ec2.describe_volumes()
        
        for volume in volumes['Volumes']:
            if volume['State'] == 'available':
                recommendations.append(
                    f"Delete unused EBS volume: {volume['VolumeId']} "
                    f"({volume['Size']}GB, ${volume['Size'] * 0.10:.2f}/month)"
                )
        
        # Check for stopped instances (still incurring EBS costs)
        instances = self.aws.list_ec2_instances([
            {'Name': 'instance-state-name', 'Values': ['stopped']}
        ])
        
        for instance in instances:
            recommendations.append(
                f"Consider terminating stopped instance: {instance['InstanceId']} "
                f"({instance['InstanceType']}) - still incurring storage costs"
            )
        
        return recommendations
```

This provides comprehensive cloud SDK integration patterns for AWS, GCP, and Azure with production-ready error handling, batch operations, and multi-cloud management capabilities.