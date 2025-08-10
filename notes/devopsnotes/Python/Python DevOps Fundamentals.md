## Production Python for DevOps Engineers

### Essential Libraries for DevOps
```python
# Infrastructure & Cloud
import boto3              # AWS SDK
import google.cloud       # GCP SDK  
import azure.mgmt         # Azure SDK
import kubernetes         # K8s client
import terraform_external_data  # Terraform integration

# Automation & Scripting
import paramiko          # SSH automation
import fabric            # Remote execution
import ansible_runner    # Ansible integration
import subprocess        # Shell command execution
import psutil            # System monitoring

# Configuration & Data
import yaml              # Config file parsing
import json              # API responses
import configparser      # INI files
import jinja2            # Template rendering
import click             # CLI applications

# Monitoring & Logging
import prometheus_client # Metrics
import logging           # Structured logging
import requests          # HTTP/API calls
import urllib3           # HTTP client
```

### Production DevOps Script Structure
```python
#!/usr/bin/env python3
"""
Production-ready DevOps script template
"""
import logging
import sys
import argparse
import os
from typing import Optional, Dict, List
from dataclasses import dataclass
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/devops-script.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Config:
    """Configuration class for script parameters"""
    environment: str
    aws_region: str
    dry_run: bool = False
    timeout: int = 300
    
    @classmethod
    def from_env(cls) -> 'Config':
        return cls(
            environment=os.getenv('ENVIRONMENT', 'development'),
            aws_region=os.getenv('AWS_REGION', 'us-west-2'),
            dry_run=os.getenv('DRY_RUN', 'false').lower() == 'true',
            timeout=int(os.getenv('TIMEOUT', '300'))
        )

class DevOpsOperation:
    """Base class for DevOps operations"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def execute(self) -> bool:
        """Execute the operation with error handling"""
        try:
            self.logger.info(f"Starting operation in {self.config.environment}")
            
            if self.config.dry_run:
                self.logger.info("DRY RUN MODE - No changes will be made")
                return self.dry_run_execute()
            
            return self.run_operation()
            
        except Exception as e:
            self.logger.error(f"Operation failed: {str(e)}")
            return False
    
    def dry_run_execute(self) -> bool:
        """Override for dry run logic"""
        self.logger.info("Would execute operation")
        return True
    
    def run_operation(self) -> bool:
        """Override for actual operation logic"""
        raise NotImplementedError

def main():
    parser = argparse.ArgumentParser(description='DevOps Automation Script')
    parser.add_argument('--environment', required=True, 
                       choices=['dev', 'staging', 'prod'],
                       help='Target environment')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    
    args = parser.parse_args()
    
    config = Config.from_env()
    config.environment = args.environment
    config.dry_run = args.dry_run
    
    operation = DevOpsOperation(config)
    success = operation.execute()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
```

