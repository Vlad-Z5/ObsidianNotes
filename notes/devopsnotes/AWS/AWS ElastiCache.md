# AWS ElastiCache

> **Service Type:** Database | **Scope:** Regional | **Serverless:** No

## Overview

Amazon ElastiCache is a fully managed in-memory caching service that supports both Redis and Memcached engines. It provides sub-millisecond latency and high throughput for real-time applications by caching frequently accessed data in memory, reducing database load and improving application performance.

## DevOps & Enterprise Use Cases

### High-Performance Caching
- **Database Query Caching** - Cache expensive database queries to reduce load and improve response times
- **Session Storage** - Store user sessions for web applications with high availability and fast access
- **Application Cache** - Cache computed results, API responses, and frequently accessed data
- **Content Delivery** - Cache static content and dynamic data closer to users

### Real-Time Applications
- **Gaming Leaderboards** - Implement real-time leaderboards with Redis sorted sets
- **Chat Applications** - Use Redis Pub/Sub for real-time messaging and notifications
- **Live Analytics** - Process and cache real-time metrics and analytics data
- **Rate Limiting** - Implement API rate limiting and throttling mechanisms

### Enterprise Integration
- **Microservices Architecture** - Shared cache layer across multiple microservices
- **Multi-Region Deployment** - Cross-region replication for global applications
- **Disaster Recovery** - Automated backup and restore for business continuity
- **Compliance and Security** - Encryption at rest and in transit, VPC isolation

## Core Architecture Components

### Engine Options

#### Redis
- **In-memory key-value store** with advanced data structures (strings, hashes, lists, sets, sorted sets)
- **Persistence options** with RDB snapshots and AOF logging
- **Multi-AZ replication** with automatic failover for high availability
- **Pub/Sub messaging** for real-time communication patterns
- **Lua scripting** for complex operations and atomic transactions
- **Clustering** for horizontal scaling across multiple nodes

#### Memcached
- **Simple caching system** optimized for high-performance key-value storage
- **Multi-threaded architecture** for efficient CPU utilization
- **Horizontal scaling** by adding/removing cache nodes
- **Simple protocol** with minimal overhead
- **Auto-discovery** for dynamic node management

### Deployment Modes

#### Standalone
- **Single Redis node** for development and testing environments
- **Simple setup** with basic caching capabilities
- **Cost-effective** for small applications with low traffic

#### Replication Group
- **Primary-replica configuration** with one primary and multiple read replicas
- **Automatic failover** to replica nodes in case of primary failure
- **Read scaling** by distributing read traffic across replicas

#### Cluster Mode
- **Sharded Redis cluster** for horizontal scaling and high availability
- **Automatic data partitioning** across multiple shards
- **Cross-shard operations** with Redis Cluster commands
- **Online scaling** by adding or removing shards

## Service Features & Capabilities

### Performance Features
- **Sub-millisecond latency** for in-memory operations
- **High throughput** supporting millions of operations per second
- **Connection pooling** for efficient resource utilization
- **Pipeline operations** for batch processing
- **Memory optimization** with configurable eviction policies

### High Availability
- **Multi-AZ deployment** with automatic failover
- **Cross-region replication** for disaster recovery
- **Backup and restore** with point-in-time recovery
- **Monitoring and alerting** with CloudWatch integration

### Security Features
```python
class ElastiCacheSecurityManager:
    def __init__(self, region='us-west-2'):
        self.elasticache = boto3.client('elasticache', region_name=region)
    
    def create_secure_redis_cluster(self, config):
        """Create a secure Redis cluster with encryption and authentication"""
        
        response = self.elasticache.create_replication_group(
            ReplicationGroupId=config['cluster_id'],
            Description=config['description'],
            NumCacheClusters=config['num_nodes'],
            CacheNodeType=config['node_type'],
            Engine='redis',
            EngineVersion='7.0',
            CacheParameterGroupName='default.redis7',
            CacheSubnetGroupName=config['subnet_group'],
            SecurityGroupIds=config['security_groups'],
            
            # Security configurations
            AtRestEncryptionEnabled=True,
            TransitEncryptionEnabled=True,
            AuthToken=config['auth_token'],
            
            # High availability
            MultiAZEnabled=True,
            AutomaticFailoverEnabled=True,
            
            # Backup configuration
            SnapshotRetentionLimit=7,
            SnapshotWindow='03:00-04:00',
            PreferredMaintenanceWindow='sun:04:00-sun:05:00',
            
            Tags=[
                {'Key': 'Environment', 'Value': config.get('environment', 'dev')},
                {'Key': 'Application', 'Value': config.get('application', '')},
                {'Key': 'ManagedBy', 'Value': 'DevOps'}
            ]
        )
        
        return response['ReplicationGroup']['ReplicationGroupId']
```

## Configuration & Setup

### Basic Redis Cluster Setup

```python
import boto3
from datetime import datetime

class ElastiCacheManager:
    def __init__(self, region='us-west-2'):
        self.elasticache = boto3.client('elasticache', region_name=region)
        self.ec2 = boto3.client('ec2', region_name=region)
    
    def create_subnet_group(self, group_name, vpc_id, subnet_ids, description):
        """Create a cache subnet group for VPC deployment"""
        
        response = self.elasticache.create_cache_subnet_group(
            CacheSubnetGroupName=group_name,
            CacheSubnetGroupDescription=description,
            SubnetIds=subnet_ids
        )
        return response['CacheSubnetGroup']
    
    def create_redis_replication_group(self, config):
        """Create Redis replication group with multiple replicas"""
        
        return self.elasticache.create_replication_group(
            ReplicationGroupId=config['replication_group_id'],
            Description=config['description'],
            GlobalReplicationGroupId=config.get('global_replication_group_id'),
            PrimaryClusterId=config.get('primary_cluster_id'),
            AutomaticFailoverEnabled=config.get('automatic_failover', True),
            MultiAZEnabled=config.get('multi_az', True),
            NumCacheClusters=config.get('num_cache_clusters', 3),
            PreferredCacheClusterAZs=config.get('preferred_azs'),
            CacheNodeType=config.get('node_type', 'cache.r6g.large'),
            Engine='redis',
            EngineVersion=config.get('engine_version', '7.0'),
            CacheParameterGroupName=config.get('parameter_group', 'default.redis7'),
            CacheSubnetGroupName=config['subnet_group_name'],
            SecurityGroupIds=config['security_group_ids'],
            SnapshotRetentionLimit=config.get('snapshot_retention', 5),
            SnapshotWindow=config.get('snapshot_window', '03:00-04:00'),
            PreferredMaintenanceWindow=config.get('maintenance_window', 'sun:04:00-sun:05:00'),
            Port=config.get('port', 6379),
            NotificationTopicArn=config.get('notification_topic_arn'),
            AutoMinorVersionUpgrade=config.get('auto_minor_version_upgrade', True),
            AtRestEncryptionEnabled=config.get('encryption_at_rest', True),
            TransitEncryptionEnabled=config.get('encryption_in_transit', True),
            AuthToken=config.get('auth_token'),
            UserGroupIds=config.get('user_group_ids', []),
            LogDeliveryConfigurations=config.get('log_delivery_configurations', []),
            DataTieringEnabled=config.get('data_tiering', False),
            NetworkType=config.get('network_type', 'ipv4'),
            IpDiscovery=config.get('ip_discovery', 'ipv4'),
            TransitEncryptionMode=config.get('transit_encryption_mode', 'preferred'),
            ClusterMode=config.get('cluster_mode', 'disabled'),
            Tags=[
                {'Key': 'Name', 'Value': config['replication_group_id']},
                {'Key': 'Environment', 'Value': config.get('environment', 'dev')},
                {'Key': 'CreatedAt', 'Value': datetime.now().isoformat()}
            ]
        )
    
    def create_memcached_cluster(self, config):
        """Create Memcached cluster for simple caching"""
        
        return self.elasticache.create_cache_cluster(
            CacheClusterId=config['cluster_id'],
            ReplicationGroupId=config.get('replication_group_id'),
            AZMode=config.get('az_mode', 'cross-az'),
            PreferredAvailabilityZones=config.get('preferred_azs'),
            NumCacheNodes=config.get('num_nodes', 3),
            CacheNodeType=config.get('node_type', 'cache.r6g.large'),
            Engine='memcached',
            EngineVersion=config.get('engine_version', '1.6.17'),
            CacheParameterGroupName=config.get('parameter_group', 'default.memcached1.6'),
            CacheSubnetGroupName=config['subnet_group_name'],
            SecurityGroupIds=config['security_group_ids'],
            PreferredMaintenanceWindow=config.get('maintenance_window', 'sun:04:00-sun:05:00'),
            Port=config.get('port', 11211),
            NotificationTopicArn=config.get('notification_topic_arn'),
            AutoMinorVersionUpgrade=config.get('auto_minor_version_upgrade', True),
            LogDeliveryConfigurations=config.get('log_delivery_configurations', []),
            NetworkType=config.get('network_type', 'ipv4'),
            IpDiscovery=config.get('ip_discovery', 'ipv4'),
            Tags=[
                {'Key': 'Name', 'Value': config['cluster_id']},
                {'Key': 'Environment', 'Value': config.get('environment', 'dev')},
                {'Key': 'CreatedAt', 'Value': datetime.now().isoformat()}
            ]
        )
```

