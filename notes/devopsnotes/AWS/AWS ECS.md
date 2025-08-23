# AWS ECS (Elastic Container Service)

> **Service Type:** Compute | **Scope:** Regional | **Serverless:** Limited

## Overview

Amazon Elastic Container Service (ECS) is a fully managed container orchestration service that enables you to run, stop, and manage Docker containers on a cluster. ECS eliminates the need to install and operate your own container orchestration software, manage and scale a cluster of virtual machines, or schedule containers on those virtual machines.

## DevOps & Enterprise Use Cases

### Microservices Architecture
- **Service decomposition** with independent container deployments
- **API gateway integration** for service-to-service communication
- **Database per service** pattern with container-based data stores
- **Event-driven architecture** with container-based message processing

### CI/CD Container Pipelines
- **Blue-green deployments** with zero-downtime service updates
- **Rolling deployments** for gradual service updates
- **Canary deployments** with traffic splitting capabilities
- **Multi-environment promotion** from development to production

### Scalable Application Hosting
- **Auto Scaling** based on CPU, memory, or custom metrics
- **Load balancing** with Application and Network Load Balancers
- **High availability** across multiple Availability Zones
- **Cost optimization** with Spot instances and resource right-sizing

### Batch Processing and ETL
- **Scheduled jobs** using ECS tasks with CloudWatch Events
- **Data processing pipelines** with container-based workers
- **Machine learning workflows** with GPU-enabled container instances
- **Log processing** and analytics with streaming data

### Legacy Application Modernization
- **Containerization** of existing applications without code changes
- **Hybrid deployments** mixing containers and traditional infrastructure
- **Gradual migration** with container-based service replacement
- **Cloud-native transformation** with modern DevOps practices

## Core Architecture Components

### Clusters
- **Logical grouping** of compute resources (EC2 instances or Fargate)
- **Capacity providers** for mixed instance types and Spot instances
- **Cluster auto scaling** for dynamic capacity management
- **Resource isolation** between different applications or environments

### Task Definitions
- **Container specifications** including image, CPU, memory, and networking
- **JSON template** defining the desired state of your application
- **Version control** with revision management and rollback capabilities
- **Environment variables** and secrets integration

### Services
- **Desired state management** maintaining specified number of running tasks
- **Rolling updates** with configurable deployment strategies
- **Load balancer integration** for traffic distribution
- **Service discovery** with AWS Cloud Map integration

### Tasks
- **Atomic unit** of work representing one or more containers
- **Ephemeral execution** for batch jobs and one-time operations
- **Task placement** strategies for optimal resource utilization
- **Network isolation** with VPC integration and security groups

## Service Features & Capabilities

### Launch Types

### AWS Fargate
- **Serverless containers** with no infrastructure management
- **Per-second billing** based on vCPU and memory consumption
- **Automatic scaling** without capacity planning
- **Enhanced security** with task-level isolation

### EC2 Launch Type
- **Full control** over the underlying infrastructure
- **Cost optimization** with Reserved Instances and Spot pricing
- **Custom AMIs** for specialized workload requirements
- **Local storage** access for high-performance applications

### External (Anywhere)
- **On-premises integration** with ECS Anywhere
- **Hybrid cloud** deployments across AWS and customer data centers
- **Consistent tooling** regardless of infrastructure location
- **Edge computing** capabilities for distributed applications

## Networking and Security

### VPC Integration
- **Task networking** with ENI attachment for Fargate tasks
- **Security groups** for fine-grained network access control
- **Subnets** placement for public, private, or isolated environments
- **NAT Gateway** configuration for outbound internet access

### Service Discovery
- **AWS Cloud Map** integration for service registration
- **DNS-based discovery** for internal service communication
- **Load balancer integration** for external traffic routing
- **Health checks** for service availability monitoring

### IAM Roles and Permissions
- **Task roles** for granular permissions to AWS services
- **Execution roles** for ECS agent and container runtime permissions
- **Service-linked roles** for ECS service operations
- **Cross-account access** for multi-account deployments

## Configuration & Setup

### Initial Cluster Setup
```bash
# Create ECS cluster with mixed capacity providers
aws ecs create-cluster \
  --cluster-name production-cluster \
  --capacity-providers EC2 FARGATE FARGATE_SPOT \
  --default-capacity-provider-strategy \
    capacityProvider=FARGATE,weight=1 \
    capacityProvider=FARGATE_SPOT,weight=2 \
  --settings name=containerInsights,value=enabled \
  --tags key=Environment,value=Production

# Create IAM roles for ECS tasks
aws iam create-role \
  --role-name ecsTaskExecutionRole \
  --assume-role-policy-document file://ecs-task-trust-policy.json

aws iam attach-role-policy \
  --role-name ecsTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
```

### Network Configuration
```bash
# Create security group for ECS tasks
aws ec2 create-security-group \
  --group-name ecs-tasks-sg \
  --description "Security group for ECS tasks" \
  --vpc-id vpc-12345678

# Add inbound rules
aws ec2 authorize-security-group-ingress \
  --group-id sg-abcdef123 \
  --protocol tcp \
  --port 8080 \
  --source-group sg-loadbalancer123
```

## Enterprise Implementation Examples

### Multi-Service Architecture
```python
import boto3
import json
from typing import Dict, List

class EnterpriseECSManager:
    def __init__(self, region='us-west-2'):
        self.ecs = boto3.client('ecs', region_name=region)
        self.elbv2 = boto3.client('elbv2', region_name=region)
        self.servicediscovery = boto3.client('servicediscovery', region_name=region)
        self.logs = boto3.client('logs', region_name=region)
    
    def deploy_microservices_platform(self, config: Dict):
        """Deploy complete microservices platform with ECS"""
        
        cluster_name = config['cluster_name']
        services = config['services']
        
        # Create cluster
        cluster_result = self.create_enterprise_cluster(cluster_name, config.get('cluster_config', {}))
        
        # Setup service discovery
        namespace_id = self.setup_service_discovery(cluster_name, config['vpc_id'])
        
        # Create load balancer
        alb_arn = self.create_application_load_balancer(cluster_name, config['subnets'], config['security_groups'])
        
        # Deploy each service
        deployed_services = {}
        for service_name, service_config in services.items():
            service_arn = self.deploy_microservice(
                cluster_name, 
                service_name, 
                service_config,
                namespace_id,
                alb_arn
            )
            deployed_services[service_name] = service_arn
        
        return {
            'cluster': cluster_result,
            'namespace_id': namespace_id,
            'load_balancer': alb_arn,
            'services': deployed_services
        }
    
    def create_enterprise_cluster(self, cluster_name: str, config: Dict) -> str:
        """Create enterprise-grade ECS cluster"""
        
        try:
            response = self.ecs.create_cluster(
                clusterName=cluster_name,
                capacityProviders=['FARGATE', 'FARGATE_SPOT', 'EC2'],
                defaultCapacityProviderStrategy=[
                    {
                        'capacityProvider': 'FARGATE',
                        'weight': config.get('fargate_weight', 1),
                        'base': config.get('fargate_base', 0)
                    },
                    {
                        'capacityProvider': 'FARGATE_SPOT', 
                        'weight': config.get('fargate_spot_weight', 3),
                        'base': config.get('fargate_spot_base', 0)
                    }
                ],
                settings=[
                    {'name': 'containerInsights', 'value': 'enabled'}
                ],
                configuration={
                    'executeCommandConfiguration': {
                        'kmsKeyId': config.get('kms_key_id'),
                        'logging': 'OVERRIDE',
                        'logConfiguration': {
                            'cloudWatchLogGroupName': f'/ecs/{cluster_name}/execute-command',
                            'cloudWatchEncryptionEnabled': True
                        }
                    }
                },
                tags=[
                    {'key': 'Environment', 'value': config.get('environment', 'production')},
                    {'key': 'ManagedBy', 'value': 'EnterpriseECSManager'}
                ]
            )
            return response['cluster']['clusterArn']
        except Exception as e:
            print(f"Error creating cluster: {e}")
            raise
    
    def deploy_microservice(self, cluster_name: str, service_name: str, 
                           config: Dict, namespace_id: str, alb_arn: str) -> str:
        """Deploy individual microservice with full enterprise configuration"""
        
        # Create CloudWatch log group
        log_group_name = f"/ecs/{cluster_name}/{service_name}"
        try:
            self.logs.create_log_group(
                logGroupName=log_group_name,
                kmsKeyId=config.get('kms_key_id'),
                tags={
                    'Application': service_name,
                    'Cluster': cluster_name
                }
            )
        except self.logs.exceptions.ResourceAlreadyExistsException:
            pass  # Log group already exists
        
        # Register task definition
        task_definition = self.create_task_definition(service_name, config, log_group_name)
        
        # Create target group
        target_group_arn = self.create_target_group(service_name, config, alb_arn)
        
        # Create service registry
        service_registry_arn = self.create_service_registry(service_name, namespace_id)
        
        # Create ECS service
        service_response = self.ecs.create_service(
            cluster=cluster_name,
            serviceName=service_name,
            taskDefinition=f"{service_name}:1",
            desiredCount=config.get('desired_count', 2),
            capacityProviderStrategy=config.get('capacity_provider_strategy', [
                {'capacityProvider': 'FARGATE', 'weight': 1}
            ]),
            networkConfiguration={
                'awsvpcConfiguration': {
                    'subnets': config['subnets'],
                    'securityGroups': config['security_groups'],
                    'assignPublicIp': 'DISABLED'
                }
            },
            loadBalancers=[{
                'targetGroupArn': target_group_arn,
                'containerName': f"{service_name}-container",
                'containerPort': config.get('container_port', 8080)
            }],
            serviceRegistries=[{
                'registryArn': service_registry_arn,
                'containerName': f"{service_name}-container"
            }],
            deploymentConfiguration={
                'maximumPercent': 200,
                'minimumHealthyPercent': 50,
                'deploymentCircuitBreaker': {
                    'enable': True,
                    'rollback': True
                }
            },
            enableExecuteCommand=True,
            enableLogging=True,
            tags=[
                {'key': 'Service', 'value': service_name},
                {'key': 'Cluster', 'value': cluster_name}
            ]
        )
        
        return service_response['service']['serviceArn']
```