### AWS Resource Management
```python
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from typing import List, Dict, Optional

class AWSResourceManager:
    """Production AWS resource management"""
    
    def __init__(self, region: str = 'us-west-2'):
        self.region = region
        self.session = boto3.Session()
        self.ec2 = self.session.client('ec2', region_name=region)
        self.s3 = self.session.client('s3')
        self.rds = self.session.client('rds', region_name=region)
        self.logger = logging.getLogger(__name__)
    
    def get_instances_by_tag(self, tag_key: str, tag_value: str) -> List[Dict]:
        """Get EC2 instances by tag with error handling"""
        try:
            response = self.ec2.describe_instances(
                Filters=[
                    {'Name': f'tag:{tag_key}', 'Values': [tag_value]},
                    {'Name': 'instance-state-name', 'Values': ['running', 'stopped']}
                ]
            )
            
            instances = []
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instances.append({
                        'InstanceId': instance['InstanceId'],
                        'State': instance['State']['Name'],
                        'InstanceType': instance['InstanceType'],
                        'LaunchTime': instance['LaunchTime'],
                        'Tags': {tag['Key']: tag['Value'] 
                                for tag in instance.get('Tags', [])}
                    })
            
            return instances
            
        except ClientError as e:
            self.logger.error(f"AWS API error: {e}")
            return []
    
    def stop_instances(self, instance_ids: List[str], dry_run: bool = False) -> bool:
        """Stop EC2 instances with safety checks"""
        try:
            if dry_run:
                self.logger.info(f"DRY RUN: Would stop instances: {instance_ids}")
                return True
            
            # Safety check - don't stop production instances
            for instance_id in instance_ids:
                instance = self.ec2.describe_instances(InstanceIds=[instance_id])
                tags = {}
                for reservation in instance['Reservations']:
                    for inst in reservation['Instances']:
                        tags = {tag['Key']: tag['Value'] 
                               for tag in inst.get('Tags', [])}
                
                if tags.get('Environment', '').lower() == 'production':
                    self.logger.error(f"Refusing to stop production instance: {instance_id}")
                    return False
            
            response = self.ec2.stop_instances(InstanceIds=instance_ids)
            self.logger.info(f"Successfully stopped instances: {instance_ids}")
            return True
            
        except ClientError as e:
            self.logger.error(f"Failed to stop instances: {e}")
            return False
    
    def cleanup_unused_snapshots(self, days_old: int = 30) -> List[str]:
        """Clean up EBS snapshots older than specified days"""
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        deleted_snapshots = []
        
        try:
            snapshots = self.ec2.describe_snapshots(OwnerIds=['self'])
            
            for snapshot in snapshots['Snapshots']:
                start_time = snapshot['StartTime'].replace(tzinfo=None)
                
                if start_time < cutoff_date:
                    # Check if snapshot is used by any AMI
                    try:
                        images = self.ec2.describe_images(
                            Filters=[{
                                'Name': 'block-device-mapping.snapshot-id',
                                'Values': [snapshot['SnapshotId']]
                            }]
                        )
                        
                        if not images['Images']:
                            self.ec2.delete_snapshot(SnapshotId=snapshot['SnapshotId'])
                            deleted_snapshots.append(snapshot['SnapshotId'])
                            self.logger.info(f"Deleted snapshot: {snapshot['SnapshotId']}")
                    
                    except ClientError as e:
                        self.logger.warning(f"Could not delete snapshot {snapshot['SnapshotId']}: {e}")
            
            return deleted_snapshots
            
        except ClientError as e:
            self.logger.error(f"Failed to cleanup snapshots: {e}")
            return []
```