### Parameter Group Configuration

```bash
# Create custom Redis parameter group
aws elasticache create-cache-parameter-group \
  --cache-parameter-group-name custom-redis7 \
  --cache-parameter-group-family redis7 \
  --description "Custom Redis 7.0 parameter group for production"

# Modify Redis parameters for optimal performance
aws elasticache modify-cache-parameter-group \
  --cache-parameter-group-name custom-redis7 \
  --parameter-name-values \
    ParameterName=maxmemory-policy,ParameterValue=allkeys-lru \
    ParameterName=timeout,ParameterValue=300 \
    ParameterName=tcp-keepalive,ParameterValue=60 \
    ParameterName=maxclients,ParameterValue=10000

# Create custom Memcached parameter group
aws elasticache create-cache-parameter-group \
  --cache-parameter-group-name custom-memcached1.6 \
  --cache-parameter-group-family memcached1.6 \
  --description "Custom Memcached parameter group for production"

# Modify Memcached parameters
aws elasticache modify-cache-parameter-group \
  --cache-parameter-group-name custom-memcached1.6 \
  --parameter-name-values \
    ParameterName=max_item_size,ParameterValue=2097152 \
    ParameterName=chunk_size_growth_factor,ParameterValue=1.25
```

## Enterprise Implementation Examples

### Multi-Tier Caching Strategy

```python
class EnterpriseElastiCacheManager:
    def __init__(self, region='us-west-2'):
        self.elasticache = boto3.client('elasticache', region_name=region)
        
    def deploy_multi_tier_cache(self, application_config):
        """Deploy a multi-tier caching strategy for enterprise applications"""
        
        cache_tiers = {
            'session_cache': {
                'engine': 'redis',
                'node_type': 'cache.r6g.large',
                'num_nodes': 3,
                'purpose': 'session_storage',
                'ttl': 3600  # 1 hour
            },
            'application_cache': {
                'engine': 'redis',
                'node_type': 'cache.r6g.xlarge', 
                'num_nodes': 5,
                'purpose': 'application_data',
                'ttl': 1800  # 30 minutes
            },
            'database_cache': {
                'engine': 'memcached',
                'node_type': 'cache.r6g.large',
                'num_nodes': 4,
                'purpose': 'database_queries',
                'ttl': 300  # 5 minutes
            }
        }
        
        deployed_clusters = {}
        
        for tier_name, config in cache_tiers.items():
            cluster_config = {
                'cluster_id': f"{application_config['app_name']}-{tier_name}-{application_config['environment']}",
                'description': f"{tier_name} for {application_config['app_name']}",
                'node_type': config['node_type'],
                'num_nodes': config['num_nodes'],
                'subnet_group_name': application_config['subnet_group'],
                'security_group_ids': application_config['security_groups'],
                'environment': application_config['environment'],
                'auth_token': application_config.get('auth_tokens', {}).get(tier_name)
            }
            
            if config['engine'] == 'redis':
                cluster_info = self.create_redis_replication_group(cluster_config)
                deployed_clusters[tier_name] = {
                    'type': 'redis',
                    'cluster_id': cluster_info['ReplicationGroupId'],
                    'endpoint': self._get_redis_endpoint(cluster_info['ReplicationGroupId']),
                    'purpose': config['purpose'],
                    'ttl': config['ttl']
                }
            else:
                cluster_info = self.create_memcached_cluster(cluster_config)
                deployed_clusters[tier_name] = {
                    'type': 'memcached',
                    'cluster_id': cluster_info['CacheClusterId'],
                    'endpoints': self._get_memcached_endpoints(cluster_info['CacheClusterId']),
                    'purpose': config['purpose'],
                    'ttl': config['ttl']
                }
        
        return deployed_clusters
    
    def _get_redis_endpoint(self, replication_group_id):
        """Get Redis primary endpoint"""
        response = self.elasticache.describe_replication_groups(
            ReplicationGroupId=replication_group_id
        )
        return response['ReplicationGroups'][0]['RedisEndpoint']['Address']
    
    def _get_memcached_endpoints(self, cluster_id):
        """Get Memcached node endpoints"""
        response = self.elasticache.describe_cache_clusters(
            CacheClusterId=cluster_id,
            ShowCacheNodeInfo=True
        )
        
        endpoints = []
        for node in response['CacheClusters'][0]['CacheNodes']:
            endpoints.append({
                'address': node['Endpoint']['Address'],
                'port': node['Endpoint']['Port']
            })
        
        return endpoints
```

### Global Data Replication

```python
class GlobalElastiCacheManager:
    def __init__(self):
        self.primary_region = 'us-west-2'
        self.secondary_regions = ['us-east-1', 'eu-west-1', 'ap-southeast-1']
        
    def setup_global_datastore(self, config):
        """Setup global datastore for cross-region replication"""
        
        # Create primary cluster in primary region
        primary_elasticache = boto3.client('elasticache', region_name=self.primary_region)
        
        primary_response = primary_elasticache.create_global_replication_group(
            GlobalReplicationGroupIdSuffix=config['global_id_suffix'],
            GlobalReplicationGroupDescription=config['description'],
            PrimaryReplicationGroupId=config['primary_replication_group_id']
        )
        
        global_replication_group_id = primary_response['GlobalReplicationGroup']['GlobalReplicationGroupId']
        
        # Wait for primary to be available
        primary_elasticache.get_waiter('replication_group_available').wait(
            ReplicationGroupId=config['primary_replication_group_id']
        )
        
        # Create secondary clusters in other regions
        secondary_clusters = {}
        
        for region in self.secondary_regions:
            secondary_elasticache = boto3.client('elasticache', region_name=region)
            
            secondary_config = {
                'replication_group_id': f"{config['app_name']}-{region}-secondary",
                'description': f"Secondary cluster in {region}",
                'global_replication_group_id': global_replication_group_id,
                'node_type': config['node_type'],
                'num_cache_clusters': config['num_nodes'],
                'subnet_group_name': config['subnet_groups'][region],
                'security_group_ids': config['security_groups'][region],
                'environment': config['environment']
            }
            
            secondary_response = secondary_elasticache.create_replication_group(
                ReplicationGroupId=secondary_config['replication_group_id'],
                Description=secondary_config['description'],
                GlobalReplicationGroupId=global_replication_group_id,
                NumCacheClusters=secondary_config['num_cache_clusters'],
                CacheNodeType=secondary_config['node_type'],
                CacheSubnetGroupName=secondary_config['subnet_group_name'],
                SecurityGroupIds=secondary_config['security_group_ids'],
                MultiAZEnabled=True,
                AutomaticFailoverEnabled=True,
                AtRestEncryptionEnabled=True,
                TransitEncryptionEnabled=True
            )
            
            secondary_clusters[region] = secondary_response['ReplicationGroup']['ReplicationGroupId']
        
        return {
            'global_replication_group_id': global_replication_group_id,
            'primary_cluster': config['primary_replication_group_id'],
            'primary_region': self.primary_region,
            'secondary_clusters': secondary_clusters
        }
```