### Blue-Green Deployment Strategy
```python
class BlueGreenDeploymentManager:
    def __init__(self, region='us-west-2'):
        self.ecs = boto3.client('ecs', region_name=region)
        self.elbv2 = boto3.client('elbv2', region_name=region)
    
    def execute_blue_green_deployment(self, deployment_config: Dict):
        """Execute blue-green deployment for ECS service"""
        
        cluster_name = deployment_config['cluster_name']
        service_name = deployment_config['service_name']
        new_task_definition = deployment_config['new_task_definition']
        
        # Create green service
        green_service_name = f"{service_name}-green"
        
        # Get current service configuration
        current_service = self.ecs.describe_services(
            cluster=cluster_name,
            services=[service_name]
        )['services'][0]
        
        # Create green service with new task definition
        green_service = self.ecs.create_service(
            cluster=cluster_name,
            serviceName=green_service_name,
            taskDefinition=new_task_definition,
            desiredCount=current_service['desiredCount'],
            capacityProviderStrategy=current_service['capacityProviderStrategy'],
            networkConfiguration=current_service['networkConfiguration'],
            deploymentConfiguration={
                'maximumPercent': 100,
                'minimumHealthyPercent': 100
            }
        )
        
        # Wait for green service to be stable
        self.wait_for_service_stable(cluster_name, green_service_name)
        
        # Create temporary target group for green service
        green_target_group = self.create_temporary_target_group(green_service_name)
        
        # Register green service with new target group
        self.ecs.update_service(
            cluster=cluster_name,
            service=green_service_name,
            loadBalancers=[{
                'targetGroupArn': green_target_group,
                'containerName': f"{service_name}-container",
                'containerPort': 8080
            }]
        )
        
        # Perform health checks and validation
        if self.validate_green_service(green_target_group):
            # Switch traffic to green
            self.switch_traffic_to_green(service_name, green_target_group)
            
            # Scale down blue service
            self.ecs.update_service(
                cluster=cluster_name,
                service=service_name,
                desiredCount=0
            )
            
            # Rename services (blue becomes old, green becomes current)
            return {'status': 'success', 'green_service': green_service_name}
        else:
            # Rollback - delete green service
            self.ecs.delete_service(
                cluster=cluster_name,
                service=green_service_name,
                force=True
            )
            return {'status': 'failed', 'reason': 'Health checks failed'}
```

## Practical CLI Examples

### Cluster Management

```bash
# Create ECS cluster
aws ecs create-cluster \
  --cluster-name production-web-cluster \
  --capacity-providers EC2 FARGATE FARGATE_SPOT \
  --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1 capacityProvider=FARGATE_SPOT,weight=4 \
  --tags key=Environment,value=Production key=Application,value=WebApp

# Create cluster with custom capacity provider
aws ecs create-capacity-provider \
  --name custom-capacity-provider \
  --auto-scaling-group-provider autoScalingGroupArn=arn:aws:autoscaling:us-west-2:123456789012:autoScalingGroup:uuid:autoScalingGroupName/my-asg,managedScaling='{status=ENABLED,targetCapacity=80,minimumScalingStepSize=1,maximumScalingStepSize=1000}',managedTerminationProtection=ENABLED

# Associate capacity provider with cluster
aws ecs put-cluster-capacity-providers \
  --cluster production-web-cluster \
  --capacity-providers EC2 FARGATE custom-capacity-provider \
  --default-capacity-provider-strategy capacityProvider=custom-capacity-provider,weight=3 capacityProvider=FARGATE,weight=1

# List clusters
aws ecs list-clusters

# Describe cluster details
aws ecs describe-clusters \
  --clusters production-web-cluster \
  --include CONFIGURATIONS,TAGS,ATTACHMENTS
```

### Task Definition Management

```bash
# Register task definition
cat > web-app-task-definition.json << 'EOF'
{
  "family": "web-app",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::123456789012:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "web-container",
      "image": "123456789012.dkr.ecr.us-west-2.amazonaws.com/my-web-app:latest",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/web-app",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "environment": [
        {
          "name": "NODE_ENV",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:us-west-2:123456789012:secret:prod/web-app/database-abc123"
        }
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
EOF

aws ecs register-task-definition \
  --cli-input-json file://web-app-task-definition.json

# List task definition families
aws ecs list-task-definition-families \
  --status ACTIVE

# Describe task definition
aws ecs describe-task-definition \
  --task-definition web-app:1

# Deregister old task definition
aws ecs deregister-task-definition \
  --task-definition web-app:1
```

### Service Management

```bash
# Create ECS service
aws ecs create-service \
  --cluster production-web-cluster \
  --service-name web-app-service \
  --task-definition web-app:2 \
  --desired-count 3 \
  --capacity-provider-strategy capacityProvider=FARGATE,weight=2 capacityProvider=FARGATE_SPOT,weight=1 \
  --network-configuration 'awsvpcConfiguration={subnets=[subnet-12345,subnet-67890],securityGroups=[sg-abcdef123],assignPublicIp=DISABLED}' \
  --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:us-west-2:123456789012:targetgroup/web-app-tg/1234567890123456,containerName=web-container,containerPort=8080 \
  --service-registries registryArn=arn:aws:servicediscovery:us-west-2:123456789012:service/srv-12345,containerName=web-container \
  --deployment-configuration maximumPercent=200,minimumHealthyPercent=50,deploymentCircuitBreaker='{enable=true,rollback=true}' \
  --tags key=Environment,value=Production key=Application,value=WebApp

# Update service with new task definition
aws ecs update-service \
  --cluster production-web-cluster \
  --service web-app-service \
  --task-definition web-app:3 \
  --desired-count 5 \
  --force-new-deployment

# Scale service
aws ecs update-service \
  --cluster production-web-cluster \
  --service web-app-service \
  --desired-count 10

# Delete service
aws ecs delete-service \
  --cluster production-web-cluster \
  --service web-app-service \
  --force
```

### Task Management

```bash
# Run standalone task
aws ecs run-task \
  --cluster production-web-cluster \
  --task-definition data-processing:1 \
  --capacity-provider-strategy capacityProvider=FARGATE_SPOT,weight=1 \
  --network-configuration 'awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-abcdef123],assignPublicIp=ENABLED}' \
  --overrides '{"containerOverrides":[{"name":"processor","environment":[{"name":"BATCH_SIZE","value":"1000"}]}]}' \
  --count 5

# Stop task
aws ecs stop-task \
  --cluster production-web-cluster \
  --task arn:aws:ecs:us-west-2:123456789012:task/production-web-cluster/abc123 \
  --reason "Manual stop for maintenance"

# List running tasks
aws ecs list-tasks \
  --cluster production-web-cluster \
  --service-name web-app-service \
  --desired-status RUNNING

# Describe tasks
aws ecs describe-tasks \
  --cluster production-web-cluster \
  --tasks arn:aws:ecs:us-west-2:123456789012:task/production-web-cluster/abc123
```