### Kubernetes Automation
```python
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import yaml
from typing import Dict, List, Optional

class KubernetesManager:
    """Production Kubernetes management"""
    
    def __init__(self, kubeconfig_path: Optional[str] = None):
        if kubeconfig_path:
            config.load_kube_config(config_file=kubeconfig_path)
        else:
            try:
                config.load_incluster_config()  # For pods running in cluster
            except:
                config.load_kube_config()  # For local development
        
        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.logger = logging.getLogger(__name__)
    
    def get_pod_logs(self, namespace: str, pod_name: str, 
                     container: Optional[str] = None, 
                     tail_lines: int = 100) -> str:
        """Get pod logs with error handling"""
        try:
            logs = self.v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container,
                tail_lines=tail_lines
            )
            return logs
        
        except ApiException as e:
            self.logger.error(f"Failed to get logs for pod {pod_name}: {e}")
            return ""
    
    def scale_deployment(self, namespace: str, deployment_name: str, 
                        replicas: int) -> bool:
        """Scale deployment with validation"""
        try:
            # Get current deployment
            deployment = self.apps_v1.read_namespaced_deployment(
                name=deployment_name, 
                namespace=namespace
            )
            
            # Update replica count
            deployment.spec.replicas = replicas
            
            # Apply update
            self.apps_v1.patch_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=deployment
            )
            
            self.logger.info(f"Scaled {deployment_name} to {replicas} replicas")
            return True
            
        except ApiException as e:
            self.logger.error(f"Failed to scale deployment {deployment_name}: {e}")
            return False
    
    def apply_manifest(self, manifest_path: str, namespace: str) -> bool:
        """Apply Kubernetes manifest from file"""
        try:
            with open(manifest_path, 'r') as f:
                manifests = yaml.safe_load_all(f)
            
            for manifest in manifests:
                if not manifest:
                    continue
                
                kind = manifest['kind']
                name = manifest['metadata']['name']
                
                if kind == 'Deployment':
                    self.apps_v1.create_namespaced_deployment(
                        namespace=namespace, 
                        body=manifest
                    )
                elif kind == 'Service':
                    self.v1.create_namespaced_service(
                        namespace=namespace,
                        body=manifest
                    )
                elif kind == 'ConfigMap':
                    self.v1.create_namespaced_config_map(
                        namespace=namespace,
                        body=manifest
                    )
                
                self.logger.info(f"Applied {kind}/{name} to namespace {namespace}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to apply manifest {manifest_path}: {e}")
            return False
    
    def check_pod_health(self, namespace: str, label_selector: str) -> Dict:
        """Check health status of pods matching label selector"""
        try:
            pods = self.v1.list_namespaced_pod(
                namespace=namespace,
                label_selector=label_selector
            )
            
            health_status = {
                'total_pods': len(pods.items),
                'running': 0,
                'pending': 0,
                'failed': 0,
                'unhealthy_pods': []
            }
            
            for pod in pods.items:
                phase = pod.status.phase
                
                if phase == 'Running':
                    # Check if all containers are ready
                    if pod.status.container_statuses:
                        all_ready = all(cs.ready for cs in pod.status.container_statuses)
                        if all_ready:
                            health_status['running'] += 1
                        else:
                            health_status['unhealthy_pods'].append({
                                'name': pod.metadata.name,
                                'reason': 'containers_not_ready'
                            })
                elif phase == 'Pending':
                    health_status['pending'] += 1
                elif phase == 'Failed':
                    health_status['failed'] += 1
                    health_status['unhealthy_pods'].append({
                        'name': pod.metadata.name,
                        'reason': phase
                    })
            
            return health_status
            
        except ApiException as e:
            self.logger.error(f"Failed to check pod health: {e}")
            return {}
```

### Monitoring & Alerting
```python
from prometheus_client import CollectorRegistry, Gauge, Counter, push_to_gateway
import requests
import time
from typing import Dict, Any

class DevOpsMetrics:
    """DevOps metrics collection and alerting"""
    
    def __init__(self, pushgateway_url: str = 'http://pushgateway:9091'):
        self.pushgateway_url = pushgateway_url
        self.registry = CollectorRegistry()
        
        # Define metrics
        self.deployment_duration = Gauge(
            'deployment_duration_seconds',
            'Time taken for deployment',
            ['service', 'environment'],
            registry=self.registry
        )
        
        self.deployment_status = Counter(
            'deployment_total',
            'Total deployments',
            ['service', 'environment', 'status'],
            registry=self.registry
        )
        
        self.resource_usage = Gauge(
            'resource_usage_percent',
            'Resource usage percentage',
            ['resource_type', 'instance'],
            registry=self.registry
        )
        
        self.logger = logging.getLogger(__name__)
    
    def track_deployment(self, service: str, environment: str):
        """Context manager for tracking deployment metrics"""
        class DeploymentTracker:
            def __init__(self, metrics, service, environment):
                self.metrics = metrics
                self.service = service
                self.environment = environment
                self.start_time = None
            
            def __enter__(self):
                self.start_time = time.time()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                duration = time.time() - self.start_time
                self.metrics.deployment_duration.labels(
                    service=self.service, 
                    environment=self.environment
                ).set(duration)
                
                status = 'failed' if exc_type else 'success'
                self.metrics.deployment_status.labels(
                    service=self.service,
                    environment=self.environment,
                    status=status
                ).inc()
                
                self.metrics.push_metrics()
        
        return DeploymentTracker(self, service, environment)
    
    def record_resource_usage(self, resource_type: str, instance: str, usage: float):
        """Record resource usage metrics"""
        self.resource_usage.labels(
            resource_type=resource_type,
            instance=instance
        ).set(usage)
    
    def push_metrics(self):
        """Push metrics to Prometheus pushgateway"""
        try:
            push_to_gateway(
                self.pushgateway_url,
                job='devops-automation',
                registry=self.registry
            )
            self.logger.info("Metrics pushed successfully")
        except Exception as e:
            self.logger.error(f"Failed to push metrics: {e}")
    
    def send_slack_alert(self, webhook_url: str, message: str, severity: str = 'info'):
        """Send alert to Slack"""
        colors = {
            'info': '#36a64f',
            'warning': '#ff9500', 
            'error': '#ff0000'
        }
        
        payload = {
            'attachments': [{
                'color': colors.get(severity, '#36a64f'),
                'title': f'{severity.upper()}: DevOps Alert',
                'text': message,
                'timestamp': int(time.time())
            }]
        }
        
        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            self.logger.info(f"Alert sent to Slack: {message}")
        except requests.RequestException as e:
            self.logger.error(f"Failed to send Slack alert: {e}")
```