### Redis Cluster Mode Implementation

```python
class RedisClusterManager:
    def __init__(self, region='us-west-2'):
        self.elasticache = boto3.client('elasticache', region_name=region)
    
    def create_redis_cluster(self, config):
        """Create Redis cluster with sharding for horizontal scaling"""
        
        response = self.elasticache.create_replication_group(
            ReplicationGroupId=config['cluster_id'],
            Description=config['description'],
            GlobalReplicationGroupId=config.get('global_replication_group_id'),
            NumNodeGroups=config['num_shards'],  # Number of shards
            ReplicasPerNodeGroup=config.get('replicas_per_shard', 2),
            CacheNodeType=config['node_type'],
            Engine='redis',
            EngineVersion='7.0',
            CacheParameterGroupName=config.get('parameter_group', 'default.redis7.cluster.on'),
            CacheSubnetGroupName=config['subnet_group'],
            SecurityGroupIds=config['security_groups'],
            
            # Enable cluster mode
            ClusterMode='enabled',
            
            # Security settings
            AtRestEncryptionEnabled=True,
            TransitEncryptionEnabled=True,
            AuthToken=config.get('auth_token'),
            
            # Backup settings
            SnapshotRetentionLimit=7,
            SnapshotWindow='03:00-04:00',
            PreferredMaintenanceWindow='sun:04:00-sun:05:00',
            
            # High availability
            MultiAZEnabled=True,
            AutomaticFailoverEnabled=True,
            
            Tags=[
                {'Key': 'Name', 'Value': config['cluster_id']},
                {'Key': 'Environment', 'Value': config.get('environment', 'prod')},
                {'Key': 'ClusterMode', 'Value': 'enabled'},
                {'Key': 'Shards', 'Value': str(config['num_shards'])}
            ]
        )
        
        return response
    
    def scale_redis_cluster(self, cluster_id, target_shards):
        """Scale Redis cluster by adding or removing shards"""
        
        # Get current cluster configuration
        current_config = self.elasticache.describe_replication_groups(
            ReplicationGroupId=cluster_id
        )['ReplicationGroups'][0]
        
        current_shards = len(current_config['NodeGroups'])
        
        if target_shards > current_shards:
            # Scale out - add shards
            response = self.elasticache.increase_node_groups_in_replication_group(
                ReplicationGroupId=cluster_id,
                NewNodeGroupCount=target_shards,
                ApplyImmediately=True
            )
        elif target_shards < current_shards:
            # Scale in - remove shards
            node_groups_to_remove = []
            for i in range(target_shards, current_shards):
                node_groups_to_remove.append(current_config['NodeGroups'][i]['NodeGroupId'])
            
            response = self.elasticache.decrease_node_groups_in_replication_group(
                ReplicationGroupId=cluster_id,
                NewNodeGroupCount=target_shards,
                NodeGroupsToRemove=node_groups_to_remove,
                ApplyImmediately=True
            )
        else:
            return {'message': 'No scaling needed, cluster already has target number of shards'}
        
        return response
```

## Monitoring & Observability

### CloudWatch Metrics and Alarms

```python
class ElastiCacheMonitoring:
    def __init__(self, region='us-west-2'):
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.elasticache = boto3.client('elasticache', region_name=region)
    
    def setup_comprehensive_monitoring(self, cluster_config, sns_topic_arn):
        """Set up comprehensive monitoring for ElastiCache clusters"""
        
        cluster_id = cluster_config['cluster_id']
        cluster_type = cluster_config['type']  # 'redis' or 'memcached'
        
        alarms = []
        
        if cluster_type == 'redis':
            alarms.extend(self._create_redis_alarms(cluster_id, sns_topic_arn))
        else:
            alarms.extend(self._create_memcached_alarms(cluster_id, sns_topic_arn))
        
        # Create all alarms
        for alarm_config in alarms:
            self.cloudwatch.put_metric_alarm(**alarm_config)
        
        return alarms
    
    def _create_redis_alarms(self, cluster_id, sns_topic_arn):
        """Create Redis-specific CloudWatch alarms"""
        
        return [
            {
                'AlarmName': f'{cluster_id}-HighCPUUtilization',
                'ComparisonOperator': 'GreaterThanThreshold',
                'EvaluationPeriods': 2,
                'MetricName': 'CPUUtilization',
                'Namespace': 'AWS/ElastiCache',
                'Period': 300,
                'Statistic': 'Average',
                'Threshold': 80.0,
                'ActionsEnabled': True,
                'AlarmActions': [sns_topic_arn],
                'AlarmDescription': 'Redis CPU utilization is high',
                'Dimensions': [
                    {'Name': 'CacheClusterId', 'Value': f'{cluster_id}-001'}
                ]
            },
            {
                'AlarmName': f'{cluster_id}-HighMemoryUsage',
                'ComparisonOperator': 'GreaterThanThreshold',
                'EvaluationPeriods': 2,
                'MetricName': 'DatabaseMemoryUsagePercentage',
                'Namespace': 'AWS/ElastiCache',
                'Period': 300,
                'Statistic': 'Average',
                'Threshold': 85.0,
                'ActionsEnabled': True,
                'AlarmActions': [sns_topic_arn],
                'AlarmDescription': 'Redis memory usage is high'
            },
            {
                'AlarmName': f'{cluster_id}-HighEvictions',
                'ComparisonOperator': 'GreaterThanThreshold',
                'EvaluationPeriods': 2,
                'MetricName': 'Evictions',
                'Namespace': 'AWS/ElastiCache',
                'Period': 300,
                'Statistic': 'Sum',
                'Threshold': 100.0,
                'ActionsEnabled': True,
                'AlarmActions': [sns_topic_arn],
                'AlarmDescription': 'Redis evictions are high'
            },
            {
                'AlarmName': f'{cluster_id}-HighReplicationLag',
                'ComparisonOperator': 'GreaterThanThreshold',
                'EvaluationPeriods': 2,
                'MetricName': 'ReplicationLag',
                'Namespace': 'AWS/ElastiCache',
                'Period': 300,
                'Statistic': 'Average',
                'Threshold': 30.0,
                'ActionsEnabled': True,
                'AlarmActions': [sns_topic_arn],
                'AlarmDescription': 'Redis replication lag is high'
            },
            {
                'AlarmName': f'{cluster_id}-LowCacheHitRate',
                'ComparisonOperator': 'LessThanThreshold',
                'EvaluationPeriods': 3,
                'MetricName': 'CacheHitRate',
                'Namespace': 'AWS/ElastiCache',
                'Period': 300,
                'Statistic': 'Average',
                'Threshold': 80.0,
                'ActionsEnabled': True,
                'AlarmActions': [sns_topic_arn],
                'AlarmDescription': 'Redis cache hit rate is low'
            }
        ]
    
    def _create_memcached_alarms(self, cluster_id, sns_topic_arn):
        """Create Memcached-specific CloudWatch alarms"""
        
        return [
            {
                'AlarmName': f'{cluster_id}-HighCPUUtilization',
                'ComparisonOperator': 'GreaterThanThreshold',
                'EvaluationPeriods': 2,
                'MetricName': 'CPUUtilization',
                'Namespace': 'AWS/ElastiCache',
                'Period': 300,
                'Statistic': 'Average',
                'Threshold': 80.0,
                'ActionsEnabled': True,
                'AlarmActions': [sns_topic_arn],
                'AlarmDescription': 'Memcached CPU utilization is high'
            },
            {
                'AlarmName': f'{cluster_id}-HighEvictions',
                'ComparisonOperator': 'GreaterThanThreshold',
                'EvaluationPeriods': 2,
                'MetricName': 'Evictions',
                'Namespace': 'AWS/ElastiCache',
                'Period': 300,
                'Statistic': 'Sum',
                'Threshold': 50.0,
                'ActionsEnabled': True,
                'AlarmActions': [sns_topic_arn],
                'AlarmDescription': 'Memcached evictions are high'
            },
            {
                'AlarmName': f'{cluster_id}-LowCacheHitRate',
                'ComparisonOperator': 'LessThanThreshold',
                'EvaluationPeriods': 3,
                'MetricName': 'CacheHitRate',
                'Namespace': 'AWS/ElastiCache',
                'Period': 300,
                'Statistic': 'Average',
                'Threshold': 85.0,
                'ActionsEnabled': True,
                'AlarmActions': [sns_topic_arn],
                'AlarmDescription': 'Memcached cache hit rate is low'
            }
        ]
    
    def create_dashboard(self, dashboard_name, clusters):
        """Create CloudWatch dashboard for ElastiCache clusters"""
        
        widgets = []
        
        for i, cluster in enumerate(clusters):
            cluster_id = cluster['cluster_id']
            cluster_type = cluster['type']
            
            # CPU utilization widget
            widgets.append({
                "type": "metric",
                "x": (i % 3) * 8,
                "y": i * 6,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/ElastiCache", "CPUUtilization", "CacheClusterId", f"{cluster_id}-001"],
                        [".", "DatabaseMemoryUsagePercentage", ".", "."] if cluster_type == 'redis' else [".", "BytesUsedForCache", ".", "."]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": "us-west-2",
                    "title": f"{cluster_id} - Resource Utilization"
                }
            })
            
            # Cache performance widget
            widgets.append({
                "type": "metric",
                "x": (i % 3) * 8,
                "y": i * 6 + 6,
                "width": 8,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/ElastiCache", "CacheHitRate", "CacheClusterId", f"{cluster_id}-001"],
                        [".", "CacheMissRate", ".", "."],
                        [".", "Evictions", ".", "."]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": "us-west-2",
                    "title": f"{cluster_id} - Cache Performance"
                }
            })
        
        dashboard_body = json.dumps({"widgets": widgets})
        
        self.cloudwatch.put_dashboard(
            DashboardName=dashboard_name,
            DashboardBody=dashboard_body
        )
        
        return dashboard_name
```