### Service Discovery and Load Balancing

```bash
# Create service discovery namespace
aws servicediscovery create-private-dns-namespace \
  --name local \
  --vpc vpc-12345678 \
  --description "Private namespace for ECS services"

# Create service discovery service
aws servicediscovery create-service \
  --name web-app \
  --namespace-id ns-12345 \
  --dns-config NamespaceId=ns-12345,DnsRecords=[{Type=A,TTL=60}] \
  --health-check-custom-config FailureThreshold=3

# Create Application Load Balancer target group
aws elbv2 create-target-group \
  --name web-app-targets \
  --protocol HTTP \
  --port 8080 \
  --vpc-id vpc-12345678 \
  --target-type ip \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3
```

## DevOps Automation Scripts

### ECS Service Deployment Script

```bash
#!/bin/bash
# deploy-ecs-service.sh - Deploy ECS service with blue-green deployment

SERVICE_NAME=$1
CLUSTER_NAME=$2
IMAGE_URI=$3
ENVIRONMENT=${4:-production}

if [ $# -lt 3 ]; then
    echo "Usage: $0 <service-name> <cluster-name> <image-uri> [environment]"
    exit 1
fi

echo "Deploying ${SERVICE_NAME} to cluster ${CLUSTER_NAME}"

# Get current service configuration
CURRENT_SERVICE=$(aws ecs describe-services \
    --cluster ${CLUSTER_NAME} \
    --services ${SERVICE_NAME} \
    --query 'services[0]')

if [ "$CURRENT_SERVICE" = "null" ]; then
    echo "Service ${SERVICE_NAME} not found in cluster ${CLUSTER_NAME}"
    exit 1
fi

# Get current task definition
CURRENT_TASK_DEF_ARN=$(echo "$CURRENT_SERVICE" | jq -r '.taskDefinition')
CURRENT_TASK_DEF=$(aws ecs describe-task-definition \
    --task-definition ${CURRENT_TASK_DEF_ARN} \
    --query 'taskDefinition')

# Extract task definition family and revision
FAMILY=$(echo "$CURRENT_TASK_DEF" | jq -r '.family')
CURRENT_REVISION=$(echo "$CURRENT_TASK_DEF" | jq -r '.revision')
NEW_REVISION=$((CURRENT_REVISION + 1))

echo "Current task definition: ${FAMILY}:${CURRENT_REVISION}"
echo "Creating new task definition: ${FAMILY}:${NEW_REVISION}"

# Update container image in task definition
NEW_TASK_DEF=$(echo "$CURRENT_TASK_DEF" | jq --arg image "$IMAGE_URI" '
    .containerDefinitions[0].image = $image |
    del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .placementConstraints, .compatibilities, .registeredAt, .registeredBy)
')

# Register new task definition
NEW_TASK_DEF_ARN=$(aws ecs register-task-definition \
    --cli-input-json "$NEW_TASK_DEF" \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)

echo "Registered new task definition: $NEW_TASK_DEF_ARN"

# Create deployment configuration for blue-green
DEPLOYMENT_CONFIG='{
    "maximumPercent": 200,
    "minimumHealthyPercent": 50,
    "deploymentCircuitBreaker": {
        "enable": true,
        "rollback": true
    }
}'

# Update service with new task definition
echo "Starting service update..."
UPDATE_RESPONSE=$(aws ecs update-service \
    --cluster ${CLUSTER_NAME} \
    --service ${SERVICE_NAME} \
    --task-definition ${NEW_TASK_DEF_ARN} \
    --deployment-configuration "$DEPLOYMENT_CONFIG" \
    --force-new-deployment)

DEPLOYMENT_ID=$(echo "$UPDATE_RESPONSE" | jq -r '.service.deployments[] | select(.status == "PRIMARY") | .id')

echo "Deployment started with ID: $DEPLOYMENT_ID"

# Monitor deployment progress
echo "Monitoring deployment progress..."
TIMEOUT=1200  # 20 minutes
ELAPSED=0

while [ $ELAPSED -lt $TIMEOUT ]; do
    SERVICE_STATUS=$(aws ecs describe-services \
        --cluster ${CLUSTER_NAME} \
        --services ${SERVICE_NAME} \
        --query 'services[0]')
    
    DEPLOYMENT_STATUS=$(echo "$SERVICE_STATUS" | jq -r --arg id "$DEPLOYMENT_ID" '
        .deployments[] | select(.id == $id) | .status
    ')
    
    RUNNING_COUNT=$(echo "$SERVICE_STATUS" | jq -r --arg id "$DEPLOYMENT_ID" '
        .deployments[] | select(.id == $id) | .runningCount
    ')
    
    DESIRED_COUNT=$(echo "$SERVICE_STATUS" | jq -r '.desiredCount')
    
    echo "Deployment status: $DEPLOYMENT_STATUS, Running: $RUNNING_COUNT/$DESIRED_COUNT"
    
    if [ "$DEPLOYMENT_STATUS" = "STEADY" ]; then
        echo "Deployment completed successfully!"
        
        # Verify service health
        echo "Verifying service health..."
        sleep 30
        
        # Check task health
        HEALTHY_TASKS=$(aws ecs describe-services \
            --cluster ${CLUSTER_NAME} \
            --services ${SERVICE_NAME} \
            --query 'services[0].deployments[] | select(.status == "PRIMARY") | .runningCount' \
            --output text)
        
        if [ "$HEALTHY_TASKS" -eq "$DESIRED_COUNT" ]; then
            echo "All tasks are healthy. Deployment verified."
            
            # Clean up old task definitions (keep last 5)
            echo "Cleaning up old task definitions..."
            aws ecs list-task-definitions \
                --family-prefix ${FAMILY} \
                --status ACTIVE \
                --sort DESC \
                --query 'taskDefinitionArns[5:]' \
                --output text | xargs -n1 aws ecs deregister-task-definition --task-definition
            
            exit 0
        else
            echo "Health check failed. Some tasks are not healthy."
            exit 1
        fi
    elif [ "$DEPLOYMENT_STATUS" = "FAILED" ]; then
        echo "Deployment failed!"
        
        # Get failure reason
        FAILURE_REASON=$(echo "$SERVICE_STATUS" | jq -r --arg id "$DEPLOYMENT_ID" '
            .deployments[] | select(.id == $id) | .failureDescription // "No failure description available"
        ')
        
        echo "Failure reason: $FAILURE_REASON"
        exit 1
    fi
    
    sleep 30
    ELAPSED=$((ELAPSED + 30))
done

echo "Deployment timeout reached. Manual intervention may be required."
exit 1
```

### ECS Cluster Auto Scaling

