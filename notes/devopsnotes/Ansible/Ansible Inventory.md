# Enterprise Ansible Inventory Management

Advanced inventory strategies, dynamic discovery, and multi-cloud automation patterns for large-scale infrastructure management.

## Table of Contents
1. [Inventory Architecture Overview](#inventory-architecture-overview)
2. [Advanced Static Inventory](#advanced-static-inventory)
3. [Dynamic Inventory Systems](#dynamic-inventory-systems)
4. [Multi-Cloud Integration](#multi-cloud-integration)
5. [Inventory Plugins & Extensions](#inventory-plugins--extensions)
6. [Security & Access Control](#security--access-control)
7. [Performance Optimization](#performance-optimization)
8. [Enterprise Patterns](#enterprise-patterns)

## Inventory Architecture Overview
```yaml
# Enterprise inventory patterns
inventory_architecture:
  static_inventory:
    description: "Fixed host definitions for stable infrastructure"
    use_cases: ["On-premises servers", "Fixed cloud instances", "Development environments"]
    formats: ["INI", "YAML", "JSON"]
    
  dynamic_inventory:
    description: "Automated host discovery from external sources"
    use_cases: ["Auto-scaling cloud environments", "Container orchestration", "Service discovery"]
    sources: ["Cloud APIs", "CMDB systems", "Container registries", "Kubernetes"]
    
  hybrid_inventory:
    description: "Combination of static and dynamic sources"
    use_cases: ["Mixed environments", "Gradual cloud migration", "Multi-cloud deployments"]
    benefits: ["Flexibility", "Gradual adoption", "Best of both worlds"]
```

## Static Inventory Patterns

### Advanced INI Format Configuration
```ini
# inventory/production/hosts.ini - Enterprise production inventory

# Database cluster with replication setup
[database_primary]
prod-db-01.company.com ansible_host=10.1.1.10 mysql_server_id=1 mysql_role=master
prod-db-02.company.com ansible_host=10.1.1.11 mysql_server_id=2 mysql_role=master

[database_replicas]
prod-db-03.company.com ansible_host=10.1.1.12 mysql_server_id=3 mysql_role=slave mysql_master=prod-db-01
prod-db-04.company.com ansible_host=10.1.1.13 mysql_server_id=4 mysql_role=slave mysql_master=prod-db-02
prod-db-05.company.com ansible_host=10.1.1.14 mysql_server_id=5 mysql_role=slave mysql_master=prod-db-01

[database:children]
database_primary
database_replicas

# Web tier with load balancing
[web_frontend]
prod-web-[01:05].company.com ansible_host_pattern=10.1.2.[10:14]

[web_backend]
prod-api-[01:08].company.com ansible_host_pattern=10.1.2.[20:27]

[web_tier:children]
web_frontend
web_backend

# Application clusters
[app_microservices]
prod-user-service-[01:03].company.com service_type=user_management port=8080
prod-order-service-[01:04].company.com service_type=order_processing port=8081
prod-payment-service-[01:02].company.com service_type=payment_gateway port=8082
prod-notification-service-[01:02].company.com service_type=notifications port=8083

# Infrastructure services
[monitoring]
prod-prometheus-01.company.com ansible_host=10.1.3.10 prometheus_role=server
prod-prometheus-02.company.com ansible_host=10.1.3.11 prometheus_role=replica
prod-grafana-01.company.com ansible_host=10.1.3.12 grafana_role=primary
prod-alertmanager-01.company.com ansible_host=10.1.3.13 alertmanager_role=cluster_member

[logging]
prod-elasticsearch-[01:03].company.com elasticsearch_node_role=data ansible_host_pattern=10.1.3.[20:22]
prod-elasticsearch-04.company.com ansible_host=10.1.3.23 elasticsearch_node_role=master
prod-logstash-[01:02].company.com ansible_host_pattern=10.1.3.[30:31]
prod-kibana-01.company.com ansible_host=10.1.3.35

# Load balancers and proxies
[load_balancers]
prod-lb-01.company.com ansible_host=10.1.0.10 lb_role=primary lb_backend_pool=web_frontend
prod-lb-02.company.com ansible_host=10.1.0.11 lb_role=secondary lb_backend_pool=web_frontend

[reverse_proxy]
prod-proxy-[01:02].company.com ansible_host_pattern=10.1.0.[15:16] proxy_upstream=web_backend

# Network infrastructure
[network_devices]
prod-fw-01.company.com ansible_host=10.1.0.1 device_type=firewall vendor=palo_alto
prod-sw-core-01.company.com ansible_host=10.1.0.2 device_type=switch vendor=cisco layer=core
prod-sw-access-[01:04].company.com device_type=switch vendor=cisco layer=access

# Environment grouping
[production:children]
database
web_tier
app_microservices
monitoring
logging
load_balancers
reverse_proxy

# Functional grouping
[data_tier:children]
database

[application_tier:children]
web_tier
app_microservices

[infrastructure_tier:children]
monitoring
logging
load_balancers
reverse_proxy

# Geographic grouping
[us_east_1]
prod-db-01.company.com
prod-db-02.company.com
prod-web-[01:03].company.com

[us_west_2]
prod-db-03.company.com
prod-db-04.company.com
prod-web-[04:05].company.com

[multi_region:children]
us_east_1
us_west_2
```

### YAML Inventory with Advanced Structure
```yaml
# inventory/production/hosts.yml - Enterprise YAML inventory
all:
  children:
    production:
      children:
        database_cluster:
          children:
            database_primary:
              hosts:
                prod-db-master-01.company.com:
                  ansible_host: 10.1.1.10
                  mysql_server_id: 1
                  mysql_role: master
                  mysql_gtid_mode: ON
                  mysql_enforce_gtid_consistency: ON
                  backup_schedule: "0 2 * * *"
                  monitoring_enabled: true
                  
                prod-db-master-02.company.com:
                  ansible_host: 10.1.1.11
                  mysql_server_id: 2
                  mysql_role: master
                  mysql_gtid_mode: ON
                  mysql_enforce_gtid_consistency: ON
                  backup_schedule: "0 3 * * *"
                  monitoring_enabled: true
            
            database_replicas:
              hosts:
                prod-db-replica-01.company.com:
                  ansible_host: 10.1.1.12
                  mysql_server_id: 3
                  mysql_role: slave
                  mysql_master_host: prod-db-master-01.company.com
                  mysql_read_only: ON
                  
                prod-db-replica-02.company.com:
                  ansible_host: 10.1.1.13
                  mysql_server_id: 4
                  mysql_role: slave
                  mysql_master_host: prod-db-master-02.company.com
                  mysql_read_only: ON
                  
                prod-db-analytics.company.com:
                  ansible_host: 10.1.1.14
                  mysql_server_id: 5
                  mysql_role: analytics_slave
                  mysql_master_host: prod-db-master-01.company.com
                  mysql_read_only: ON
                  mysql_slow_query_log: ON
          
          vars:
            mysql_version: "8.0"
            mysql_root_password: "{{ vault_mysql_root_password }}"
            mysql_backup_user: "backup"
            mysql_backup_password: "{{ vault_mysql_backup_password }}"
            mysql_innodb_buffer_pool_size: "8G"
            mysql_max_connections: 500
            mysql_query_cache_size: 0
            ssl_cert_path: "/etc/ssl/certs/mysql-server.crt"
            ssl_key_path: "/etc/ssl/private/mysql-server.key"
        
        application_services:
          children:
            microservices:
              children:
                user_service:
                  hosts:
                    prod-user-svc-01.company.com:
                      ansible_host: 10.1.2.20
                      service_port: 8080
                      service_version: "v2.1.0"
                      health_check_path: "/health"
                      metrics_port: 9090
                      
                    prod-user-svc-02.company.com:
                      ansible_host: 10.1.2.21
                      service_port: 8080
                      service_version: "v2.1.0"
                      health_check_path: "/health"
                      metrics_port: 9090
                      
                    prod-user-svc-03.company.com:
                      ansible_host: 10.1.2.22
                      service_port: 8080
                      service_version: "v2.0.8"  # Canary deployment
                      health_check_path: "/health"
                      metrics_port: 9090
                      canary_deployment: true
                      traffic_percentage: 10
                  
                  vars:
                    service_name: "user-service"
                    database_connection: "{{ hostvars['prod-db-replica-01.company.com']['ansible_host'] }}"
                    redis_connection: "prod-redis-cluster.company.com:6379"
                    jwt_secret: "{{ vault_jwt_secret }}"
                    log_level: "INFO"
                    max_heap_size: "2G"
                
                order_service:
                  hosts:
                    prod-order-svc-01.company.com:
                      ansible_host: 10.1.2.30
                      service_port: 8081
                      service_version: "v1.5.2"
                      replica_count: 4
                      
                    prod-order-svc-02.company.com:
                      ansible_host: 10.1.2.31
                      service_port: 8081
                      service_version: "v1.5.2"
                      replica_count: 4
                  
                  vars:
                    service_name: "order-service"
                    database_connection: "{{ hostvars['prod-db-master-01.company.com']['ansible_host'] }}"
                    queue_connection: "prod-rabbitmq-cluster.company.com:5672"
                    payment_service_url: "http://prod-payment-svc.company.com:8082"
                    inventory_service_url: "http://prod-inventory-svc.company.com:8084"
        
        infrastructure:
          children:
            monitoring:
              hosts:
                prod-prometheus-01.company.com:
                  ansible_host: 10.1.3.10
                  prometheus_role: server
                  prometheus_storage_retention: "30d"
                  prometheus_storage_size: "500GB"
                  scrape_interval: "15s"
                  
                prod-prometheus-02.company.com:
                  ansible_host: 10.1.3.11
                  prometheus_role: replica
                  prometheus_storage_retention: "30d"
                  prometheus_storage_size: "500GB"
                  
                prod-grafana-01.company.com:
                  ansible_host: 10.1.3.12
                  grafana_admin_password: "{{ vault_grafana_admin_password }}"
                  grafana_database_type: "postgres"
                  grafana_database_host: "prod-db-replica-01.company.com"
                  
                prod-alertmanager-01.company.com:
                  ansible_host: 10.1.3.13
                  alertmanager_cluster_peers:
                    - prod-alertmanager-02.company.com:9094
                  slack_webhook: "{{ vault_slack_webhook_url }}"
                  pagerduty_key: "{{ vault_pagerduty_integration_key }}"
            
            logging:
              hosts:
                prod-elasticsearch-01.company.com:
                  ansible_host: 10.1.3.20
                  elasticsearch_node_role: "master,data"
                  elasticsearch_heap_size: "4g"
                  elasticsearch_cluster_name: "production-logs"
                  
                prod-elasticsearch-02.company.com:
                  ansible_host: 10.1.3.21
                  elasticsearch_node_role: "data"
                  elasticsearch_heap_size: "8g"
                  elasticsearch_cluster_name: "production-logs"
                  
                prod-logstash-01.company.com:
                  ansible_host: 10.1.3.30
                  logstash_heap_size: "2g"
                  logstash_pipeline_workers: 8
                  
                prod-kibana-01.company.com:
                  ansible_host: 10.1.3.35
                  kibana_elasticsearch_hosts:
                    - "http://prod-elasticsearch-01.company.com:9200"
                    - "http://prod-elasticsearch-02.company.com:9200"
    
    # Environment-specific variables
    production:
      vars:
        environment: production
        environment_tier: prod
        backup_enabled: true
        monitoring_enabled: true
        logging_level: INFO
        ssl_enabled: true
        firewall_strict: true
        audit_logging: true
        
        # Network configuration
        network_cidr: "10.1.0.0/16"
        subnet_database: "10.1.1.0/24"
        subnet_application: "10.1.2.0/24"
        subnet_infrastructure: "10.1.3.0/24"
        
        # Security configuration
        ssh_port: 22
        ssh_key_type: "ed25519"
        sudo_timeout: 5
        password_max_age: 90
        
        # Application configuration
        app_max_memory: "4G"
        app_max_cpu: "2000m"
        database_max_connections: 1000
        cache_ttl: 3600
        
        # Compliance settings
        compliance_frameworks:
          - sox
          - gdpr
          - iso27001
        audit_log_retention: 2555  # 7 years in days
        encryption_at_rest: true
        encryption_in_transit: true
```

## Dynamic Inventory Implementation

### Multi-Cloud Dynamic Inventory
```python
#!/usr/bin/env python3
"""
Enterprise multi-cloud dynamic inventory
Supports AWS, Azure, GCP, and VMware vSphere
"""

import json
import os
import sys
import time
import concurrent.futures
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

import boto3
import yaml
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from google.cloud import compute_v1
from pyVim.connect import SmartConnect
from pyVmomi import vim

@dataclass
class InventoryHost:
    name: str
    ip_address: str
    private_ip: str
    public_ip: Optional[str]
    instance_type: str
    region: str
    zone: Optional[str]
    state: str
    tags: Dict[str, str]
    platform: str
    provider: str
    metadata: Dict[str, Any]

class CloudProvider(ABC):
    """Abstract base class for cloud providers"""
    
    @abstractmethod
    def get_instances(self) -> List[InventoryHost]:
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        pass

class AWSProvider(CloudProvider):
    def __init__(self, config: Dict[str, Any]):
        self.regions = config.get('regions', ['us-east-1'])
        self.profile = config.get('profile')
        self.filters = config.get('filters', {})
        
    def get_provider_name(self) -> str:
        return 'aws'
    
    def get_instances(self) -> List[InventoryHost]:
        instances = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(self._get_region_instances, region): region 
                for region in self.regions
            }
            
            for future in concurrent.futures.as_completed(futures):
                region = futures[future]
                try:
                    region_instances = future.result(timeout=60)
                    instances.extend(region_instances)
                except Exception as e:
                    print(f"Error processing AWS region {region}: {e}", file=sys.stderr)
        
        return instances
    
    def _get_region_instances(self, region: str) -> List[InventoryHost]:
        session = boto3.Session(profile_name=self.profile, region_name=region)
        ec2 = session.client('ec2')
        
        # Build filters
        filters = [
            {'Name': 'instance-state-name', 'Values': ['running', 'stopped']}
        ]
        
        for key, values in self.filters.items():
            if key.startswith('tag:'):
                filters.append({'Name': key, 'Values': values})
            else:
                filters.append({'Name': key, 'Values': values})
        
        instances = []
        
        try:
            paginator = ec2.get_paginator('describe_instances')
            
            for page in paginator.paginate(Filters=filters):
                for reservation in page['Reservations']:
                    for instance in reservation['Instances']:
                        instances.append(self._process_aws_instance(instance, region))
        
        except Exception as e:
            print(f"Error fetching AWS instances in {region}: {e}", file=sys.stderr)
        
        return instances
    
    def _process_aws_instance(self, instance: Dict, region: str) -> InventoryHost:
        # Extract tags
        tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
        
        # Get instance name
        name = tags.get('Name', instance['InstanceId'])
        
        # Get networking info
        private_ip = instance.get('PrivateIpAddress', '')
        public_ip = instance.get('PublicIpAddress')
        primary_ip = public_ip or private_ip
        
        # Platform detection
        platform = 'linux'
        if instance.get('Platform') == 'windows':
            platform = 'windows'
        
        return InventoryHost(
            name=name,
            ip_address=primary_ip,
            private_ip=private_ip,
            public_ip=public_ip,
            instance_type=instance['InstanceType'],
            region=region,
            zone=instance['Placement']['AvailabilityZone'],
            state=instance['State']['Name'],
            tags=tags,
            platform=platform,
            provider='aws',
            metadata={
                'instance_id': instance['InstanceId'],
                'vpc_id': instance.get('VpcId'),
                'subnet_id': instance.get('SubnetId'),
                'security_groups': [sg['GroupName'] for sg in instance.get('SecurityGroups', [])],
                'image_id': instance.get('ImageId'),
                'launch_time': instance.get('LaunchTime').isoformat() if instance.get('LaunchTime') else None
            }
        )

class AzureProvider(CloudProvider):
    def __init__(self, config: Dict[str, Any]):
        self.subscription_id = config['subscription_id']
        self.resource_groups = config.get('resource_groups', [])
        self.credential = DefaultAzureCredential()
        
    def get_provider_name(self) -> str:
        return 'azure'
    
    def get_instances(self) -> List[InventoryHost]:
        compute_client = ComputeManagementClient(self.credential, self.subscription_id)
        network_client = NetworkManagementClient(self.credential, self.subscription_id)
        
        instances = []
        
        try:
            # Get all VMs
            vms = compute_client.virtual_machines.list_all()
            
            for vm in vms:
                # Filter by resource group if specified
                if self.resource_groups:
                    vm_rg = vm.id.split('/')[4]
                    if vm_rg not in self.resource_groups:
                        continue
                
                instance = self._process_azure_vm(vm, network_client)
                if instance:
                    instances.append(instance)
        
        except Exception as e:
            print(f"Error fetching Azure VMs: {e}", file=sys.stderr)
        
        return instances
    
    def _process_azure_vm(self, vm, network_client) -> Optional[InventoryHost]:
        try:
            # Get networking information
            private_ip = None
            public_ip = None
            
            if vm.network_profile and vm.network_profile.network_interfaces:
                nic_ref = vm.network_profile.network_interfaces[0].id
                nic_name = nic_ref.split('/')[-1]
                resource_group = nic_ref.split('/')[4]
                
                nic = network_client.network_interfaces.get(resource_group, nic_name)
                
                if nic.ip_configurations:
                    ip_config = nic.ip_configurations[0]
                    private_ip = ip_config.private_ip_address
                    
                    if ip_config.public_ip_address:
                        public_ip_name = ip_config.public_ip_address.id.split('/')[-1]
                        public_ip_obj = network_client.public_ip_addresses.get(resource_group, public_ip_name)
                        public_ip = public_ip_obj.ip_address
            
            # Extract region from location
            region = vm.location
            
            # Get tags
            tags = vm.tags or {}
            
            # Platform detection
            platform = 'linux'
            if vm.storage_profile.os_disk.os_type and 'windows' in vm.storage_profile.os_disk.os_type.lower():
                platform = 'windows'
            
            return InventoryHost(
                name=vm.name,
                ip_address=public_ip or private_ip or '',
                private_ip=private_ip or '',
                public_ip=public_ip,
                instance_type=vm.hardware_profile.vm_size,
                region=region,
                zone=None,  # Azure doesn't have zones in the same way
                state=vm.provisioning_state,
                tags=tags,
                platform=platform,
                provider='azure',
                metadata={
                    'resource_group': vm.id.split('/')[4],
                    'vm_id': vm.vm_id,
                    'os_disk_type': vm.storage_profile.os_disk.managed_disk.storage_account_type if vm.storage_profile.os_disk.managed_disk else None
                }
            )
        
        except Exception as e:
            print(f"Error processing Azure VM {vm.name}: {e}", file=sys.stderr)
            return None

class GCPProvider(CloudProvider):
    def __init__(self, config: Dict[str, Any]):
        self.project_id = config['project_id']
        self.zones = config.get('zones', [])
        self.filters = config.get('filters', {})
        
    def get_provider_name(self) -> str:
        return 'gcp'
    
    def get_instances(self) -> List[InventoryHost]:
        instances = []
        
        try:
            instances_client = compute_v1.InstancesClient()
            
            # If no zones specified, get all zones
            if not self.zones:
                zones_client = compute_v1.ZonesClient()
                request = compute_v1.ListZonesRequest(project=self.project_id)
                zones_list = zones_client.list(request=request)
                self.zones = [zone.name for zone in zones_list]
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = {
                    executor.submit(self._get_zone_instances, zone): zone 
                    for zone in self.zones
                }
                
                for future in concurrent.futures.as_completed(futures):
                    zone = futures[future]
                    try:
                        zone_instances = future.result(timeout=60)
                        instances.extend(zone_instances)
                    except Exception as e:
                        print(f"Error processing GCP zone {zone}: {e}", file=sys.stderr)
        
        except Exception as e:
            print(f"Error fetching GCP instances: {e}", file=sys.stderr)
        
        return instances
    
    def _get_zone_instances(self, zone: str) -> List[InventoryHost]:
        instances_client = compute_v1.InstancesClient()
        instances = []
        
        try:
            request = compute_v1.ListInstancesRequest(
                project=self.project_id,
                zone=zone
            )
            
            for instance in instances_client.list(request=request):
                processed_instance = self._process_gcp_instance(instance, zone)
                if processed_instance:
                    instances.append(processed_instance)
        
        except Exception as e:
            print(f"Error fetching instances in zone {zone}: {e}", file=sys.stderr)
        
        return instances
    
    def _process_gcp_instance(self, instance, zone: str) -> Optional[InventoryHost]:
        try:
            # Extract networking
            private_ip = None
            public_ip = None
            
            if instance.network_interfaces:
                network_interface = instance.network_interfaces[0]
                private_ip = network_interface.network_ip
                
                if network_interface.access_configs:
                    public_ip = network_interface.access_configs[0].nat_ip
            
            # Extract labels (GCP equivalent of tags)
            tags = dict(instance.labels) if instance.labels else {}
            
            # Extract region from zone
            region = '-'.join(zone.split('-')[:-1])
            
            # Platform detection
            platform = 'linux'
            if instance.disks and instance.disks[0].licenses:
                for license_uri in instance.disks[0].licenses:
                    if 'windows' in license_uri.lower():
                        platform = 'windows'
                        break
            
            return InventoryHost(
                name=instance.name,
                ip_address=public_ip or private_ip or '',
                private_ip=private_ip or '',
                public_ip=public_ip,
                instance_type=instance.machine_type.split('/')[-1],
                region=region,
                zone=zone,
                state=instance.status,
                tags=tags,
                platform=platform,
                provider='gcp',
                metadata={
                    'instance_id': str(instance.id),
                    'self_link': instance.self_link,
                    'creation_timestamp': instance.creation_timestamp
                }
            )
        
        except Exception as e:
            print(f"Error processing GCP instance {instance.name}: {e}", file=sys.stderr)
            return None

class EnterpriseInventory:
    def __init__(self, config_file: str = 'inventory_config.yml'):
        self.config = self._load_config(config_file)
        self.providers = self._initialize_providers()
        self.cache_ttl = self.config.get('cache_ttl', 300)  # 5 minutes default
        self.cache_file = self.config.get('cache_file', '/tmp/ansible_inventory_cache.json')
        
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load inventory configuration"""
        try:
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Config file {config_file} not found, using defaults", file=sys.stderr)
            return {}
        except Exception as e:
            print(f"Error loading config: {e}", file=sys.stderr)
            return {}
    
    def _initialize_providers(self) -> List[CloudProvider]:
        """Initialize configured cloud providers"""
        providers = []
        
        provider_configs = self.config.get('providers', {})
        
        if 'aws' in provider_configs:
            providers.append(AWSProvider(provider_configs['aws']))
        
        if 'azure' in provider_configs:
            providers.append(AzureProvider(provider_configs['azure']))
        
        if 'gcp' in provider_configs:
            providers.append(GCPProvider(provider_configs['gcp']))
        
        return providers
    
    def _should_use_cache(self) -> bool:
        """Check if cache should be used"""
        if not os.path.exists(self.cache_file):
            return False
        
        cache_age = time.time() - os.path.getmtime(self.cache_file)
        return cache_age < self.cache_ttl
    
    def _load_cache(self) -> Optional[Dict[str, Any]]:
        """Load inventory from cache"""
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except Exception:
            return None
    
    def _save_cache(self, inventory: Dict[str, Any]):
        """Save inventory to cache"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(inventory, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not save cache: {e}", file=sys.stderr)
    
    def generate_inventory(self) -> Dict[str, Any]:
        """Generate complete inventory"""
        
        # Try cache first
        if self._should_use_cache():
            cached_inventory = self._load_cache()
            if cached_inventory:
                return cached_inventory
        
        all_hosts = []
        
        # Collect instances from all providers
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.providers)) as executor:
            future_to_provider = {
                executor.submit(provider.get_instances): provider
                for provider in self.providers
            }
            
            for future in concurrent.futures.as_completed(future_to_provider):
                provider = future_to_provider[future]
                try:
                    instances = future.result(timeout=120)
                    all_hosts.extend(instances)
                except Exception as e:
                    print(f"Error from {provider.get_provider_name()}: {e}", file=sys.stderr)
        
        # Build Ansible inventory structure
        inventory = self._build_inventory(all_hosts)
        
        # Save to cache
        self._save_cache(inventory)
        
        return inventory
    
    def _build_inventory(self, hosts: List[InventoryHost]) -> Dict[str, Any]:
        """Build Ansible inventory from hosts"""
        inventory = {
            'all': {'children': []},
            '_meta': {'hostvars': {}}
        }
        
        # Group tracking
        groups = set()
        
        for host in hosts:
            host_name = host.name
            
            # Add host variables
            host_vars = {
                'ansible_host': host.ip_address,
                'ansible_user': self._get_ansible_user(host),
                'private_ip': host.private_ip,
                'public_ip': host.public_ip,
                'instance_type': host.instance_type,
                'region': host.region,
                'zone': host.zone,
                'state': host.state,
                'platform': host.platform,
                'provider': host.provider,
            }
            
            # Add tags as variables
            for key, value in host.tags.items():
                host_vars[f'tag_{key.lower().replace("-", "_")}'] = value
            
            # Add metadata
            host_vars.update({f'meta_{k}': v for k, v in host.metadata.items()})
            
            inventory['_meta']['hostvars'][host_name] = host_vars
            
            # Create groups
            group_names = self._generate_groups(host)
            
            for group_name in group_names:
                if group_name not in inventory:
                    inventory[group_name] = {'hosts': []}
                    groups.add(group_name)
                
                inventory[group_name]['hosts'].append(host_name)
        
        # Add groups to 'all' children
        inventory['all']['children'] = list(groups)
        
        return inventory
    
    def _get_ansible_user(self, host: InventoryHost) -> str:
        """Determine appropriate ansible_user based on platform and provider"""
        if host.platform == 'windows':
            return 'Administrator'
        
        # Linux users by provider/image
        if host.provider == 'aws':
            if 'ubuntu' in host.tags.get('Name', '').lower():
                return 'ubuntu'
            elif 'centos' in host.tags.get('Name', '').lower():
                return 'centos'
            else:
                return 'ec2-user'
        elif host.provider == 'azure':
            return 'azureuser'
        elif host.provider == 'gcp':
            return 'gce-user'
        
        return 'root'  # Default
    
    def _generate_groups(self, host: InventoryHost) -> List[str]:
        """Generate group names for a host"""
        groups = []
        
        # Provider groups
        groups.append(f'provider_{host.provider}')
        
        # Platform groups
        groups.append(f'platform_{host.platform}')
        
        # Region groups
        groups.append(f'region_{host.region.replace("-", "_")}')
        
        # Zone groups (if available)
        if host.zone:
            groups.append(f'zone_{host.zone.replace("-", "_")}')
        
        # State groups
        groups.append(f'state_{host.state.lower().replace("-", "_")}')
        
        # Instance type groups
        groups.append(f'type_{host.instance_type.replace(".", "_").replace("-", "_")}')
        
        # Tag-based groups
        for key, value in host.tags.items():
            if key.lower() in ['environment', 'env', 'stage']:
                groups.append(f'env_{value.lower().replace("-", "_")}')
            elif key.lower() in ['role', 'function', 'service']:
                groups.append(f'role_{value.lower().replace("-", "_")}')
            elif key.lower() in ['application', 'app']:
                groups.append(f'app_{value.lower().replace("-", "_")}')
            elif key.lower() in ['team', 'owner']:
                groups.append(f'team_{value.lower().replace("-", "_")}')
        
        return groups

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enterprise Multi-Cloud Ansible Inventory')
    parser.add_argument('--list', action='store_true', help='List all hosts')
    parser.add_argument('--host', help='Get specific host vars')
    parser.add_argument('--config', default='inventory_config.yml', help='Config file path')
    parser.add_argument('--refresh-cache', action='store_true', help='Refresh inventory cache')
    
    args = parser.parse_args()
    
    inventory_manager = EnterpriseInventory(args.config)
    
    if args.refresh_cache:
        # Remove cache file to force refresh
        if os.path.exists(inventory_manager.cache_file):
            os.remove(inventory_manager.cache_file)
    
    if args.list:
        inventory = inventory_manager.generate_inventory()
        print(json.dumps(inventory, indent=2, default=str))
    elif args.host:
        inventory = inventory_manager.generate_inventory()
        host_vars = inventory.get('_meta', {}).get('hostvars', {}).get(args.host, {})
        print(json.dumps(host_vars, indent=2, default=str))
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
```

### Dynamic Inventory Configuration
```yaml
# inventory_config.yml - Multi-cloud inventory configuration
cache_ttl: 300  # 5 minutes
cache_file: "/tmp/ansible_inventory_cache.json"

providers:
  aws:
    regions:
      - us-east-1
      - us-west-2
      - eu-west-1
    profile: production  # AWS CLI profile
    filters:
      tag:Environment:
        - production
        - staging
      instance-state-name:
        - running
  
  azure:
    subscription_id: "12345678-1234-1234-1234-123456789abc"
    resource_groups:
      - prod-rg-east
      - prod-rg-west
      - staging-rg
    
  gcp:
    project_id: "my-production-project"
    zones:
      - us-central1-a
      - us-central1-b
      - us-east1-a
    filters:
      labels.environment:
        - production
        - staging

# Group variable mappings
group_vars:
  env_production:
    environment_tier: prod
    backup_enabled: true
    monitoring_level: comprehensive
    ssl_enforcement: true
    
  env_staging:
    environment_tier: stage
    backup_enabled: false
    monitoring_level: basic
    ssl_enforcement: false
    
  platform_windows:
    ansible_connection: winrm
    ansible_winrm_transport: ntlm
    ansible_winrm_server_cert_validation: ignore
    
  platform_linux:
    ansible_connection: ssh
    ansible_ssh_common_args: "-o StrictHostKeyChecking=no"

# Host naming conventions
naming_conventions:
  aws:
    pattern: "{environment}-{role}-{instance_number}.{region}.aws.company.com"
  azure:
    pattern: "{environment}-{role}-{instance_number}.{region}.azure.company.com"
  gcp:
    pattern: "{environment}-{role}-{instance_number}.{zone}.gcp.company.com"
```

This comprehensive inventory management guide provides enterprise-grade patterns for managing complex, multi-cloud environments with both static and dynamic inventory sources, advanced grouping strategies, and automated host discovery capabilities.