### Performance Monitoring Script

```bash
#!/bin/bash
# monitor-elasticache-performance.sh - Monitor ElastiCache performance metrics

CLUSTER_ID=$1
CLUSTER_TYPE=${2:-redis}  # redis or memcached
REGION=${3:-us-west-2}
HOURS=${4:-24}

if [ $# -lt 1 ]; then
    echo "Usage: $0 <cluster-id> [redis|memcached] [region] [hours]"
    exit 1
fi

echo "Monitoring ElastiCache cluster: $CLUSTER_ID ($CLUSTER_TYPE) for last $HOURS hours"

# Function to get CloudWatch metrics
get_metric() {
    local metric_name=$1
    local statistic=$2
    
    aws cloudwatch get-metric-statistics \
        --namespace AWS/ElastiCache \
        --metric-name $metric_name \
        --dimensions Name=CacheClusterId,Value=${CLUSTER_ID}-001 \
        --start-time $(date -u -d "$HOURS hours ago" +%Y-%m-%dT%H:%M:%S) \
        --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
        --period 3600 \
        --statistics $statistic \
        --region $REGION \
        --output table
}

echo "=== CPU Utilization ==="
get_metric "CPUUtilization" "Average"

echo "=== Memory Usage ==="
if [ "$CLUSTER_TYPE" = "redis" ]; then
    get_metric "DatabaseMemoryUsagePercentage" "Average"
else
    get_metric "BytesUsedForCache" "Average"
fi

echo "=== Cache Hit Rate ==="
get_metric "CacheHitRate" "Average"

echo "=== Evictions ==="
get_metric "Evictions" "Sum"

echo "=== Current Connections ==="
get_metric "CurrConnections" "Average"

if [ "$CLUSTER_TYPE" = "redis" ]; then
    echo "=== Replication Lag ==="
    get_metric "ReplicationLag" "Average"
    
    echo "=== Key-based Metrics ==="
    get_metric "CurrItems" "Average"
fi

# Generate performance report
cat > /tmp/elasticache-report-${CLUSTER_ID}.txt << EOF
ElastiCache Performance Report
=============================
Cluster ID: $CLUSTER_ID
Cluster Type: $CLUSTER_TYPE
Region: $REGION
Report Period: Last $HOURS hours
Generated: $(date)

Key Metrics Summary:
- Monitor CPU utilization (should be < 80%)
- Monitor memory usage (should be < 85%)
- Monitor cache hit rate (should be > 80%)
- Monitor evictions (should be minimal)
- Monitor connection count

EOF

echo "Performance report saved to /tmp/elasticache-report-${CLUSTER_ID}.txt"
```

## Security & Compliance

### VPC and Network Security

```python
class ElastiCacheSecuritySetup:
    def __init__(self, region='us-west-2'):
        self.ec2 = boto3.client('ec2', region_name=region)
        self.elasticache = boto3.client('elasticache', region_name=region)
    
    def create_secure_network_setup(self, config):
        """Create secure network setup for ElastiCache"""
        
        # Create security group for ElastiCache
        security_group_response = self.ec2.create_security_group(
            GroupName=f"{config['app_name']}-elasticache-sg",
            Description=f"Security group for {config['app_name']} ElastiCache cluster",
            VpcId=config['vpc_id']
        )
        
        security_group_id = security_group_response['GroupId']
        
        # Configure security group rules
        # Allow Redis/Memcached access from application security groups
        for app_sg in config['application_security_groups']:
            if config['engine'] == 'redis':
                self.ec2.authorize_security_group_ingress(
                    GroupId=security_group_id,
                    IpPermissions=[
                        {
                            'IpProtocol': 'tcp',
                            'FromPort': 6379,
                            'ToPort': 6379,
                            'UserIdGroupPairs': [
                                {
                                    'GroupId': app_sg,
                                    'Description': f'Redis access from {app_sg}'
                                }
                            ]
                        }
                    ]
                )
            else:  # Memcached
                self.ec2.authorize_security_group_ingress(
                    GroupId=security_group_id,
                    IpPermissions=[
                        {
                            'IpProtocol': 'tcp',
                            'FromPort': 11211,
                            'ToPort': 11211,
                            'UserIdGroupPairs': [
                                {
                                    'GroupId': app_sg,
                                    'Description': f'Memcached access from {app_sg}'
                                }
                            ]
                        }
                    ]
                )
        
        # Create cache subnet group
        subnet_group_response = self.elasticache.create_cache_subnet_group(
            CacheSubnetGroupName=f"{config['app_name']}-subnet-group",
            CacheSubnetGroupDescription=f"Subnet group for {config['app_name']} ElastiCache",
            SubnetIds=config['private_subnet_ids']
        )
        
        return {
            'security_group_id': security_group_id,
            'subnet_group_name': subnet_group_response['CacheSubnetGroup']['CacheSubnetGroupName']
        }
    
    def setup_encryption_and_auth(self, cluster_id, engine='redis'):
        """Configure encryption and authentication for existing cluster"""
        
        if engine == 'redis':
            # Generate auth token
            import secrets
            import string
            
            # Generate secure auth token
            alphabet = string.ascii_letters + string.digits
            auth_token = ''.join(secrets.choice(alphabet) for _ in range(32))
            
            # Enable encryption in transit and at rest
            response = self.elasticache.modify_replication_group(
                ReplicationGroupId=cluster_id,
                AtRestEncryptionEnabled=True,
                TransitEncryptionEnabled=True,
                AuthToken=auth_token,
                AuthTokenUpdateStrategy='ROTATE',
                ApplyImmediately=False  # Apply during next maintenance window
            )
            
            return {
                'auth_token': auth_token,
                'encryption_enabled': True,
                'transit_encryption': True
            }
        else:
            # Memcached doesn't support auth tokens or encryption at rest
            return {
                'message': 'Memcached does not support authentication or encryption at rest',
                'recommendations': [
                    'Use Redis for enhanced security features',
                    'Implement network-level security with VPC and security groups',
                    'Consider application-level encryption for sensitive data'
                ]
            }
```