```python
# ecs-autoscaling.py - Custom ECS cluster auto scaling based on metrics
import boto3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ECSAutoScaler:
    def __init__(self, region_name: str = 'us-west-2'):
        self.ecs_client = boto3.client('ecs', region_name=region_name)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=region_name)
        self.asg_client = boto3.client('autoscaling', region_name=region_name)
        
    def get_cluster_metrics(self, cluster_name: str) -> Dict:
        """Get comprehensive cluster metrics"""
        
        # Get cluster details
        cluster_info = self.ecs_client.describe_clusters(
            clusters=[cluster_name],
            include=['STATISTICS', 'CONFIGURATIONS']
        )['clusters'][0]
        
        # Get service information
        services = self.ecs_client.list_services(cluster=cluster_name)['serviceArns']
        service_details = []
        
        if services:
            service_info = self.ecs_client.describe_services(
                cluster=cluster_name,
                services=services
            )['services']
            
            for service in service_info:
                service_details.append({
                    'name': service['serviceName'],
                    'desired': service['desiredCount'],
                    'running': service['runningCount'],
                    'pending': service['pendingCount']
                })
        
        # Get CloudWatch metrics
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=10)
        
        cpu_utilization = self._get_metric_average(
            'AWS/ECS',
            'CPUUtilization',
            [{'Name': 'ClusterName', 'Value': cluster_name}],
            start_time,
            end_time
        )
        
        memory_utilization = self._get_metric_average(
            'AWS/ECS',
            'MemoryUtilization',
            [{'Name': 'ClusterName', 'Value': cluster_name}],
            start_time,
            end_time
        )
        
        return {
            'cluster_info': cluster_info,
            'services': service_details,
            'metrics': {
                'cpu_utilization': cpu_utilization,
                'memory_utilization': memory_utilization,
                'active_services': cluster_info['activeServicesCount'],
                'running_tasks': cluster_info['runningTasksCount'],
                'pending_tasks': cluster_info['pendingTasksCount'],
                'registered_instances': cluster_info['registeredContainerInstancesCount']
            }
        }
    
    def _get_metric_average(self, namespace: str, metric_name: str, 
                           dimensions: List[Dict], start_time: datetime, 
                           end_time: datetime) -> float:
        """Get average metric value over time period"""
        
        try:
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                Dimensions=dimensions,
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Average']
            )
            
            if response['Datapoints']:
                return sum(dp['Average'] for dp in response['Datapoints']) / len(response['Datapoints'])
            return 0.0
            
        except Exception as e:
            logger.error(f"Error getting metric {metric_name}: {e}")
            return 0.0
    
    def calculate_scaling_decision(self, cluster_metrics: Dict, 
                                 scaling_config: Dict) -> Dict:
        """Calculate scaling decision based on metrics and configuration"""
        
        metrics = cluster_metrics['metrics']
        cpu_util = metrics['cpu_utilization']
        memory_util = metrics['memory_utilization']
        
        # Get thresholds from config
        cpu_scale_up_threshold = scaling_config.get('cpu_scale_up_threshold', 70)
        cpu_scale_down_threshold = scaling_config.get('cpu_scale_down_threshold', 30)
        memory_scale_up_threshold = scaling_config.get('memory_scale_up_threshold', 80)
        memory_scale_down_threshold = scaling_config.get('memory_scale_down_threshold', 40)
        
        # Scaling logic
        scale_up_reasons = []
        scale_down_reasons = []
        
        if cpu_util > cpu_scale_up_threshold:
            scale_up_reasons.append(f"CPU utilization ({cpu_util:.1f}%) > {cpu_scale_up_threshold}%")
        elif cpu_util < cpu_scale_down_threshold:
            scale_down_reasons.append(f"CPU utilization ({cpu_util:.1f}%) < {cpu_scale_down_threshold}%")
        
        if memory_util > memory_scale_up_threshold:
            scale_up_reasons.append(f"Memory utilization ({memory_util:.1f}%) > {memory_scale_up_threshold}%")
        elif memory_util < memory_scale_down_threshold:
            scale_down_reasons.append(f"Memory utilization ({memory_util:.1f}%) < {memory_scale_down_threshold}%")
        
        # Determine final action
        if scale_up_reasons:
            action = 'scale_up'
            reasons = scale_up_reasons
        elif scale_down_reasons and not metrics['pending_tasks']:
            action = 'scale_down'
            reasons = scale_down_reasons
        else:
            action = 'no_change'
            reasons = ['Metrics within acceptable range']
        
        return {
            'action': action,
            'reasons': reasons,
            'current_metrics': {
                'cpu_utilization': cpu_util,
                'memory_utilization': memory_util,
                'running_tasks': metrics['running_tasks'],
                'pending_tasks': metrics['pending_tasks']
            }
        }
    
    def scale_cluster_capacity(self, cluster_name: str, capacity_provider: str, 
                              action: str, scaling_config: Dict) -> bool:
        """Scale cluster capacity using Auto Scaling Group"""
        
        try:
            # Get capacity provider details
            cp_response = self.ecs_client.describe_capacity_providers(
                capacityProviders=[capacity_provider]
            )
            
            if not cp_response['capacityProviders']:
                logger.error(f"Capacity provider {capacity_provider} not found")
                return False
            
            cp_config = cp_response['capacityProviders'][0]
            asg_arn = cp_config['autoScalingGroupProvider']['autoScalingGroupArn']
            asg_name = asg_arn.split('/')[-1]
            
            # Get current ASG configuration
            asg_response = self.asg_client.describe_auto_scaling_groups(
                AutoScalingGroupNames=[asg_name]
            )
            
            if not asg_response['AutoScalingGroups']:
                logger.error(f"Auto Scaling Group {asg_name} not found")
                return False
            
            asg = asg_response['AutoScalingGroups'][0]
            current_capacity = asg['DesiredCapacity']
            min_size = asg['MinSize']
            max_size = asg['MaxSize']
            
            # Calculate new capacity
            scale_increment = scaling_config.get('scale_increment', 1)
            
            if action == 'scale_up':
                new_capacity = min(current_capacity + scale_increment, max_size)
            elif action == 'scale_down':
                new_capacity = max(current_capacity - scale_increment, min_size)
            else:
                new_capacity = current_capacity
            
            if new_capacity == current_capacity:
                logger.info(f"No scaling needed. Current capacity: {current_capacity}")
                return True
            
            logger.info(f"Scaling {action}: {current_capacity} -> {new_capacity}")
            
            # Update ASG capacity
            self.asg_client.set_desired_capacity(
                AutoScalingGroupName=asg_name,
                DesiredCapacity=new_capacity,
                HonorCooldown=True
            )
            
            # Send CloudWatch metric
            self.cloudwatch_client.put_metric_data(
                Namespace='ECS/AutoScaling',
                MetricData=[
                    {
                        'MetricName': 'CapacityChange',
                        'Value': new_capacity - current_capacity,
                        'Unit': 'Count',
                        'Dimensions': [
                            {
                                'Name': 'ClusterName',
                                'Value': cluster_name
                            },
                            {
                                'Name': 'Action',
                                'Value': action
                            }
                        ]
                    }
                ]
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error scaling cluster capacity: {e}")
            return False
    
    def optimize_service_placement(self, cluster_name: str) -> Dict:
        """Optimize task placement across cluster instances"""
        
        services = self.ecs_client.list_services(cluster=cluster_name)['serviceArns']
        optimization_report = {
            'cluster': cluster_name,
            'services_analyzed': 0,
            'optimizations': [],
            'recommendations': []
        }
        
        if not services:
            return optimization_report
        
        service_details = self.ecs_client.describe_services(
            cluster=cluster_name,
            services=services
        )['services']
        
        for service in service_details:
            service_name = service['serviceName']
            optimization_report['services_analyzed'] += 1
            
            # Analyze task distribution
            tasks = self.ecs_client.list_tasks(
                cluster=cluster_name,
                serviceName=service_name
            )['taskArns']
            
            if tasks:
                task_details = self.ecs_client.describe_tasks(
                    cluster=cluster_name,
                    tasks=tasks
                )['tasks']
                
                # Count tasks per container instance
                instance_distribution = {}
                for task in task_details:
                    instance_arn = task.get('containerInstanceArn', 'fargate')
                    instance_distribution[instance_arn] = instance_distribution.get(instance_arn, 0) + 1
                
                # Check for uneven distribution
                if len(instance_distribution) > 1:
                    max_tasks = max(instance_distribution.values())
                    min_tasks = min(instance_distribution.values())
                    
                    if max_tasks - min_tasks > 1:
                        optimization_report['recommendations'].append({
                            'service': service_name,
                            'issue': 'Uneven task distribution',
                            'recommendation': 'Consider updating placement strategy',
                            'distribution': instance_distribution
                        })
        
        return optimization_report

def main():
    """Main auto scaling workflow"""
    
    cluster_name = 'production-web-cluster'
    capacity_provider = 'custom-capacity-provider'
    
    scaling_config = {
        'cpu_scale_up_threshold': 70,
        'cpu_scale_down_threshold': 30,
        'memory_scale_up_threshold': 80,
        'memory_scale_down_threshold': 40,
        'scale_increment': 2,
        'cooldown_period': 300
    }
    
    autoscaler = ECSAutoScaler()
    
    # Get cluster metrics
    logger.info(f"Analyzing cluster: {cluster_name}")
    cluster_metrics = autoscaler.get_cluster_metrics(cluster_name)
    
    # Calculate scaling decision
    scaling_decision = autoscaler.calculate_scaling_decision(cluster_metrics, scaling_config)
    
    logger.info(f"Scaling decision: {scaling_decision['action']}")
    for reason in scaling_decision['reasons']:
        logger.info(f"Reason: {reason}")
    
    # Execute scaling if needed
    if scaling_decision['action'] in ['scale_up', 'scale_down']:
        success = autoscaler.scale_cluster_capacity(
            cluster_name, 
            capacity_provider, 
            scaling_decision['action'], 
            scaling_config
        )
        
        if success:
            logger.info("Scaling operation completed successfully")
        else:
            logger.error("Scaling operation failed")
    
    # Generate optimization report
    optimization_report = autoscaler.optimize_service_placement(cluster_name)
    
    if optimization_report['recommendations']:
        logger.info("Service placement optimizations available:")
        for rec in optimization_report['recommendations']:
            logger.info(f"- {rec['service']}: {rec['recommendation']}")

if __name__ == "__main__":
    main()
```