### Configuration Management
```python
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader

class ConfigManager:
    """Production configuration management"""
    
    def __init__(self, config_dir: str = '/etc/devops-configs'):
        self.config_dir = Path(config_dir)
        self.templates_dir = self.config_dir / 'templates'
        self.environments = ['dev', 'staging', 'prod']
        self.logger = logging.getLogger(__name__)
    
    def load_config(self, environment: str, service: str) -> Optional[Dict[str, Any]]:
        """Load configuration for environment and service"""
        config_file = self.config_dir / environment / f'{service}.yml'
        
        if not config_file.exists():
            self.logger.error(f"Config file not found: {config_file}")
            return None
        
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            # Merge with common config if exists
            common_file = self.config_dir / 'common.yml'
            if common_file.exists():
                with open(common_file, 'r') as f:
                    common_config = yaml.safe_load(f)
                
                # Deep merge configurations
                config = self._deep_merge(common_config, config)
            
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to load config {config_file}: {e}")
            return None
    
    def render_template(self, template_name: str, variables: Dict[str, Any]) -> str:
        """Render Jinja2 template with variables"""
        try:
            env = Environment(loader=FileSystemLoader(str(self.templates_dir)))
            template = env.get_template(template_name)
            return template.render(**variables)
        
        except Exception as e:
            self.logger.error(f"Failed to render template {template_name}: {e}")
            return ""
    
    def validate_config(self, config: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Validate configuration against schema"""
        try:
            # Simple validation - could use jsonschema for complex validation
            for key, expected_type in schema.items():
                if key not in config:
                    self.logger.error(f"Missing required config key: {key}")
                    return False
                
                if not isinstance(config[key], expected_type):
                    self.logger.error(f"Config key {key} should be {expected_type}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Config validation failed: {e}")
            return False
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
```

### Error Handling & Retries
```python
import functools
import time
import random
from typing import Callable, Any, Type, Tuple

def retry_with_backoff(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    jitter: bool = True
):
    """Decorator for retrying functions with exponential backoff"""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = logging.getLogger(func.__module__)
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                
                except exceptions as e:
                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries: {e}")
                        raise
                    
                    # Calculate backoff time
                    backoff_time = backoff_factor ** attempt
                    if jitter:
                        backoff_time += random.uniform(0, 1)
                    
                    logger.warning(f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}), retrying in {backoff_time:.2f}s: {e}")
                    time.sleep(backoff_time)
            
        return wrapper
    return decorator

# Usage example
@retry_with_backoff(max_retries=3, exceptions=(requests.RequestException, ConnectionError))
def call_external_api(url: str) -> Dict[str, Any]:
    """Make API call with automatic retries"""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()
```

This gives you production-ready Python patterns for DevOps automation with proper error handling, logging, and monitoring integration.