### User Management and Access Control

```python
class ElastiCacheUserManager:
    def __init__(self, region='us-west-2'):
        self.elasticache = boto3.client('elasticache', region_name=region)
    
    def create_redis_user_group(self, config):
        """Create Redis user group with role-based access control"""
        
        # Create users with different permission levels
        users = []
        
        # Admin user
        admin_user = self.elasticache.create_user(
            UserId=f"{config['app_name']}-admin",
            UserName=f"{config['app_name']}-admin",
            Engine='Redis',
            Passwords=[config['admin_password']],
            AccessString='on ~* &* +@all',  # Full access
            Tags=[
                {'Key': 'Role', 'Value': 'Admin'},
                {'Key': 'Application', 'Value': config['app_name']}
            ]
        )
        users.append(admin_user['UserId'])
        
        # Read-write user for applications
        app_user = self.elasticache.create_user(
            UserId=f"{config['app_name']}-app",
            UserName=f"{config['app_name']}-app",
            Engine='Redis',
            Passwords=[config['app_password']],
            AccessString='on ~* &* +@read +@write +@string +@hash +@list +@set +@sortedset +@stream +@bitmap +@hyperloglog +@geo -@dangerous',
            Tags=[
                {'Key': 'Role', 'Value': 'Application'},
                {'Key': 'Application', 'Value': config['app_name']}
            ]
        )
        users.append(app_user['UserId'])
        
        # Read-only user for analytics/reporting
        readonly_user = self.elasticache.create_user(
            UserId=f"{config['app_name']}-readonly",
            UserName=f"{config['app_name']}-readonly",
            Engine='Redis',
            Passwords=[config['readonly_password']],
            AccessString='on ~* &* +@read -@dangerous',  # Read-only access
            Tags=[
                {'Key': 'Role', 'Value': 'ReadOnly'},
                {'Key': 'Application', 'Value': config['app_name']}
            ]
        )
        users.append(readonly_user['UserId'])
        
        # Create user group
        user_group = self.elasticache.create_user_group(
            UserGroupId=f"{config['app_name']}-user-group",
            Engine='Redis',
            UserIds=users,
            Tags=[
                {'Key': 'Application', 'Value': config['app_name']},
                {'Key': 'Environment', 'Value': config.get('environment', 'prod')}
            ]
        )
        
        return {
            'user_group_id': user_group['UserGroupId'],
            'users': {
                'admin': admin_user['UserId'],
                'application': app_user['UserId'],
                'readonly': readonly_user['UserId']
            }
        }
```

## Cost Optimization

### Right-Sizing and Cost Analysis

```python
class ElastiCacheCostOptimizer:
    def __init__(self, region='us-west-2'):
        self.elasticache = boto3.client('elasticache', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.ce = boto3.client('ce', region_name='us-east-1')  # Cost Explorer
    
    def analyze_cluster_utilization(self, days=30):
        """Analyze ElastiCache cluster utilization for cost optimization"""
        
        # Get all clusters
        redis_clusters = self.elasticache.describe_replication_groups()['ReplicationGroups']
        memcached_clusters = self.elasticache.describe_cache_clusters()['CacheClusters']
        
        utilization_analysis = []
        
        # Analyze Redis clusters
        for cluster in redis_clusters:
            cluster_id = cluster['ReplicationGroupId']
            analysis = self._analyze_redis_cluster(cluster_id, cluster, days)
            utilization_analysis.append(analysis)
        
        # Analyze Memcached clusters
        for cluster in memcached_clusters:
            if cluster.get('ReplicationGroupId') is None:  # Skip if part of replication group
                cluster_id = cluster['CacheClusterId']
                analysis = self._analyze_memcached_cluster(cluster_id, cluster, days)
                utilization_analysis.append(analysis)
        
        return utilization_analysis
    
    def _analyze_redis_cluster(self, cluster_id, cluster_info, days):
        """Analyze Redis cluster utilization"""
        
        # Get utilization metrics
        metrics = self._get_cluster_metrics(f"{cluster_id}-001", days)
        
        # Calculate utilization scores
        cpu_score = min(100, metrics.get('avg_cpu', 0) * 1.5)  # Weight CPU higher
        memory_score = metrics.get('avg_memory', 0)
        hit_rate_score = metrics.get('avg_hit_rate', 0)
        
        overall_score = (cpu_score + memory_score + hit_rate_score) / 3
        
        # Generate recommendations
        recommendations = []
        node_type = cluster_info['CacheNodeType']
        current_cost = self._estimate_monthly_cost(node_type, len(cluster_info['NodeGroups']))
        
        if overall_score < 30:
            recommendations.append("Cluster is underutilized - consider downsizing")
            recommended_instance = self._recommend_smaller_instance(node_type)
            if recommended_instance:
                savings = current_cost * 0.3  # Estimate 30% savings
                recommendations.append(f"Consider {recommended_instance} for ~${savings:.2f}/month savings")
        
        elif overall_score > 85:
            recommendations.append("Cluster is highly utilized - consider upsizing")
            recommended_instance = self._recommend_larger_instance(node_type)
            if recommended_instance:
                recommendations.append(f"Consider {recommended_instance} for better performance")
        
        if metrics.get('avg_hit_rate', 100) < 80:
            recommendations.append("Low cache hit rate - review caching strategy")
        
        return {
            'cluster_id': cluster_id,
            'cluster_type': 'redis',
            'node_type': node_type,
            'node_count': len(cluster_info['NodeGroups']),
            'utilization_score': overall_score,
            'metrics': metrics,
            'estimated_monthly_cost': current_cost,
            'recommendations': recommendations
        }
    
    def _get_cluster_metrics(self, cache_cluster_id, days):
        """Get CloudWatch metrics for cluster analysis"""
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        metrics = {}
        
        # CPU Utilization
        cpu_response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/ElastiCache',
            MetricName='CPUUtilization',
            Dimensions=[{'Name': 'CacheClusterId', 'Value': cache_cluster_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Average']
        )
        
        if cpu_response['Datapoints']:
            metrics['avg_cpu'] = sum(dp['Average'] for dp in cpu_response['Datapoints']) / len(cpu_response['Datapoints'])
        
        # Memory Usage
        memory_response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/ElastiCache',
            MetricName='DatabaseMemoryUsagePercentage',
            Dimensions=[{'Name': 'CacheClusterId', 'Value': cache_cluster_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Average']
        )
        
        if memory_response['Datapoints']:
            metrics['avg_memory'] = sum(dp['Average'] for dp in memory_response['Datapoints']) / len(memory_response['Datapoints'])
        
        # Cache Hit Rate
        hit_rate_response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/ElastiCache',
            MetricName='CacheHitRate',
            Dimensions=[{'Name': 'CacheClusterId', 'Value': cache_cluster_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Average']
        )
        
        if hit_rate_response['Datapoints']:
            metrics['avg_hit_rate'] = sum(dp['Average'] for dp in hit_rate_response['Datapoints']) / len(hit_rate_response['Datapoints'])
        
        return metrics
    
    def _estimate_monthly_cost(self, node_type, node_count):
        """Estimate monthly cost for cluster"""
        
        # Simplified pricing (US West 2, on-demand, as of 2024)
        hourly_rates = {
            'cache.t3.micro': 0.017,
            'cache.t3.small': 0.034,
            'cache.t3.medium': 0.068,
            'cache.r6g.large': 0.151,
            'cache.r6g.xlarge': 0.302,
            'cache.r6g.2xlarge': 0.604,
            'cache.r6g.4xlarge': 1.209,
            'cache.r7g.large': 0.158,
            'cache.r7g.xlarge': 0.315,
        }
        
        hourly_rate = hourly_rates.get(node_type, 0.151)  # Default to r6g.large
        return hourly_rate * 24 * 30 * node_count
    
    def generate_cost_optimization_report(self):
        """Generate comprehensive cost optimization report"""
        
        utilization_data = self.analyze_cluster_utilization()
        
        total_monthly_cost = sum(cluster['estimated_monthly_cost'] for cluster in utilization_data)
        underutilized_clusters = [c for c in utilization_data if c['utilization_score'] < 40]
        potential_savings = sum(c['estimated_monthly_cost'] * 0.3 for c in underutilized_clusters)
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_clusters': len(utilization_data),
            'total_monthly_cost': total_monthly_cost,
            'underutilized_clusters': len(underutilized_clusters),
            'potential_monthly_savings': potential_savings,
            'recommendations': [],
            'cluster_details': utilization_data
        }
        
        # Generate high-level recommendations
        if underutilized_clusters:
            report['recommendations'].append(f"Right-size {len(underutilized_clusters)} underutilized clusters")
            report['recommendations'].append(f"Potential savings: ${potential_savings:.2f}/month")
        
        # Check for clusters with low hit rates
        low_hit_rate_clusters = [c for c in utilization_data if c['metrics'].get('avg_hit_rate', 100) < 70]
        if low_hit_rate_clusters:
            report['recommendations'].append(f"Optimize caching strategy for {len(low_hit_rate_clusters)} clusters with low hit rates")
        
        return report
```