### ECS Service Discovery and Load Balancing

```bash
#!/bin/bash
# setup-service-mesh.sh - Setup service discovery and load balancing for ECS

CLUSTER_NAME=$1
VPC_ID=$2
NAMESPACE_NAME=${3:-local}

if [ $# -lt 2 ]; then
    echo "Usage: $0 <cluster-name> <vpc-id> [namespace-name]"
    exit 1
fi

echo "Setting up service mesh for cluster: $CLUSTER_NAME"

# Create private DNS namespace for service discovery
echo "Creating service discovery namespace..."
NAMESPACE_ID=$(aws servicediscovery create-private-dns-namespace \
    --name $NAMESPACE_NAME \
    --vpc $VPC_ID \
    --description "Service discovery namespace for $CLUSTER_NAME" \
    --query 'OperationId' \
    --output text)

# Wait for namespace creation
echo "Waiting for namespace creation..."
while true; do
    OPERATION_STATUS=$(aws servicediscovery get-operation \
        --operation-id $NAMESPACE_ID \
        --query 'Operation.Status' \
        --output text)
    
    if [ "$OPERATION_STATUS" = "SUCCESS" ]; then
        NAMESPACE_ID=$(aws servicediscovery get-operation \
            --operation-id $NAMESPACE_ID \
            --query 'Operation.Targets.NAMESPACE' \
            --output text)
        echo "Namespace created: $NAMESPACE_ID"
        break
    elif [ "$OPERATION_STATUS" = "FAIL" ]; then
        echo "Failed to create namespace"
        exit 1
    fi
    
    sleep 10
done

# Create Application Load Balancer
echo "Creating Application Load Balancer..."
ALB_ARN=$(aws elbv2 create-load-balancer \
    --name ${CLUSTER_NAME}-alb \
    --subnets subnet-12345 subnet-67890 \
    --security-groups sg-abcdef123 \
    --scheme internet-facing \
    --type application \
    --ip-address-type ipv4 \
    --tags Key=Cluster,Value=$CLUSTER_NAME \
    --query 'LoadBalancers[0].LoadBalancerArn' \
    --output text)

echo "Load balancer created: $ALB_ARN"

# Create default listener with 404 response
aws elbv2 create-listener \
    --load-balancer-arn $ALB_ARN \
    --protocol HTTP \
    --port 80 \
    --default-actions Type=fixed-response,FixedResponseConfig='{MessageBody="Not Found",StatusCode="404",ContentType="text/plain"}'

# Create service discovery services and target groups for common services
SERVICES=("web-app" "api-service" "user-service" "notification-service")

for SERVICE in "${SERVICES[@]}"; do
    echo "Setting up service discovery and load balancing for: $SERVICE"
    
    # Create service discovery service
    SERVICE_REGISTRY_ARN=$(aws servicediscovery create-service \
        --name $SERVICE \
        --namespace-id $NAMESPACE_ID \
        --dns-config "NamespaceId=$NAMESPACE_ID,DnsRecords=[{Type=A,TTL=60}]" \
        --health-check-custom-config FailureThreshold=3 \
        --description "Service registry for $SERVICE" \
        --query 'Service.Arn' \
        --output text)
    
    echo "Service registry created for $SERVICE: $SERVICE_REGISTRY_ARN"
    
    # Create target group
    TARGET_GROUP_ARN=$(aws elbv2 create-target-group \
        --name ${SERVICE}-tg \
        --protocol HTTP \
        --port 8080 \
        --vpc-id $VPC_ID \
        --target-type ip \
        --health-check-path /health \
        --health-check-interval-seconds 30 \
        --health-check-timeout-seconds 5 \
        --healthy-threshold-count 2 \
        --unhealthy-threshold-count 3 \
        --matcher HttpCode=200 \
        --tags Key=Service,Value=$SERVICE Key=Cluster,Value=$CLUSTER_NAME \
        --query 'TargetGroups[0].TargetGroupArn' \
        --output text)
    
    echo "Target group created for $SERVICE: $TARGET_GROUP_ARN"
    
    # Create listener rule for the service
    PRIORITY=$((10 + ${#SERVICE}))  # Simple priority calculation
    
    aws elbv2 create-rule \
        --listener-arn $(aws elbv2 describe-listeners --load-balancer-arn $ALB_ARN --query 'Listeners[0].ListenerArn' --output text) \
        --priority $PRIORITY \
        --conditions Field=path-pattern,Values=/${SERVICE}/* \
        --actions Type=forward,TargetGroupArn=$TARGET_GROUP_ARN
    
    # Create sample ECS service configuration file
    cat > ${SERVICE}-service-config.json << EOF
{
  "cluster": "$CLUSTER_NAME",
  "serviceName": "$SERVICE",
  "taskDefinition": "${SERVICE}:1",
  "desiredCount": 2,
  "capacityProviderStrategy": [
    {
      "capacityProvider": "FARGATE",
      "weight": 1
    }
  ],
  "networkConfiguration": {
    "awsvpcConfiguration": {
      "subnets": ["subnet-12345", "subnet-67890"],
      "securityGroups": ["sg-abcdef123"],
      "assignPublicIp": "DISABLED"
    }
  },
  "loadBalancers": [
    {
      "targetGroupArn": "$TARGET_GROUP_ARN",
      "containerName": "${SERVICE}-container",
      "containerPort": 8080
    }
  ],
  "serviceRegistries": [
    {
      "registryArn": "$SERVICE_REGISTRY_ARN",
      "containerName": "${SERVICE}-container"
    }
  ],
  "deploymentConfiguration": {
    "maximumPercent": 200,
    "minimumHealthyPercent": 50,
    "deploymentCircuitBreaker": {
      "enable": true,
      "rollback": true
    }
  }
}
EOF
    
    echo "Service configuration saved to: ${SERVICE}-service-config.json"
done

# Output DNS configuration for applications
echo ""
echo "=== Service Discovery Configuration ==="
echo "Namespace: $NAMESPACE_NAME"
echo "Service endpoints:"
for SERVICE in "${SERVICES[@]}"; do
    echo "  $SERVICE: ${SERVICE}.${NAMESPACE_NAME}"
done

echo ""
echo "=== Load Balancer Configuration ==="
ALB_DNS=$(aws elbv2 describe-load-balancers \
    --load-balancer-arns $ALB_ARN \
    --query 'LoadBalancers[0].DNSName' \
    --output text)

echo "Load Balancer DNS: $ALB_DNS"
echo "Service endpoints:"
for SERVICE in "${SERVICES[@]}"; do
    echo "  $SERVICE: http://${ALB_DNS}/${SERVICE}/"
done

echo ""
echo "Setup completed successfully!"
echo "Use the generated *-service-config.json files to create your ECS services."
```

## Monitoring & Observability

### CloudWatch Container Insights
```bash
# Enable Container Insights at cluster level
aws ecs put-cluster-capacity-providers \
  --cluster production-cluster \
  --settings name=containerInsights,value=enabled

# Create custom CloudWatch dashboard
aws cloudwatch put-dashboard \
  --dashboard-name ECS-Production-Dashboard \
  --dashboard-body file://ecs-dashboard.json
```

### Custom Metrics and Alarms
```python
def setup_ecs_monitoring(cluster_name, service_name):
    cloudwatch = boto3.client('cloudwatch')
    
    # Create alarm for service CPU utilization
    cloudwatch.put_metric_alarm(
        AlarmName=f'{service_name}-HighCPU',
        ComparisonOperator='GreaterThanThreshold',
        EvaluationPeriods=2,
        MetricName='CPUUtilization',
        Namespace='AWS/ECS',
        Period=300,
        Statistic='Average',
        Threshold=80.0,
        ActionsEnabled=True,
        AlarmActions=['arn:aws:sns:region:account:ecs-alerts'],
        AlarmDescription=f'High CPU utilization for {service_name}',
        Dimensions=[
            {'Name': 'ServiceName', 'Value': service_name},
            {'Name': 'ClusterName', 'Value': cluster_name}
        ]
    )
    
    # Create alarm for service task count
    cloudwatch.put_metric_alarm(
        AlarmName=f'{service_name}-TaskCount',
        ComparisonOperator='LessThanThreshold',
        EvaluationPeriods=1,
        MetricName='RunningTaskCount',
        Namespace='AWS/ECS',
        Period=60,
        Statistic='Average',
        Threshold=1.0,
        ActionsEnabled=True,
        AlarmActions=['arn:aws:sns:region:account:ecs-alerts'],
        AlarmDescription=f'No running tasks for {service_name}'
    )
```