### Reserved Instance Recommendations

```bash
#!/bin/bash
# elasticache-ri-calculator.sh - Calculate potential savings with Reserved Instances

REGION=${1:-us-west-2}
TERM=${2:-1}  # 1 or 3 years

echo "Calculating ElastiCache Reserved Instance savings for $REGION (${TERM}-year term)"

# Get all current clusters
echo "=== Current ElastiCache Clusters ==="
aws elasticache describe-cache-clusters \
  --region $REGION \
  --show-cache-node-info \
  --output table \
  --query 'CacheClusters[?CacheClusterStatus==`available`].[CacheClusterId,CacheNodeType,NumCacheNodes,Engine]'

echo ""
echo "=== Reserved Instance Pricing Comparison ==="
echo "Node Type          | On-Demand $/hr | RI $/hr (${TERM}yr) | Monthly Savings | Annual Savings"
echo "-------------------|----------------|---------------------|-----------------|---------------"

# Sample pricing data (would need to be updated with current prices)
declare -A ON_DEMAND_PRICES
declare -A RI_PRICES_1YR
declare -A RI_PRICES_3YR

# Redis pricing (example - update with current pricing)
ON_DEMAND_PRICES["cache.r6g.large"]=0.151
RI_PRICES_1YR["cache.r6g.large"]=0.108
RI_PRICES_3YR["cache.r6g.large"]=0.089

ON_DEMAND_PRICES["cache.r6g.xlarge"]=0.302
RI_PRICES_1YR["cache.r6g.xlarge"]=0.216
RI_PRICES_3YR["cache.r6g.xlarge"]=0.178

for node_type in "${!ON_DEMAND_PRICES[@]}"; do
    on_demand=${ON_DEMAND_PRICES[$node_type]}
    
    if [ "$TERM" = "1" ]; then
        ri_price=${RI_PRICES_1YR[$node_type]}
    else
        ri_price=${RI_PRICES_3YR[$node_type]}
    fi
    
    hourly_savings=$(echo "$on_demand - $ri_price" | bc -l)
    monthly_savings=$(echo "$hourly_savings * 24 * 30" | bc -l)
    annual_savings=$(echo "$hourly_savings * 24 * 365" | bc -l)
    
    printf "%-18s | \$%-13.3f | \$%-18.3f | \$%-14.2f | \$%-13.2f\n" \
        "$node_type" "$on_demand" "$ri_price" "$monthly_savings" "$annual_savings"
done

echo ""
echo "=== Recommendations ==="
echo "1. Review cluster utilization before purchasing RIs"
echo "2. Consider purchasing RIs for stable, long-running workloads"
echo "3. Mix of 1-year and 3-year terms based on business requirements"
echo "4. Monitor usage patterns to optimize RI purchases"
```

## Automation & Infrastructure as Code

### Terraform Configuration

```hcl
# Redis cluster with comprehensive configuration
resource "aws_elasticache_subnet_group" "redis" {
  name       = "${var.application_name}-redis-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name        = "${var.application_name}-redis-subnet-group"
    Environment = var.environment
  }
}

resource "aws_security_group" "redis" {
  name_prefix = "${var.application_name}-redis-"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = var.application_security_group_ids
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.application_name}-redis-sg"
    Environment = var.environment
  }
}

resource "aws_elasticache_parameter_group" "redis" {
  family = "redis7"
  name   = "${var.application_name}-redis-params"

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  parameter {
    name  = "timeout"
    value = "300"
  }

  parameter {
    name  = "tcp-keepalive"
    value = "60"
  }

  tags = {
    Name        = "${var.application_name}-redis-params"
    Environment = var.environment
  }
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "${var.application_name}-redis"
  description                = "Redis cluster for ${var.application_name}"
  
  node_type                  = var.redis_node_type
  port                       = 6379
  parameter_group_name       = aws_elasticache_parameter_group.redis.name
  
  num_cache_clusters         = var.redis_num_cache_clusters
  automatic_failover_enabled = var.redis_num_cache_clusters > 1
  multi_az_enabled          = var.redis_num_cache_clusters > 1
  
  subnet_group_name = aws_elasticache_subnet_group.redis.name
  security_group_ids = [aws_security_group.redis.id]
  
  # Cluster mode configuration
  cluster_mode {
    num_node_groups         = var.redis_num_shards
    replicas_per_node_group = var.redis_replicas_per_shard
  }
  
  # Security
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                = var.redis_auth_token
  
  # Backup
  snapshot_retention_limit = 7
  snapshot_window         = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"
  
  # Monitoring
  notification_topic_arn = var.sns_topic_arn
  
  # Logging
  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis_slow_log.name
    destination_type = "cloudwatch-logs"
    log_format      = "text"
    log_type        = "slow-log"
  }

  tags = {
    Name        = "${var.application_name}-redis"
    Environment = var.environment
    Engine      = "redis"
    ManagedBy   = "terraform"
  }

  depends_on = [aws_cloudwatch_log_group.redis_slow_log]
}

resource "aws_cloudwatch_log_group" "redis_slow_log" {
  name              = "/aws/elasticache/redis/${var.application_name}/slow-log"
  retention_in_days = 7

  tags = {
    Name        = "${var.application_name}-redis-slow-log"
    Environment = var.environment
  }
}

# CloudWatch alarms
resource "aws_cloudwatch_metric_alarm" "redis_cpu_high" {
  alarm_name          = "${var.application_name}-redis-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors redis cpu utilization"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    CacheClusterId = "${aws_elasticache_replication_group.redis.replication_group_id}-001"
  }

  tags = {
    Name        = "${var.application_name}-redis-cpu-alarm"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_metric_alarm" "redis_memory_high" {
  alarm_name          = "${var.application_name}-redis-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseMemoryUsagePercentage"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = "85"
  alarm_description   = "This metric monitors redis memory utilization"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    CacheClusterId = "${aws_elasticache_replication_group.redis.replication_group_id}-001"
  }

  tags = {
    Name        = "${var.application_name}-redis-memory-alarm"
    Environment = var.environment
  }
}

# Outputs
output "redis_endpoint" {
  description = "Redis primary endpoint"
  value       = aws_elasticache_replication_group.redis.configuration_endpoint_address
}

output "redis_auth_token" {
  description = "Redis authentication token"
  value       = var.redis_auth_token
  sensitive   = true
}
```

### CloudFormation Template

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Parameters:
  ApplicationName:
    Type: String
    Description: Name of the application
  Environment:
    Type: String
    Default: dev
    AllowedValues: [dev, staging, prod]
  VPCId:
    Type: AWS::EC2::VPC::Id
  PrivateSubnetIds:
    Type: List<AWS::EC2::Subnet::Id>
  RedisNodeType:
    Type: String
    Default: cache.r6g.large
    AllowedValues: [cache.t3.micro, cache.t3.small, cache.r6g.large, cache.r6g.xlarge]
  RedisNumNodes:
    Type: Number
    Default: 3
    MinValue: 1
    MaxValue: 20

Resources:
  RedisSubnetGroup:
    Type: AWS::ElastiCache::SubnetGroup
    Properties:
      Description: !Sub 'Subnet group for ${ApplicationName} Redis cluster'
      SubnetIds: !Ref PrivateSubnetIds
      CacheSubnetGroupName: !Sub '${ApplicationName}-redis-subnet-group'

  RedisSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: !Sub 'Security group for ${ApplicationName} Redis cluster'
      VpcId: !Ref VPCId
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 6379
          ToPort: 6379
          SourceSecurityGroupId: !Ref ApplicationSecurityGroup
      Tags:
        - Key: Name
          Value: !Sub '${ApplicationName}-redis-sg'
        - Key: Environment
          Value: !Ref Environment

  RedisParameterGroup:
    Type: AWS::ElastiCache::ParameterGroup
    Properties:
      CacheParameterGroupFamily: redis7
      Description: !Sub 'Parameter group for ${ApplicationName} Redis cluster'
      Properties:
        maxmemory-policy: allkeys-lru
        timeout: 300
        tcp-keepalive: 60

  RedisReplicationGroup:
    Type: AWS::ElastiCache::ReplicationGroup
    Properties:
      ReplicationGroupId: !Sub '${ApplicationName}-redis'
      ReplicationGroupDescription: !Sub 'Redis cluster for ${ApplicationName}'
      NumCacheClusters: !Ref RedisNumNodes
      CacheNodeType: !Ref RedisNodeType
      Engine: redis
      EngineVersion: '7.0'
      CacheParameterGroupName: !Ref RedisParameterGroup
      CacheSubnetGroupName: !Ref RedisSubnetGroup
      SecurityGroupIds:
        - !Ref RedisSecurityGroup
      
      # High Availability
      AutomaticFailoverEnabled: !If [MultiNode, true, false]
      MultiAZEnabled: !If [MultiNode, true, false]
      
      # Security
      AtRestEncryptionEnabled: true
      TransitEncryptionEnabled: true
      AuthToken: !Ref RedisAuthToken
      
      # Backup
      SnapshotRetentionLimit: 7
      SnapshotWindow: '03:00-04:00'
      PreferredMaintenanceWindow: 'sun:04:00-sun:05:00'
      
      # Logging
      LogDeliveryConfigurations:
        - DestinationType: cloudwatch-logs
          DestinationDetails:
            LogGroup: !Ref RedisSlowLogGroup
          LogFormat: text
          LogType: slow-log
      
      Tags:
        - Key: Name
          Value: !Sub '${ApplicationName}-redis'
        - Key: Environment
          Value: !Ref Environment

  RedisSlowLogGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: !Sub '/aws/elasticache/redis/${ApplicationName}/slow-log'
      RetentionInDays: 7

  # CloudWatch Alarms
  RedisCPUAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub '${ApplicationName}-redis-cpu-high'
      AlarmDescription: 'Redis CPU utilization is high'
      MetricName: CPUUtilization
      Namespace: AWS/ElastiCache
      Statistic: Average
      Period: 300
      EvaluationPeriods: 2
      Threshold: 80
      ComparisonOperator: GreaterThanThreshold
      Dimensions:
        - Name: CacheClusterId
          Value: !Sub '${RedisReplicationGroup}-001'
      AlarmActions:
        - !Ref SNSTopic

  RedisMemoryAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub '${ApplicationName}-redis-memory-high'
      AlarmDescription: 'Redis memory utilization is high'
      MetricName: DatabaseMemoryUsagePercentage
      Namespace: AWS/ElastiCache
      Statistic: Average
      Period: 300
      EvaluationPeriods: 2
      Threshold: 85
      ComparisonOperator: GreaterThanThreshold
      Dimensions:
        - Name: CacheClusterId
          Value: !Sub '${RedisReplicationGroup}-001'
      AlarmActions:
        - !Ref SNSTopic

Conditions:
  MultiNode: !Not [!Equals [!Ref RedisNumNodes, 1]]

Outputs:
  RedisEndpoint:
    Description: Redis primary endpoint
    Value: !GetAtt RedisReplicationGroup.RedisEndpoint.Address
    Export:
      Name: !Sub '${AWS::StackName}-RedisEndpoint'
  
  RedisPort:
    Description: Redis port
    Value: !GetAtt RedisReplicationGroup.RedisEndpoint.Port
    Export:
      Name: !Sub '${AWS::StackName}-RedisPort'
```

## Troubleshooting & Operations

### Common Issues and Solutions

#### Connection Issues
```python
def diagnose_elasticache_connectivity(cluster_endpoint, port=6379, engine='redis'):
    """Diagnose ElastiCache connectivity issues"""
    
    import socket
    import redis
    import telnetlib
    
    issues = []
    recommendations = []
    
    # Test basic network connectivity
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((cluster_endpoint, port))
        sock.close()
        
        if result != 0:
            issues.append(f"Cannot connect to {cluster_endpoint}:{port}")
            recommendations.extend([
                "Check security group allows inbound traffic on port",
                "Verify cluster is in same VPC as client",
                "Check if cluster is in available state"
            ])
    except Exception as e:
        issues.append(f"Network connectivity test failed: {e}")
    
    # Test Redis-specific connectivity
    if engine == 'redis':
        try:
            r = redis.Redis(host=cluster_endpoint, port=port, decode_responses=True)
            r.ping()
        except redis.ConnectionError as e:
            issues.append(f"Redis connection failed: {e}")
            recommendations.extend([
                "Check if AUTH token is required",
                "Verify encryption in transit settings",
                "Check Redis client configuration"
            ])
        except redis.AuthenticationError:
            issues.append("Redis authentication failed")
            recommendations.append("Verify AUTH token is correct")
    
    return {
        'cluster_endpoint': cluster_endpoint,
        'port': port,
        'engine': engine,
        'issues': issues,
        'recommendations': recommendations
    }