## Security & Compliance

### IAM Roles and Policies
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:region:account:secret:prod/*"
    }
  ]
}
```

### Network Security Configuration
```bash
# Create security group with least privilege
aws ec2 create-security-group \
  --group-name ecs-secure-tasks \
  --description "Secure ECS task security group" \
  --vpc-id vpc-12345678

# Allow inbound only from ALB
aws ec2 authorize-security-group-ingress \
  --group-id sg-ecs123 \
  --protocol tcp \
  --port 8080 \
  --source-group sg-alb456

# Allow outbound HTTPS for API calls
aws ec2 authorize-security-group-egress \
  --group-id sg-ecs123 \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0
```

### Task Definition Security
```python
def create_secure_task_definition(service_name, config):
    """Create task definition with security best practices"""
    
    task_definition = {
        "family": service_name,
        "networkMode": "awsvpc",
        "requiresCompatibilities": ["FARGATE"],
        "cpu": "512",
        "memory": "1024",
        "executionRoleArn": f"arn:aws:iam::{account_id}:role/ecsTaskExecutionRole",
        "taskRoleArn": f"arn:aws:iam::{account_id}:role/{service_name}TaskRole",
        "containerDefinitions": [{
            "name": f"{service_name}-container",
            "image": config['image_uri'],
            "essential": True,
            "readonlyRootFilesystem": True,
            "user": "1000:1000",  # Non-root user
            "portMappings": [{
                "containerPort": config.get('port', 8080),
                "protocol": "tcp"
            }],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": f"/ecs/{service_name}",
                    "awslogs-region": "us-west-2",
                    "awslogs-stream-prefix": "ecs"
                }
            },
            "secrets": [{
                "name": "DB_PASSWORD",
                "valueFrom": f"arn:aws:secretsmanager:us-west-2:{account_id}:secret:prod/{service_name}/db:password::"
            }],
            "healthCheck": {
                "command": ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"],
                "interval": 30,
                "timeout": 5,
                "retries": 3,
                "startPeriod": 60
            }
        }]
    }
    
    return task_definition
```

## Cost Optimization

### Fargate vs EC2 Cost Analysis
```python
class ECSCostOptimizer:
    def __init__(self):
        self.ecs = boto3.client('ecs')
        self.pricing = boto3.client('pricing', region_name='us-east-1')
        self.cloudwatch = boto3.client('cloudwatch')
    
    def analyze_service_costs(self, cluster_name, service_name, days=30):
        """Analyze ECS service costs and provide optimization recommendations"""
        
        # Get service details
        service = self.ecs.describe_services(
            cluster=cluster_name,
            services=[service_name]
        )['services'][0]
        
        task_definition_arn = service['taskDefinition']
        task_def = self.ecs.describe_task_definition(
            taskDefinition=task_definition_arn
        )['taskDefinition']
        
        # Extract resource requirements
        cpu = int(task_def['cpu'])
        memory = int(task_def['memory'])
        
        # Get historical metrics
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        cpu_utilization = self._get_average_metric(
            'AWS/ECS', 'CPUUtilization', 
            cluster_name, service_name, 
            start_time, end_time
        )
        
        memory_utilization = self._get_average_metric(
            'AWS/ECS', 'MemoryUtilization',
            cluster_name, service_name,
            start_time, end_time
        )
        
        # Calculate current cost (simplified Fargate pricing)
        hourly_cost = self._calculate_fargate_cost(cpu, memory)
        monthly_cost = hourly_cost * 24 * 30
        
        # Optimization recommendations
        recommendations = []
        
        if cpu_utilization < 20:
            recommended_cpu = max(256, cpu // 2)
            potential_savings = self._calculate_fargate_cost(cpu - recommended_cpu, memory) * 24 * 30
            recommendations.append({
                'type': 'cpu_optimization',
                'current_cpu': cpu,
                'recommended_cpu': recommended_cpu,
                'potential_monthly_savings': potential_savings
            })
        
        if memory_utilization < 30:
            recommended_memory = max(512, memory // 2)
            potential_savings = self._calculate_fargate_cost(cpu, memory - recommended_memory) * 24 * 30
            recommendations.append({
                'type': 'memory_optimization',
                'current_memory': memory,
                'recommended_memory': recommended_memory,
                'potential_monthly_savings': potential_savings
            })
        
        # Spot instance recommendation
        if self._is_fault_tolerant_workload(service_name):
            spot_savings = monthly_cost * 0.7  # ~70% savings with Spot
            recommendations.append({
                'type': 'fargate_spot',
                'potential_monthly_savings': spot_savings,
                'recommendation': 'Consider using Fargate Spot for fault-tolerant workloads'
            })
        
        return {
            'service': service_name,
            'current_monthly_cost': monthly_cost,
            'cpu_utilization': cpu_utilization,
            'memory_utilization': memory_utilization,
            'recommendations': recommendations,
            'total_potential_savings': sum(r.get('potential_monthly_savings', 0) for r in recommendations)
        }
```

### Resource Right-Sizing Automation
```bash
#!/bin/bash
# ecs-cost-optimize.sh - Automated ECS cost optimization

CLUSTER_NAME=$1
SERVICE_NAME=$2
ENVIRONMENT=${3:-production}

if [ $# -lt 2 ]; then
    echo "Usage: $0 <cluster-name> <service-name> [environment]"
    exit 1
fi

echo "Analyzing cost optimization opportunities for ${SERVICE_NAME}"

# Get current task definition
TASK_DEF_ARN=$(aws ecs describe-services \
    --cluster ${CLUSTER_NAME} \
    --services ${SERVICE_NAME} \
    --query 'services[0].taskDefinition' \
    --output text)

TASK_DEF=$(aws ecs describe-task-definition \
    --task-definition ${TASK_DEF_ARN} \
    --query 'taskDefinition')

CURRENT_CPU=$(echo "$TASK_DEF" | jq -r '.cpu')
CURRENT_MEMORY=$(echo "$TASK_DEF" | jq -r '.memory')

echo "Current resources: ${CURRENT_CPU} CPU, ${CURRENT_MEMORY} MB memory"

# Get utilization metrics from CloudWatch
CPU_UTIL=$(aws cloudwatch get-metric-statistics \
    --namespace AWS/ECS \
    --metric-name CPUUtilization \
    --dimensions Name=ServiceName,Value=${SERVICE_NAME} Name=ClusterName,Value=${CLUSTER_NAME} \
    --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 3600 \
    --statistics Average \
    --query 'Datapoints[].Average' \
    --output text | awk '{sum+=$1; count++} END {if(count>0) print sum/count; else print 0}')

MEMORY_UTIL=$(aws cloudwatch get-metric-statistics \
    --namespace AWS/ECS \
    --metric-name MemoryUtilization \
    --dimensions Name=ServiceName,Value=${SERVICE_NAME} Name=ClusterName,Value=${CLUSTER_NAME} \
    --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 3600 \
    --statistics Average \
    --query 'Datapoints[].Average' \
    --output text | awk '{sum+=$1; count++} END {if(count>0) print sum/count; else print 0}')

echo "Average utilization: ${CPU_UTIL}% CPU, ${MEMORY_UTIL}% memory"

# Calculate optimization recommendations
OPTIMIZED=false

# CPU optimization
if (( $(echo "$CPU_UTIL < 30" | bc -l) )); then
    NEW_CPU=$((CURRENT_CPU / 2))
    if [ $NEW_CPU -lt 256 ]; then
        NEW_CPU=256
    fi
    echo "Recommendation: Reduce CPU from ${CURRENT_CPU} to ${NEW_CPU}"
    OPTIMIZED=true
else
    NEW_CPU=$CURRENT_CPU
fi

# Memory optimization  
if (( $(echo "$MEMORY_UTIL < 40" | bc -l) )); then
    NEW_MEMORY=$((CURRENT_MEMORY / 2))
    if [ $NEW_MEMORY -lt 512 ]; then
        NEW_MEMORY=512
    fi
    echo "Recommendation: Reduce memory from ${CURRENT_MEMORY} to ${NEW_MEMORY}"
    OPTIMIZED=true
else
    NEW_MEMORY=$CURRENT_MEMORY
fi

if [ "$OPTIMIZED" = true ]; then
    # Create optimized task definition
    OPTIMIZED_TASK_DEF=$(echo "$TASK_DEF" | jq --arg cpu "$NEW_CPU" --arg memory "$NEW_MEMORY" '
        .cpu = $cpu | .memory = $memory |
        del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .registeredAt, .registeredBy)
    ')
    
    # Register new task definition
    NEW_TASK_DEF_ARN=$(aws ecs register-task-definition \
        --cli-input-json "$OPTIMIZED_TASK_DEF" \
        --query 'taskDefinition.taskDefinitionArn' \
        --output text)
    
    echo "Created optimized task definition: $NEW_TASK_DEF_ARN"
    
    if [ "$ENVIRONMENT" != "production" ]; then
        # Auto-update for non-production environments
        echo "Updating service with optimized task definition..."
        aws ecs update-service \
            --cluster ${CLUSTER_NAME} \
            --service ${SERVICE_NAME} \
            --task-definition ${NEW_TASK_DEF_ARN}
        
        echo "Service updated. Monitor performance and apply to production if successful."
    else
        echo "Production environment detected. Manual approval required."
        echo "To apply optimization:"
        echo "aws ecs update-service --cluster ${CLUSTER_NAME} --service ${SERVICE_NAME} --task-definition ${NEW_TASK_DEF_ARN}"
    fi
else
    echo "No optimization opportunities found. Current resource allocation appears optimal."
fi
```

## Automation & Infrastructure as Code

### CloudFormation Template
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Complete ECS Service with ALB and Service Discovery'

Parameters:
  ServiceName:
    Type: String
    Description: Name of the ECS service
  ImageURI:
    Type: String
    Description: Container image URI
  VpcId:
    Type: AWS::EC2::VPC::Id
    Description: VPC ID
  PrivateSubnets:
    Type: List<AWS::EC2::Subnet::Id>
    Description: Private subnet IDs
  PublicSubnets:
    Type: List<AWS::EC2::Subnet::Id>
    Description: Public subnet IDs

Resources:
  ECSCluster:
    Type: AWS::ECS::Cluster
    Properties:
      ClusterName: !Sub '${ServiceName}-cluster'
      CapacityProviders:
        - FARGATE
        - FARGATE_SPOT
      DefaultCapacityProviderStrategy:
        - CapacityProvider: FARGATE
          Weight: 1
        - CapacityProvider: FARGATE_SPOT
          Weight: 3
      ClusterSettings:
        - Name: containerInsights
          Value: enabled

  TaskDefinition:
    Type: AWS::ECS::TaskDefinition
    Properties:
      Family: !Ref ServiceName
      NetworkMode: awsvpc
      RequiresCompatibilities:
        - FARGATE
      Cpu: 512
      Memory: 1024
      ExecutionRoleArn: !Ref TaskExecutionRole
      TaskRoleArn: !Ref TaskRole
      ContainerDefinitions:
        - Name: !Sub '${ServiceName}-container'
          Image: !Ref ImageURI
          Essential: true
          PortMappings:
            - ContainerPort: 8080
              Protocol: tcp
          LogConfiguration:
            LogDriver: awslogs
            Options:
              awslogs-group: !Ref LogGroup
              awslogs-region: !Ref AWS::Region
              awslogs-stream-prefix: ecs
          HealthCheck:
            Command:
              - CMD-SHELL
              - 'curl -f http://localhost:8080/health || exit 1'
            Interval: 30
            Timeout: 5
            Retries: 3
            StartPeriod: 60

  ECSService:
    Type: AWS::ECS::Service
    DependsOn: ALBListener
    Properties:
      ServiceName: !Ref ServiceName
      Cluster: !Ref ECSCluster
      TaskDefinition: !Ref TaskDefinition
      DesiredCount: 2
      LaunchType: FARGATE
      NetworkConfiguration:
        AwsvpcConfiguration:
          SecurityGroups:
            - !Ref TaskSecurityGroup
          Subnets: !Ref PrivateSubnets
          AssignPublicIp: DISABLED
      LoadBalancers:
        - ContainerName: !Sub '${ServiceName}-container'
          ContainerPort: 8080
          TargetGroupArn: !Ref TargetGroup
      DeploymentConfiguration:
        MaximumPercent: 200
        MinimumHealthyPercent: 50
        DeploymentCircuitBreaker:
          Enable: true
          Rollback: true

  ApplicationLoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Name: !Sub '${ServiceName}-alb'
      Scheme: internet-facing
      Type: application
      SecurityGroups:
        - !Ref ALBSecurityGroup
      Subnets: !Ref PublicSubnets

  TargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      Name: !Sub '${ServiceName}-tg'
      Port: 8080
      Protocol: HTTP
      VpcId: !Ref VpcId
      TargetType: ip
      HealthCheckPath: /health
      HealthCheckIntervalSeconds: 30
      HealthCheckTimeoutSeconds: 5
      HealthyThresholdCount: 2
      UnhealthyThresholdCount: 3

  ALBListener:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      DefaultActions:
        - Type: forward
          TargetGroupArn: !Ref TargetGroup
      LoadBalancerArn: !Ref ApplicationLoadBalancer
      Port: 80
      Protocol: HTTP
```

### Terraform Configuration
```hcl
resource "aws_ecs_cluster" "app_cluster" {
  name = "${var.app_name}-cluster"

  capacity_providers = ["FARGATE", "FARGATE_SPOT"]
  
  default_capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight           = 1
  }
  
  default_capacity_provider_strategy {
    capacity_provider = "FARGATE_SPOT"
    weight           = 3
  }

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Environment = var.environment
    Application = var.app_name
  }
}

resource "aws_ecs_task_definition" "app_task" {
  family                   = var.app_name
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = aws_iam_role.task_execution_role.arn
  task_role_arn           = aws_iam_role.task_role.arn

  container_definitions = jsonencode([
    {
      name      = "${var.app_name}-container"
      image     = var.container_image
      essential = true
      
      portMappings = [
        {
          containerPort = var.container_port
          protocol      = "tcp"
        }
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.app_logs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
      
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:${var.container_port}/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])
}

resource "aws_ecs_service" "app_service" {
  name            = var.app_name
  cluster         = aws_ecs_cluster.app_cluster.id
  task_definition = aws_ecs_task_definition.app_task.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    security_groups  = [aws_security_group.ecs_tasks.id]
    subnets         = var.private_subnet_ids
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.app_tg.arn
    container_name   = "${var.app_name}-container"
    container_port   = var.container_port
  }

  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 50
    
    deployment_circuit_breaker {
      enable   = true
      rollback = true
    }
  }

  depends_on = [aws_lb_listener.app_listener]
}
```

## Troubleshooting & Operations

### Common Issues and Solutions

#### Task Launch Issues
```bash
# Check task definition issues
aws ecs describe-task-definition --task-definition myapp:1

# Check service events
aws ecs describe-services \
  --cluster production-cluster \
  --services web-app \
  --query 'services[0].events[:10]'

# Check task details and errors
aws ecs describe-tasks \
  --cluster production-cluster \
  --tasks $(aws ecs list-tasks --cluster production-cluster --service-name web-app --query 'taskArns[0]' --output text) \
  --query 'tasks[0].{LastStatus:lastStatus,StopReason:stoppedReason,Containers:containers[0].{Name:name,LastStatus:lastStatus,Reason:reason}}'
```

#### Service Connectivity Issues
```python
def diagnose_service_connectivity(cluster_name, service_name):
    """Diagnose ECS service connectivity issues"""
    
    ecs = boto3.client('ecs')
    ec2 = boto3.client('ec2')
    elbv2 = boto3.client('elbv2')
    
    # Get service details
    service = ecs.describe_services(
        cluster=cluster_name,
        services=[service_name]
    )['services'][0]
    
    # Get tasks
    tasks = ecs.list_tasks(
        cluster=cluster_name,
        serviceName=service_name
    )['taskArns']
    
    if not tasks:
        print("❌ No running tasks found")
        return
    
    task_details = ecs.describe_tasks(
        cluster=cluster_name,
        tasks=tasks
    )['tasks']
    
    print(f"✅ Service {service_name} has {len(task_details)} running tasks")
    
    # Check task networking
    for task in task_details:
        task_arn = task['taskArn']
        print(f"\n📋 Task: {task_arn.split('/')[-1]}")
        
        # Check ENI details
        for attachment in task.get('attachments', []):
            if attachment['type'] == 'ElasticNetworkInterface':
                eni_id = next(detail['value'] for detail in attachment['details'] 
                             if detail['name'] == 'networkInterfaceId')
                
                eni = ec2.describe_network_interfaces(
                    NetworkInterfaceIds=[eni_id]
                )['NetworkInterfaces'][0]
                
                print(f"  🔌 ENI: {eni_id}")
                print(f"  📍 Private IP: {eni['PrivateIpAddress']}")
                print(f"  🔒 Security Groups: {[sg['GroupId'] for sg in eni['Groups']]}")
                
                # Check if ENI is in correct subnet
                subnet_id = eni['SubnetId']
                subnet = ec2.describe_subnets(SubnetIds=[subnet_id])['Subnets'][0]
                print(f"  🌐 Subnet: {subnet_id} (AZ: {subnet['AvailabilityZone']})")
    
    # Check load balancer health
    if service.get('loadBalancers'):
        lb_config = service['loadBalancers'][0]
        tg_arn = lb_config['targetGroupArn']
        
        health = elbv2.describe_target_health(TargetGroupArn=tg_arn)
        healthy_count = sum(1 for target in health['TargetHealthDescriptions'] 
                          if target['TargetHealth']['State'] == 'healthy')
        
        print(f"\n🎯 Target Group Health: {healthy_count}/{len(health['TargetHealthDescriptions'])} healthy")
        
        for target in health['TargetHealthDescriptions']:
            state = target['TargetHealth']['State']
            reason = target['TargetHealth'].get('Reason', '')
            print(f"  Target {target['Target']['Id']}: {state} {reason}")
```

#### Performance Debugging
```bash
#!/bin/bash
# ecs-debug.sh - Debug ECS service performance issues

CLUSTER_NAME=$1
SERVICE_NAME=$2

if [ $# -lt 2 ]; then
    echo "Usage: $0 <cluster-name> <service-name>"
    exit 1
fi

echo "=== ECS Service Debug Report: ${SERVICE_NAME} ==="

# Service overview
echo "📊 Service Status:"
aws ecs describe-services \
  --cluster ${CLUSTER_NAME} \
  --services ${SERVICE_NAME} \
  --query 'services[0].{Status:status,Running:runningCount,Pending:pendingCount,Desired:desiredCount}'

# Recent service events
echo -e "\n📋 Recent Service Events:"
aws ecs describe-services \
  --cluster ${CLUSTER_NAME} \
  --services ${SERVICE_NAME} \
  --query 'services[0].events[:5].[createdAt,message]' \
  --output table

# Task analysis
echo -e "\n🔍 Task Analysis:"
TASKS=$(aws ecs list-tasks --cluster ${CLUSTER_NAME} --service-name ${SERVICE_NAME} --query 'taskArns' --output text)

for TASK in $TASKS; do
    echo "Task: $(basename $TASK)"
    
    # Task status
    aws ecs describe-tasks \
      --cluster ${CLUSTER_NAME} \
      --tasks $TASK \
      --query 'tasks[0].{LastStatus:lastStatus,HealthStatus:healthStatus,CPU:cpu,Memory:memory}' \
      --output table
    
    # Container status
    aws ecs describe-tasks \
      --cluster ${CLUSTER_NAME} \
      --tasks $TASK \
      --query 'tasks[0].containers[0].{Name:name,Status:lastStatus,Health:healthStatus,ExitCode:exitCode}' \
      --output table
done

# CloudWatch metrics
echo -e "\n📈 Performance Metrics (Last Hour):"
END_TIME=$(date -u +%Y-%m-%dT%H:%M:%S)
START_TIME=$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S)

echo "CPU Utilization:"
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=${SERVICE_NAME} Name=ClusterName,Value=${CLUSTER_NAME} \
  --start-time ${START_TIME} \
  --end-time ${END_TIME} \
  --period 3600 \
  --statistics Average,Maximum \
  --query 'Datapoints[0].{Average:Average,Maximum:Maximum}' \
  --output table

echo "Memory Utilization:"
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name MemoryUtilization \
  --dimensions Name=ServiceName,Value=${SERVICE_NAME} Name=ClusterName,Value=${CLUSTER_NAME} \
  --start-time ${START_TIME} \
  --end-time ${END_TIME} \
  --period 3600 \
  --statistics Average,Maximum \
  --query 'Datapoints[0].{Average:Average,Maximum:Maximum}' \
  --output table

# Load balancer health
echo -e "\n🎯 Load Balancer Health:"
TARGET_GROUP_ARN=$(aws ecs describe-services \
  --cluster ${CLUSTER_NAME} \
  --services ${SERVICE_NAME} \
  --query 'services[0].loadBalancers[0].targetGroupArn' \
  --output text)

if [ "$TARGET_GROUP_ARN" != "None" ]; then
    aws elbv2 describe-target-health \
      --target-group-arn ${TARGET_GROUP_ARN} \
      --query 'TargetHealthDescriptions[].{Target:Target.Id,Port:Target.Port,State:TargetHealth.State,Reason:TargetHealth.Reason}' \
      --output table
fi

echo -e "\n✅ Debug report completed"
```

## Best Practices

### Container and Task Optimization
- **Right-sizing:** Use appropriate CPU and memory allocation based on application needs
- **Health checks:** Implement comprehensive health checks for reliable service management
- **Graceful shutdown:** Handle SIGTERM signals properly for clean container shutdowns
- **Resource limits:** Set resource limits to prevent noisy neighbor problems

### Security Best Practices
- **Task roles:** Use least privilege IAM roles for tasks accessing AWS services
- **Network isolation:** Deploy tasks in private subnets with proper security group configuration
- **Secrets management:** Use AWS Secrets Manager or Parameter Store for sensitive data
- **Image scanning:** Enable ECR vulnerability scanning for container images

### Operational Excellence
- **Logging strategy:** Use structured logging with CloudWatch Logs integration
- **Monitoring:** Implement comprehensive monitoring with custom metrics and alarms
- **Service discovery:** Use AWS Cloud Map for internal service communication
- **Deployment strategies:** Implement blue-green or rolling deployments for zero downtime

### Cost Optimization
- **Fargate vs EC2:** Choose appropriate launch type based on workload characteristics
- **Spot instances:** Use Fargate Spot for fault-tolerant workloads
- **Auto Scaling:** Implement proper auto scaling for optimal resource utilization
- **Resource allocation:** Regularly review and optimize CPU and memory allocations

## Additional Resources

### AWS Documentation
- [Amazon ECS Developer Guide](https://docs.aws.amazon.com/ecs/latest/developerguide/)
- [ECS Task Definitions](https://docs.aws.amazon.com/ecs/latest/developerguide/task_definitions.html)
- [ECS Services](https://docs.aws.amazon.com/ecs/latest/developerguide/ecs_services.html)
- [AWS Fargate User Guide](https://docs.aws.amazon.com/ecs/latest/userguide/)

### Tools & SDKs
- **AWS CLI** - Command-line interface for ECS operations
- **ECS CLI** - Simplified interface for local development and testing
- **AWS SDKs** - Programmatic access to ECS APIs
- **Docker Compose** - Local development with ECS integration

### Container Orchestration
- **AWS Copilot** - Application-centric CLI for containerized apps
- **Amazon EKS** - Managed Kubernetes alternative
- **AWS App Runner** - Fully managed container service
- **AWS Batch** - Batch computing with containers

### Best Practices Guides
- [ECS Best Practices](https://docs.aws.amazon.com/ecs/latest/bestpracticesguide/)
- [Container Security Best Practices](https://aws.amazon.com/blogs/containers/)
- [ECS Cost Optimization](https://aws.amazon.com/blogs/containers/theoretical-cost-optimization/)
- [Blue-Green Deployments with ECS](https://aws.amazon.com/blogs/compute/bluegreen-deployments-with-amazon-ecs/)

### Community Resources
- **AWS Container Roadmap** - Public roadmap for container services
- **ECS Workshop** - Hands-on training materials
- **AWS re:Invent Sessions** - Deep-dive technical sessions
- **Container Blog** - Latest updates and best practices