```

#### Performance Issues
```python
def diagnose_elasticache_performance(cluster_id, region='us-west-2'):
    """Diagnose ElastiCache performance issues"""
    
    cloudwatch = boto3.client('cloudwatch', region_name=region)
    elasticache = boto3.client('elasticache', region_name=region)
    
    # Get cluster information
    try:
        cluster_info = elasticache.describe_replication_groups(
            ReplicationGroupId=cluster_id
        )['ReplicationGroups'][0]
    except:
        cluster_info = elasticache.describe_cache_clusters(
            CacheClusterId=cluster_id
        )['CacheClusters'][0]
    
    # Get recent performance metrics
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=1)
    
    performance_issues = []
    recommendations = []
    
    # Check CPU utilization
    cpu_metrics = cloudwatch.get_metric_statistics(
        Namespace='AWS/ElastiCache',
        MetricName='CPUUtilization',
        Dimensions=[{'Name': 'CacheClusterId', 'Value': f'{cluster_id}-001'}],
        StartTime=start_time,
        EndTime=end_time,
        Period=300,
        Statistics=['Average', 'Maximum']
    )
    
    if cpu_metrics['Datapoints']:
        avg_cpu = sum(dp['Average'] for dp in cpu_metrics['Datapoints']) / len(cpu_metrics['Datapoints'])
        max_cpu = max(dp['Maximum'] for dp in cpu_metrics['Datapoints'])
        
        if avg_cpu > 80:
            performance_issues.append(f"High average CPU utilization: {avg_cpu:.1f}%")
            recommendations.extend([
                "Consider scaling up to larger instance type",
                "Review application connection pooling",
                "Check for inefficient operations"
            ])
        
        if max_cpu > 95:
            performance_issues.append(f"CPU spikes detected: {max_cpu:.1f}%")
    
    # Check memory utilization
    memory_metrics = cloudwatch.get_metric_statistics(
        Namespace='AWS/ElastiCache',
        MetricName='DatabaseMemoryUsagePercentage',
        Dimensions=[{'Name': 'CacheClusterId', 'Value': f'{cluster_id}-001'}],
        StartTime=start_time,
        EndTime=end_time,
        Period=300,
        Statistics=['Average', 'Maximum']
    )
    
    if memory_metrics['Datapoints']:
        avg_memory = sum(dp['Average'] for dp in memory_metrics['Datapoints']) / len(memory_metrics['Datapoints'])
        max_memory = max(dp['Maximum'] for dp in memory_metrics['Datapoints'])
        
        if avg_memory > 85:
            performance_issues.append(f"High memory utilization: {avg_memory:.1f}%")
            recommendations.extend([
                "Review memory configuration and eviction policies",
                "Consider scaling to instance with more memory",
                "Optimize data structures and TTL settings"
            ])
    
    # Check cache hit rate
    hit_rate_metrics = cloudwatch.get_metric_statistics(
        Namespace='AWS/ElastiCache',
        MetricName='CacheHitRate',
        Dimensions=[{'Name': 'CacheClusterId', 'Value': f'{cluster_id}-001'}],
        StartTime=start_time,
        EndTime=end_time,
        Period=300,
        Statistics=['Average']
    )
    
    if hit_rate_metrics['Datapoints']:
        avg_hit_rate = sum(dp['Average'] for dp in hit_rate_metrics['Datapoints']) / len(hit_rate_metrics['Datapoints'])
        
        if avg_hit_rate < 80:
            performance_issues.append(f"Low cache hit rate: {avg_hit_rate:.1f}%")
            recommendations.extend([
                "Review caching strategy and key patterns",
                "Optimize TTL settings",
                "Consider warming up cache after deployments"
            ])
    
    return {
        'cluster_id': cluster_id,
        'performance_issues': performance_issues,
        'recommendations': recommendations,
        'metrics_summary': {
            'avg_cpu': avg_cpu if 'avg_cpu' in locals() else 0,
            'avg_memory': avg_memory if 'avg_memory' in locals() else 0,
            'avg_hit_rate': avg_hit_rate if 'avg_hit_rate' in locals() else 0
        }
    }
```

#### Backup and Recovery Operations
```bash
#!/bin/bash
# elasticache-backup-restore.sh - ElastiCache backup and restore operations

OPERATION=$1
CLUSTER_ID=$2
SNAPSHOT_NAME=$3
REGION=${4:-us-west-2}

if [ $# -lt 2 ]; then
    echo "Usage: $0 <backup|restore|list> <cluster-id> [snapshot-name] [region]"
    exit 1
fi

case $OPERATION in
    "backup")
        if [ -z "$SNAPSHOT_NAME" ]; then
            SNAPSHOT_NAME="${CLUSTER_ID}-manual-$(date +%Y%m%d-%H%M%S)"
        fi
        
        echo "Creating manual backup of cluster: $CLUSTER_ID"
        aws elasticache create-snapshot \
          --replication-group-id $CLUSTER_ID \
          --snapshot-name $SNAPSHOT_NAME \
          --region $REGION
        
        echo "Backup initiated: $SNAPSHOT_NAME"
        echo "Monitor progress with: aws elasticache describe-snapshots --snapshot-name $SNAPSHOT_NAME"
        ;;
        
    "restore")
        if [ -z "$SNAPSHOT_NAME" ]; then
            echo "Snapshot name required for restore operation"
            exit 1
        fi
        
        NEW_CLUSTER_ID="${CLUSTER_ID}-restored-$(date +%Y%m%d)"
        
        echo "Restoring from snapshot: $SNAPSHOT_NAME"
        echo "New cluster ID: $NEW_CLUSTER_ID"
        
        # Get original cluster configuration
        ORIGINAL_CONFIG=$(aws elasticache describe-replication-groups \
          --replication-group-id $CLUSTER_ID \
          --region $REGION \
          --query 'ReplicationGroups[0]')
        
        NODE_TYPE=$(echo $ORIGINAL_CONFIG | jq -r '.CacheNodeType')
        SUBNET_GROUP=$(echo $ORIGINAL_CONFIG | jq -r '.CacheSubnetGroupName')
        SECURITY_GROUPS=$(echo $ORIGINAL_CONFIG | jq -r '.SecurityGroups[].SecurityGroupId' | tr '\n' ' ')
        
        aws elasticache create-replication-group \
          --replication-group-id $NEW_CLUSTER_ID \
          --replication-group-description "Restored from $SNAPSHOT_NAME" \
          --snapshot-name $SNAPSHOT_NAME \
          --cache-node-type $NODE_TYPE \
          --cache-subnet-group-name $SUBNET_GROUP \
          --security-group-ids $SECURITY_GROUPS \
          --region $REGION
        
        echo "Restore initiated. Monitor progress with:"
        echo "aws elasticache describe-replication-groups --replication-group-id $NEW_CLUSTER_ID"
        ;;
        
    "list")
        echo "Available snapshots for cluster: $CLUSTER_ID"
        aws elasticache describe-snapshots \
          --replication-group-id $CLUSTER_ID \
          --region $REGION \
          --output table \
          --query 'Snapshots[*].[SnapshotName,SnapshotStatus,SnapshotSource,NodeSnapshots[0].SnapshotCreateTime]'
        ;;
        
    *)
        echo "Invalid operation. Use: backup, restore, or list"
        exit 1
        ;;
esac
```

## Best Practices

### Cache Design Patterns
- **Cache-Aside (Lazy Loading)** - Load data into cache only when needed
- **Write-Through** - Update cache and database simultaneously
- **Write-Behind (Write-Back)** - Update cache immediately, database asynchronously
- **Refresh-Ahead** - Proactively refresh cache before expiration

### Performance Optimization
- **Right-size instances** based on memory and CPU requirements
- **Use connection pooling** to minimize connection overhead
- **Implement proper TTL strategies** to balance freshness and performance
- **Monitor cache hit ratios** and optimize caching strategies accordingly
- **Use pipelining** for batch operations to reduce network round trips

### Security Best Practices
- **Enable encryption** at rest and in transit for sensitive data
- **Use VPC deployment** for network isolation
- **Implement authentication** with Redis AUTH tokens
- **Apply least privilege** security group rules
- **Regular security audits** and compliance checks

### Operational Excellence
- **Automate backups** with appropriate retention policies
- **Monitor key metrics** with CloudWatch alarms
- **Implement proper logging** for troubleshooting
- **Plan for disaster recovery** with cross-region replication
- **Regular performance reviews** and capacity planning

## Additional Resources

### AWS Documentation
- [Amazon ElastiCache User Guide](https://docs.aws.amazon.com/elasticache/latest/userguide/)
- [ElastiCache for Redis User Guide](https://docs.aws.amazon.com/elasticache/latest/red-ug/)
- [ElastiCache for Memcached User Guide](https://docs.aws.amazon.com/elasticache/latest/mem-ug/)

### Tools & Utilities
- **Redis CLI** - Command-line interface for Redis operations
- **redis-py** - Python client library for Redis
- **pymemcache** - Python client library for Memcached
- **ElastiCache Cluster Client** - Enhanced Memcached client with auto-discovery

### Best Practices Guides
- [ElastiCache Best Practices](https://docs.aws.amazon.com/elasticache/latest/userguide/BestPractices.html)
- [Redis Best Practices](https://docs.aws.amazon.com/elasticache/latest/red-ug/BestPractices.html)
- [Caching Strategies](https://docs.aws.amazon.com/elasticache/latest/userguide/Strategies.html)

### Integration Examples
- [ElastiCache with Lambda](https://docs.aws.amazon.com/elasticache/latest/userguide/Lambda.html)
- [ElastiCache with ECS](https://aws.amazon.com/blogs/containers/microservices-with-amazon-ecs-and-application-load-balancer/)
- [ElastiCache Monitoring](https://docs.aws.amazon.com/elasticache/latest/userguide/CacheMetrics.html)